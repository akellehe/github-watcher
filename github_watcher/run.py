#!/usr/bin/env python
import json
import logging
import subprocess
import os.path
import time
import sys

import unidiff
import requests
from pync import Notifier
import yaml
from github import Github


logger = logging.getLogger('github-watcher.run')

WATCHER_ALERT_LOG = '/tmp/watcher_alert.log'


class Noop(Exception): pass


def raise_value_error(parser, parameter_name):
    parser.print_help()
    raise ValueError("--{} is required for the check action".format(parameter_name))


def validate_args(parser):
    args = parser.parse_args()
    if args.repo is None:
        raise_value_error(parser, 'repo') 
    if args.user is None:
        raise_value_error(parser, 'user') 
    if args.filepath is None:
        raise_value_error(parser, 'filepath')


def read_access_token(parser):
    args = parser.parse_args()
    try:
        with open(args.access_token_file, 'rb') as github_auth_fp:
            return github_auth_fp.read().strip()
    except IOError as e:
        print "You must store your github access token at ~/.github." 
        print "  1. Go to your github site (e.g. github.com) and"
        print "  2. click your avatar in the top right then"
        print "  3. click Settings then"
        print "  4. click Personal access tokens on the left then"
        print "  5. Generate access token then"
        print "  6. click repo and user permissions checkboxes. next"
        print "  7. click Generate Token. "
        print "  8. SAVE THAT. copy/paste to ~/.github you will never see it again."
        sys.exit(1)


def get_cli_config(parser):
    validate_args(parser)
    args = parser.parse_args()
    return args.github_url, {
            'github_api_base_url': args.github_url or 'https://api.github.com',
        args.user: {
            args.repo: {
                args.filepath: [
                    [args.start, args.end]
                ]
            }
        }
    }


def get_file_config(parser):
    try:
        with open(os.path.join(os.path.expanduser('~'), 
            '.github-watcher.yml'), 'rb') as config:
            return yaml.load(config.read())
    except IOError as e:
        print "You must include a configuration of what to watch at ~/.github-watcher.yml"
        sys.exit(1)


def get_config(parser, action='run'):
    conf = {}

    if action != 'run':
        github_url, cli_config = get_cli_config(parser)
        if not github_url:
            del cli_config['github_api_base_url']
    conf.update(get_file_config(parser))
    if action != 'run':
        conf.update(cli_config) # CLI args override file settings

    return conf


def get_open_pull_requests(parser, user, repo):
    repo_name = '{}/{}'.format(user, repo)
    logger.info("getting open pull requests for repo name={}".format(repo_name))
    gh = Github(login_or_token=read_access_token(parser), 
            base_url=get_config(parser).get('github_api_base_url'))
    prs = gh.get_repo(repo_name).get_pulls(state='open')
    for pr in prs:
        yield pr


def get_diff(parser, pull_request):
    compare_url = get_config(parser).get('github_api_base_url') + \
        '/repos/{user}/{repo}/compare/{user}:{base_sha}...{head_user}:{head_sha}'.format(
            user=pull_request.base.user.login,
            repo=pull_request.base.repo.name,
            base_sha=pull_request.base.sha,
            head_user=pull_request.head.user.login,
            head_sha=pull_request.head.sha)

    headers = {'Authorization': 'token {}'.format(read_access_token(parser))}

    diff_json = requests.get(compare_url, headers=headers).json()
    diff_headers = "diff --git a/{filename} b/{filename}\n"
    diff_headers += "index foo..bar 100644\n"
    diff_headers += "--- a/{filename}\n"
    diff_headers += "+++ b/{filename}\n"
    diff = ""
    if not diff_json.get('files'):
        logger.info("Noop encountered: {}".format(pull_request.html_url))
        raise Noop("Pull request effects no files")

    for head_file in diff_json.get('files'):
        head_filename = head_file.get('filename')
        head_diff_headers = diff_headers.format(
                filename=head_filename)

        if head_file.get('patch') is None:
            msg = "Found a None patch. Deletion/Creation/Rename. "
            msg += "Adding only headers for {} in {}"
            msg = msg.format(head_filename, pull_request.html_url)
            logger.info(msg)
            continue
        diff += head_diff_headers + head_file.get('patch', '')
        diff += "\n"

    return diff


def get_watched_file(config, user, repo, hunk_path):
    paths = config.get(user, {}).get(repo, [])
    if not paths:
        return None
    for path in paths:
        if hunk_path == path:
            return path
    return None


def get_watched_directory(config, user, repo, hunk_path):
    paths = config.get(user, {}).get(repo, [])
    if not paths:
        return None
    for path in paths:
        if hunk_path.startswith(path):
            return path
    return None


def alert(user, repo, file, range, pr_link):
    msg = 'Found a PR effecting {file} {range}'.format(
	file=file,
	range=str(range))
    logger.info(msg)
    subprocess.call('say ' + msg, shell=True)
    Notifier.notify(
	msg,
	title='Github Watcher',
        open=pr_link)


def are_watched_lines(watchpaths, filepath, start, end):
    if filepath not in watchpaths:
        return False
    logger.info("Filepath: {}".format(filepath))
    logger.info("Watchpaths: {}".format(str(watchpaths[filepath])))
    for watched_start, watched_end in watchpaths[filepath]:
        if watched_start < start < watched_end:
            return True
        if watched_start < end < watched_end:
            return True
    return False


def alert_if_watched_changes(config, watchpaths, user, repo, patched_file, link, source_or_target='source'):
    filepath = getattr(patched_file, source_or_target + '_file')
    if filepath.startswith('a/') or filepath.startswith('b/'):
        filepath = filepath[2:]

    watched_directory = get_watched_directory(config, user, repo, filepath)
    if watched_directory and not already_alerted(link):
        alert(user, repo, watched_directory, '', link)
        mark_as_alerted(link)
        return True

    watched_file = get_watched_file(config, user, repo, filepath)
    if watched_file:
        for hunk in patched_file:
            start = getattr(hunk, source_or_target + '_start')
            offset = getattr(hunk, source_or_target + '_length')
            end = start + offset
            if are_watched_lines(watchpaths, filepath, start, end):
                if not already_alerted(link):

                    alert(user, repo, watched_file, (start, end), link)
                    mark_as_alerted(link)
                return True
    return False


def mark_as_alerted(pr_link):
    logger.info("Marking as alerted.")
    with open(WATCHER_ALERT_LOG, 'a+') as fp:
        fp.write(pr_link + '\n')


def already_alerted(pr_link):
    try:
        with open(WATCHER_ALERT_LOG, 'rb') as fp:
            alerted = fp.readlines()
            for line in alerted:
                if pr_link in line:
                    return True
    except IOError as e:
        pass
    return False


def check_config(parser, config):
    logger.info("check_config() running...")
    for user, repo_watchpaths in config.items():
        if not isinstance(repo_watchpaths, dict):
            continue # Not all configs are watchpaths
        logger.info("User: {}, repo_watchpaths: {}".format(user, repo_watchpaths))
        for repo, watchpaths in repo_watchpaths.items():
            open_prs = get_open_pull_requests(parser, user, repo)
            for open_pr in open_prs:
                link = open_pr.html_url
                try:
                    logger.info("Extracting diff and creating patchset. This is a hack.")
                    patchset = unidiff.PatchSet.from_string(get_diff(parser, open_pr))
                except Noop:
                    logger.info("Got a noop diff")
                    continue
                logger.info("Checking each file...")
                for patched_file in patchset:
                    logger.info("Checking {}/{}/{}".format(user, repo, patched_file.source_file))
                    if alert_if_watched_changes(config, watchpaths, user, repo, patched_file, link, 'source'):
                        continue
                    logger.info("Checking {}/{}/{}".format(user, repo, patched_file.target_file))
                    alert_if_watched_changes(config, watchpaths, user, repo, patched_file, link, 'target')

def main(parser):
    config = get_config(parser)
    while True:
        check_config(parser, config)
        logger.info("sleeping...")
        time.sleep(60 * 10) # 10 minutes
        logger.info("waking up!")

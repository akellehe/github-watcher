#!/usr/bin/env python
import logging
import subprocess
import time

import unidiff
from pync import Notifier

import github_watcher.settings as settings
import github_watcher.util as util
import github_watcher.commands.config as config
import github_watcher.services.git as git


def get_watched_file(conf, user, repo, hunk_path):
    paths = conf.get(user, {}).get(repo, [])
    if not paths:
        return None
    for path in paths:
        if hunk_path == path:
            return path
    return None


def get_watched_directory(conf, user, repo, hunk_path):
    paths = conf.get(user, {}).get(repo, [])
    if not paths:
        return None
    for path in paths:
        if hunk_path.startswith(path):
            return path
    return None


def alert(file, range, pr_link):
    msg = 'Found a PR effecting {file} {range}'.format(file=file, range=str(range))
    logging.info(msg)
    subprocess.call('say ' + msg, shell=True)
    Notifier.notify(msg, title='Github Watcher', open=pr_link)


def are_watched_lines(watchpaths, filepath, start, end):
    if filepath not in watchpaths:
        return False
    logging.info("Filepath: %s", filepath)
    logging.info("Watchpaths: %s", str(watchpaths[filepath]))
    for watched_start, watched_end in watchpaths[filepath]:
        if watched_start < start < watched_end:
            return True
        if watched_start < end < watched_end:
            return True
    return False


def alert_if_watched_changes(conf, watchpaths, user, repo, patched_file, link, source_or_target='source'):
    filepath = getattr(patched_file, source_or_target + '_file')
    if filepath.startswith('a/') or filepath.startswith('b/'):
        filepath = filepath[2:]

    watched_directory = get_watched_directory(conf, user, repo, filepath)
    if watched_directory and not already_alerted(link):
        alert(watched_directory, '', link)
        mark_as_alerted(link)
        return True

    watched_file = get_watched_file(conf, user, repo, filepath)
    if watched_file:
        for hunk in patched_file:
            start = getattr(hunk, source_or_target + '_start')
            offset = getattr(hunk, source_or_target + '_length')
            end = start + offset
            if are_watched_lines(watchpaths, filepath, start, end):
                if not already_alerted(link):

                    alert(watched_file, (start, end), link)
                    mark_as_alerted(link)
                return True
    return False


def mark_as_alerted(pr_link):
    logging.info("Marking as alerted.")
    with open(settings.WATCHER_ALERT_LOG, 'a+') as fp:
        fp.write(pr_link + '\n')


def already_alerted(pr_link):
    try:
        with open(settings.WATCHER_ALERT_LOG, 'rb') as fp:
            alerted = fp.readlines()
            for line in alerted:
                line = line.decode('utf-8')
                if pr_link in line:
                    return True
    except IOError as e:
        pass
    return False


def find_changes(parser, conf):
    logging.info("check_config() running...")
    base_url = conf.get('github_api_base_url')
    access_token = util.read_access_token(parser)
    for user, repo_watchpaths in list(conf.items()):
        if not isinstance(repo_watchpaths, dict):
            continue  # Not all configs are watchpaths
        logging.info("User: {}, repo_watchpaths: {}".format(user, repo_watchpaths))
        for repo, watchpaths in list(repo_watchpaths.items()):
            open_prs = git.open_pull_requests(base_url, access_token, user, repo)
            for open_pr in open_prs:
                link = open_pr.html_url
                try:
                    logging.info("Extracting diff and creating patchset. This is a hack.")
                    patchset = unidiff.PatchSet.from_string(git.diff(base_url, access_token, open_pr))
                except git.Noop:
                    logging.info("Got a noop diff")
                    continue
                logging.info("Checking each file...")
                for patched_file in patchset:
                    logging.info("Checking {}/{}/{}".format(user, repo, patched_file.source_file))
                    if alert_if_watched_changes(conf, watchpaths, user, repo, patched_file, link, 'source'):
                        continue
                    logging.info("Checking {}/{}/{}".format(user, repo, patched_file.target_file))
                    alert_if_watched_changes(conf, watchpaths, user, repo, patched_file, link, 'target')


def main(parser):
    conf = config.get_config(parser)
    while True:
        find_changes(parser, conf)
        logging.info("sleeping...")
        time.sleep(60 * 10) # 10 minutes
        logging.info("waking up!")

import logging
import json

from github import Github
import requests


class Noop(Exception): pass


def open_pull_requests(base_url, access_token, user, repo):
    repo_name = '{}/{}'.format(user, repo)
    logging.info("getting open pull requests for repo name={}".format(repo_name))
    gh = Github(access_token, base_url=base_url)
    prs = gh.get_repo(repo_name).get_pulls(state='open')
    for pr in prs:
        yield pr


def diff(base_url, access_token, pull_request):
    compare_url = base_url + \
                  '/repos/{user}/{repo}/compare/{user}:{base_sha}...{head_user}:{head_sha}'.format(
                      user=pull_request.base.user.login,
                      repo=pull_request.base.repo.name,
                      base_sha=pull_request.base.sha,
                      head_user=pull_request.head.user.login,
                      head_sha=pull_request.head.sha)

    headers = {'Authorization': 'token {}'.format(access_token)}
    logging.info("headers %s", json.dumps(headers))

    diff_json = requests.get(compare_url, headers=headers).json()
    logging.info("diff json %s", json.dumps(diff_json))
    diff_headers = "diff --git a/{filename} b/{filename}\n"
    diff_headers += "index foo..bar 100644\n"
    diff_headers += "--- a/{filename}\n"
    diff_headers += "+++ b/{filename}\n"
    diff = ""
    if not diff_json.get('files'):
        logging.info("Noop encountered: {}".format(pull_request.html_url))
        raise Noop("Pull request effects no files")

    for head_file in diff_json.get('files'):
        head_filename = head_file.get('filename')
        head_diff_headers = diff_headers.format(
            filename=head_filename)

        if head_file.get('patch') is None:
            msg = "Found a None patch. Deletion/Creation/Rename. "
            msg += "Adding only headers for {} in {}"
            msg = msg.format(head_filename, pull_request.html_url)
            logging.info(msg)
            continue
        diff += head_diff_headers + head_file.get('patch', '')
        diff += "\n"

    return diff

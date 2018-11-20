import logging
import json

from github import Github
import requests


class Noop(Exception): pass


def open_pull_requests(base_url, access_token, user, repo):
    repo_name = '{}/{}'.format(user, repo)
    logging.info("getting open pull requests for repo name={}".format(repo_name))
    logging.info("base_url=%s, access_token=%s, repo=%s", base_url, access_token, repo_name)
    gh = Github(access_token, base_url=base_url)
    repo = gh.get_repo(repo_name)
    pulls = repo.get_pulls(state='open')
    for pr in pulls:
        yield pr


def construct_compare_url(base_url, pull_request):
    return base_url + \
          '/repos/{user}/{repo}/compare/{user}:{base_sha}...{head_user}:{head_sha}'.format(
              user=pull_request.base.user.login,
              repo=pull_request.base.repo.name,
              base_sha=pull_request.base.sha,
              head_user=pull_request.head.user.login,
              head_sha=pull_request.head.sha)


def get_sentinel_diff_headers():
    diff_headers = "diff --git a/{filename} b/{filename}\n"
    diff_headers += "index foo..bar 100644\n"
    diff_headers += "--- a/{filename}\n"
    diff_headers += "+++ b/{filename}\n"
    return diff_headers


def diff(base_url, access_token, pull_request):
    compare_url = construct_compare_url(base_url, pull_request)
    headers = {'Authorization': 'token {}'.format(access_token)}

    diff_json = requests.get(compare_url, headers=headers).json()

    if not diff_json.get('files'):
        raise Noop("Pull request effects no files")

    complete_diff = ""
    diff_headers = get_sentinel_diff_headers()
    for head_file in diff_json.get('files'):
        head_filename = head_file.get('filename')
        head_diff_headers = diff_headers.format(filename=head_filename)

        # When a file is deleted, created, or renamed; the patch is None
        if head_file.get('patch') is None:
            continue

        complete_diff += head_diff_headers + head_file.get('patch', '')
        complete_diff += "\n"

    return complete_diff

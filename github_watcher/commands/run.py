#!/usr/bin/env python
import os
import logging
import subprocess
import time
import platform
import unidiff

import github_watcher.settings as settings
import github_watcher.util as util
import github_watcher.commands.config as config
import github_watcher.services.git as git

SYSTEM = platform.system()
if SYSTEM == 'Darwin':
    from pync import Notifier
if SYSTEM == 'Linux' and os.environ.get('TRAVIS') != 'true':
    import notify2


def is_watched_file(conf, user, repo, hunk_path):
    paths = conf.get(user, {}).get(repo, [])
    if not paths:
        return False
    for path in paths:
        if hunk_path == path:
            return True
    return False


def is_watched_directory(conf, user, repo, hunk_path):
    paths = conf.get(user, {}).get(repo, [])
    if not paths:
        return False
    for path in paths:
        if path.endswith('/') and hunk_path.startswith(path):
            return True
    return False


def alert(file, range, pr_link):
    msg = 'Found a PR effecting {file} {range}'.format(file=file, range=str(range))
    logging.info(msg)
    if SYSTEM == 'Darwin':
        subprocess.call('say ' + msg, shell=True)
        Notifier.notify(msg, title='Github Watcher', open=pr_link)
    elif SYSTEM == 'Linux' and os.environ.get('TRAVIS') != 'true':
        notify2.init(app_name='github-watcher')
        note = notify2.Notification(
            'Github Watcher', message=msg)
        note.show()
        time.sleep(5)
        note.close()



def are_watched_lines(watchpaths, filepath, start, end):
    if filepath not in watchpaths:
        return False
    if end < start:
        raise ValueError("Changed line ranges were out of order.")
    for watched_start, watched_end in watchpaths[filepath]:
        if start < watched_start and end < watched_start:
            return False
        if start > watched_end:
            return False
    return True


def alert_if_watched_changes(conf, user, repo, patched_file, link, source_or_target='source'):
    filepath = getattr(patched_file, source_or_target + '_file')
    if filepath.startswith('a/') or filepath.startswith('b/'):
        filepath = filepath[2:]

    if is_watched_directory(conf, user, repo, filepath) and not already_alerted(link):
        alert(filepath, '', link)
        mark_as_alerted(link)
        return True

    if is_watched_file(conf, user, repo, filepath):
        for hunk in patched_file:
            start = getattr(hunk, source_or_target + '_start')
            offset = getattr(hunk, source_or_target + '_length')
            end = start + offset
            if are_watched_lines(conf.get(user, {}).get(repo, {}), filepath, start, end):
                if not already_alerted(link):
                    alert(filepath, (start, end), link)
                    mark_as_alerted(link)
                return True
    return False


def mark_as_alerted(pr_link):
    with open(settings.WATCHER_ALERT_LOG, 'a+') as fp:
        fp.write(pr_link + '\n')
        fp.flush()


def already_alerted(pr_link):
    try:
        with open(settings.WATCHER_ALERT_LOG, 'rb') as fp:
            alerted = fp.readlines()
            for line in alerted:
                line = line.decode('utf-8')
                if pr_link in line:
                    return True
    except IOError:
        pass
    return False


def find_changes(conf):
    base_url = conf.get('github_api_base_url')
    access_token = util.read_access_token(conf)
    for user, repo_watchpaths in conf.items():
        if not isinstance(repo_watchpaths, dict):
            continue  # Not all configs are watchpaths
        for repo in repo_watchpaths.keys():
            open_prs = git.open_pull_requests(base_url, access_token, user, repo)
            for open_pr in open_prs:
                link = open_pr.html_url
                try:
                    patchset = unidiff.PatchSet.from_string(
                        git.diff(base_url, access_token, open_pr))
                except git.Noop:
                    continue
                for patched_file in patchset:
                    if alert_if_watched_changes(
                            conf, user, repo, patched_file, link, 'source'):
                        continue
                    alert_if_watched_changes(
                        conf, user, repo, patched_file, link, 'target')


def main(parser):
    conf = config.get_config(parser)
    while True:
        find_changes(conf)
        time.sleep(60 * 10) # 10 minutes

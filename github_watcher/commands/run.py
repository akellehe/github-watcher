#!/usr/bin/env python
"""
The Run Command Module
----------------------

This module contains the business logic for the `watch` functionality. It interprets configurations and evaluates files
against those configurations.

It also manages alerting on those files across Linux and Darwin systems.

"""
from typing import Dict, Tuple
import re
import os
import logging
import subprocess
import time
import platform
import unidiff

import github_watcher.settings as settings
import github_watcher.commands.config as config
import github_watcher.services.git as git

SYSTEM = platform.system()
if SYSTEM == 'Darwin':
    from pync import Notifier
if SYSTEM == 'Linux' and os.environ.get('TRAVIS') != 'true':
    import notify2


def is_watched_file(repo: config.Repo, hunk_path: str) -> config.Path or False:
    """
    Determines whether or not the file at `user/repo/hunk_path` is watched based on the configuration passed as `conf`.

    :param :py:class:`config.Repo` repo: The repo owned by `owner`, in which this file resides.
    :param str hunk_path: The relative path to the file to evaluate against `conf` in order to determine whether or not it is watched.
    :return: A boolean value specifying whether or not `hunk_path` is watched under `conf`.
    """
    if not repo or not repo.paths:
        return False
    for path in repo.paths:
        if hunk_path == path.path:
            return path
    return False


def is_watched_directory(repo: config.Repo, hunk_path: str) -> bool:
    """
    Determines whether or not the file at `user/repo/hunk_path` is watched based on whether or not it lies in a
    directory specified by `conf`

    :param :py:class:`config.Repo`: The repo owned by `owner`, in which this file resides.
    :param str hunk_path: The relative path to the file to evaluate against `conf` in order to determine whether or not it is watched.

    :return: A boolean value specifying whether or not `hunk_path` is watched under `conf`.
    """
    if not repo or not repo.paths:
        return False
    for path in repo.paths:
        if path.path.endswith('/') and hunk_path.startswith(path.path):
            return True
    return False


def contains_watched_regex(repo: config.Repo, blob: str) -> bool:
    """
    Searches a blob of text for a match to the regexes configured as the `watched_regexes` attribute of `conf`.

    :param :py:class:`config.Repo`: The repo for which `regexes` is configured.
    :param str blob: A blob of text to check for the regex.

    :rtype: bool
    :return: True if `blob` contains one of the configured regexes.
    """
    lines = blob.splitlines()
    for regex in repo.regexes:
        for line in lines:
            if re.search(regex, line):
                return True
    return False


def alert(file: str, range: Tuple[int, int], pr_link: str, silent=False) -> None:
    """
    Alerts that a file has been changed over range `range`. Also provides a link as supported by the target system.

    :param str file: The name of the file that has been changed.
    :param tuple range: The range over which the change coincides with the watcher configuration.
    :param str pr_link: A link to the pull request containing the change.
    :param bool silent: Whether or not to silence audio alerts.
    :return: None
    """
    msg = 'Found a PR effecting {file} {range}'.format(file=file, range=str(range))
    logging.info(msg)
    if SYSTEM == 'Darwin':
        if not silent:
            subprocess.call('say ' + msg, shell=True)
        Notifier.notify(msg, title='Github Watcher', open=pr_link)
    elif SYSTEM == 'Linux' and os.environ.get('TRAVIS') != 'true':
        notify2.init(app_name='github-watcher')
        note = notify2.Notification(
            'Github Watcher', message=msg)
        note.show()
        time.sleep(5)
        note.close()


def are_watched_lines(path: config.Path, start, end):
    if not path.ranges:
        return False
    if end < start:
        raise ValueError("Changed line ranges were out of order.")
    for watched in path.ranges:
        if start < watched.start and end < watched.start:
            return False
        if start > watched.end:
            return False
    return True


def alert_if_watched_changes(conf: config.Configuration, user: config.User, repo: config.Repo,
                             patched_file, link, diffstring, source_or_target='source'):
    filepath = getattr(patched_file, source_or_target + '_file')
    if filepath.startswith('a/') or filepath.startswith('b/'):
        filepath = filepath[2:]

    if already_alerted(link):
        return False

    if is_watched_directory(repo, filepath) or contains_watched_regex(repo, diffstring):
        alert(filepath, '', link)
        mark_as_alerted(link)
        return True

    path = is_watched_file(repo, filepath)
    if path:
        for hunk in patched_file:
            start = getattr(hunk, source_or_target + '_start')
            offset = getattr(hunk, source_or_target + '_length')
            end = start + offset
            if are_watched_lines(path, start, end):
                alert(filepath, (start, end), link, silent=conf.silent)
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
    for user in conf.users:
        for repo in user.repos:
            logging.info("Searching for pull requests in repo %s...", repo.name)
            open_prs = [pr for pr in git.open_pull_requests(user.base_url, user.token, user.name, repo.name)]
            logging.info("Found %s pull requests in %s", len(open_prs), repo.name)
            for open_pr in open_prs:
                link = open_pr.html_url
                logging.info("Checking link %s for overlaps in watched files...", link)
                try:
                    diffstring = git.diff(user.base_url, user.token, open_pr)
                    patchset = unidiff.PatchSet.from_string(diffstring)
                except git.Noop:
                    continue
                for patched_file in patchset:
                    if alert_if_watched_changes(
                            conf, user, repo, patched_file, link, diffstring, 'source'):
                        continue
                    if alert_if_watched_changes(
                        conf, user, repo, patched_file, link, diffstring, 'target'):
                        continue


def main(parser):
    conf = config.Configuration.from_file()
    conf.add_cli_options(parser.parse_args())
    while True:
        logging.info("Finding changes...")
        find_changes(conf)
        logging.info("Sleeping...")
        time.sleep(60 * 10) # 10 minutes

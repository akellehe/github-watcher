"""
This module implements methods to sanitize your code base. It automates some best practices such as

- Enforce users to fork rather than branching off the organization code base
- Close/delete branches and pull requests that match particular criteria
- Comment on branches that match certain criteria

The supported actions vary based on whether you're operating on a pull request or a branch.

+----------------+----------------+
| Branches       | Pull Requests  |
+================+================+
| Delete         | Close          |
+----------------+----------------+
|                | Comment        |
+----------------+----------------+

Available CLI arguments include

+----------------+----------------+---------+------------------------------------------------------------------+
| CLI Argument   | Argument       | Default | Description                                                      |
+================+================+=========+==================================================================+
| --older-than   | YYYY-MM-DD     | None    | Branches and pull requests last updated before this date will be |
|                |                |         | matched.                                                         |
+----------------+----------------+---------+------------------------------------------------------------------+
| --dry-run      | (none)         | False   | Will print out what would happen, but doesn't apply any changes. |
+----------------+----------------+---------+------------------------------------------------------------------+
| --close        | (none)         | False   | If passed; will close matched pull requests unless --dry-run is  |
|                |                |         | also passed.                                                     |
+----------------+----------------+---------+------------------------------------------------------------------+
| --delete       | (none)         | False   | If passed; will delete matched branches.                         |
+----------------+----------------+---------+------------------------------------------------------------------+
| --comment      | str            | ""      | If passed; will comment on matched pull requests with the        |
|                |                |         | argument passed.                                                 |
+----------------+----------------+---------+------------------------------------------------------------------+

"""

import logging
import datetime
import json

import github_watcher.services.git as git
import github_watcher.commands.config as config


def _datetime_strptime(string, _format):
    """
    Convenience function because datetime attributes are built-in and not patch-able
    """
    return datetime.datetime.strptime(string, _format)


def clean_branch(branch, opts):
    """
    Cleans the branch, `branch` based on the options passed by the user.

    :param github.Branch.Branch branch: The branch to clean.
    :param opts: User defined options (on the CLI) specifying how the branches should be cleaned.
    """
    logging.info('opts.comment %s, opts.delete %s', opts.comment, opts.delete)
    if opts.comment:
        logging.info('commenting. %s', opts.comment)
        git.comment(branch, message=opts.comment, dry_run=opts.dry_run)
    if opts.delete:
        logging.info('deleting')
        git.delete(branch, dry_run=opts.dry_run)


def clean_pull_request(pull_request, opts):
    """
    Cleans the pull request, `pull_request`, based on the options passed by the user.
    :param github.PullRequest.PullRequest pull_request: The pull request to clean.
    :param opts: The user defined options about how to clean this PR.
    """
    logging.info('opts.close %s, opts.comments %s', opts.close, opts.comment)
    if opts.close:
        logging.info('closing.')
        git.close(pull_request, dry_run=opts.dry_run)
    if opts.comment:
        logging.info('commenting %s', opts.comment)
        git.comment(pull_request, message=opts.comment, dry_run=opts.dry_run)


def too_old(entity, cutoff: str=None) -> bool:
    """
    Given a `cutoff`, determines whether the `entity` is too old. If so, it's triggered as a match.

    :param entity: A pull request or branch to decide whether or not it's too old.
    :type entity: github.PullRequest.PullRequest|github.Branch.Branch
    :param str cutoff: The YYYY-MM-DD formatted date at which to cut off entities.
    :return bool: True if the entity is too old.
    """
    min_birthday = _datetime_strptime(cutoff, "%Y-%m-%d")
    if git.get_last_updated(entity) < min_birthday:
        return True
    return False


def should_clean_pull_request(pull_request, opts):
    """
    Determines whether or not a pull request should be cleaned based on the user-defined criteria.

    :param github.PullRequest.PullRequest pull_request:
    :param opts: User defined options.
    :return: bool. True if the pull request should be cleaned.
    """
    if too_old(pull_request, opts.older_than):
        return True
    return False


def should_clean_branch(branch, opts):
    """
    Determines whether or not a branch should be cleaned based on the user-defined criteria.

    :param github.Branch.Branch branch:
    :param opts: User defined options.
    :return: bool. True if the pull request should be cleaned.
    """
    if too_old(branch, opts.older_than):
        return True
    return False


def main(parser):
    """
    Executes checks one time.
    """
    logging.info("Running clean...")
    conf = config.Configuration.from_file()
    opts = parser.parse_args()
    logging.info("Got configuration %s", json.dumps(conf.to_json()))
    for user in conf.users:
        logging.info("Getting repos for user %s", user.name)
        for repo in user.repos:
            logging.info("Checking repo %s, getting branches...", repo.name)
            branches = git.get_branches(user, repo)
            for branch in branches:
                logging.info("Checking branch %s", branch.name)
                if should_clean_branch(branch, opts):
                    logging.info("cleaning!")
                    clean_branch(branch, opts)

            logging.info("Getting open pull requests...")
            pull_requests = git.open_pull_requests(
                user.base_url, user.token, user.name, repo.name)
            for pull_request in pull_requests:
                logging.info("Checking pull request %s", pull_request.title)
                if should_clean_pull_request(pull_request, opts):
                    logging.info("Cleaning...")
                    clean_pull_request(pull_request, opts)


"""
The Config Command Module
-------------------------

This module defines configuration data structures and supporting business logic. For the sake of brevity, a complete
example configuration is

.. code-block:: yaml

    ---
    akellehe:
        github_watcher:
            paths:
                docs/: <null>,
                github_watcher/settings.py:
                    - [0, 1]
                    - [4, 5]
            base_url: 'https://api.gitub.com'
            token: '*****'
            regexes:
                - foo
                - bar

{'akellehe': {
    'github_watcher': {
        'paths': {
            'docs/': '<null>,',
            'github_watcher/settings.py': [[0, 1], [4, 5]]
        },
        'base_url': 'https://api.gitub.com',
        'token': '*****',
        'regexes': ['foo', 'bar']
        }
    }
}


If the configuration above doesn't answer your questions, more explanation is below.

Configurations are defined _per user_ (account) being watched. The `user` is the "top-level" configuration. Each user
can have many repositories.

The parameters in a repository are

+-----------+-----------+----------------------------------------------------------------------------------------------+
| parameter | type      | description                                                                                  |
+===========+===========+==============================================================================================+
| name      | str       | The name of the repository to watch. e.g. github_watcher                                     |
+-----------+-----------+----------------------------------------------------------------------------------------------+
| paths     | Dict      | Relative file/directory paths (from the root of the project) are the keys. Lists of lists    |
|           |           | containing line ranges are the value. If you pass a directory, you can just pass `null` as   |
|           |           | the line ranges.                                                                             |
+-----------+-----------+----------------------------------------------------------------------------------------------+
| regexes   | List[str] | A list of regexes for which to scan every pull request.                                      |
+-----------+-----------+----------------------------------------------------------------------------------------------+
| token     | str       | Your secret user token that grants `User` and `Repo` privileges on the target repository.    |
+-----------+-----------+----------------------------------------------------------------------------------------------+
| base_url  | str       | The base URL for the target github API. Defaults to https://api.gitub.com                    |
+-----------+-----------+----------------------------------------------------------------------------------------------+

"""

from typing import List, Dict
import collections
import logging

import yaml

import github_watcher.settings as settings


class Range:

    def __init__(self, start: float=float('-inf'), stop: float=float('inf')):
        self.start = start
        self.stop = stop


class Path:

    def __init__(self, path: str, ranges: List[Range]):
        self.path = path
        self.ranges = ranges


class Repo:

    def __init__(self, name: str, paths: List[Path], regexes: List[str],
                 token: str, base_url: str):
        self.name = name
        self.paths = paths
        self.regexes = regexes
        self.token = token
        self.base_url = base_url

    @classmethod
    def from_yml(cls, name, yml):
        paths = [
            Path(path=path,
                 ranges=[Range(start=r[0], stop=r[1])
                         for r in ranges if r] if ranges else [])
            for path, ranges in yml.get('paths', {}).items()]

        return Repo(
            name=name,
            paths=paths,
            base_url=yml.get('base_url', 'https://api.github.com'),
            token=yml.get('token'),
            regexes=yml.get('regexes')
        )


class User:

    def __init__(self, name: str, repos: List[Repo]):
        self.name = name
        self.repos = repos

    @classmethod
    def from_yml(cls, name, yml):
        return User(
            name=name,
            repos=[Repo.from_yml(name, repo) for name, repo in yml.items()]
        )


class Configuration:

    def __init__(self, users: List[User]):
        self.users = users

    @classmethod
    def from_yml(self, yml):
        return Configuration(
            users=[User.from_yml(name, user_conf) for name, user_conf in yml.items()]
        )


def nonempty_watch_path(args):
    if all([args.user, args.repo, args.filepath]):
        return True
    elif any([args.user, args.repo, args.filepath]):
        raise RuntimeError("If you pass any of --user, --repo, and --filepath you must pass all of them.")
    return False


def get_cli_config(parser):
    args = parser.parse_args()
    cli_config = {}
    if nonempty_watch_path(args):
        cli_config = {
            args.user: {
                args.repo: {
                    args.filepath: []}}}
        if args.start is not None and args.end is not None:
            cli_config[args.user][args.repo][args.filepath].append(
                [args.start, args.end])
    if args.github_url:
        cli_config['github_api_base_url'] = args.github_url
    if args.regex:
        cli_config['watched_regexes'] = [args.regex]
    if args.silent:
        cli_config['silent'] = True
    return cli_config


def get_file_config():
    try:
        with open(settings.WATCHER_CONFIG, 'rb') as config:
            return yaml.load(config.read().decode('utf-8'))
    except IOError as e:
        logging.warning("{} configuration file not found.".format(settings.WATCHER_CONFIG))
        return {}


def get_config(parser):
    conf = {}
    cli_config = get_cli_config(parser)
    file_config = get_file_config()
    if not cli_config and not file_config:
        raise RuntimeError("No configuration found.")

    conf['github_api_secret_token'] = file_config.get('github_api_secret_token')
    conf['github_api_base_url'] = file_config.get('github_api_base_url')

    if cli_config:
        conf.update(cli_config)
        return conf

    conf.update(file_config)
    conf.update(cli_config)  # CLI args override file settings

    return conf


def update(d, u):
    for k, v in list(u.items()):
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        elif isinstance(v, list) and k in d:
            d[k] += v
        else:
            d[k] = v
    return d


def get_line_range():
    line_start = input("What is the beginning of the line range you would like to watch in that file?\n(0) >> ")
    line_end = input("What is the end of the line range you would like to watch in that file?\n(infinity) >> ")
    return [int(line_start or 0), int(line_end or 10000000)]


def should_stop():
    another = input("Would you like to add another line range (y/n)?\n>> ") or "n"
    return another.startswith("n")


def get_project_metadata():
    username = input("What github username or company owns the project you would like to watch?\n>> ")
    project = input("What is the project name you would like to watch?\n>> ")
    filepath = input("What is the file path you would like to watch (directories must end with /)?\n>> ")
    while filepath.startswith("/"):
        filepath = input("No absolute file paths. Try again.\n>> ")
    return username, project, filepath


def display_configuration(config):
    print("=================================")
    print("Updated configuration:")
    print("")
    print((yaml.dump(config)))
    print("=================================")
    print("")


def get_api_base_url(config):
    base_url = config.get('github_api_base_url')
    if base_url:
        return base_url
    base_url = input("What is the base API url for your github site? (api.github.com)\n>> ")
    if base_url:
        return base_url
    return 'https://api.github.com'


def main(parser):
    try:
        config = get_config(parser)
    except RuntimeError:
        config = {}

    while True:
        username, project, filepath = get_project_metadata()
        line_ranges = None
        if not filepath.endswith("/"):
            line_ranges = []
            while True:
                line_ranges.append(get_line_range())
                if should_stop(): break
        config = update(config, {
            'github_api_base_url': get_api_base_url(config),
            username: {
                project: {
                    filepath: line_ranges
                }
            }
        })
        display_configuration(config)
        add_another_file = input("Would you like to add another (a), or quit (q)?\n(q) >> ") or "q"
        if add_another_file.startswith('q'):
            break
    write = input("Write the config (y/n)?\n(n) >> ")
    if write.startswith('y'):
        with open(settings.WATCHER_CONFIG, 'w+') as config_fp:
            config_fp.write(yaml.dump(config))
    if 'github_api_secret_token' not in config:
        print("You will need to add your `github_api_secret_token` to {}".format(settings.WATCHER_CONFIG))

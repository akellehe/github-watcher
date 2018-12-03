"""
Configuration
-------------------------

For the sake of brevity, a complete example configuration is

.. code-block:: yaml

    ---
    akellehe:
        base_url: 'https://api.gitub.com'
        token: '*****'
        repos:
            github_watcher:
                paths:
                    docs/: <null>,
                    github_watcher/settings.py:
                        - [0, 1]
                        - [4, 5]
                regexes:
                    - foo
                    - bar

If the configuration above doesn't answer your questions, more explanation is below.

Configurations are defined _per user_ (account) being watched. The :py:class:`github_watcher.commands.config.User` is
the "top-level" configuration. Each user can have many repositories.

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

from typing import List

import yaml

import github_watcher.settings as settings


class Range:

    def __init__(self, start: float=float('-inf'), end: float=float('inf')):
        self.start = start
        self.end = end

    def to_json(self):
        return [self.start, self.end]


class Path:

    def __init__(self, path: str, ranges: List[Range]):
        self.path = path
        self.ranges = ranges

    def to_json(self):
        return {
            self.path: [r.to_json() for r in self.ranges]
        }


class Repo:

    def __init__(self, name: str, paths: List[Path]=None, regexes: List[str]=None):
        self.name = name
        self.paths = paths
        self.regexes = regexes
        if paths is None:
            self.paths = []
        if regexes is None:
            self.regexes = []

    def to_json(self):
        paths = {}
        for p in self.paths:
            paths.update(p.to_json())
        return {
            self.name: {
                'paths': paths,
                'regexes': [r for r in self.regexes] if self.regexes else [],
            }
        }

    @classmethod
    def from_json(cls, name, yml):
        paths = [
            Path(path=path,
                 ranges=[Range(start=r[0], end=r[1])
                         for r in ranges if r] if ranges else [])
            for path, ranges in yml.get('paths', {}).items()]

        return Repo(
            name=name,
            paths=paths,
            regexes=yml.get('regexes')
        )


class User:

    def __init__(self, name: str, repos: List[Repo], token: str, base_url: str):
        self.name = name
        self.repos = repos
        self.token = token
        self.base_url = base_url

    def to_json(self):
        repos = {}
        for r in self.repos:
            repos.update(r.to_json())
        return {
            self.name: {
                'repos': repos,
                'token': self.token,
                'base_url': self.base_url
            }
        }

    @classmethod
    def from_json(cls, name, yml):
        return User(
            name=name,
            repos=[Repo.from_json(name, repo) for name, repo in yml.get('repos').items()],
            base_url=yml.get('base_url', 'https://api.github.com'),
            token=yml.get('token')
        )


class Configuration:

    def __init__(self, users: List[User], silent: bool=False, verbose: bool=False):
        self.users = users
        self.silent = silent
        self.verbose = verbose

    def to_json(self):
        users = {}
        for user in self.users:
            users.update(user.to_json())
        return users

    def append_ranges(self, source: List[Range], destination: List[Range]):
        for source_range in source:
            destination.append(source_range)

    def append_source_path_to_destination(self, source_path: Path, destination: List[Path]):
        for dest_path in destination:
            if source_path.path == dest_path.path:
                self.append_ranges(source_path.ranges, dest_path.ranges)
                return
        destination.append(source_path)

    def append_paths(self, source: List[Path], destination: List[Path]):
        for source_path in source:
            self.append_source_path_to_destination(source_path, destination)

    def append_repo(self, source: Repo, destination: List[Repo]):
        for dest in destination:
            if dest.name == source.name:
                self.append_paths(source.paths, dest.paths)
                return
        destination.append(source)

    def append_user(self, user):
        for u in self.users:
            if u.name == user.name:
                self.append_repo(user.repo, u.repos)

        self.users.append(user)


    def serialize(self):
        return yaml.dump(self.to_json(), default_flow_style=False)

    @classmethod
    def from_json(cls, yml):
        if not yml:
            raise RuntimeError("No configuration found.")
        return Configuration(
            users=[User.from_json(name, user_conf) for name, user_conf in yml.items()],
            silent=yml.get('silent', False),
            verbose=yml.get('verbose', False)
        )

    @classmethod
    def from_file(cls, filepath: str=None):
        if filepath is None:
            filepath = settings.WATCHER_CONFIG
        try:
            with open(filepath, 'rb') as config:
                return Configuration.from_json(yaml.load(config.read().decode('utf-8')))
        except IOError as e:
            raise RuntimeError("Config file not found <{}>".format(filepath))

    def add_cli_options(self, options):
        if not options:
            return
        if options.silent is not None:
            self.silent = options.silent
        if options.verbose is not None:
            self.verbose = options.verbose


def get_line_range():
    line_start = input("What is the beginning of the line range you would like to watch in that file?\n(0) >> ")
    line_end = input("What is the end of the line range you would like to watch in that file?\n(infinity) >> ")
    return [int(line_start or 0), int(line_end or 10000000)]


def should_end():
    another = input("Would you like to add another line range (y/n)?\n>> ") or "n"
    return another.startswith("n")


def get_project_metadata():
    username = input("What github username or company owns the project you would like to watch?\n>> ")
    project = input("What is the project name you would like to watch?\n>> ")
    filepath = input("What is the file path you would like to watch (directories must end with /)?\n>> ")
    while filepath.startswith("/"):
        filepath = input("No absolute file paths. Try again.\n>> ")
    return username, project, filepath


def get_api_base_url(username, config):
    for user in config.users:
        if user.name == username:
            return user.base_url
    base_url = input("What is the base API url for your github site? (api.github.com)\n>> ")
    if base_url:
        return base_url
    return 'https://api.github.com'


def main(parser):
    try:
        config = Configuration.from_file()
    except RuntimeError:
        config = Configuration(users=[])

    config.add_cli_options(parser)

    while True:
        username, project, filepath = get_project_metadata()
        line_ranges = None
        if not filepath.endswith("/"):
            line_ranges = []
            while True:
                line_ranges.append(get_line_range())
                if should_end(): break

        config.append_user(User(
            name=username,
            base_url=get_api_base_url(username, config),
            token='',
            repos=[Repo(name=project,
                        regexes=[],
                        paths=[Path(
                            path=filepath,
                            ranges=[Range(start, end) for start, end in line_ranges])])]))

        add_another_file = input("Would you like to add another (a), or quit (q)?\n(q) >> ") or "q"
        if add_another_file.startswith('q'):
            break
    print(config.serialize())
    write = input("Write the config (y/n)?\n(n) >> ")
    if write.startswith('y'):
        with open(settings.WATCHER_CONFIG, 'w+') as config_fp:
            config_fp.write(config.serialize())
    print("You will need to add your `token` to {}".format(settings.WATCHER_CONFIG))
    return config

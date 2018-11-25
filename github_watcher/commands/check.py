from github_watcher.commands.run import find_changes
from github_watcher.commands.config import get_config


def main(parser):
    find_changes(get_config(parser))

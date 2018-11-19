from github_watcher.commands.run import find_changes
from github_watcher.commands.config import get_cli_config


def main(parser):
    find_changes(parser, get_cli_config(parser)[1])

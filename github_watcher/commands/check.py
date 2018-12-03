from github_watcher.commands.run import find_changes
from github_watcher.commands.config import Configuration


def main(parser):
    conf = Configuration.from_file()
    conf.add_cli_options(parser.parse_args())
    find_changes(conf)

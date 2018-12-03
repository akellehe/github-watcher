import github_watcher.services.git as git
import github_watcher.settings as settings
import github_watcher.commands.config as config


def main(parser):
    conf = config.Configuration.from_file()
    cli_args = parser.parse_args()
    git.open_pull_requests(base_url=conf.)

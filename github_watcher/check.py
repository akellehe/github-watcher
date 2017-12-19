from github_watcher.run import check_config, get_cli_config 


def main(parser):
    check_config(parser, get_cli_config(parser)[1])

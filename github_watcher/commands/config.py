import collections
import json
import logging

import yaml

import github_watcher.settings as settings


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
    logging.info("get_config called.")
    cli_config = get_cli_config(parser)
    logging.info("Client config %s", json.dumps(cli_config))
    file_config = get_file_config()
    logging.info("File config %s", json.dumps(file_config))
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
    print("Getting input for apii base url")
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

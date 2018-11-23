import collections
import logging

import yaml

import github_watcher.settings as settings
import github_watcher.util as util


def get_cli_config(parser):
    util.validate_args(parser)
    args = parser.parse_args()
    return {
        'github_api_base_url': args.github_url or 'https://api.github.com',
        args.user: {
            args.repo: {
                args.filepath: [
                    [args.start, args.end]
                ]
            }
        }
    }


def get_file_config():
    try:
        with open(settings.WATCHER_CONFIG, 'rb') as config:
            return yaml.load(config.read().decode('utf-8'))
    except IOError as e:
        logging.warning("~/.github-watcher.yml configuration file not found.")
        return {}


def get_config(parser):
    conf = {}

    cli_config = get_cli_config(parser)
    file_config = get_file_config()
    if not cli_config and not file_config:
        raise SystemExit("No configuration found.")

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


def main(parser):
    config = get_config(parser)
    while True:
        username, project, filepath = get_project_metadata()
        line_ranges = None
        if not filepath.endswith("/"):
            line_ranges = []
            while True:
                line_ranges.append(get_line_range())
                if should_stop(): break
        config = update(config, {
            username: {
                project: {
                    filepath: line_ranges
                }
            }
        })
        print('display configuration', config)
        display_configuration(config)
        add_another_file = input("Would you like to add another (a), or quit (q)?\n(q) >> ") or "q"
        if add_another_file.startswith('q'):
            break
    write = input("Write the config (y/n)?\n(n) >> ")
    if write.startswith('y'):
        with open(settings.WATCHER_CONFIG, 'w+') as config_fp:
            config_fp.write(yaml.dump(config))


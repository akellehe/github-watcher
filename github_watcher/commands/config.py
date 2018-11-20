import collections
import sys
import logging

import yaml

import github_watcher.settings as settings
import github_watcher.util as util


def get_cli_config(parser):
    util.validate_args(parser)
    args = parser.parse_args()
    return args.github_url, {
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
        logging.info("You must include a configuration of what to watch at ~/.github-watcher.yml")
        sys.exit(1)


def get_config(parser, action='run'):
    conf = {}

    if action != 'run':
        github_url, cli_config = get_cli_config(parser)
        if not github_url:
            del cli_config['github_api_base_url']
    conf.update(get_file_config())
    if action != 'run':
        conf.update(cli_config) # CLI args override file settings

    return conf


@util.assert_string
def load_access_token(parser):
    try:
        return util.read_access_token(parser)
    except ValueError:
        return input("What is your personal github API token (with user and repo grants)? >> ").strip()


def load_previous_config():
    config = {}
    try:
        with open(settings.WATCHER_CONFIG, 'rb') as config_fp:
            config = yaml.load(config_fp.read().decode('utf-8'))
    finally:
        return config


def load_api_url(previous_config):
    if 'github_api_base_url' in previous_config:
        return previous_config.get('github_api_base_url')
    api_domain = input("What is your site domain?\n(api.github.com) >> ")
    if not api_domain:
        return "https://api.github.com"
    return "https://" + api_domain + "/api/v3"


def update(d, u):
    for k, v in list(u.items()):
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        elif isinstance(v, list) and k in d:
            d[k] += v
        else:
            d[k] = v
    return d


def main(parser):
    access_token = load_access_token(parser)
    config = load_previous_config()
    api_url = load_api_url(config)

    config['github_api_secret_token'] = access_token
    config['github_api_base_url'] = api_url

    while True:
        username = input("What github username or company owns the project you would like to watch?\n>> ")
        project = input("What is the project name you would like to watch?\n>> ")
        filepath = input("What is the file path you would like to watch (directories must end with /)?\n>> ")
        if filepath.startswith("/"):
            filepath = input("No absolute file paths. Try again.\n>> ")
        if not filepath.endswith("/"):
            line_ranges = []
            while True:
                line_start = input("What is the beginning of the line range you would like to watch in that file?\n(0) >> ")
                line_end = input("What is the end of the line range you would like to watch in that file?\n(infinity) >> ")
                line_range = [int(line_start or 0), int(line_end or 10000000)]
                line_ranges.append(line_range)
                another = input("Would you like to add another line range (y/n)?\n>> ") or "n"
                if another.startswith("n"):
                    break
        else:
            line_ranges = None

        config = update(config, {
            username: {
                project: {
                    filepath: line_ranges
                }
            }
        })

        print("=================================")
        print("Updated configuration:")
        print("")
        print((yaml.dump(config)))
        print("=================================")
        print("")

        add_another_file = input("Would you like to add another (a), or quit (q)?\n(q) >> ") or "q"
        if add_another_file.startswith('q'):
            break

    write = input("Write the config (y/n)?\n(n) >> ")
    if write.startswith('y'):
        with open(settings.WATCHER_CONFIG, 'w+') as config_fp:
            config_fp.write(yaml.dump(config))

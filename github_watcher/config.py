import os
import collections
import logging

import yaml


HOME = os.path.expanduser('~')
WATCHER_CONFIG = os.path.join(HOME, '.github-watcher.yml')
TOKEN_CONFIG = os.path.join(HOME, ".github")

def main(conf):
    try:
        with open(TOKEN_CONFIG, "rb") as fp:
            api_token = fp.read().strip()
    except IOError:
        api_token = None

    if not api_token:
        api_token = input("What is your personal github API token (with user and repo grants)?").strip()
        try:
            with open(TOKEN_CONFIG, 'w+') as token_fp:
               token_fp.write(api_token)
        except IOError:
            logging.info("Couldn't open your token file. Make sure it's writeable at ~/.github")
        except:
            logging.info("You must store your github access token at ~/.github.") 
            logging.info("  1. Go to your github site (e.g. github.com) and")
            logging.info("  2. click your avatar in the top right then")
            logging.info("  3. click Settings then")
            logging.info("  4. click Personal access tokens on the left then")
            logging.info("  5. Generate access token then")
            logging.info("  6. click repo and user permissions checkboxes. next")
            logging.info("  7. click Generate Token. ")
            logging.info("  8. SAVE THAT. copy/paste to ~/.github you will never see it again.")

    try:
        with open(WATCHER_CONFIG, 'rb') as config_fp:
            config = yaml.load(config_fp.read())
    except IOError:
        config = {}

    logging.info("Starting with config")
    logging.info("")
    logging.info((yaml.dump(config)))
    logging.info("")

    api_domain = input("What is your site domain?\n(api.github.com) >> ")
    if not api_domain:
        api_url = "https://api.github.com"
    else:
        api_url = "https://" + api_domain + "/api/v3"

    if 'github_api_base_url' in config:
        overwrite = input("Ok to overwrite {} with {} (y/n)?\n(n) >> ".format(config.get('github_api_base_url'), api_url))
        if overwrite.startswith('y'):
            config['github_api_base_url'] = api_url

    def update(d, u):
        for k, v in list(u.items()):
            if isinstance(v, collections.Mapping):
                d[k] = update(d.get(k, {}), v)
            elif isinstance(v, list) and k in d:
                d[k] += v
            else:
                d[k] = v
        return d

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

        logging.info("=================================")
        logging.info("Updated configuration:")
        logging.info("")
        logging.info((yaml.dump(config)))
        logging.info("=================================")
        logging.info("")
        add_another_file = input("Would you like to add another (a), or quit (q)?\n(q) >> ") or q
        if add_another_file.startswith('q'):
            break

    write = input("Write the config (y/n)?\n(n) >> ")
    if write.startswith('y'):
        try:
            with open(WATCHER_CONFIG, 'w+') as config_fp:
                config_fp.write(yaml.dump(config))
        except IOError:
            logging.info("Permission denied.")

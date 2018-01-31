import os
import collections
import logging

import yaml


logger = logging.getLogger('github-watcher.config')

HOME = os.path.expanduser('~')
WATCHER_CONFIG = os.path.join(HOME, '.github-watcher.yml')
TOKEN_CONFIG = os.path.join(HOME, ".github")
TOKEN_FAILURE_MESSAGE = """
You must store your github access token at ~/.github.\n 
  1. Go to your github site (e.g. github.com) and\n
  2. click your avatar in the top right then\n
  3. click Settings then\n
  4. click Personal access tokens on the left then\n
  5. Generate access token then\n
  6. click repo and user permissions checkboxes. next\n
  7. click Generate Token. \n
  8. SAVE THAT. copy/paste to ~/.github you will never see it again.\n
"""


def update(d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        elif isinstance(v, list):
            d[k] += v
        else:
            d[k] = v
    return d


def get_base_config():
    try:
        with open(TOKEN_CONFIG, "rb") as fp:
            api_token = fp.read().strip()
    except IOError:
        api_token = None

    if not api_token:
        api_token = raw_input("What is your personal github API token (with user and repo grants)?").strip()
        try:
            with open(TOKEN_CONFIG, 'w+') as token_fp:
               token_fp.write(api_token)
        except IOError:
            logger.error("Couldn't open your token file. Make sure it's writeable at ~/.github")
        except:
            logger.error(TOKEN_FAILURE_MESSAGE)

    try:
        with open(WATCHER_CONFIG, 'rb') as config_fp:
            config = yaml.load(config_fp.read())
    except IOError:
        config = {}

    logger.info("Starting with config\n")
    logger.info(yaml.dump(config))
    logger.info("\n")

    return api_token, config


def get_github_api_base_url(config):
    api_url = "https://api.github.com"
    if 'github_api_base_url' not in config:
        api_domain = raw_input("What is your site domain?\n(api.github.com) >> ")
        if api_domain:
            api_url = "https://" + api_domain + "/api/v3"


def prompt_for_project_path():
    username = raw_input("What github username or company owns the project you would like to watch?\n>> ")
    project = raw_input("What is the project name you would like to watch?\n>> ")
    return username, project


def prompt_for_filepath():
    filepath = raw_input("What is the file path you would like to watch (directories must end with /)?\n>> ")
    if filepath.startswith("/"):
        filepath = raw_input("No absolute file paths. Try again.\n>> ")
    is_directory = filepath.endswith('/')
    return filepath, is_directory


def prompt_for_line_range():
    line_start = raw_input("What is the beginning of the line range you would like to watch in that file?\n(0) >> ")
    line_end = raw_input("What is the end of the line range you would like to watch in that file?\n(infinity) >> ")
    line_range = [int(line_start or 0), int(line_end or 10000000)]
    return line_range


def should_get_additional_line_range():
    another = raw_input("Would you like to add another line range (y/n)?\n>> ") or "n"
    return another.startswith('y')
        

def should_get_additional_watched_file(config):
    logger.info("=================================")
    logger.info("Updated configuration:")
    logger.info("")
    logger.info(yaml.dump(config)))
    logger.info("=================================")
    logger.info("")
    add_another_file = raw_input("Would you like to add another (a), or quit (q)?\n(q) >> ") or 'q'


def write_new_config(config):
    write = raw_input("Write the config (y/n)?\n(n) >> ")
    if write.startswith('y'):
        try:
            with open(WATCHER_CONFIG, 'w+') as config_fp:
                config_fp.write(yaml.dump(config))
        except IOError:
            print "Permission denied."


def main():
    api_token, config = get_base_config()
    api_url = get_github_api_base_url(config)
    username, project = prompt_for_project_path()

    while True:
        filepath, is_directory = prompt_for_filepath()
        if not is_directory:
            line_ranges = []
            while True:
                line_ranges.append(prompt_for_line_range())
                if not should_get_additional_line_range(): 
                    break
        else:
            line_ranges = None

        config = update(config, {
            'github_api_base_url': api_url,
            username: {
                project: {
                    filepath: line_ranges
                }
            }
        })
        if not should_get_additional_watched_file(config):
            break

    write_new_config(config)
 

import os
import collections

import yaml


HOME = os.path.expanduser('~')
WATCHER_CONFIG = os.path.join(HOME, '.github-watcher.yml')
TOKEN_CONFIG = os.path.join(HOME, ".github")

def main():
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
            print "Couldn't open your token file. Make sure it's writeable at ~/.github"
        except:
            print "You must store your github access token at ~/.github." 
            print "  1. Go to your github site (e.g. github.com) and"
            print "  2. click your avatar in the top right then"
            print "  3. click Settings then"
            print "  4. click Personal access tokens on the left then"
            print "  5. Generate access token then"
            print "  6. click repo and user permissions checkboxes. next"
            print "  7. click Generate Token. "
            print "  8. SAVE THAT. copy/paste to ~/.github you will never see it again."

    try:
        with open(WATCHER_CONFIG, 'rb') as config_fp:
            config = yaml.load(config_fp.read())
    except IOError:
        config = {}

    print "Starting with config"
    print ""
    print yaml.dump(config)
    print ""

    api_domain = raw_input("What is your site domain?\n(api.github.com) >> ")
    if not api_domain:
        api_url = "https://api.github.com"
    else:
        api_url = "https://" + api_domain + "/api/v3"

    if 'github_api_base_url' in config:
        overwrite = raw_input("Ok to overwrite {} with {} (y/n)?\n(n) >> ".format(config.get('github_api_base_url'), api_url))
        if overwrite.startswith('y'):
            config['github_api_base_url'] = api_url

    def update(d, u):
        for k, v in u.iteritems():
            if isinstance(v, collections.Mapping):
                d[k] = update(d.get(k, {}), v)
            elif isinstance(v, list):
                d[k] += v
            else:
                d[k] = v
        return d

    while True:
        username = raw_input("What github username or company owns the project you would like to watch?\n>> ")
        project = raw_input("What is the project name you would like to watch?\n>> ")
        filepath = raw_input("What is the file path you would like to watch (directories must end with /)?\n>> ")
        if filepath.startswith("/"):
            filepath = raw_input("No absolute file paths. Try again.\n>> ")
        if not filepath.endswith("/"):
            line_ranges = []
            while True:
                line_start = raw_input("What is the beginning of the line range you would like to watch in that file?\n(0) >> ")
                line_end = raw_input("What is the end of the line range you would like to watch in that file?\n(infinity) >> ")
                line_range = [int(line_start or 0), int(line_end or 10000000)]
                line_ranges.append(line_range)
                another = raw_input("Would you like to add another line range (y/n)?\n>> ") or "n"
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

        print "================================="
        print "Updated configuration:"
        print ""
        print yaml.dump(config)
        print "================================="
        print ""
        add_another_file = raw_input("Would you like to add another (a), or quit (q)?\n(q) >> ") or q
        if add_another_file.startswith('q'):
            break

    write = raw_input("Write the config (y/n)?\n(n) >> ")
    if write.startswith('y'):
        try:
            with open(WATCHER_CONFIG, 'w+') as config_fp:
                config_fp.write(yaml.dump(config))
        except IOError:
            print "Permission denied."

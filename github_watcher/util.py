import logging

import yaml

import github_watcher.settings as settings


HELP_MESSAGE = """
You must store your github access token at ~/.github.
  1. Go to your github site (e.g. github.com) and
  2. click your avatar in the top right then
  3. click Settings then
  4. click Personal access tokens on the left then
  5. Generate access token then
  6. click repo and user permissions checkboxes. next
  7. click Generate Token. 
  8. SAVE THAT. copy/paste to ~/.github you will never see it again.
"""


def assert_string(f):
    def _(*args, **kwargs):
        target = f(*args, **kwargs)
        assert isinstance(target, str), "Expected <{}>to be a string.".format(target)
        return target
    return _


def raise_value_error(parser, parameter_name):
    parser.print_help()
    raise ValueError("--{} is required for the check action".format(parameter_name))


@assert_string
def read_access_token():
    with open(settings.WATCHER_CONFIG, 'rb') as watcher_config:
        return yaml.load(watcher_config.read().decode('utf-8').strip()).get('github_api_secret_token')

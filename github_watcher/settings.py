import os


HOME = os.path.expanduser('~')
WATCHER_CONFIG = os.path.join(HOME, '.github-watcher.yml')
TOKEN_CONFIG = os.path.join(HOME, ".github")
WATCHER_ALERT_LOG = '/tmp/watcher_alert.log'

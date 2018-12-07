#!/usr/bin/env python
long_description = """
github_watcher is a package for keeping an eye for pull requests that fulfill certain criteria. If you're overseeing some tricky lines of code, you can get an alert and a link to any pull request that modifies those lines.

You can also specify a list of regular expressions for which to watch each pull request. If you get a match in any file (source or destination) in any PR you'll get an alert and a link to it.

You can find more info on the github page. https://github.com/akellehe/github-watcher

"""


import sys
if sys.version_info[0] < 3 or sys.version_info[1] < 3:
    raise Exception("This package only supports Python3.3+")

import platform
import os
try:
    from disutils.core import setup, find_packages
except ImportError:
    from setuptools import setup, find_packages

dependencies = [
    'PyYAML==3.13',
    'PyGithub==1.43',
    'requests==2.20.0',
    'typing==3.6.6',
    'unidiff==0.5.4',
]

SYSTEM = platform.system()
if SYSTEM == 'Darwin':
    dependencies.append('pync==2.0.3')
elif SYSTEM == 'Linux' and not os.environ.get('TRAVIS'):
    dependencies.append('dbus-python==1.2.8')
    dependencies.append('notify2==0.3.1')


setup(name='github_watcher',
        version='5.2',
        description='Monitors files/directories on github and alerts you when someone submits a PR with changes',
        long_description=long_description,
        author='Andrew Kelleher',
        author_email='keats.kelleher@gmail.com',
        packages=find_packages(),
        scripts=['github_watcher/github-watcher'],
        url='https://github.com/akellehe/github-watcher',
        install_requires=dependencies)

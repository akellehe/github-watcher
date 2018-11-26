#!/usr/bin/env python
import platform
try:
    from disutils.core import setup, find_packages
except ImportError:
    from setuptools import setup, find_packages

dependencies = [
    'unidiff==0.5.4',
    'requests==2.20.0',
    'PyYAML==3.11',
    'PyGithub==1.43',
]

SYSTEM = platform.system()
if SYSTEM == 'Darwin':
    dependencies.append('pync==2.0.3')
elif SYSTEM == 'Linux':
    dependencies.append('notify2==0.3.1')

setup(name='github_watcher',
        version='3.5',
        description='Monitors files/directories on github and alerts you when someone submits a PR with changes',
        author='Andrew Kelleher',
        author_email='keats.kelleher@gmail.com',
        packages=find_packages(),
        scripts=['github_watcher/github-watcher'],
        url='https://github.com/akellehe/github-watcher',
        install_requires=dependencies)

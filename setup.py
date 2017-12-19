#!/usr/bin/env python

try:
    from disutils.core import setup
except ImportError:
    from setuptools import setup


setup(name='github_watcher',
        version='2.4',
        description='Monitors files/directories on github and alerts you when someone submits a PR with changes',
        author='Andrew Kelleher',
        author_email='keats.kelleher@gmail.com',
        packages=['github_watcher'],
        scripts=['github_watcher/github-watcher'],
        url='https://github.com/akellehe/github-watcher',
        install_requires=[
           'unidiff==0.5.4',
           'requests==2.18.4',
           'pync==1.6.1',
           'PyYAML==3.11',
           'PyGithub==1.35',
        ])

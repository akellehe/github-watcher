#!/usr/bin/env python

try:
    from disutils.core import setup
except ImportError:
    from setuptools import setup


setup(name='github_watcher',
        version='1.0',
        description='Monitors files/directories in github for changes',
        author='Andrew Kelleher',
        author_email='keats.kelleher@gmail.com',
        packages=['github_watcher'],
        scripts=['github_watcher/github-watcher'],
        install_requires=[
           'unidiff==0.5.4',
           'requests==2.18.4',
           'pync==1.6.1',
           'PyYAML==3.11',
        ])

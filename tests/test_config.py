import unittest
import os
import tempfile

import yaml
import mock

from github_watcher import config

test_token = '1234567890abcdefghijklmnopqrstuvwxyz'
test_watcher_config = """
github_api_base_url: https://github.mycompany.com/api/v3
mygithubhandle:
  mygithubproject:
    mydirectory/: null
    mydirectory/myfile.py:
      - [0, 100]
      - [105, 200]
"""
def happy_raw_input(prompt):
    return 'y'

class TestConfig(unittest.TestCase):

    def test_watcher_config_paths(self):
        home = config.HOME
        assert config.WATCHER_CONFIG == os.path.join(home, '.github-watcher.yml')
        assert config.TOKEN_CONFIG == os.path.join(home, '.github')

    def test_update(self):
        target = {}
        assert config.update(target, {'a': 1, 'b': 2}) == \
                {'a': 1, 'b': 2}
        assert config.update({'a': 1}, {'a': 2}) == {'a': 2}
        assert config.update({'a': 1}, {}) == {'a': 1}

    def test_get_base_config_from_files(self):
        with tempfile.NamedTemporaryFile() as token_file:
            token_file.write(test_token)
            token_file.flush()
            with tempfile.NamedTemporaryFile() as watcher_config_file:
                watcher_config_file.write(test_watcher_config)
                watcher_config_file.flush()
                with mock.patch('github_watcher.config.TOKEN_CONFIG',
                        token_file.name):
                    with mock.patch('github_watcher.config.WATCHER_CONFIG',
                            watcher_config_file.name):
                        target_token, target_config = config.get_base_config()
                        self.assertEquals(target_token, test_token)
                        self.assertEquals(target_config,
                                yaml.load(test_watcher_config))

    @mock.patch('github_watcher.config.TOKEN_CONFIG', 'foobar')
    @mock.patch('github_watcher.config.WATCHER_CONFIG', 'raboof')
    def test_get_base_config_from_user(self):
        mock_raw_input = mock.Mock()
        mock_raw_input.return_value = test_token
        with mock.patch('github_watcher.config.raw_input', mock_raw_input):
            target_token, target_config = config.get_base_config()
            self.assertEquals(target_token, test_token)
            self.assertEquals(target_config, {})


    def test_get_github_api_base_url_defaults_to_github(self):
        raw_input_mock = mock.Mock()
        raw_input_mock.return_value = ''
        with mock.patch('github_watcher.config.raw_input', raw_input_mock):
            base_url = config.get_github_api_base_url({})
            self.assertEquals(base_url, 'https://api.github.com')

    def test_get_github_api_base_url_accepts_user_input(self):
        base_url = config.get_github_api_base_url({'github_api_base_url': 'http://github.example.com'})
        self.assertEquals(base_url, 'http://github.example.com')

    

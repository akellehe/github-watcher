import unittest
import unittest.mock as mock
import tempfile

import yaml

import github_watcher.util as util


class TestUtil(unittest.TestCase):

    def test_read_access_token(self):
        tmpfile = tempfile.NamedTemporaryFile()
        tmpfile.write(bytes(yaml.dump({'github_api_secret_token': '*****'}), 'utf8'))
        tmpfile.flush()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', tmpfile.name):
            self.assertEqual(util.read_access_token(), '*****')

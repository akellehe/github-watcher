import tempfile
import unittest
import unittest.mock as mock

import github_watcher.util as util


class TestUtil(unittest.TestCase):

    def test_validate_args(self):
        parser = mock.MagicMock()
        args = mock.MagicMock()
        parser.parse_args.return_value = args

        args.filepath = None
        with self.assertRaisesRegex(ValueError, "--filepath is required for the check action"):
            util.validate_args(parser)

        args.user = None
        with self.assertRaisesRegex(ValueError, "--user is required for the check action"):
            util.validate_args(parser)

        args.repo = None
        with self.assertRaisesRegex(ValueError, "--repo is required for the check action"):
            util.validate_args(parser)

    def test_read_access_token(self):
        parser = mock.MagicMock()
        args = mock.MagicMock()
        parser.parse_args.return_value = args
        args.access_token_file = ''

        with mock.patch('logging.error') as logging_error:
            util.read_access_token(parser)
            logging_error.assert_any_call("No token file found. Checking ~/.github-watcher.yml...")


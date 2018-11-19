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

        with self.assertRaisesRegex(ValueError, ">> github-watcher --help for more information"):
            util.read_access_token(parser)

import unittest
import unittest.mock as mock

import github_watcher.commands.check as check


class TestCheck(unittest.TestCase):

    def test_main(self):
        parser = mock.MagicMock()
        with mock.patch('github_watcher.commands.check.get_config') as get_config:
            with mock.patch('github_watcher.commands.check.find_changes') as find_changes:
                get_config.return_value = 1
                check.main(parser)
                get_config.assert_any_call(parser)
                find_changes.assert_any_call(1)

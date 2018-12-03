import unittest
import unittest.mock as mock

import github_watcher.commands.check as check


class TestCheck(unittest.TestCase):

    def test_main(self):
        parser = mock.MagicMock()
        with mock.patch('github_watcher.commands.check.find_changes') as find_changes:
            with mock.patch('github_watcher.commands.config.Configuration.from_file') as from_file:
                args = mock.MagicMock()
                conf = mock.MagicMock()

                parser.parse_args.return_value = args
                from_file.return_value = conf

                check.main(parser)

                from_file.assert_called_once()
                conf.add_cli_options.assert_any_call(args)
                find_changes.assert_any_call(conf)

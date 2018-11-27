import tempfile
import unittest
import unittest.mock as mock

import yaml

import github_watcher.commands.config as config


class TestConfig(unittest.TestCase):

    def test_nonempty_watch_path(self):
        args = mock.MagicMock()
        args.user = 'akellehe'
        args.repo = 'github-watcher'
        args.filepath = 'path/to/some/file.py'
        self.assertTrue(config.nonempty_watch_path(args))

        args = mock.MagicMock()
        args.user = 'akellehe'
        args.repo = None
        args.filepath = None
        with self.assertRaisesRegex(RuntimeError,
            "If you pass any of --user, --repo, and --filepath you must pass all of them."):
            config.nonempty_watch_path(args)

        args = mock.MagicMock()
        args.user = None
        args.repo = None
        args.filepath = None
        self.assertFalse(config.nonempty_watch_path(args))

    def test_get_cli_config(self,):
        args = mock.MagicMock()
        github_url = 'http://github.com'
        args.github_url = github_url
        args.user = 'akellehe'
        args.repo = 'github-watcher'
        args.filepath = '/'
        args.start = 0
        args.end = 100
        args.regex = 'foobar'
        parser = mock.MagicMock()
        parser.parse_args.return_value = args
        observed_config = config.get_cli_config(parser)
        self.assertEqual(observed_config, {
            'github_api_base_url': github_url,
            'akellehe': {
                'github-watcher': {
                    '/': [[0, 100]]
                }
            },
            'watched_regexes': ['foobar']
        })

    def test_get_file_config(self):
        tmpfile = tempfile.NamedTemporaryFile()
        expected = {
            'github_api_base_url': 'https://github.com',
            'akellehe': {
                'github-watcher': {
                    '/': [[0, 100]]
                }
            }
        }
        tmpfile.write(bytes(yaml.dump(expected), 'utf8'))
        tmpfile.flush()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', tmpfile.name):
            observed = config.get_file_config()
            self.assertEqual(expected, observed)

    def test_get_file_config_with_regexes(self):
        tmpfile = tempfile.NamedTemporaryFile()
        expected = {
            'github_api_base_url': 'https://github.com',
            'akellehe': {
                'github-watcher': {
                    '/': [[0, 100]]
                }
            },
            'watched_regexes': ['foo', 'bar', 'pants']
        }
        tmpfile.write(bytes(yaml.dump(expected), 'utf8'))
        tmpfile.flush()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', tmpfile.name):
            observed = config.get_file_config()
            self.assertEqual(expected, observed)

    def test_get_config_raises_runtime_error(self):
        parser = mock.MagicMock()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', ''):
            with mock.patch('github_watcher.commands.config.get_cli_config',
                            return_value={}):
                with self.assertRaisesRegex(RuntimeError, 'No configuration found.'):
                    config.get_config(parser)

    @mock.patch('github_watcher.commands.config.get_cli_config')
    def test_get_config_returns_cli_config_with_no_file_config(self, get_cli_config):
        get_cli_config.return_value = {
            'github_api_base_url': 'my url',
            'github_api_secret_token': '*****',
            'my': 'cli config'
        }
        parser = mock.MagicMock()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', ''):
            conf = config.get_config(parser)
            self.assertEqual(conf, get_cli_config.return_value)

    @mock.patch('github_watcher.commands.config.get_cli_config')
    def test_get_config_returns_file_config_with_no_cli_config(self, get_cli_config):
        get_cli_config.return_value = {}
        parser = mock.MagicMock()
        tmpfile = tempfile.NamedTemporaryFile()
        expected = {
            'github_api_base_url': 'https://github.com',
            'github_api_secret_token': '*****',
            'akelleh': {
                'github-watcher-2': {
                    'foobar/': [[10, 15]]
                }
            }
        }
        tmpfile.write(bytes(yaml.dump(expected), 'utf8'))
        tmpfile.flush()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', tmpfile.name):
            conf = config.get_config(parser)
            self.assertEqual(expected, conf)

    @mock.patch('github_watcher.commands.config.get_cli_config')
    def test_get_config_overrides_file_config_with_cli_config(self, get_cli_config):
        get_cli_config.return_value = {
            'akelleh': {
                'bazbiz': {
                    'pants/': [[1, 2], [3, 4]]
                }
            }
        }
        parser = mock.MagicMock()
        tmpfile = tempfile.NamedTemporaryFile()
        fileconf = {
            'github_api_base_url': 'https://github.com',  # should fall back to this one
            'github_api_secret_token': '*****',
            'akelleh': {
                'github-watcher-2': {
                    'foobar/': [[10, 15]]
                }
            }
        }
        tmpfile.write(bytes(yaml.dump(fileconf), 'utf8'))
        tmpfile.flush()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', tmpfile.name):
            self.assertEqual(
                config.get_config(parser),
                {
                    'github_api_base_url': 'https://github.com',
                    'github_api_secret_token': '*****',
                    'akelleh': {
                        'bazbiz': {
                            'pants/': [[1, 2], [3, 4]]
                        }
                    }
                }
            )

    def test_update(self):
        old = {
            'github_api_base_url': 'http://github.old.com',
            'github_api_secret_token': 'old token',
            'old username': {
                'old project name': {
                    'old file name': [[0, 1], [2, 3]],
                    'old file name 2': [[4, 5], [6, 7]]
                }
            },
            'not replaced': {
                'foo': {
                    'bar': [[12, 23]]
                }
            }
        }
        overrides = {
            'github_api_base_url': 'http://github.new.com',
            'old username': {
                'old project name': {
                    'old file name': [[8, 9]],
                    'new file name': [[10, 11]]
                }
            },
            'new username': {
                'new project': {
                    'new file 2': [[1, 2]]
                }
            }
        }
        expected = {
            'github_api_base_url': 'http://github.new.com',
            'github_api_secret_token': 'old token',
            'old username': {
                'old project name': {
                    'old file name': [[0, 1], [2, 3], [8, 9]],
                    'old file name 2': [[4, 5], [6, 7]],
                    'new file name': [[10, 11]]
                }
            },
            'not replaced': {
                'foo': {
                    'bar': [[12, 23]]
                }
            },
            'new username': {
                'new project': {
                    'new file 2': [[1, 2]]
                }
            }
        }
        observed = config.update(old, overrides)
        self.assertEqual(expected, observed)

    @mock.patch('github_watcher.commands.config.input')
    def test_get_line_range(self, _input):
        _input.return_value = 1
        line_range = config.get_line_range()
        self.assertEqual(line_range, [1, 1])
        _input.assert_any_call("What is the beginning of the line range you would like to watch in that file?\n(0) >> ")
        _input.assert_any_call("What is the end of the line range you would like to watch in that file?\n(infinity) >> ")

    @mock.patch('github_watcher.commands.config.input')
    def test_should_stop(self, _input):
        _input.return_value = 'y'
        self.assertFalse(config.should_stop())
        _input.assert_any_call("Would you like to add another line range (y/n)?\n>> ")

    @mock.patch('github_watcher.commands.config.input')
    def test_get_project_metadata(self, _input):
        _input.side_effect = ['username', 'project', 'filepath']
        username, project, filepath = config.get_project_metadata()
        self.assertEqual(username, 'username')
        self.assertEqual(project, 'project')
        self.assertEqual(filepath, 'filepath')
        _input.assert_any_call("What github username or company owns the project you would like to watch?\n>> ")
        _input.assert_any_call("What is the project name you would like to watch?\n>> ")
        _input.assert_any_call("What is the file path you would like to watch (directories must end with /)?\n>> ")

        _input.side_effect = ['username', 'project', '/filepath', Exception('foobar')]
        with self.assertRaisesRegex(Exception, 'foobar'):
            config.get_project_metadata()
        _input.assert_any_call("What github username or company owns the project you would like to watch?\n>> ")
        _input.assert_any_call("What is the project name you would like to watch?\n>> ")
        _input.assert_any_call("What is the file path you would like to watch (directories must end with /)?\n>> ")
        _input.assert_any_call("No absolute file paths. Try again.\n>> ")

    @mock.patch('github_watcher.commands.config.should_stop')
    @mock.patch('github_watcher.commands.config.display_configuration')
    @mock.patch('github_watcher.commands.config.get_project_metadata')
    @mock.patch('github_watcher.commands.config.input')
    @mock.patch('github_watcher.commands.config.get_config')
    def test_main(self, get_config, _input, get_project_metadata, display_configuration, should_stop):
        get_project_metadata.return_value = ('username', 'project', 'filepath')
        should_stop.return_value = True
        get_config.return_value = {}

        args = mock.MagicMock()
        github_url = 'http://github.com'
        args.github_url = github_url
        args.user = 'akellehe'
        args.repo = 'github-watcher'
        args.filepath = '/'
        args.start = 0
        args.end = 100
        parser = mock.MagicMock()
        parser.parse_args.return_value = args

        tmpfile = tempfile.NamedTemporaryFile()
        tmpfile.write(bytes('', 'utf8'))
        tmpfile.flush()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', tmpfile.name):
            with mock.patch('github_watcher.commands.config.input') as inp:
                inp.return_value = ''
                config.main(parser)

        get_config.assert_any_call(parser)
        get_project_metadata.assert_called()
        display_configuration.assert_any_call({'github_api_base_url': 'https://api.github.com', 'username': {'project': {'filepath': [[0, 10000000]]}}})

    @mock.patch('github_watcher.commands.config.should_stop')
    @mock.patch('github_watcher.commands.config.display_configuration')
    @mock.patch('github_watcher.commands.config.input')
    @mock.patch('github_watcher.commands.config.get_config')
    def test_main_with_write_config(self, get_config, _input, display_configuration, should_stop):
        should_stop.return_value = True
        get_config.return_value = {}

        args = mock.MagicMock()
        github_url = 'http://github.com'
        args.github_url = github_url
        args.user = 'akellehe'
        args.repo = 'github-watcher'
        args.filepath = '/'
        args.start = 0
        args.end = 100
        parser = mock.MagicMock()
        parser.parse_args.return_value = args

        tmpfile = tempfile.NamedTemporaryFile()
        tmpfile.write(bytes('', 'utf8'))
        tmpfile.flush()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', tmpfile.name):
            with mock.patch('github_watcher.commands.config.input') as inp:
                inp.side_effect = ['username', 'project', 'filepath', 0, 10, 'my base url', 'q', 'y']
                config.main(parser)

        get_config.assert_any_call(parser)
        display_configuration.assert_any_call({'github_api_base_url': 'my base url', 'username': {'project': {'filepath': [[0, 10]]}}})

    @mock.patch('github_watcher.commands.config.should_stop')
    @mock.patch('github_watcher.commands.config.display_configuration')
    @mock.patch('github_watcher.commands.config.get_project_metadata')
    @mock.patch('github_watcher.commands.config.input')
    @mock.patch('github_watcher.commands.config.get_config')
    def test_main_with_runtime_error(self, get_config, _input, get_project_metadata, display_configuration, should_stop):
        get_project_metadata.return_value = ('username', 'project', 'filepath')
        should_stop.return_value = True
        get_config.side_effect = RuntimeError

        args = mock.MagicMock()
        github_url = 'http://github.com'
        args.github_url = github_url
        args.user = 'akellehe'
        args.repo = 'github-watcher'
        args.filepath = '/'
        args.start = 0
        args.end = 100
        parser = mock.MagicMock()
        parser.parse_args.return_value = args

        tmpfile = tempfile.NamedTemporaryFile()
        tmpfile.write(bytes('', 'utf8'))
        tmpfile.flush()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', tmpfile.name):
            with mock.patch('github_watcher.commands.config.input') as inp:
                inp.return_value = ''
                config.main(parser)
                get_config.assert_any_call(parser)
                get_project_metadata.assert_called()
                display_configuration.assert_any_call({'github_api_base_url': 'https://api.github.com', 'username': {'project': {'filepath': [[0, 10000000]]}}})

    @mock.patch('github_watcher.commands.config.print')
    def test_display_configuration(self, _print):
        config.display_configuration({'my': 'configuration'})
        _print.assert_any_call("Updated configuration:")

    def test_get_api_base_url(self):
        conf = {'github_api_base_url': 'my base url'}
        base_url = config.get_api_base_url(conf)
        self.assertEqual(base_url, 'my base url')

        with mock.patch('github_watcher.commands.config.input') as _input:
            conf = {'github_api_base_url': None}
            _input.return_value = 'second base url'
            base_url = config.get_api_base_url(conf)
            self.assertEqual(base_url, 'second base url')

        with mock.patch('github_watcher.commands.config.input') as _input:
            conf = {'github_api_base_url': None}
            _input.return_value = None
            base_url = config.get_api_base_url(conf)

        self.assertEqual(base_url, 'https://api.github.com')


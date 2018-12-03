import tempfile
import unittest
import unittest.mock as mock

import yaml

import github_watcher.commands.config as config


class TestConfig(unittest.TestCase):

    def test_get_file_config(self):
        tmpfile = tempfile.NamedTemporaryFile()
        expected = {
            'akellehe': {
                'base_url': 'https://github.com',
                'token': '',
                'repos': {
                    'github-watcher': {
                        'paths': {'/': [[0, 100]]},
                        'regexes': [],
                    }
                }
            }
        }
        tmpfile.write(bytes(yaml.dump(expected), 'utf8'))
        tmpfile.flush()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', tmpfile.name):
            observed = config.Configuration.from_file().to_json()
            self.assertEqual(expected, observed)

    def test_get_file_config_with_regexes(self):
        tmpfile = tempfile.NamedTemporaryFile()
        expected = {
            'akellehe': {
                'repos': {
                    'github-watcher': {
                        'paths': {
                            '/': [[0, 100]]
                        },
                        'regexes': ['foo', 'bar'],
                    },
                },
                'base_url': 'https://github.com',
                'token': ''
            }
        }
        tmpfile.write(bytes(yaml.dump(expected), 'utf8'))
        tmpfile.flush()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', tmpfile.name):
            observed = config.Configuration.from_file(tmpfile.name).to_json()
            self.assertEqual(expected, observed)

    def test_config_from_file_raises_runtime_error(self):
        with self.assertRaisesRegex(RuntimeError, 'Config file not found <>'):
            config.Configuration.from_file('')

    def test_basic_file_config(self):
        tmpfile = tempfile.NamedTemporaryFile()
        expected = {'akellehe': {
            'repos': {
                'github_watcher': {
                    'paths': {
                        'docs/': [],
                        'github_watcher/settings.py': [[0, 1], [4, 5]]
                    },
                    'regexes': ['foo', 'bar']
                },
            },
            'base_url': 'https://api.gitub.com',
            'token': '*****',
        }}
        tmpfile.write(bytes(yaml.dump(expected, default_flow_style=False), 'utf8'))
        tmpfile.flush()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', tmpfile.name):
            conf = config.Configuration.from_file(tmpfile.name)
            self.assertEqual(expected, conf.to_json())

    @mock.patch('github_watcher.commands.config.input')
    def test_get_line_range(self, _input):
        _input.return_value = 1
        line_range = config.get_line_range()
        self.assertEqual(line_range, [1, 1])
        _input.assert_any_call("What is the beginning of the line range you would like to watch in that file?\n(0) >> ")
        _input.assert_any_call("What is the end of the line range you would like to watch in that file?\n(infinity) >> ")

    @mock.patch('github_watcher.commands.config.input')
    def test_should_end(self, _input):
        _input.return_value = 'y'
        self.assertFalse(config.should_end())
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

    @mock.patch('github_watcher.commands.config.should_end')
    @mock.patch('github_watcher.commands.config.input')
    @mock.patch('github_watcher.commands.config.print')
    def test_main(self, _print, _input, should_end):
        _input.side_effect = ['username', 'project', 'filepath', 0, 10, 'my base url', 'q', 'y']
        should_end.return_value = True
        args = mock.MagicMock()
        args.silent = True
        args.verbose = False
        parser = mock.MagicMock()
        parser.parse_args.return_value = args
        tmpfile = tempfile.NamedTemporaryFile()
        tmpfile.write(bytes('', 'utf8'))
        tmpfile.flush()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', tmpfile.name):
            c = config.main(parser)
        _print.assert_any_call("""username:
  base_url: my base url
  repos:
    project:
      paths:
        filepath:
        - - 0
          - 10
      regexes: []
  token: ''
""")

    @mock.patch('github_watcher.commands.config.should_end')
    @mock.patch('github_watcher.commands.config.input')
    def test_main_with_write_new_user_config(self, _input, should_end):
        should_end.return_value = True
        expected = {'akellehe': {
            'base_url': 'https://api.gitub.com',
            'token': '*****',
            'repos': {
                'github_watcher': {
                    'paths': {
                        'docs/': [],
                        'github_watcher/settings.py': [[0, 1], [4, 5]]
                    },
                    'regexes': ['foo', 'bar']
                },
            }
        }}
        tmpfile = tempfile.NamedTemporaryFile()
        tmpfile.write(bytes(yaml.dump(expected), 'utf8'))
        tmpfile.flush()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', tmpfile.name):
            with mock.patch('github_watcher.commands.config.input') as inp:
                with mock.patch('github_watcher.commands.config.print') as _print:
                    inp.side_effect = ['username', 'project', 'filepath', 0, 10, 'my base url', 'q', 'y']
                    config.main(None)
        expected = """akellehe:
  base_url: https://api.gitub.com
  repos:
    github_watcher:
      paths:
        docs/: []
        github_watcher/settings.py:
        - - 0
          - 1
        - - 4
          - 5
      regexes:
      - foo
      - bar
  token: '*****'
username:
  base_url: my base url
  repos:
    project:
      paths:
        filepath:
        - - 0
          - 10
      regexes: []
  token: ''
"""
        with open(tmpfile.name, 'rb') as fp:
            self.assertEqual(fp.read().decode('utf8'), expected)

    @mock.patch('github_watcher.commands.config.should_end')
    @mock.patch('github_watcher.commands.config.input')
    def test_main_with_runtime_error(self, _input, should_end):
        _input.side_effect = ['username', 'project', 'filepath', 0, 10, 'my base url', 'q', 'y']
        should_end.return_value = True

        tmpfile = tempfile.NamedTemporaryFile()
        tmpfile.write(bytes('', 'utf8'))
        tmpfile.flush()
        with mock.patch('github_watcher.settings.WATCHER_CONFIG', tmpfile.name):
            with mock.patch('github_watcher.commands.config.input') as inp:
                inp.return_value = ''
                config.main(None)

    def test_get_api_base_url(self):
        conf = config.Configuration(users=[config.User(name='akellehe', repos=[], token='', base_url='foobar')])
        base_url = config.get_api_base_url('akellehe', conf)
        self.assertEqual(base_url, 'foobar')

        with mock.patch('github_watcher.commands.config.input') as _input:
            conf = config.Configuration(users=[])
            _input.return_value = 'second base url'
            base_url = config.get_api_base_url('akellehe', conf)
            self.assertEqual(base_url, 'second base url')

        with mock.patch('github_watcher.commands.config.input') as _input:
            conf = config.Configuration(users=[])
            _input.return_value = None
            base_url = config.get_api_base_url('akellehe', conf)

        self.assertEqual(base_url, 'https://api.github.com')

    def test_configuration_model_from_yml(self):
        conf = {'akellehe': {
            'base_url': 'https://api.gitub.com',
            'token': '*****',
            'repos': {
                'github_watcher': {
                    'paths': {
                        'docs/': None,
                        'github_watcher/settings.py': [[0, 1], [4, 5]]
                    },
                    'regexes': ['foo', 'bar']
                },
                'github_watcher_2': {
                    'paths': {'docs/': None,
                              'github_watcher/settings.py': [[0, 1], [4, 5]]},
                    'regexes': ['foo', 'bar']
                }
            }
        }}
        target = config.Configuration.from_json(conf)

        self.assertEqual(len(target.users), 1)
        self.assertEqual(target.users[0].name, 'akellehe')
        self.assertEqual(target.users[0].repos[0].name, 'github_watcher')
        self.assertEqual(target.users[0].repos[1].name, 'github_watcher_2')
        self.assertEqual(target.users[0].repos[1].paths[0].path, 'docs/')
        self.assertEqual(target.users[0].repos[1].paths[0].ranges, [])
        self.assertEqual(target.users[0].repos[1].paths[1].path, 'github_watcher/settings.py')
        self.assertEqual(target.users[0].repos[1].paths[1].ranges[0].start, 0)
        self.assertEqual(target.users[0].repos[1].paths[1].ranges[0].end, 1)
        self.assertEqual(target.users[0].repos[1].paths[1].ranges[1].start, 4)
        self.assertEqual(target.users[0].repos[1].paths[1].ranges[1].end, 5)

    def test_configuration_to_from_json(self):
        conf = {'akellehe': {
            'repos': {
                'github_watcher': {
                    'paths': {
                        'docs/': [],
                        'github_watcher/settings.py': [[0, 1], [4, 5]]
                    },
                    'regexes': ['foo', 'bar']
                },
                'github_watcher_2': {
                    'paths': {'docs/': [],
                              'github_watcher/settings.py': [[0, 1], [4, 5]]},
                    'regexes': ['foo', 'bar']
                }
            },
            'base_url': 'https://api.gitub.com',
            'token': '*****',
        }}
        self.assertEqual(config.Configuration.from_json(conf).to_json(), conf)


if __name__ == '__main__':
    unittest.main()

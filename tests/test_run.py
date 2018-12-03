import tempfile
import os
import platform
import unittest
import unittest.mock as mock

from github_watcher.commands import run
from github_watcher.services import git

from github_watcher.commands.config import (
    Configuration,
    User,
    Repo,
    Path,
    Range,
)


class TestRun(unittest.TestCase):

    def test_is_watched_file(self):
        conf = Configuration(users=[User(
            name='akellehe',
            repos=[Repo(name='github_watcher',
                        paths=[Path(path='util.py',ranges=[Range(0, 100)])],
                        regexes=[]
                        )],
            token='',
            base_url='https://api.github.com',
        )])

        target = run.is_watched_file(conf.users[0].repos[0], 'util.py')
        self.assertTrue(target)

        target = run.is_watched_file(conf.users[0].repos[0], 'not-watched.py')
        self.assertFalse(target)
        self.assertFalse(run.is_watched_file(None, '/foo/bar'))

    def test_is_watched_directory(self):
        conf = Configuration(users=[User(
            name='akellehe',
            repos=[Repo(name='github_watcher',
                        paths=[Path(path='tests/',ranges=[])],
                        regexes=[])],
            token='',
            base_url='https://api.github.com',
        )])

        target = run.is_watched_directory(
            conf.users[0].repos[0],
            'tests/watched.py'
        )
        self.assertTrue(target)

        target = run.is_watched_directory(
            conf.users[0].repos[0],
            'not-watched.py'
        )
        self.assertFalse(target)
        self.assertFalse(run.is_watched_directory(None, '/foo/bar'))

    @unittest.skipIf(platform.system() != 'Darwin', "This test only for OSX")
    @mock.patch('github_watcher.commands.run.logging.info')
    @mock.patch('github_watcher.commands.run.subprocess.call')
    def test_alert_osx(self, subprocess_call, logging_info):
        msg = 'Found a PR effecting myfile myrange'
        with mock.patch('github_watcher.commands.run.Notifier.notify') as notify:
            run.alert('myfile', 'myrange', 'my_pr_link')
            notify.assert_any_call(msg, title='Github Watcher', open='my_pr_link')
        logging_info.assert_any_call(msg)
        subprocess_call.assert_any_call('say ' + msg, shell=True)

    @unittest.skipIf(platform.system() != 'Linux', "This test only for Linux")
    @unittest.skipIf(os.environ.get('TRAVIS') == 'true', "Skip during CI runs.")
    @mock.patch('github_watcher.commands.run.logging.info')
    def test_alert_linux(self, logging_info):
        msg = 'Found a PR effecting myfile myrange'
        with mock.patch('github_watcher.commands.run.notify2.init') as _init:
            with mock.patch('github_watcher.commands.run.notify2.Notification') as _Note:
                run.alert('myfile', 'myrange', 'my_pr_link')
                _init.assert_any_call(app_name='github-watcher')
                _Note.assert_any_call('Github Watcher', messages=msg)
        logging_info.assert_any_call(msg)

    def test_are_watched_lines(self):
        paths = [Path(path='foo/bar/pants.py', ranges=[Range(0, 5)]),
                 Path(path='baz/biz/goat.py', ranges=[Range(10, 20)])]
        self.assertTrue(run.are_watched_lines(paths[0], 0, 10))
        self.assertFalse(run.are_watched_lines(paths[1], 6, 9))
        with self.assertRaisesRegex(ValueError, 'Changed line ranges were out of order.'):
            self.assertTrue(run.are_watched_lines(
                paths[1], 10, 0
            ))

    @mock.patch('github_watcher.commands.run.already_alerted')
    @mock.patch('github_watcher.commands.run.alert')
    def test_alert_if_watched_changes_with_watched_directory(self, alert, already_alerted):
        already_alerted.return_value = False
        hunk_1 = mock.MagicMock()
        hunk_2 = mock.MagicMock()
        hunk_1.source_start = 0
        hunk_1.source_length = 10
        hunk_2.source_start = 40
        hunk_2.source_length = 10
        patched_file = mock.MagicMock()
        patched_file.source_file = 'a/foo/bar/pants.py'
        patched_file.target_file = 'b/foo/bar/pants.py'
        patched_file.__iter__.return_value = [hunk_1, hunk_2]
        conf = Configuration.from_json({
            'akellehe': {
                'repos': {
                    'github-watcher': {
                        'paths': {
                            'foo/bar/': None
                        }
                    }
                }
            },
        })
        self.assertTrue(run.alert_if_watched_changes(
            conf,
            conf.users[0],
            conf.users[0].repos[0],
            patched_file,
            'my link',
            'diffstring',
            'source'
        ))

    @mock.patch('github_watcher.commands.run.already_alerted')
    @mock.patch('github_watcher.commands.run.alert')
    def test_alert_if_watched_changes_when_should_alert(self, alert, already_alerted):
        already_alerted.return_value = False
        hunk_1 = mock.MagicMock()
        hunk_2 = mock.MagicMock()
        hunk_1.source_start = 0
        hunk_1.source_length = 10
        hunk_2.source_start = 40
        hunk_2.source_length = 10
        patched_file = mock.MagicMock()
        patched_file.source_file = 'a/foo/bar/pants.py'
        patched_file.target_file = 'b/foo/bar/pants.py'
        patched_file.__iter__.return_value = [hunk_1, hunk_2]
        conf = Configuration.from_json({
                'akellehe': {
                    'repos': {
                        'github-watcher': {
                            'paths': {
                                'foo/bar/pants.py': [[0, 5]],
                                'baz/biz/goat.py': [[10, 20]]
                            }
                        }
                    }
                },
            })
        self.assertTrue(run.alert_if_watched_changes(
            conf,
            conf.users[0],
            conf.users[0].repos[0],
            patched_file,
            'my link',
            'my diffstring',
            'source'
        ))
        alert.assert_any_call('foo/bar/pants.py', (0, 10), 'my link', silent=False)

    @unittest.skipIf(platform.system() != 'Darwin', "This test only for OSX")
    @mock.patch('github_watcher.commands.run.subprocess.call')
    @mock.patch('github_watcher.commands.run.Notifier.notify')
    def test_alert_doesnt_make_noise_when_silent(self, notify, _call):
        run.alert('myfile', (1, 100), 'my pr link', silent=False)
        _call.assert_any_call('say Found a PR effecting myfile (1, 100)', shell=True)
        _call.reset_mock()
        run.alert('myfile2', (10, 1000), 'my pr link2', silent=True)
        _call.assert_not_called()

    def test_contains_watched_regex(self):
        repo = Repo(name='github-watcher', paths=[], regexes=['foo'])
        self.assertTrue(run.contains_watched_regex(repo, 'my sentence contains foo'))
        self.assertFalse(run.contains_watched_regex(repo, 'my sentence does not contain it'))


    @mock.patch('github_watcher.commands.run.already_alerted')
    def test_alert_if_watched_changes_for_regex(self, already_alerted):
        already_alerted.return_value = True
        hunk_1 = mock.MagicMock()
        hunk_2 = mock.MagicMock()
        hunk_1.source_start = 0
        hunk_1.source_length = 10
        hunk_2.source_start = 40
        hunk_2.source_length = 10
        patched_file = mock.MagicMock()
        patched_file.source_file = 'a/foo/bar/pants.py'
        patched_file.target_file = 'b/foo/bar/pants.py'
        patched_file.__iter__.return_value = [hunk_1, hunk_2]
        conf = Configuration.from_json({
                'akellehe': {
                    'repos': {
                        'github-watcher': {
                            'paths': {
                                'foo/bar/pants.py': [[0, 5]],
                                'baz/biz/goat.py': [[10, 20]]
                            }
                        }
                    }
                },
            })
        self.assertFalse(run.alert_if_watched_changes(
            conf,
            conf.users[0],
            conf.users[0].repos[0],
            patched_file,
            'my link',
            'my diffstring'
            'source'
        ))
        already_alerted.assert_any_call('my link')


    @mock.patch('github_watcher.commands.run.already_alerted')
    def test_alert_if_already_alerted(self, already_alerted):
        already_alerted.return_value = True
        hunk_1 = mock.MagicMock()
        hunk_2 = mock.MagicMock()
        hunk_1.source_start = 0
        hunk_1.source_length = 10
        hunk_2.source_start = 40
        hunk_2.source_length = 10
        patched_file = mock.MagicMock()
        patched_file.source_file = 'a/foo/bar/pants.py'
        patched_file.target_file = 'b/foo/bar/pants.py'
        patched_file.__iter__.return_value = [hunk_1, hunk_2]
        conf = Configuration.from_json(
            {
                'akellehe': {
                    'repos': {
                        'github-watcher': {
                            'paths': {
                                'foo/bar/pants.py': [[0, 5]],
                                'baz/biz/goat.py': [[10, 20]]
                            }
                        }
                    }
                }
            })
        self.assertFalse(run.alert_if_watched_changes(
            conf,
            conf.users[0],
            conf.users[0].repos[0],
            patched_file,
            'my link',
            'source'

        ))
        already_alerted.assert_any_call('my link')

    @mock.patch('github_watcher.commands.run.already_alerted')
    def test_alert_if_watched_changes(self, already_alerted):
        already_alerted.return_value = False
        hunk_1 = mock.MagicMock()
        hunk_2 = mock.MagicMock()
        hunk_1.source_start = 0
        hunk_1.source_length = 10
        hunk_2.source_start = 40
        hunk_2.source_length = 10
        patched_file = mock.MagicMock()
        patched_file.source_file = 'a/foo/bar/pants.py'
        patched_file.target_file = 'b/foo/bar/pants.py'
        patched_file.__iter__.return_value = [hunk_1, hunk_2]
        conf = Configuration.from_json({
                'akellehe': {
                    'repos': {
                        'github-watcher': {
                            'paths': {
                                'foo/bar/pants.py': [[0, 5]],
                                'baz/biz/goat.py': [[10, 20]]
                            }
                        }
                    }
                },
            })
        self.assertTrue(run.alert_if_watched_changes(
            conf,
            conf.users[0],
            conf.users[0].repos[0],
            patched_file,
            'my link',
            'source'
        ))
        conf = Configuration.from_json({
                'akellehe': {
                    'repos': {
                        'github-watcher': {
                            'paths': {
                                'foo/bar/pants.py': [[11, 35]],
                                'baz/biz/goat.py': [[10, 20]]
                            }
                        }
                    }
                },
            })
        self.assertFalse(run.alert_if_watched_changes(
            conf,
            conf.users[0],
            conf.users[0].repos[0],
            patched_file,
            'my link',
            'source'
        ))
        patched_file = mock.MagicMock()
        patched_file.source_file = 'a/foo/bar/not-watched.py'
        patched_file.target_file = 'b/foo/bar/not-watched.py'
        patched_file.__iter__.return_value = [hunk_1, hunk_2]
        conf = Configuration.from_json({
                'akellehe': {
                    'repos': {
                        'github-watcher': {
                            'paths': {
                                'foo/bar/pants.py': [[0, 5]],
                                'baz/biz/goat.py': [[10, 20]]
                            }
                        }
                    }
                }
            })
        self.assertFalse(run.alert_if_watched_changes(
            conf,
            conf.users[0],
            conf.users[0].repos[0],
            patched_file,
            'my link',
            'source'
        ))

    def test_mark_as_alerted(self):
        tmpfile = tempfile.NamedTemporaryFile()
        with mock.patch('github_watcher.settings.WATCHER_ALERT_LOG', tmpfile.name):
            run.mark_as_alerted('my pr link')
        with open(tmpfile.name, 'rb') as fp:
            self.assertIn('my pr link', fp.read().decode('utf8'))

    def test_already_alerted(self):
        tmpfile = tempfile.NamedTemporaryFile()
        with open(tmpfile.name, 'w') as fp:
            fp.write('my pr link')
            fp.flush()
        with mock.patch('github_watcher.settings.WATCHER_ALERT_LOG', tmpfile.name):
            self.assertTrue(run.already_alerted('my pr link'))

    @mock.patch('github_watcher.commands.run.open')
    def test_already_alerted_with_ioerror(self, _open):
        _open.side_effect = IOError
        self.assertFalse((run.already_alerted('my pr link')))

    @mock.patch('github_watcher.commands.run.alert_if_watched_changes')
    @mock.patch('github_watcher.services.git.diff')
    @mock.patch('github_watcher.commands.run.unidiff.PatchSet.from_string')
    @mock.patch('github_watcher.services.git.open_pull_requests')
    def test_find_changes_with_watched_source(self, open_pull_requests, patch_set_from_string, git_diff,
                          alert_if_watched_changes):
        open_prs = [mock.MagicMock()]
        open_prs[0].html_url = 'my html url'
        open_pull_requests.return_value = open_prs
        git_diff.return_value = 'my diff'
        patched_file_1 = mock.MagicMock()
        patch_set = [patched_file_1]
        patch_set_from_string.return_value = patch_set
        conf = Configuration.from_json({
            'akellehe': {
                'repos': {
                    'github-watcher': {
                        'foo/bar/pants.py': [[0, 5]],
                        'baz/biz/goat.py': [[10, 20]]
                    }
                },
                'base_url': 'my base url',
                'token': '*****'
            }
        })
        run.find_changes(conf)
        open_pull_requests.assert_any_call(
            'my base url', '*****', 'akellehe', 'github-watcher')
        patch_set_from_string.assert_any_call('my diff')
        git_diff.assert_any_call('my base url', '*****', open_prs[0])
        alert_if_watched_changes.assert_any_call(
            conf, conf.users[0], conf.users[0].repos[0], patched_file_1, 'my html url', 'my diff', 'source'
        )

    @mock.patch('github_watcher.commands.run.alert_if_watched_changes')
    @mock.patch('github_watcher.services.git.diff')
    @mock.patch('github_watcher.commands.run.unidiff.PatchSet.from_string')
    @mock.patch('github_watcher.services.git.open_pull_requests')
    def test_find_changes_with_watched_target(self, open_pull_requests, patch_set_from_string, git_diff,
                                              alert_if_watched_changes):
        alert_if_watched_changes.side_effect = [False, True]
        open_prs = [mock.MagicMock()]
        open_prs[0].html_url = 'my html url'
        open_pull_requests.return_value = open_prs
        git_diff.return_value = 'my diff'
        patched_file_1 = mock.MagicMock()
        patch_set = [patched_file_1]
        patch_set_from_string.return_value = patch_set
        conf = Configuration.from_json({
            'akellehe': {
                'repos': {
                    'github-watcher': {
                        'foo/bar/pants.py': [[0, 5]],
                        'baz/biz/goat.py': [[10, 20]]
                    }
                },
                'base_url': 'my base url',
                'token': '*****'
            },
        })
        run.find_changes(conf)
        open_pull_requests.assert_any_call(
            'my base url', '*****', 'akellehe', 'github-watcher')
        patch_set_from_string.assert_any_call('my diff')
        git_diff.assert_any_call('my base url', '*****', open_prs[0])
        alert_if_watched_changes.assert_any_call(
            conf, conf.users[0], conf.users[0].repos[0], patched_file_1, 'my html url', 'my diff', 'target'
        )

    @mock.patch('github_watcher.commands.run.alert_if_watched_changes')
    @mock.patch('github_watcher.services.git.diff')
    @mock.patch('github_watcher.commands.run.unidiff.PatchSet.from_string')
    @mock.patch('github_watcher.services.git.open_pull_requests')
    def test_find_changes_with_noop(self, open_pull_requests, patch_set_from_string, git_diff,
                          alert_if_watched_changes):
        open_prs = [mock.MagicMock()]
        open_prs[0].html_url = 'my html url'
        open_pull_requests.return_value = open_prs
        diff = mock.MagicMock()
        diff.return_value = 'my diff'
        git_diff.return_value = diff
        patch_set_from_string.side_effect = git.Noop
        conf = Configuration.from_json({
            'akellehe': {
                'repos': {
                    'github-watcher': {
                        'paths': {
                            'foo/bar/pants.py': [[0, 5]],
                            'baz/biz/goat.py': [[10, 20]]
                        }
                    }
                },
                'base_url': 'my base url',
                'token': '*****'

            }
        })
        run.find_changes(conf)
        open_pull_requests.assert_any_call(
            'my base url', '*****', 'akellehe', 'github-watcher')
        patch_set_from_string.assert_any_call(diff)
        git_diff.assert_any_call('my base url', '*****', open_prs[0])
        alert_if_watched_changes.assert_not_called()

    @mock.patch('github_watcher.commands.run.config.Configuration.from_file')
    @mock.patch('github_watcher.commands.run.find_changes')
    def test_main(self, find_changes, configuration_from_file):
        conf = mock.MagicMock()
        configuration_from_file.return_value = conf
        parser = mock.MagicMock()
        with mock.patch('time.sleep') as time_sleep:
            time_sleep.side_effect = StopIteration
            with self.assertRaisesRegex(StopIteration, ''):
                run.main(parser)
        configuration_from_file.assert_called_once()
        conf.add_cli_options.assert_called_once()
        find_changes.assert_any_call(conf)
        time_sleep.assert_any_call(600)

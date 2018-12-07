import unittest
import datetime
import unittest.mock as mock

import github_watcher.commands.clean as clean
import github_watcher.commands.config as config



class TestClean(unittest.TestCase):

    def test_clean_branch_with_no_options(self):
        branch = mock.MagicMock()
        options = mock.MagicMock()
        options.comment = None
        options.delete = None
        with mock.patch('github_watcher.commands.clean.git.comment') as comment:
            with mock.patch('github_watcher.commands.clean.git.delete') as delete:
                clean.clean_branch(branch, options)
                comment.assert_not_called()
                delete.assert_not_called()

    def test_clean_branch_with_delete_only(self):
        branch = mock.MagicMock()
        options = mock.MagicMock()
        options.comment = None
        options.delete = True
        options.dry_run = True
        with mock.patch('github_watcher.commands.clean.git.comment') as comment:
            with mock.patch('github_watcher.commands.clean.git.delete') as delete:
                clean.clean_branch(branch, options)
                comment.assert_not_called()
                delete.assert_any_call(branch, dry_run=True)

    def test_clean_branch_with_comment_only(self):
        branch = mock.MagicMock()
        options = mock.MagicMock()
        options.comment = 'foo bar'
        options.delete = False
        options.dry_run = True
        with mock.patch('github_watcher.commands.clean.git.comment') as comment:
            with mock.patch('github_watcher.commands.clean.git.delete') as delete:
                clean.clean_branch(branch, options)
                comment.assert_any_call(branch, message='foo bar', dry_run=True)
                delete.assert_not_called()

    def test_clean_branch_with_both(self):
        branch = mock.MagicMock()
        options = mock.MagicMock()
        options.comment = 'foo bar'
        options.delete = True
        options.dry_run = True
        with mock.patch('github_watcher.commands.clean.git.comment') as comment:
            with mock.patch('github_watcher.commands.clean.git.delete') as delete:
                clean.clean_branch(branch, options)
                comment.assert_any_call(branch, message='foo bar', dry_run=True)
                delete.assert_any_call(branch, dry_run=True)

    def test_clean_pull_request_with_no_options(self):
        pull_request = mock.MagicMock()
        options = mock.MagicMock()
        options.comment = None
        options.close = None
        options.delete = None
        options.dry_run = True
        with mock.patch('github_watcher.commands.clean.git.comment') as comment:
            with mock.patch('github_watcher.commands.clean.git.close') as close:
                clean.clean_pull_request(pull_request, options)
                comment.assert_not_called()
                close.assert_not_called()

    def test_clean_pull_request_with_close_only(self):
        pull_request = mock.MagicMock()
        options = mock.MagicMock()
        options.comment = None
        options.close = True
        options.delete = None
        options.dry_run = True
        with mock.patch('github_watcher.commands.clean.git.comment') as comment:
            with mock.patch('github_watcher.commands.clean.git.close') as close:
                clean.clean_pull_request(pull_request, options)
                comment.assert_not_called()
                close.assert_any_call(pull_request, dry_run=True)

    def test_clean_pull_request_with_comment_only(self):
        pull_request = mock.MagicMock()
        options = mock.MagicMock()
        options.comment = 'foo bar'
        options.close = None
        options.delete = None
        options.dry_run = True
        with mock.patch('github_watcher.commands.clean.git.comment') as comment:
            with mock.patch('github_watcher.commands.clean.git.close') as close:
                clean.clean_pull_request(pull_request, options)
                comment.assert_any_call(pull_request, message='foo bar', dry_run=True)
                close.assert_not_called()

    def test_clean_pull_request_with_both(self):
        pull_request = mock.MagicMock()
        options = mock.MagicMock()
        options.comment = 'foo bar'
        options.close = True
        options.dry_run = True
        with mock.patch('github_watcher.commands.clean.git.comment') as comment:
            with mock.patch('github_watcher.commands.clean.git.close') as close:
                clean.clean_pull_request(pull_request, options)
                comment.assert_any_call(pull_request, message='foo bar', dry_run=True)
                close.assert_any_call(pull_request, dry_run=True)

    def test_clean_pull_request_does_not_delete(self):
        pull_request = mock.MagicMock()
        options = mock.MagicMock()
        options.comment = None
        options.close = None
        options.delete = True
        options.dry_run = True
        with mock.patch('github_watcher.commands.clean.git.comment') as comment:
            with mock.patch('github_watcher.commands.clean.git.close') as close:
                with mock.patch('github_watcher.commands.clean.git.delete') as delete:
                    clean.clean_pull_request(pull_request, options)
                    comment.assert_not_called()
                    close.assert_not_called()
                    delete.assert_not_called()

    @mock.patch('github_watcher.services.git.get_last_updated')
    def test_too_old(self, get_last_updated):
        get_last_updated.return_value = datetime.datetime.now()
        entity = mock.MagicMock()
        cutoff = '1970-12-01'
        self.assertFalse(clean.too_old(entity, cutoff))

        get_last_updated.return_value = datetime.datetime.now()
        entity = mock.MagicMock()
        cutoff = '3000-12-01'
        self.assertTrue(clean.too_old(entity, cutoff))

    @mock.patch('github_watcher.commands.clean.too_old')
    def test_should_clean_pull_request(self, too_old):
        too_old.return_value = True
        pull_request = mock.MagicMock()
        opts = mock.MagicMock()
        self.assertTrue(clean.should_clean_pull_request(pull_request, opts))

        too_old.return_value = False
        pull_request = mock.MagicMock()
        opts = mock.MagicMock()
        self.assertFalse(clean.should_clean_pull_request(pull_request, opts))

    @mock.patch('github_watcher.commands.clean.too_old')
    def test_should_clean_branch(self, too_old):
        too_old.return_value = True
        branch = mock.MagicMock()
        opts = mock.MagicMock()
        self.assertTrue(clean.should_clean_branch(branch, opts))

        too_old.return_value = False
        branch = mock.MagicMock()
        opts = mock.MagicMock()
        self.assertFalse(clean.should_clean_branch(branch, opts))

    @mock.patch('github_watcher.commands.clean.clean_pull_request')
    @mock.patch('github_watcher.services.git.open_pull_requests')
    @mock.patch('github_watcher.commands.clean.clean_branch')
    @mock.patch('github_watcher.services.git.get_branches')
    @mock.patch('github_watcher.commands.clean.should_clean_branch')
    def test_main_with_only_branch_to_clean(self, should_clean_branch, get_branches, clean_branch, open_prs, clean_pr):
        conf = config.Configuration.from_json({
                'akellehe': {
                    'repos': {
                        'github_watcher': {
                            'paths': {
                                'A/PATH/TO/A/FILE.PY': [[0, 100]]
                            },
                            'regexes': ['foo', 'bar'],
                        }
                    },
                    'token': '*****',
                    'base_url': 'https://api.github.com'
                    },
                })
        branch = mock.MagicMock()
        open_prs.return_value = []
        should_clean_branch.return_value = True
        get_branches.return_value = [branch]
        now = datetime.datetime.now()
        opts = mock.MagicMock()
        opts.older_than = now.strftime('%Y-%m-%d')
        parser = mock.MagicMock()
        parser.parse_args.return_value = opts
        with mock.patch('github_watcher.commands.clean.config.Configuration.from_file') as ff:
            ff.return_value = conf
            clean.main(parser)
        assert clean_branch.called
        clean_pr.assert_not_called()

    @mock.patch('github_watcher.commands.clean.clean_pull_request')
    @mock.patch('github_watcher.services.git.open_pull_requests')
    @mock.patch('github_watcher.commands.clean.clean_branch')
    @mock.patch('github_watcher.services.git.get_branches')
    @mock.patch('github_watcher.commands.clean.should_clean_branch')
    def test_main_with_one_branch_to_clean_one_branch_not(self, should_clean_branch, get_branches, clean_branch, open_prs, clean_pr):
        conf = config.Configuration.from_json({
            'akellehe': {
                'repos': {
                    'github_watcher': {
                        'paths': {
                            'A/PATH/TO/A/FILE.PY': [[0, 100]]
                        },
                        'regexes': ['foo', 'bar'],
                    }
                },
                'token': '*****',
                'base_url': 'https://api.github.com'
            },
        })
        branch_to_clean = mock.MagicMock()
        branch_not_to_clean = mock.MagicMock()
        open_prs.return_value = []
        should_clean_branch.side_effect = [True, False]
        get_branches.return_value = [branch_to_clean, branch_not_to_clean]
        now = datetime.datetime.now()
        opts = mock.MagicMock()
        opts.older_than = now.strftime('%Y-%m-%d')
        parser = mock.MagicMock()
        parser.parse_args.return_value = opts
        with mock.patch('github_watcher.commands.clean.config.Configuration.from_file') as ff:
            ff.return_value = conf
            clean.main(parser)
        clean_branch.assert_called_once_with(branch_to_clean, opts)
        clean_pr.assert_not_called()

    @mock.patch('github_watcher.commands.clean.should_clean_pull_request')
    @mock.patch('github_watcher.commands.clean.clean_pull_request')
    @mock.patch('github_watcher.services.git.open_pull_requests')
    @mock.patch('github_watcher.commands.clean.clean_branch')
    @mock.patch('github_watcher.services.git.get_branches')
    @mock.patch('github_watcher.commands.clean.should_clean_branch')
    def test_main_with_only_pull_request_to_clean(self, should_clean_branch, get_branches, clean_branch, open_prs, clean_pr, should_clean_pull_request):
        conf = config.Configuration.from_json({
            'akellehe': {
                'repos': {
                    'github_watcher': {
                        'paths': {
                            'A/PATH/TO/A/FILE.PY': [[0, 100]]
                        },
                        'regexes': ['foo', 'bar'],
                    }
                },
                'token': '*****',
                'base_url': 'https://api.github.com'
            },
        })
        pr_to_clean = mock.MagicMock()
        open_prs.return_value = [pr_to_clean]
        get_branches.return_value = []
        should_clean_pull_request.return_value = True
        open_prs.return_value = [pr_to_clean]
        now = datetime.datetime.now()
        opts = mock.MagicMock()
        opts.older_than = now.strftime('%Y-%m-%d')
        parser = mock.MagicMock()
        parser.parse_args.return_value = opts
        with mock.patch('github_watcher.commands.clean.config.Configuration.from_file') as ff:
            ff.return_value = conf
            clean.main(parser)
        clean_branch.assert_not_called()
        clean_pr.assert_called_once_with(pr_to_clean, opts)

    @mock.patch('github_watcher.commands.clean.should_clean_pull_request')
    @mock.patch('github_watcher.commands.clean.clean_pull_request')
    @mock.patch('github_watcher.services.git.open_pull_requests')
    @mock.patch('github_watcher.commands.clean.clean_branch')
    @mock.patch('github_watcher.services.git.get_branches')
    @mock.patch('github_watcher.commands.clean.should_clean_branch')
    def test_main_with_one_pr_to_clean_one_pr_not(self, should_clean_branch, get_branches, clean_branch, open_prs, clean_pr, should_clean_pull_request):
        conf = config.Configuration.from_json({
            'akellehe': {
                'repos': {
                    'github_watcher': {
                        'paths': {
                            'A/PATH/TO/A/FILE.PY': [[0, 100]]
                        },
                        'regexes': ['foo', 'bar'],
                    }
                },
                'token': '*****',
                'base_url': 'https://api.github.com'
            },
        })
        pr_to_clean = mock.MagicMock()
        pr_not_to_clean = mock.MagicMock()
        open_prs.return_value = [pr_to_clean, pr_not_to_clean]
        get_branches.return_value = []
        should_clean_pull_request.side_effect = [True, False]
        now = datetime.datetime.now()
        opts = mock.MagicMock()
        opts.older_than = now.strftime('%Y-%m-%d')
        parser = mock.MagicMock()
        parser.parse_args.return_value = opts
        with mock.patch('github_watcher.commands.clean.config.Configuration.from_file') as ff:
            ff.return_value = conf
            clean.main(parser)
        clean_branch.assert_not_called()
        clean_pr.assert_called_once_with(pr_to_clean, opts)

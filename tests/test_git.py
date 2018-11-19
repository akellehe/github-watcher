import unittest
import unittest.mock as mock


from github_watcher.services import git


class TestGit(unittest.TestCase):

    def test_open_pull_requests(self):
        base_url = 'my base url'
        access_token = '*******'
        user = 'akellehe'
        repo = 'github-watcher'
        prs = [1, 2, 3, 4, 5]
        github = mock.MagicMock()
        with mock.patch('github_watcher.services.git.Github', return_value=github):
            Repo = mock.MagicMock()
            Repo.get_pulls.return_value = prs
            get_repo = mock.MagicMock()
            get_repo.return_value = Repo

            github.get_repo = get_repo

            target = [pr for pr in git.open_pull_requests(base_url, access_token, user, repo)]
            self.assertEqual(prs, target)

    def test_construct_compare_url(self):
        base_url = 'all of your base'
        base = mock.MagicMock()
        head = mock.MagicMock()
        user = mock.MagicMock()

        pull_request = mock.MagicMock()
        pull_request.base = base
        pull_request.head = head
        pull_request.head.user = user

        base.user.login = 'akellehe'
        head.user.login = 'akelleh'
        base.repo.name = 'github-watcher'
        base.sha = '12345'
        head.sha = '56789'

        url = git.construct_compare_url(base_url, pull_request)
        self.assertEqual(url, 'all of your base/repos/akellehe/github-watcher/compare/akellehe:12345...akelleh:56789')

    def test_get_sentinel_diff_headers(self):
        target = git.get_sentinel_diff_headers()
        diff_headers = "diff --git a/{filename} b/{filename}\n"
        diff_headers += "index foo..bar 100644\n"
        diff_headers += "--- a/{filename}\n"
        diff_headers += "+++ b/{filename}\n"

        self.assertEqual(diff_headers, target)

    def test_noop_diff(self):
        base_url = 'all of your base'
        base = mock.MagicMock()
        head = mock.MagicMock()
        user = mock.MagicMock()

        pull_request = mock.MagicMock()
        pull_request.base = base
        pull_request.head = head
        pull_request.head.user = user

        base.user.login = 'akellehe'
        head.user.login = 'akelleh'
        base.repo.name = 'github-watcher'
        base.sha = '12345'
        head.sha = '56789'

        with self.assertRaisesRegex(git.Noop, "Pull request effects no files"):
            with mock.patch('requests.get') as requests_get:
                resp = mock.MagicMock()
                requests_get.return_value = resp
                resp.json = mock.MagicMock()
                resp.json.return_value = {
                    'files': None
                }
                git.diff(base_url, '*****', pull_request)

    def test_empty_diff(self):
        base_url = 'all of your base'
        base = mock.MagicMock()
        head = mock.MagicMock()
        user = mock.MagicMock()

        pull_request = mock.MagicMock()
        pull_request.base = base
        pull_request.head = head
        pull_request.head.user = user

        base.user.login = 'akellehe'
        head.user.login = 'akelleh'
        base.repo.name = 'github-watcher'
        base.sha = '12345'
        head.sha = '56789'

        head_files = [{
            'filename': 'my head file',
            'patch': None
        }]

        expected = ''

        with mock.patch('requests.get') as requests_get:
            resp = mock.MagicMock()
            requests_get.return_value = resp
            resp.json = mock.MagicMock()
            resp.json.return_value = {
                'files': head_files
            }
            complete_diff = git.diff(base_url, '*****', pull_request)
            self.assertEqual(complete_diff, expected)

    def test_diff(self):
        base_url = 'all of your base'
        base = mock.MagicMock()
        head = mock.MagicMock()
        user = mock.MagicMock()

        pull_request = mock.MagicMock()
        pull_request.base = base
        pull_request.head = head
        pull_request.head.user = user

        base.user.login = 'akellehe'
        head.user.login = 'akelleh'
        base.repo.name = 'github-watcher'
        base.sha = '12345'
        head.sha = '56789'

        head_files = [{
            'filename': 'my head file',
            'patch': 'foo bar biz baz'
        }]

        expected = """diff --git a/my head file b/my head file
index foo..bar 100644
--- a/my head file
+++ b/my head file
foo bar biz baz
"""

        with mock.patch('requests.get') as requests_get:
            resp = mock.MagicMock()
            requests_get.return_value = resp
            resp.json = mock.MagicMock()
            resp.json.return_value = {
                'files': head_files
            }
            complete_diff = git.diff(base_url, '*****', pull_request)
            self.assertEqual(complete_diff, expected)

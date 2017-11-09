Github Watcher
==============

Github Watcher is a daemon that monitors the files, line ranges, and directories in a repository you configure it to watch. When there is a pull request sent to that repository making a change to something you're watching; you'll get an OSX notification. There's also a really annoying voice that tells you what was found.

Installation
------------

You'll need to create a github access token with `repo` and `user` permissions. Add that token to a file at `~/.github`. We'll need it to authenticate with your repos.

Next you can just pull this down like

```bash
git pull git@github.com:akellehe/github-watcher.git ./github-watcher
```

and install it like

```bash
python setup.py install
```

Now you have an executable probably located at `/usr/local/bin/github-watcher`. Wherever it is it's on your path now and you can run

```
>> github-watcher
```

from anywhere you like. Daemonize it how you see fit... I have mine set up in my dotfile `~/.bash_profile` with a simple guard...

```bash
if [[ -z "$(pgrep -f github-watcher)" ]]; then
    github-watcher 2>1 >> /dev/null &
fi
```

but you can probably do something more clever like using daemontools or init.d or whatever your preferred service manager is. If you do one of those implementations [let me know!](mailto:keats.kelleher@gmail.com).


Configuration
-------------

Github Watcher expects a `.yml` formatted config file at `~/.github-watcher.yml`. The file should be of the format:

```yaml
---

username:
  repository_name:
    filepath1:
      - [starting_line1, stopping_line1]
      - [starting_line2, stopping_line2]
    filepath2:
      - [starting_line1, stopping_line1]
    directory_path: null
```

So, for example, if I wanted to watch [this](https://github.com/akellehe/fb_calendar/blob/8cc6e867aa67732fab869872eec7586fd1a9c0c2/deploy/roles/fb_calendar_api/tasks/main.yml#L30-L40) line range I would use the configuration:

```yaml
---

akellehe:
  fb_calendar:
    deploy/roles/fb_calendar_api/tasks/main.yml
      - [30, 40]
```

Or if I wanted to watch the whole `deploy/` directory I would use:

```yaml
---

akellehe:
  fb_calendar:
    deploy/: null
```

If you need to use this on github enterprise you'll have to specify the API base url yourself. For example...

```yaml
---

github_api_base_url: https://[your site name]/api/v3
akellehe:
  fb_calendar:
    deploy/: null

```

Execution
---------

To run this after it's configured you can just do:

```bash
python watcher.py
```

If you want to run it in the background you can do:

```bash
python watcher.py &
```

[![Build Status](https://travis-ci.org/akellehe/github-watcher.svg?branch=master)](https://travis-ci.org/akellehe/github-watcher)

Github Watcher
==============

Github Watcher is a daemon that monitors the files, line ranges, and directories in a repository you configure it to watch. When there is a pull request sent to that repository making a change to something you're watching; you'll get an OSX notification. There's also a really annoying voice that tells you what was found.


Configuration
-------------

If you want to skip a lot of configuration you can run `github-watcher` as a one-off using the `check` action:

```bash
github-watcher check --repo [your repo name] --user [your username] --filepath path/to/your/file.py --github-url https://[site name]/api/v3
```

You only need to specify your `--github-url` if you're using Github Enterprise. Otherwise you can leave that argument out. This will run, looking for files matching your args _once_, then exit. You can get help on CLI args `github-watcher` accepts by passing the `-h` or `--help` option. If you want to daemonize `github-watcher` it will take some configuration.

You can configure `github-watcher` after you install it by running `github-watcher config`. Just follow the prompts and your config will be written to `~/.github-watcher.yml`. If you mess up it's ok, just edit the file manually after you exit or re-run `github-watcher config`.

You can also use this tool to edit existing configs, but only to add to them. If you want to delete something you have to do it manually.

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


Installation
------------

You'll need to create a github access token with `repo` and `user` permissions. Add that token to a file at `~/.github`. We'll need it to authenticate with your repos.

Next you can install via pip

```bash
pip install github_watcher
```

Or you can just pull this down like

```bash
git pull git@github.com:akellehe/github-watcher.git ./github-watcher
```

and install it like

```bash
python setup.py install
```


Execution
---------

Now you have an executable probably located at `/usr/local/bin/github-watcher`. Wherever it is it's on your path now and you can run

```
>> github-watcher run
```

from anywhere you like. You can run it in the background by adding an `&`.

```
>> github-watcher run &
```

Daemonize it how you see fit... I have mine set up in my dotfile `~/.bash_profile` with a simple guard...

```bash
if [[ -z "$(pgrep -f github-watcher)" ]]; then
    github-watcher run 2> > /dev/null &
fi
```

but you can probably do something more clever like using daemontools or init.d or whatever your preferred service manager is. If you do one of those implementations [let me know!](mailto:keats.kelleher@gmail.com).

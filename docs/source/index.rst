github_watcher
==============

`github_watcher` watches for pull requests on repositories you specify. When it finds them, it checks them against directories, files, and lines in which you're interested in keeping an eye out for changes. If something is changed, it will send you a desktop notification (Linux and OSX only).

This project is developed in Python3. You can install it with `pip3` from the python package index:

.. code-block:: bash

   pip3 install github_watcher

After that it will be added to your `PATH`. To get it configured and running on your machine you can either add your own configuration manually (details below) or you can run 

.. code-block:: bash

   github-watcher config

To run through a prompt. It will write a file at `~/.github-watcher.yml`. Feel free to modify that file as your needs change.

For more information on configuration and authentication, check out these primers.

.. toctree::
   :maxdepth: 0

   authentication
   configuration

Running github_watcher
----------------------

To set up `github_watcher` as a daemon, you can just run it like

.. code-block:: bash

   github-watcher run 

If something is going funky you can get verbose output like

.. code-block:: bash

   github-watcher run --verbose

There are a bunch of other options you can pass. Get a complete listing by passing the "help" flag

.. code-block:: bash

   github-watcher --help


.. automodule:: github_watcher.commands.run

.. automodule:: github_watcher.commands.clean


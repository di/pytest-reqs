py.test plugin for checking requirements files
==================================================

Description
-----------

This plugin checks your requirements files for specific versions, and compares
those versions with the installed libraries in your environment, failing your
test suite if any are invalid or out of date.

This is useful for keeping virtual environments up-to-date, and ensuring that
your test suite is always being passed with the requirements you have
specified.

It also has the added bonus of verifying that your requirements files are
syntatically valid, and can check if there are new releases of your
dependencies available.

Usage
-----

install via::

    pip install pytest-reqs

if you then type::

    py.test --reqs

by default it will search for dependencies in the files matching:

- ``req*.txt``
- ``req*.pip``
- ``requirements/*.txt``
- ``requirements/*.pip``

and the declared dependencies will be checked against the current environment.

A little example
----------------

If your environment has dependencies installed like this::

    $ pip freeze
    foo==0.9.9

But you have a ``requirements.txt`` file like this::

    $ cat requirements.txt
    foo==1.0.0

you can run ``py.test`` with the plugin installed::

    $ py.test --reqs
    =================================== FAILURES ===================================
    ______________________________ requirements-check ______________________________
    Distribution "foo" requires foo==1.0.0 (from -r requirements.txt (line 1)) but
    0.9.9 is installed

It also handles ``pip``'s version containment syntax (e.g, ``foo<=1.0.0``,
``foo>=1.0.0``, etc)::

    $ py.test --reqs
    =================================== FAILURES ===================================
    ______________________________ requirements-check ______________________________
    Distribution "foo" requires foo>=1.0.0 (from -r requirements.txt (line 1)) but
    0.9.9 is installed

Furthermore, it will tell you if your requirements file is invalid (for
example, if there is not enough ``=`` symbols)::

    $ py.test --reqs
    ______________________________ requirements-check ______________________________
    Invalid requirement: 'foo=1.0.0' (from -r requirements.txt)


Configuring options
-------------------

Ignoring local projects
~~~~~~~~~~~~~~~~~~~~~~~

You might have requirements files with paths to local projects, e.g. for local
development::

    $ cat requirements/local_development.txt
    -e ../foo

However, testing these requirements will fail if the test environment is
missing the local project (e.g., on a CI build)::

    =================================== FAILURES ===================================
    ______________________________ requirements-check ______________________________
    ../foo should either be a path to a local project or a VCS url beginning with
    svn+, git+, hg+, or bzr+ (from -r requirements.txt)

To get around this, you can disable checking for local projects with the
following ``pytest`` option::

    # content of setup.cfg
    [pytest]
    reqsignorelocal = True

Declaring your own filename patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You might have requirements files in files other than the default filename
patterns:

- ``req*.txt``
- ``req*.pip``
- ``requirements/*.txt``
- ``requirements/*.pip``

While there aren't any restrictions on what filenames are or are not valid for
requirements files, the patterns which are currently supported by
``pytest-reqs`` are the same common patterns supported by other automated tools
around requirements files.

However, you can override these default patterns with the following ``pytest``
option::

    # content of setup.cfg
    [pytest]
    reqsfilenamepatterns =
        mycustomrequirementsfile.txt
        someotherfilename.ext

Running ``pytest-reqs`` before any other tests
----------------------------------------------

Currently there is no way to define the order of pytest plugins (see
`pytest-dev/pytest#935 <https://github.com/pytest-dev/pytest/issues/935>`__)

This means that if you don't use any other plugins, ``pytest-reqs`` will run
it's tests last. If you do use other plugins, there is no way to guarantee when
the ``pytest-reqs`` tests will be run.

If you absolutely need to run ``pytest-reqs`` before any other tests and
plugins, instead of using the ``--reqs`` flag, you can define a
``tests/conftest.py`` file as follows:

.. code-block:: python

    from pytest_reqs import check_requirements

    def pytest_collection_modifyitems(config, session, items):
        check_requirements(config, session, items)

Running requirements checks and no other tests
----------------------------------------------

You can also restrict your test run to only perform "reqs" tests and not any
other tests by typing::

    py.test --reqs -m reqs

This will only run test items with the "reqs" marker which this plugin adds
dynamically.

Checking for out-of-date dependencies
-------------------------------------

You can use the ``--reqs-outdated`` flag to determine if any of your
dependencies are out-of-date::

    $ py.test --reqs-outdated
    ______________________________ requirements-check ______________________________
    Distribution "foo" is outdated (from -r requirements.txt (line 1)),
    latest version is foo==1.0.1

This feature is only available with ``pip>=9.0.0``.

Authors
-------

-  `Dustin Ingram <https://github.com/di>`__
-  `Victor Titor <https://github.com/vtitor>`__

License
-------

Open source MIT license.

Notes
-----

The repository of this plugin is at http://github.com/di/pytest-reqs.

For more info on py.test see http://pytest.org.

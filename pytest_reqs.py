
from distutils.util import strtobool
from glob import glob
from itertools import chain
from json import loads
from os import devnull
from subprocess import check_output
from sys import executable
from warnings import warn

import packaging.version
import pytest
from pkg_resources import get_distribution

max_version = packaging.version.parse('18.1.0')
pip_version = packaging.version.parse(get_distribution('pip').version)
if pip_version > max_version:
    warn(
        'Version pip=={} is possibly incompatible, highest '
        'known compatible version is {}.'.format(
            pip_version, max_version
        )
    )

from pip import get_installed_distributions  # noqa
from pip.download import PipSession  # noqa
from pip.exceptions import InstallationError  # noqa
from pip.req import parse_requirements  # noqa


__version__ = '0.0.4'

DEFAULT_PATTERNS = [
    'req*.txt', 'req*.pip', 'requirements/*.txt', 'requirements/*.pip'
]


def pytest_addoption(parser):
    group = parser.getgroup('general')
    group.addoption(
        '--reqs', action='store_true',
        help='check requirements files against what is installed'
    )
    group.addoption(
        '--reqs-outdated', action='store_true',
        help='check requirements files for updates'
    )
    parser.addini(
        'reqsignorelocal',
        help='ignore local requirements (default: False)',
    )
    parser.addini(
        'reqsfilenamepatterns',
        help='Override the default filename patterns to search (default:'
             'req*.txt, req*.pip, requirements/*.txt, requirements/*.pip)',
        type='linelist',
    )


def pytest_sessionstart(session):
    config = session.config
    if not hasattr(config, 'ignore_local'):
        ignore_local = config.getini('reqsignorelocal') or 'no'
        config.ignore_local = strtobool(ignore_local)
    if not hasattr(config, 'patterns'):
        config.patterns = config.getini('reqsfilenamepatterns')


def pytest_collection_modifyitems(config, session, items):
    if config.option.reqs:
        check_requirements(config, session, items)
    if config.option.reqs_outdated:
        check_outdated_requirements(config, session, items)


def get_reqs_filenames(config):
    patterns = config.patterns or DEFAULT_PATTERNS
    return set(chain.from_iterable(map(glob, patterns)))


def check_requirements(config, session, items):
    installed_distributions = dict(
        (d.project_name.lower(), d)
        for d in get_installed_distributions()
    )

    items.extend(
        ReqsItem(filename, installed_distributions, config, session)
        for filename in get_reqs_filenames(config)
    )


def check_outdated_requirements(config, session, items):
    local_pip_version = packaging.version.parse(
        get_distribution('pip').version
    )
    required_pip_version = packaging.version.parse('9.0.0')

    if local_pip_version >= required_pip_version:
        with open(devnull, 'w') as DEVNULL:
            pip_outdated_dists = loads(check_output(
                [executable, '-m', 'pip', 'list', '-o', '--format', 'json'],
                stderr=DEVNULL
            ))

            items.extend(
                OutdatedReqsItem(filename, pip_outdated_dists, config, session)
                for filename in get_reqs_filenames(config)
            )


class PipOption:
    def __init__(self, config):
        self.skip_requirements_regex = '^-e' if config.ignore_local else ''
        self.isolated_mode = False
        self.default_vcs = None


class ReqsError(Exception):
    """ indicates an error during requirements checks. """


class ReqsItem(pytest.Item, pytest.File):

    def __init__(self, filename, installed_distributions, config, session):
        super(ReqsItem, self).__init__(
            filename, config=config, session=session
        )
        self.add_marker('reqs')
        self.filename = filename
        self.installed_distributions = installed_distributions
        self.config = config

    def get_requirements(self):
        reqs = parse_requirements(
            self.filename, session=PipSession(), options=PipOption(self.config)
        )
        try:
            name_to_req = dict(
                (r.name.lower(), r)
                for r in reqs
                if r.name and self.filename in r.comes_from
            )
        except InstallationError as e:
            raise ReqsError('%s (from -r %s)' % (
                e.args[0].split('\n')[0],
                self.filename,
            ))
        return name_to_req

    def runtest(self):
        for name, req in self.get_requirements().items():
            try:
                installed_distribution = self.installed_distributions[name]
            except KeyError:
                raise ReqsError(
                    'Distribution "%s" is not installed' % (name)
                )
            if not req.specifier.contains(installed_distribution.version):
                raise ReqsError(
                    'Distribution "%s" requires %s but %s is installed' % (
                        installed_distribution.project_name,
                        req,
                        installed_distribution.version,
                    ))

    def repr_failure(self, excinfo):
        if excinfo.errisinstance(ReqsError):
            return excinfo.value.args[0]
        return super(ReqsItem, self).repr_failure(excinfo)

    def reportinfo(self):
        return (self.fspath, -1, 'requirements-check')


class OutdatedReqsItem(ReqsItem):
    def __init__(self, filename, pip_outdated_dists, config, session):
        super(ReqsItem, self).__init__(
            filename, config=config, session=session
        )
        self.add_marker('reqs-outdated')
        self.filename = filename
        self.pip_outdated_dists = pip_outdated_dists
        self.config = config

    def runtest(self):
        for name, req in self.get_requirements().items():
            for dist in self.pip_outdated_dists:
                if name == dist['name']:
                    raise ReqsError(
                        'Distribution "%s" is outdated (from %s), '
                        'latest version is %s==%s' % (
                            name,
                            req.comes_from,
                            name,
                            dist['latest_version']
                        ))

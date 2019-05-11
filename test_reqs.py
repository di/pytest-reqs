from distutils.version import LooseVersion
from pip_api._installed_distributions import Distribution
from pkg_resources import get_distribution

from pretend import stub
import pytest

pytest_plugins = ("pytester",)


def test_version():
    import pytest_reqs

    assert pytest_reqs.__version__


@pytest.fixture
def mock_dist():
    return Distribution(name="foo", version="1.0")


@pytest.mark.parametrize(
    "requirements", ["foo", "Foo", "foo==1.0", "foo>=1.0", "foo<=1.0", "# comment"]
)
def test_existing_requirement(requirements, mock_dist, testdir, monkeypatch):
    testdir.makefile(".txt", requirements=requirements)
    monkeypatch.setattr(
        "pytest_reqs.pip_api.installed_distributions",
        lambda: {mock_dist.name: mock_dist},
    )

    result = testdir.runpytest("--reqs")
    assert "passed" in result.stdout.str()


@pytest.mark.parametrize(
    "requirements, dist",
    [
        ("foo-bar", stub(name="foo-bar", version="1.0")),
        ("foo-bar==1.0", stub(name="foo-bar", version="1.0")),
        # Capitalization
        ("Foo-bar", stub(name="foo-bar", version="1.0")),
        ("foo-bar", stub(name="Foo-bar", version="1.0")),
        # Periods
        ("foo.bar", stub(name="foo-bar", version="1.0")),
        ("foo-bar", stub(name="foo.bar", version="1.0")),
        # Underscores
        ("foo_bar", stub(name="foo-bar", version="1.0")),
        ("foo-bar", stub(name="foo_bar", version="1.0")),
    ],
)
def test_canonicalization(requirements, dist, testdir, monkeypatch):
    testdir.makefile(".txt", requirements=requirements)
    monkeypatch.setattr(
        "pytest_reqs.pip_api.installed_distributions", lambda: {dist.name: dist}
    )

    result = testdir.runpytest("--reqs")
    assert "passed" in result.stdout.str()


def test_missing_requirement(mock_dist, testdir, monkeypatch):
    testdir.makefile(".txt", requirements="foo")
    monkeypatch.setattr("pytest_reqs.pip_api.installed_distributions", lambda: {})

    result = testdir.runpytest("--reqs")
    result.stdout.fnmatch_lines(['*Distribution "foo" is not installed*', "*1 failed*"])
    assert "passed" not in result.stdout.str()


@pytest.mark.parametrize("requirements", ["foo==2.0", "foo>1.0", "foo<1.0"])
def test_wrong_version(requirements, mock_dist, testdir, monkeypatch):
    testdir.makefile(".txt", requirements=requirements)
    monkeypatch.setattr(
        "pytest_reqs.pip_api.installed_distributions",
        lambda: {mock_dist.name: mock_dist},
    )

    result = testdir.runpytest("--reqs")
    result.stdout.fnmatch_lines(
        ['*Distribution "foo" requires %s*' % (requirements), "*1 failed*"]
    )
    assert "passed" not in result.stdout.str()


@pytest.mark.parametrize("requirements", ["foo=1.0", "foo=>1.0"])
def test_invalid_requirement(requirements, mock_dist, testdir, monkeypatch):
    testdir.makefile(".txt", requirements=requirements)
    monkeypatch.setattr(
        "pytest_reqs.pip_api.installed_distributions",
        lambda: {mock_dist.name: mock_dist},
    )

    result = testdir.runpytest("--reqs")
    result.stdout.fnmatch_lines(["*Invalid requirement*", "*1 failed*"])

    assert "passed" not in result.stdout.str()


def test_missing_local_requirement(testdir, monkeypatch):
    testdir.makefile(".txt", requirements="-e ../foo")
    monkeypatch.setattr("pytest_reqs.pip_api.installed_distributions", lambda: {})

    result = testdir.runpytest("--reqs")
    result.stdout.fnmatch_lines(["*foo should either be a path to a local project*"])
    assert "passed" not in result.stdout.str()


def test_local_requirement_ignored(testdir, monkeypatch):
    testdir.makefile(".txt", requirements="-e ../foo")
    testdir.makeini("[pytest]\nreqsignorelocal=True")
    monkeypatch.setattr("pytest_reqs.pip_api.installed_distributions", lambda: {})

    result = testdir.runpytest("--reqs")
    assert "passed" in result.stdout.str()


def test_local_requirement_ignored_using_dynamic_config(testdir, monkeypatch):
    testdir.makefile(".txt", requirements="-e ../foo")
    testdir.makeconftest(
        """
    def pytest_configure(config):
        config.ignore_local = True
    """
    )
    monkeypatch.setattr("pytest_reqs.pip_api.installed_distributions", lambda: {})

    result = testdir.runpytest("--reqs")
    assert "passed" in result.stdout.str()


def test_no_option(testdir, monkeypatch):
    testdir.makefile(".txt", requirements="foo")
    monkeypatch.setattr("pytest_reqs.pip_api.installed_distributions", lambda: {})

    result = testdir.runpytest()
    assert "collected 0 items" in result.stdout.str()


def test_override_filenamepatterns(testdir, monkeypatch):
    testdir.makefile(".txt", a="foo")
    testdir.makefile(".txt", b="bar")
    testdir.makeini("[pytest]\nreqsfilenamepatterns=\n    a.txt\n    b.txt")
    monkeypatch.setattr(
        "pytest_reqs.pip_api.installed_distributions",
        lambda: {
            "bar": stub(name="bar", version="1.0"),
            "foo": stub(name="foo", version="1.0"),
        },
    )

    result = testdir.runpytest("--reqs")
    assert "passed" in result.stdout.str()


def test_override_filenamepatterns_using_dynamic_config(testdir, monkeypatch):
    testdir.makefile(".txt", a="foo")
    testdir.makefile(".txt", b="bar")
    testdir.makeconftest(
        """
    def pytest_configure(config):
        config.patterns = ['a.txt', 'b.txt']
    """
    )
    monkeypatch.setattr(
        "pytest_reqs.pip_api.installed_distributions",
        lambda: {
            "bar": stub(name="bar", version="1.0"),
            "foo": stub(name="foo", version="1.0"),
        },
    )

    result = testdir.runpytest("--reqs")
    assert "passed" in result.stdout.str()


@pytest.mark.skipif(
    LooseVersion("9.0.0") > LooseVersion(get_distribution("pip").version),
    reason="incompatible pip version",
)
@pytest.mark.parametrize("requirements", ["foo", "foo==1.0"])
def test_outdated_version(requirements, testdir, monkeypatch):
    testdir.makefile(".txt", requirements=requirements)
    pip_outdated_dists_output = '[{"name": "foo", "latest_version": "1.0.1"}]'
    monkeypatch.setattr(
        "pytest_reqs.check_output", lambda *_, **__: pip_outdated_dists_output
    )

    result = testdir.runpytest("--reqs-outdated")
    result.stdout.fnmatch_lines(
        [
            '*Distribution "foo" is outdated (from -r requirements.txt (line 1)), '
            "latest version is foo==1.0.1*",
            "*1 failed*",
        ]
    )
    assert "passed" not in result.stdout.str()

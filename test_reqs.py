import pip
from pretend import stub
import pytest

pytest_plugins = "pytester",


def test_version():
    import pytest_reqs
    assert pytest_reqs.__version__


@pytest.fixture
def mock_dist():
    return stub(project_name='foo', version='1.0')


@pytest.mark.parametrize('requirements', [
    'foo',
    'foo==1.0',
    'foo>=1.0',
    'foo<=1.0',
])
def test_existing_requirement(requirements, mock_dist, testdir, monkeypatch):
    testdir.makefile('.txt', requirements=requirements)
    monkeypatch.setattr(
        'pytest_reqs.get_installed_distributions',
        lambda: [mock_dist]
    )

    result = testdir.runpytest("--reqs")
    assert 'passed' in result.stdout.str()


def test_missing_requirement(mock_dist, testdir, monkeypatch):
    testdir.makefile('.txt', requirements='foo')
    monkeypatch.setattr('pytest_reqs.get_installed_distributions', lambda: [])

    result = testdir.runpytest("--reqs")
    result.stdout.fnmatch_lines([
        '*Distribution "foo" is not installed*',
        "*1 failed*",
    ])
    assert 'passed' not in result.stdout.str()


@pytest.mark.parametrize('requirements', [
    'foo==2.0',
    'foo>1.0',
    'foo<1.0',
])
def test_wrong_version(requirements, mock_dist, testdir, monkeypatch):
    testdir.makefile('.txt', requirements=requirements)
    monkeypatch.setattr(
        'pytest_reqs.get_installed_distributions',
        lambda: [mock_dist]
    )

    result = testdir.runpytest("--reqs")
    result.stdout.fnmatch_lines([
        '*Distribution "foo" requires %s*' % (requirements),
        "*1 failed*",
    ])
    assert 'passed' not in result.stdout.str()


@pytest.mark.parametrize('requirements', [
    'foo=1.0',
    'foo=>1.0',
])
def test_invalid_requirement(requirements, mock_dist, testdir, monkeypatch):
    testdir.makefile('.txt', requirements='foo=1.0')
    monkeypatch.setattr(
        'pytest_reqs.get_installed_distributions',
        lambda: [mock_dist]
    )

    result = testdir.runpytest("--reqs")
    if pip.__version__ < '8.0.0':
        result.stdout.fnmatch_lines([
            '*RequirementParseError*',
            "*1 failed*",
        ])
    else:
        result.stdout.fnmatch_lines([
            '*Invalid requirement*',
            "*1 failed*",
        ])
    assert 'passed' not in result.stdout.str()

from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from tracker.fetcher import TemplateFetcher
from tracker.models import RepoInfo


def _make_mock_repo(full_name="tuna/thuthesis", stars=3800):
    """Create a mock GitHub Repository object."""
    repo = MagicMock()
    repo.full_name = full_name
    repo.stargazers_count = stars
    repo.forks_count = 100
    repo.open_issues_count = 10
    repo.updated_at = datetime.utcnow()
    return repo


def _make_mock_release(tag_name="v7.5.0", days_ago=30):
    """Create a mock GitHub Release object."""
    release = MagicMock()
    release.tag_name = tag_name
    release.published_at = datetime.utcnow() - timedelta(days=days_ago)
    return release


def _make_mock_commit(days_ago=10):
    """Create a mock GitHub Commit object."""
    commit = MagicMock()
    commit.commit.author.date = datetime.utcnow() - timedelta(days=days_ago)
    return commit


@patch("tracker.fetcher.Github")
def test_fetch_basic_info(MockGithub):
    mock_repo = _make_mock_repo()
    MockGithub.return_value.get_repo.return_value = mock_repo

    fetcher = TemplateFetcher(token="fake")
    info = RepoInfo(id="tuna/thuthesis", university="清华大学")
    result = fetcher.fetch(info)

    assert result.stars == 3800
    assert result.forks == 100
    assert result.open_issues == 10
    assert result.error is None


@patch("tracker.fetcher.Github")
def test_fetch_release_info(MockGithub):
    mock_repo = _make_mock_repo()
    mock_release = _make_mock_release(tag_name="v7.5.0", days_ago=30)
    mock_repo.get_releases.return_value = [mock_release]
    MockGithub.return_value.get_repo.return_value = mock_repo

    fetcher = TemplateFetcher(token="fake")
    info = RepoInfo(id="tuna/thuthesis", university="清华大学")
    result = fetcher.fetch(info)

    assert result.latest_release == "v7.5.0"
    assert result.release_date is not None


@patch("tracker.fetcher.Github")
def test_fetch_no_release_uses_tags(MockGithub):
    mock_repo = _make_mock_repo()
    mock_repo.get_releases.return_value = []
    mock_tag = MagicMock()
    mock_tag.name = "v7.4.0"
    mock_repo.get_tags.return_value = [mock_tag]
    MockGithub.return_value.get_repo.return_value = mock_repo

    fetcher = TemplateFetcher(token="fake")
    info = RepoInfo(id="tuna/thuthesis", university="清华大学")
    result = fetcher.fetch(info)

    assert result.latest_release == "v7.4.0"


@patch("tracker.fetcher.Github")
def test_fetch_handles_api_error(MockGithub):
    MockGithub.return_value.get_repo.side_effect = Exception("API Error")

    fetcher = TemplateFetcher(token="fake")
    info = RepoInfo(id="bad/repo", university="测试")
    result = fetcher.fetch(info)

    assert result.error is not None
    assert "API Error" in result.error


@patch("tracker.fetcher.Github")
def test_detect_latex3_feature(MockGithub):
    mock_repo = _make_mock_repo()
    mock_file = MagicMock()
    mock_file.path = "thuthesis.cls"
    mock_file.decoded_content = b"\\ProvidesExplClass{thuthesis}"
    mock_repo.get_contents.return_value = [mock_file]
    MockGithub.return_value.get_repo.return_value = mock_repo

    fetcher = TemplateFetcher(token="fake")
    info = RepoInfo(id="tuna/thuthesis", university="清华大学")
    result = fetcher.fetch(info)

    assert "LaTeX3" in result.features


@patch("tracker.fetcher.Github")
def test_detect_overleaf_feature(MockGithub):
    mock_repo = _make_mock_repo()
    mock_file = MagicMock()
    mock_file.path = "overleaf.tex"
    mock_repo.get_contents.return_value = [mock_file]
    mock_repo.get_readme.return_value = MagicMock(decoded_content=b"# Thuthesis\nUse on Overleaf")
    MockGithub.return_value.get_repo.return_value = mock_repo

    fetcher = TemplateFetcher(token="fake")
    info = RepoInfo(id="tuna/thuthesis", university="清华大学")
    result = fetcher.fetch(info)

    assert "Overleaf" in result.features

from unittest.mock import MagicMock, patch

from tracker.discover import TemplateDiscoverer
from tracker.models import RepoInfo, RepoSource


def _make_search_result(full_name, stars=50, description="LaTeX thesis template"):
    repo = MagicMock()
    repo.full_name = full_name
    repo.stargazers_count = stars
    repo.description = description
    return repo


@patch("tracker.discover.Github")
def test_discover_finds_new_repos(MockGithub):
    search_result = MagicMock()
    search_result.totalCount = 1
    search_result.__iter__ = MagicMock(
        return_value=iter([_make_search_result("new-school/thesis", stars=100)])
    )
    MockGithub.return_value.search_repositories.return_value = search_result

    discoverer = TemplateDiscoverer(token="fake")
    existing = [RepoInfo(id="tuna/thuthesis", university="清华大学")]
    candidates = discoverer.discover(existing)

    assert len(candidates) == 1
    assert candidates[0].id == "new-school/thesis"
    assert candidates[0].source == RepoSource.DISCOVERED


@patch("tracker.discover.Github")
def test_discover_skips_existing_repos(MockGithub):
    search_result = MagicMock()
    search_result.totalCount = 1
    search_result.__iter__ = MagicMock(
        return_value=iter([_make_search_result("tuna/thuthesis", stars=3800)])
    )
    MockGithub.return_value.search_repositories.return_value = search_result

    discoverer = TemplateDiscoverer(token="fake")
    existing = [RepoInfo(id="tuna/thuthesis", university="清华大学")]
    candidates = discoverer.discover(existing)

    assert len(candidates) == 0


@patch("tracker.discover.Github")
def test_discover_handles_api_error(MockGithub):
    MockGithub.return_value.search_repositories.side_effect = Exception("Rate limited")

    discoverer = TemplateDiscoverer(token="fake")
    candidates = discoverer.discover([])

    assert candidates == []

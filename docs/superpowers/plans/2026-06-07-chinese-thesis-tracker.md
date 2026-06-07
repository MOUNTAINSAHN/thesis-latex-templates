# Chinese Thesis LaTeX Template Tracker — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python tool that tracks Chinese university LaTeX thesis templates on GitHub, generating Markdown reports via GitHub Actions.

**Architecture:** A Python package (`tracker`) with four modules — `fetcher` (GitHub API data), `discover` (find new repos), `generator` (Markdown output), `models` (data structures). Orchestrated by `main.py`, run weekly via GitHub Actions.

**Tech Stack:** Python 3.10+, PyGithub, GitHub Actions

---

## File Map

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Project metadata, dependencies, entry point |
| `requirements.txt` | Pinned dependencies for CI |
| `tracker/__init__.py` | Package marker |
| `tracker/models.py` | `RepoInfo` dataclass — single source of truth for data shape |
| `tracker/fetcher.py` | Fetch repo metadata + detect features via GitHub API |
| `tracker/discover.py` | Search GitHub for new template repos |
| `tracker/generator.py` | Render `RepoInfo` list to Markdown files |
| `tracker/main.py` | Orchestrate: load → discover → fetch → generate → save |
| `data/repos.json` | Seed list of known template repos |
| `output/README.md` | Generated main page (auto-committed) |
| `output/universities/*.md` | Generated per-school pages (auto-committed) |
| `.github/workflows/update.yml` | Weekly cron + manual trigger |
| `tests/test_models.py` | Model tests |
| `tests/test_fetcher.py` | Fetcher tests (mocked API) |
| `tests/test_discover.py` | Discovery tests (mocked API) |
| `tests/test_generator.py` | Generator tests |

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `tracker/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "thesis-tracker"
version = "0.1.0"
description = "Track Chinese university LaTeX thesis templates on GitHub"
requires-python = ">=3.10"
dependencies = [
    "PyGithub>=2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-mock>=3.10",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create `requirements.txt`**

```
PyGithub>=2.1.0
```

- [ ] **Step 3: Create package markers**

`tracker/__init__.py`:
```python
"""Track Chinese university LaTeX thesis templates on GitHub."""
```

`tests/__init__.py`:
```python
```

- [ ] **Step 4: Install and verify**

```bash
cd /data1/shanhuang/Project/thesis_ZN
pip install -e ".[dev]"
python -c "from tracker import __doc__; print(__doc__)"
```

Expected: `Track Chinese university LaTeX thesis templates on GitHub.`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml requirements.txt tracker/__init__.py tests/__init__.py
git commit -m "chore: scaffold project structure"
```

---

### Task 2: Data Models

**Files:**
- Create: `tracker/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

`tests/test_models.py`:
```python
from tracker.models import RepoInfo, RepoSource


def test_repo_info_defaults():
    info = RepoInfo(id="tuna/thuthesis", university="清华大学")
    assert info.university_en == ""
    assert info.type == "unified"
    assert info.source == RepoSource.MANUAL
    assert info.stars == 0
    assert info.features == []


def test_repo_info_to_dict():
    info = RepoInfo(
        id="tuna/thuthesis",
        university="清华大学",
        university_en="Tsinghua University",
        stars=3800,
        features=["LaTeX3", "Overleaf"],
    )
    d = info.to_dict()
    assert d["id"] == "tuna/thuthesis"
    assert d["stars"] == 3800
    assert d["features"] == ["LaTeX3", "Overleaf"]


def test_repo_info_from_dict():
    d = {
        "id": "tuna/thuthesis",
        "university": "清华大学",
        "university_en": "Tsinghua University",
        "type": "unified",
        "source": "manual",
        "added_at": "2026-06-07",
    }
    info = RepoInfo.from_dict(d)
    assert info.id == "tuna/thuthesis"
    assert info.source == RepoSource.MANUAL


def test_activity_level():
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    info = RepoInfo(id="test/repo", university="测试")
    # No commit data → unknown
    assert info.activity_level == "⚪ 无数据"

    # 1 month ago → active
    info.last_commit = (now - timedelta(days=30)).isoformat()
    assert info.activity_level == "🟢 活跃"

    # 5 months ago → moderate
    info.last_commit = (now - timedelta(days=150)).isoformat()
    assert info.activity_level == "🟡 一般"

    # 8 months ago → inactive
    info.last_commit = (now - timedelta(days=240)).isoformat()
    assert info.activity_level == "🔴 不活跃"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /data1/shanhuang/Project/thesis_ZN
python -m pytest tests/test_models.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tracker.models'`

- [ ] **Step 3: Implement `tracker/models.py`**

```python
"""Data models for thesis template tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class RepoSource(str, Enum):
    MANUAL = "manual"
    DISCOVERED = "discovered"


@dataclass
class RepoInfo:
    """All tracked data for a single thesis template repository."""

    # Static fields (from repos.json)
    id: str  # "owner/repo"
    university: str
    university_en: str = ""
    type: str = "unified"  # doctoral|master|bachelor|unified
    source: RepoSource = RepoSource.MANUAL
    added_at: str = ""

    # Runtime fields (fetched from GitHub API)
    latest_release: Optional[str] = None
    release_date: Optional[str] = None
    last_commit: Optional[str] = None
    commits_last_year: int = 0
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    features: list[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def activity_level(self) -> str:
        """Return emoji-tagged activity level based on last commit date."""
        if not self.last_commit:
            return "⚪ 无数据"
        try:
            last = datetime.fromisoformat(self.last_commit)
        except (ValueError, TypeError):
            return "⚪ 无数据"
        now = datetime.utcnow()
        delta = now - last
        if delta <= timedelta(days=90):
            return "🟢 活跃"
        elif delta <= timedelta(days=180):
            return "🟡 一般"
        else:
            return "🔴 不活跃"

    @property
    def github_url(self) -> str:
        return f"https://github.com/{self.id}"

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage."""
        d = {
            "id": self.id,
            "university": self.university,
            "university_en": self.university_en,
            "type": self.type,
            "source": self.source.value,
            "added_at": self.added_at,
        }
        # Only include runtime fields if they have values
        if self.latest_release:
            d["latest_release"] = self.latest_release
        if self.release_date:
            d["release_date"] = self.release_date
        if self.last_commit:
            d["last_commit"] = self.last_commit
        if self.commits_last_year:
            d["commits_last_year"] = self.commits_last_year
        if self.stars:
            d["stars"] = self.stars
        if self.forks:
            d["forks"] = self.forks
        if self.open_issues:
            d["open_issues"] = self.open_issues
        if self.features:
            d["features"] = self.features
        if self.error:
            d["error"] = self.error
        return d

    @classmethod
    def from_dict(cls, d: dict) -> RepoInfo:
        """Deserialize from a JSON dict."""
        source = RepoSource(d["source"]) if "source" in d else RepoSource.MANUAL
        return cls(
            id=d["id"],
            university=d["university"],
            university_en=d.get("university_en", ""),
            type=d.get("type", "unified"),
            source=source,
            added_at=d.get("added_at", ""),
            latest_release=d.get("latest_release"),
            release_date=d.get("release_date"),
            last_commit=d.get("last_commit"),
            commits_last_year=d.get("commits_last_year", 0),
            stars=d.get("stars", 0),
            forks=d.get("forks", 0),
            open_issues=d.get("open_issues", 0),
            features=d.get("features", []),
            error=d.get("error"),
        )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_models.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add tracker/models.py tests/test_models.py
git commit -m "feat: add RepoInfo data model with activity level logic"
```

---

### Task 3: Seed Data

**Files:**
- Create: `data/repos.json`

- [ ] **Step 1: Create seed data file**

`data/repos.json`:
```json
[
  {"id": "mohuangrui/ucasthesis", "university": "中国科学院大学", "university_en": "University of Chinese Academy of Sciences", "type": "unified", "source": "manual", "added_at": "2026-06-07"},
  {"id": "sjtug/SJTUThesis", "university": "上海交通大学", "university_en": "Shanghai Jiao Tong University", "type": "unified", "source": "manual", "added_at": "2026-06-07"},
  {"id": "TheNetAdmin/zjuthesis", "university": "浙江大学", "university_en": "Zhejiang University", "type": "unified", "source": "manual", "added_at": "2026-06-07"},
  {"id": "ustctug/ustcthesis", "university": "中国科学技术大学", "university_en": "University of Science and Technology of China", "type": "unified", "source": "manual", "added_at": "2026-06-07"},
  {"id": "tuna/thuthesis", "university": "清华大学", "university_en": "Tsinghua University", "type": "unified", "source": "manual", "added_at": "2026-06-07"},
  {"id": "NWPUMetaphysicsOffice/Yet-Another-LaTeX-Template-for-NPU-Thesis", "university": "西北工业大学", "university_en": "Northwestern Polytechnical University", "type": "unified", "source": "manual", "added_at": "2026-06-07"},
  {"id": "mengchaoheng/SCUT_thesis", "university": "华南理工大学", "university_en": "South China University of Technology", "type": "unified", "source": "manual", "added_at": "2026-06-07"},
  {"id": "obster-y/XJTU-thesis", "university": "西安交通大学", "university_en": "Xi'an Jiaotong University", "type": "unified", "source": "manual", "added_at": "2026-06-07"},
  {"id": "HFUTTUG/HFUT_Thesis", "university": "合肥工业大学", "university_en": "Hefei University of Technology", "type": "unified", "source": "manual", "added_at": "2026-06-07"},
  {"id": "NewFuture/NKThesis", "university": "南开大学", "university_en": "Nankai University", "type": "unified", "source": "manual", "added_at": "2026-06-07"},
  {"id": "Koyamin/ecnuthesis", "university": "华东师范大学", "university_en": "East China Normal University", "type": "unified", "source": "manual", "added_at": "2026-06-07"},
  {"id": "sheng-qiang/BUPTBachelorThesis", "university": "北京邮电大学", "university_en": "Beijing University of Posts and Telecommunications", "type": "bachelor", "source": "manual", "added_at": "2026-06-07"}
]
```

- [ ] **Step 2: Verify JSON is valid**

```bash
python -c "import json; data = json.load(open('data/repos.json')); print(f'{len(data)} repos loaded')"
```

Expected: `12 repos loaded`

- [ ] **Step 3: Commit**

```bash
git add data/repos.json
git commit -m "chore: add seed data for 12 known thesis template repos"
```

---

### Task 4: Fetcher Module

**Files:**
- Create: `tracker/fetcher.py`
- Create: `tests/test_fetcher.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_fetcher.py`:
```python
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
    # Simulate a .cls file that uses LaTeX3
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_fetcher.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tracker.fetcher'`

- [ ] **Step 3: Implement `tracker/fetcher.py`**

```python
"""Fetch repository metadata from GitHub API."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from github import Github, GithubException

from tracker.models import RepoInfo

logger = logging.getLogger(__name__)


class TemplateFetcher:
    """Fetches thesis template repo metadata from GitHub."""

    def __init__(self, token: Optional[str] = None):
        self.gh = Github(token) if token else Github()

    def fetch(self, info: RepoInfo) -> RepoInfo:
        """Fetch all runtime data for a repo. Returns updated RepoInfo.

        On any error, sets info.error and returns partial data.
        """
        try:
            repo = self.gh.get_repo(info.id)
        except Exception as e:
            info.error = f"Failed to access repo: {e}"
            logger.warning("Failed to access %s: %s", info.id, e)
            return info

        try:
            self._fetch_basic(repo, info)
            self._fetch_release(repo, info)
            self._fetch_commit_activity(repo, info)
            self._detect_features(repo, info)
        except Exception as e:
            info.error = f"Partial fetch error: {e}"
            logger.warning("Error fetching %s: %s", info.id, e)

        return info

    def _fetch_basic(self, repo, info: RepoInfo) -> None:
        info.stars = repo.stargazers_count
        info.forks = repo.forks_count
        info.open_issues = repo.open_issues_count

    def _fetch_release(self, repo, info: RepoInfo) -> None:
        try:
            releases = list(repo.get_releases())
            if releases:
                latest = releases[0]
                info.latest_release = latest.tag_name
                if latest.published_at:
                    info.release_date = latest.published_at.strftime("%Y-%m-%d")
                return
        except GithubException:
            pass

        # Fallback: use tags
        try:
            tags = list(repo.get_tags())
            if tags:
                info.latest_release = tags[0].name
        except GithubException:
            pass

    def _fetch_commit_activity(self, repo, info: RepoInfo) -> None:
        try:
            commits = list(repo.get_commits()[:1])
            if commits:
                info.last_commit = commits[0].commit.author.date.strftime("%Y-%m-%d")
        except (GithubException, IndexError):
            pass

    def _detect_features(self, repo, info: RepoInfo) -> None:
        features = []
        try:
            contents = repo.get_contents("")
            file_names = [f.path for f in contents]
            file_contents = {}

            # Read .cls files for LaTeX3 detection
            for item in contents:
                if item.path.endswith(".cls"):
                    try:
                        file_contents[item.path] = item.decoded_content.decode(
                            "utf-8", errors="ignore"
                        )
                    except Exception:
                        pass

            # LaTeX3 detection
            for content in file_contents.values():
                if "\\ProvidesExplClass" in content or "\\RequirePackage{expl3}" in content:
                    features.append("LaTeX3")
                    break

            # latexmk detection
            if "latexmkrc" in file_names or ".latexmkrc" in file_names:
                features.append("latexmk")

            # Overleaf detection
            has_overleaf_file = any("overleaf" in f.lower() for f in file_names)
            if has_overleaf_file:
                features.append("Overleaf")
            else:
                try:
                    readme = repo.get_readme()
                    readme_text = readme.decoded_content.decode("utf-8", errors="ignore").lower()
                    if "overleaf" in readme_text:
                        features.append("Overleaf")
                except GithubException:
                    pass

        except GithubException as e:
            logger.debug("Could not detect features for %s: %s", info.id, e)

        info.features = features
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_fetcher.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add tracker/fetcher.py tests/test_fetcher.py
git commit -m "feat: add GitHub API fetcher with feature detection"
```

---

### Task 5: Discovery Module

**Files:**
- Create: `tracker/discover.py`
- Create: `tests/test_discover.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_discover.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_discover.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tracker.discover'`

- [ ] **Step 3: Implement `tracker/discover.py`**

```python
"""Discover new thesis template repositories on GitHub."""

from __future__ import annotations

import logging
from typing import Optional

from github import Github

from tracker.models import RepoInfo, RepoSource

logger = logging.getLogger(__name__)

# 985 universities (subset) for targeted search
UNIVERSITY_NAMES = [
    "清华大学", "北京大学", "浙江大学", "上海交通大学",
    "复旦大学", "南京大学", "中国科学技术大学", "华中科技大学",
    "武汉大学", "西安交通大学", "哈尔滨工业大学", "中山大学",
    "北京航空航天大学", "北京理工大学", "南开大学", "天津大学",
    "大连理工大学", "同济大学", "华东师范大学", "东南大学",
    "厦门大学", "山东大学", "中南大学", "华南理工大学",
    "四川大学", "电子科技大学", "重庆大学", "西北工业大学",
    "兰州大学", "中国农业大学", "北京师范大学", "中国海洋大学",
    "西北农林科技大学", "中央民族大学", "国防科技大学",
    "中国科学院大学", "北京邮电大学", "西安电子科技大学",
    "华东理工大学", "南京理工大学", "南京航空航天大学",
]

SEARCH_QUERIES = [
    "{name} thesis LaTeX",
    "{name} 毕业论文 template",
    "{name} dissertation LaTeX",
]

AUTO_CONFIRM_STARS = 50
AUTO_CANDIDATE_STARS = 10


class TemplateDiscoverer:
    """Search GitHub for new thesis template repositories."""

    def __init__(self, token: Optional[str] = None):
        self.gh = Github(token) if token else Github()

    def discover(self, existing: list[RepoInfo]) -> list[RepoInfo]:
        """Search for new template repos not in existing list.

        Returns list of candidate RepoInfo with source=DISCOVERED.
        Returns empty list on any API error (graceful degradation).
        """
        existing_ids = {r.id for r in existing}
        found: dict[str, RepoInfo] = {}

        for name in UNIVERSITY_NAMES:
            for query_template in SEARCH_QUERIES:
                query = query_template.format(name=name)
                try:
                    results = self.gh.search_repositories(
                        query=f"{query} language:TeX",
                        sort="stars",
                        order="desc",
                    )
                    for repo in results:
                        if repo.full_name in existing_ids:
                            continue
                        if repo.full_name in found:
                            continue
                        if repo.stargazers_count < AUTO_CANDIDATE_STARS:
                            continue

                        info = RepoInfo(
                            id=repo.full_name,
                            university=name,
                            university_en="",
                            source=RepoSource.DISCOVERED,
                        )
                        found[repo.full_name] = info

                except Exception as e:
                    logger.warning("Search failed for '%s': %s", query, e)
                    continue

        return list(found.values())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_discover.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add tracker/discover.py tests/test_discover.py
git commit -m "feat: add GitHub search-based template discovery"
```

---

### Task 6: Generator Module

**Files:**
- Create: `tracker/generator.py`
- Create: `tests/test_generator.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_generator.py`:
```python
import os
import tempfile

from tracker.generator import MarkdownGenerator
from tracker.models import RepoInfo


def _make_info(id="tuna/thuthesis", university="清华大学", stars=3800, **kwargs):
    defaults = dict(
        university_en="Tsinghua University",
        latest_release="v7.5.0",
        release_date="2026-05-15",
        last_commit="2026-06-01",
        features=["LaTeX3", "Overleaf"],
    )
    defaults.update(kwargs)
    return RepoInfo(id=id, university=university, stars=stars, **defaults)


def test_generate_readme_contains_table():
    gen = MarkdownGenerator()
    repos = [_make_info(), _make_info(id="sjtug/SJTUThesis", university="上海交通大学")]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "README.md")
        gen.generate_readme(repos, path)
        content = open(path).read()
        assert "中国高校 LaTeX 论文模板追踪" in content
        assert "清华大学" in content
        assert "上海交通大学" in content
        assert "thuthesis" in content
        assert "v7.5.0" in content


def test_generate_readme_has_stats():
    gen = MarkdownGenerator()
    repos = [_make_info(), _make_info(id="sjtug/SJTUThesis", university="上海交通大学")]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "README.md")
        gen.generate_readme(repos, path)
        content = open(path).read()
        assert "追踪 2 个模板" in content


def test_generate_readme_handles_no_release():
    gen = MarkdownGenerator()
    repos = [_make_info(latest_release=None, release_date=None)]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "README.md")
        gen.generate_readme(repos, path)
        content = open(path).read()
        assert "无" in content  # Should show placeholder for missing release


def test_generate_detail_pages():
    gen = MarkdownGenerator()
    repos = [
        _make_info(id="tuna/thuthesis", university="清华大学"),
        _make_info(id="sjtug/SJTUThesis", university="上海交通大学"),
        _make_info(id="tuna/another-thu", university="清华大学"),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        outdir = os.path.join(tmpdir, "universities")
        gen.generate_detail_pages(repos, outdir)
        # Should have one file per university
        assert os.path.exists(os.path.join(outdir, "清华大学.md"))
        assert os.path.exists(os.path.join(outdir, "上海交通大学.md"))
        thu_content = open(os.path.join(outdir, "清华大学.md")).read()
        assert "thuthesis" in thu_content
        assert "another-thu" in thu_content


def test_generate_readme_error_repos():
    gen = MarkdownGenerator()
    repos = [_make_info(error="API Error")]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "README.md")
        gen.generate_readme(repos, path)
        content = open(path).read()
        assert "⚠️" in content or "错误" in content
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_generator.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tracker.generator'`

- [ ] **Step 3: Implement `tracker/generator.py`**

```python
"""Generate Markdown reports from tracked template data."""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime

from tracker.models import RepoInfo


class MarkdownGenerator:
    """Render RepoInfo lists to Markdown files."""

    def generate_readme(self, repos: list[RepoInfo], path: str) -> None:
        """Generate the main README.md with overview table."""
        now = datetime.utcnow().strftime("%Y-%m-%d")
        active_count = sum(1 for r in repos if r.activity_level == "🟢 活跃")
        error_count = sum(1 for r in repos if r.error)

        lines = [
            "# 中国高校 LaTeX 论文模板追踪",
            "",
            f"> 自动更新于 {now} · 追踪 {len(repos)} 个模板",
            "",
            "## 📊 总览",
            "",
            "| 学校 | 模板 | 版本 | 最近更新 | ⭐ Stars | 活跃度 | 特性 |",
            "|------|------|------|----------|---------|--------|------|",
        ]

        # Sort by last_commit descending, repos without commit data go last
        sorted_repos = sorted(
            repos,
            key=lambda r: r.last_commit or "0000-00-00",
            reverse=True,
        )

        for r in sorted_repos:
            name = f"[{r.id.split('/')[-1]}]({r.github_url})"
            version = r.latest_release or "无"
            update = r.release_date or "无"
            stars = self._format_stars(r.stars)
            activity = r.activity_level
            features = ", ".join(r.features) if r.features else "-"

            if r.error:
                activity = "⚠️ 错误"

            lines.append(
                f"| {r.university} | {name} | {version} | {update} | {stars} | {activity} | {features} |"
            )

        lines.extend([
            "",
            "## 📈 活跃度说明",
            "",
            "- 🟢 活跃：过去 3 个月有 commit",
            "- 🟡 一般：过去 6 个月有 commit",
            "- 🔴 不活跃：超过 6 个月无更新",
            "- ⚪ 无数据：无法获取信息",
            "- ⚠️ 错误：获取数据时出错",
            "",
            "## 🏫 按学校查看",
            "",
        ])

        # Generate per-school links
        schools = defaultdict(list)
        for r in repos:
            schools[r.university].append(r)
        for school in sorted(schools.keys()):
            safe_name = self._safe_filename(school)
            lines.append(f"- [{school}](universities/{safe_name}.md)")

        lines.append("")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def generate_detail_pages(self, repos: list[RepoInfo], outdir: str) -> None:
        """Generate per-university detail pages."""
        os.makedirs(outdir, exist_ok=True)
        schools: dict[str, list[RepoInfo]] = defaultdict(list)
        for r in repos:
            schools[r.university].append(r)

        for school, school_repos in schools.items():
            safe_name = self._safe_filename(school)
            path = os.path.join(outdir, f"{safe_name}.md")
            lines = [
                f"# {school} — LaTeX 论文模板",
                "",
                "| 模板 | 版本 | 最近更新 | Stars | 活跃度 | 特性 |",
                "|------|------|----------|-------|--------|------|",
            ]
            for r in school_repos:
                name = f"[{r.id.split('/')[-1]}]({r.github_url})"
                version = r.latest_release or "无"
                update = r.release_date or "无"
                stars = self._format_stars(r.stars)
                activity = r.activity_level
                features = ", ".join(r.features) if r.features else "-"
                if r.error:
                    activity = "⚠️ 错误"
                lines.append(
                    f"| {name} | {version} | {update} | {stars} | {activity} | {features} |"
                )

            lines.append("")
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

    @staticmethod
    def _format_stars(n: int) -> str:
        if n >= 1000:
            return f"{n / 1000:.1f}k"
        return str(n)

    @staticmethod
    def _safe_filename(name: str) -> str:
        return name.replace("/", "_").replace(" ", "_")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_generator.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add tracker/generator.py tests/test_generator.py
git commit -m "feat: add Markdown report generator"
```

---

### Task 7: Main Entry Point

**Files:**
- Create: `tracker/main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write the failing test**

`tests/test_main.py`:
```python
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from tracker.main import load_repos, save_repos


def test_load_repos():
    data = [
        {"id": "tuna/thuthesis", "university": "清华大学", "source": "manual"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()
        repos = load_repos(f.name)
    os.unlink(f.name)
    assert len(repos) == 1
    assert repos[0].id == "tuna/thuthesis"


def test_save_repos():
    from tracker.models import RepoInfo
    repos = [RepoInfo(id="tuna/thuthesis", university="清华大学")]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        save_repos(repos, f.name)
        f.flush()
        loaded = json.load(open(f.name))
    os.unlink(f.name)
    assert len(loaded) == 1
    assert loaded[0]["id"] == "tuna/thuthesis"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_main.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tracker.main'`

- [ ] **Step 3: Implement `tracker/main.py`**

```python
"""Main entry point: orchestrate discover → fetch → generate."""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Optional

from tracker.discover import TemplateDiscoverer
from tracker.fetcher import TemplateFetcher
from tracker.generator import MarkdownGenerator
from tracker.models import RepoInfo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def load_repos(path: str) -> list[RepoInfo]:
    """Load repo list from JSON file."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [RepoInfo.from_dict(d) for d in data]


def save_repos(repos: list[RepoInfo], path: str) -> None:
    """Save repo list to JSON file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in repos], f, ensure_ascii=False, indent=2)


def main(
    repos_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    discover: bool = True,
) -> None:
    """Run the full tracking pipeline."""
    repos_path = repos_path or os.path.join(DATA_DIR, "repos.json")
    output_dir = output_dir or OUTPUT_DIR
    token = os.environ.get("GITHUB_TOKEN")

    # 1. Load existing repos
    logger.info("Loading repos from %s", repos_path)
    repos = load_repos(repos_path)
    logger.info("Loaded %d repos", len(repos))

    # 2. Discover new repos (optional)
    if discover:
        logger.info("Discovering new repos...")
        discoverer = TemplateDiscoverer(token=token)
        candidates = discoverer.discover(repos)
        if candidates:
            logger.info("Found %d new candidates", len(candidates))
            # Auto-confirm repos with enough stars
            from tracker.discover import AUTO_CONFIRM_STARS
            confirmed = [c for c in candidates if c.stars >= AUTO_CONFIRM_STARS]
            if confirmed:
                logger.info("Auto-confirming %d repos with >= %d stars", len(confirmed), AUTO_CONFIRM_STARS)
                repos.extend(confirmed)
                save_repos(repos, repos_path)
        else:
            logger.info("No new repos found")

    # 3. Fetch data for all repos
    logger.info("Fetching repo data...")
    fetcher = TemplateFetcher(token=token)
    for i, repo in enumerate(repos):
        logger.info("Fetching %d/%d: %s", i + 1, len(repos), repo.id)
        fetcher.fetch(repo)

    # 4. Generate Markdown output
    logger.info("Generating Markdown reports...")
    gen = MarkdownGenerator()
    readme_path = os.path.join(output_dir, "README.md")
    univ_dir = os.path.join(output_dir, "universities")
    gen.generate_readme(repos, readme_path)
    gen.generate_detail_pages(repos, univ_dir)
    logger.info("Output written to %s", output_dir)

    # 5. Print summary
    errors = sum(1 for r in repos if r.error)
    logger.info("Done. %d repos tracked, %d errors.", len(repos), errors)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_main.py -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add tracker/main.py tests/test_main.py
git commit -m "feat: add main entry point with pipeline orchestration"
```

---

### Task 8: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/update.yml`

- [ ] **Step 1: Create the workflow file**

```yaml
name: Update Templates

on:
  schedule:
    - cron: '0 3 * * 1'  # Every Monday UTC 03:00 (Beijing 11:00)
  workflow_dispatch:       # Manual trigger

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tracker
        run: python -m tracker.main
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add output/ data/repos.json
          git diff --staged --quiet || git commit -m "chore: update template data [skip ci]"
          git push
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/update.yml
git commit -m "ci: add weekly GitHub Actions workflow for template tracking"
```

---

### Task 9: Run All Tests

- [ ] **Step 1: Run the full test suite**

```bash
cd /data1/shanhuang/Project/thesis_ZN
python -m pytest tests/ -v
```

Expected: All tests pass (approximately 20 tests)

- [ ] **Step 2: Verify project structure**

```bash
find . -type f -not -path './.git/*' -not -path './docs/*' -not -path './__pycache__/*' -not -path '*/pytest_cache/*' -not -path '*.egg-info/*' | sort
```

Expected files:
```
.github/workflows/update.yml
data/repos.json
pyproject.toml
requirements.txt
tests/__init__.py
tests/test_discover.py
tests/test_fetcher.py
tests/test_generator.py
tests/test_main.py
tests/test_models.py
tracker/__init__.py
tracker/discover.py
tracker/fetcher.py
tracker/generator.py
tracker/main.py
tracker/models.py
```

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "chore: add test suite for all modules"
```

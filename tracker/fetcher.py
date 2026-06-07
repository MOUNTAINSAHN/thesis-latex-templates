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

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

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

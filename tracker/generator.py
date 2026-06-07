"""Generate Markdown reports from tracked template data."""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime

from pypinyin import lazy_pinyin

from tracker.models import RepoInfo


class MarkdownGenerator:
    """Render RepoInfo lists to Markdown files."""

    def generate_readme(self, repos: list[RepoInfo], path: str) -> None:
        """Generate the main README.md with overview table."""
        now = datetime.utcnow().strftime("%Y-%m-%d")

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

        # Sort by university pinyin, then by repo name
        sorted_repos = sorted(
            repos,
            key=lambda r: (lazy_pinyin(r.university), r.id),
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

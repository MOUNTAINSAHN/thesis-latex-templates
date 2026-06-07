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

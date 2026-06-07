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
        assert "无" in content


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

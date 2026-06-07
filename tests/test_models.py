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

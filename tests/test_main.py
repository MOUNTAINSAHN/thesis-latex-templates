import json
import os
import tempfile

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

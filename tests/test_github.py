# -*- coding: utf-8 -*-
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from monikanews.github import fetch_new_pushes, _get_repos, _fetch_repo_commits, _fetch_commit_details


@pytest.mark.asyncio
async def test_get_repos_returns_list():
    mock_raw = '["FQingLars/repo1", "FQingLars/repo2"]'
    mock_proc = MagicMock()
    mock_proc.communicate = AsyncMock(return_value=(mock_raw.encode(), b""))
    mock_proc.returncode = 0
    with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)):
        repos = await _get_repos()
    assert repos == ["FQingLars/repo1", "FQingLars/repo2"]


@pytest.mark.asyncio
async def test_fetch_commit_details():
    # Mock returns jq-processed output from gh api
    mock_raw = '{"stats": {"additions": 5, "deletions": 2, "total": 7}, "files": ["file1.py", "file2.py"]}'
    mock_proc = MagicMock()
    mock_proc.communicate = AsyncMock(return_value=(mock_raw.encode(), b""))
    mock_proc.returncode = 0
    with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)):
        stats, files = await _fetch_commit_details("FQingLars/repo1", "abc123")
    assert stats == {"additions": 5, "deletions": 2, "total": 7}
    assert files == ["file1.py", "file2.py"]


@pytest.mark.asyncio
async def test_fetch_repo_commits_returns_commits():
    mock_raw = [
        {"sha": "abc123", "commit": {"message": "Fix bug", "author": {"name": "FQingLars", "date": "2026-09-20T15:00:00Z"}}},
    ]
    mock_proc = MagicMock()
    mock_proc.communicate = AsyncMock(return_value=(json.dumps(mock_raw).encode(), b""))
    mock_proc.returncode = 0
    with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)):
        with patch("monikanews.github._fetch_commit_details", AsyncMock(return_value=({"additions": 5, "deletions": 2}, ["file.py"]))):
            commits = await _fetch_repo_commits("FQingLars/repo1", None)
    assert len(commits) == 1
    assert commits[0]["message"] == "Fix bug"
    assert commits[0]["repo"] == "FQingLars/repo1"
    assert commits[0]["stats"] == {"additions": 5, "deletions": 2}
    assert commits[0]["files"] == ["file.py"]


@pytest.mark.asyncio
async def test_fetch_repo_commits_returns_empty_on_error():
    mock_proc = MagicMock()
    mock_proc.communicate = AsyncMock(return_value=(b"", b"gh: error"))
    mock_proc.returncode = 1
    with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)):
        commits = await _fetch_repo_commits("FQingLars/repo1", None)
    assert commits == []


@pytest.mark.asyncio
async def test_fetch_new_pushes_returns_all_commits():
    mock_repos_proc = MagicMock()
    mock_repos_proc.communicate = AsyncMock(return_value=('["FQingLars/repo1", "FQingLars/repo2"]'.encode(), b""))
    mock_repos_proc.returncode = 0
    
    mock_commit_proc = MagicMock()
    mock_commit_proc.communicate = AsyncMock(return_value=('[]'.encode(), b""))
    mock_commit_proc.returncode = 0
    
    with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_repos_proc)):
        with patch("monikanews.github._fetch_repo_commits", AsyncMock(return_value=[])):
            commits = await fetch_new_pushes("FQingLars", None)
    assert commits == []


@pytest.mark.asyncio
async def test_fetch_new_pushes_sorts_by_date():
    def mock_fetch_side_effect(repo, last_timestamp):
        if "repo1" in repo:
            return [{"sha": "a", "message": "repo1 commit", "repo": repo, "date": "2026-09-20T15:00:00Z", "stats": {}, "files": []}]
        return [{"sha": "b", "message": "repo2 commit", "repo": repo, "date": "2026-09-20T14:00:00Z", "stats": {}, "files": []}]
    
    mock_repos_proc = MagicMock()
    mock_repos_proc.communicate = AsyncMock(return_value=('["FQingLars/repo1", "FQingLars/repo2"]'.encode(), b""))
    mock_repos_proc.returncode = 0
    
    mock_commit_proc = MagicMock()
    mock_commit_proc.communicate = AsyncMock(return_value=('[]'.encode(), b""))
    mock_commit_proc.returncode = 0
    
    with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_repos_proc)):
        with patch("monikanews.github._fetch_repo_commits", AsyncMock(side_effect=mock_fetch_side_effect)):
            commits = await fetch_new_pushes("FQingLars", None)
    assert len(commits) == 2
    assert commits[0]["repo"] == "FQingLars/repo1"

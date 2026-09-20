# -*- coding: utf-8 -*-
"""GitHub client using gh CLI for fetching new commits from all repos."""

import asyncio
import json
from typing import List, Dict, Any


async def _get_repos() -> List[str]:
    """Get all public repo full names for FQingLars."""
    proc = await asyncio.create_subprocess_exec(
        "gh", "api", "/users/FQingLars/repos",
        "--jq", "[.[] | select(.private==false) | .full_name]",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"gh repos failed: {stderr.decode().strip()}")
    return json.loads(stdout.decode())


async def _fetch_commit_details(repo: str, sha: str) -> tuple[dict, list[str]]:
    """Fetch stats and files for a single commit."""
    proc = await asyncio.create_subprocess_exec(
        "gh", "api", f"/repos/{repo}/commits/{sha}",
        "--jq", "{stats: .stats, files: [.files[]?.filename]}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        return {}, []
    try:
        data = json.loads(stdout.decode())
        return data.get("stats", {}), data.get("files", [])
    except json.JSONDecodeError:
        return {}, []


async def _fetch_repo_commits(repo: str, last_timestamp: str | None) -> List[Dict[str, Any]]:
    """Fetch commits for a single repo."""
    url = f"/repos/{repo}/commits"
    if last_timestamp:
        url += f"?since={last_timestamp}"
    
    proc = await asyncio.create_subprocess_exec(
        "gh", "api", url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        return []
    try:
        raw = json.loads(stdout.decode())
    except json.JSONDecodeError:
        return []
    
    commits = []
    for ev in raw:
        sha = ev.get("sha", "")
        stats, files = await _fetch_commit_details(repo, sha)
        commit = ev.get("commit", {})
        commits.append({
            "message": commit.get("message", ""),
            "sha": sha,
            "author": commit.get("author", {}).get("name", ""),
            "repo": repo,
            "date": commit.get("author", {}).get("date", ""),
            "stats": stats,
            "files": files,
        })
    return commits


async def fetch_new_pushes(
    github_user: str,
    last_timestamp: str | None,
) -> List[Dict[str, Any]]:
    """Fetch new commits from ALL public repos of the user.
    Uses gh CLI: gh api /users/FQingLars/repos for repo list,
    then gh api /repos/{repo}/commits?since=<timestamp> for each.
    Returns all commits merged and sorted by date descending.
    Each commit includes stats (additions/deletions) and files list.
    """
    repos = await _get_repos()
    
    tasks = [_fetch_repo_commits(repo, last_timestamp) for repo in repos]
    results = await asyncio.gather(*tasks)
    
    all_commits = []
    for commits in results:
        all_commits.extend(commits)
    
    all_commits.sort(key=lambda c: c.get("date", ""), reverse=True)
    
    return all_commits

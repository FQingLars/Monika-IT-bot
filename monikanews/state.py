# -*- coding: utf-8 -*-
"""Per-commit state management.

State file structure:
{
  "last_timestamp": "2026-09-20T15:21:02Z",
  "FQingLars/Monika-IT-bot": {
    "abc123def45678901234567890abcdef": "published",
    "def456new789abcdef0123456789abcdef": "ignored"
  }
}
"""

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = str(PROJECT_ROOT / "state" / "commits_state.json")

os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)


def load_commits_state() -> dict:
    """Load state: {last_timestamp: str, repo: {full_sha: state}}."""
    if not os.path.exists(STATE_FILE):
        return {"last_timestamp": ""}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            if "last_timestamp" not in data:
                data["last_timestamp"] = ""
            return data
        return {"last_timestamp": ""}
    except (json.JSONDecodeError, IOError):
        return {"last_timestamp": ""}


def save_commits_state(state_dict: dict) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state_dict, f, ensure_ascii=False, indent=2)


def get_last_timestamp(state_dict: dict) -> str:
    return state_dict.get("last_timestamp", "")


def set_last_timestamp(state_dict: dict, timestamp: str) -> None:
    state_dict["last_timestamp"] = timestamp


def get_unpublished_commits(commits: list[dict], state_dict: dict | None = None) -> list[dict]:
    if state_dict is None:
        state_dict = load_commits_state()
    result = []
    for c in commits:
        repo = c.get("repo", "unknown")
        sha = c.get("sha", "")
        repo_state = state_dict.get(repo, {})
        state = repo_state.get(sha)
        if state != "published" and state != "ignored":
            result.append(c)
    return result


def mark_published(state_dict: dict, commit: dict) -> None:
    repo = commit.get("repo", "unknown")
    sha = commit.get("sha", "")
    if repo not in state_dict:
        state_dict[repo] = {}
    state_dict[repo][sha] = "published"


def mark_ignored(state_dict: dict, commit: dict) -> None:
    repo = commit.get("repo", "unknown")
    sha = commit.get("sha", "")
    if repo not in state_dict:
        state_dict[repo] = {}
    state_dict[repo][sha] = "ignored"

# -*- coding: utf-8 -*-
"""State management: commit states, timestamp, chat history, reply cooldown."""

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = str(PROJECT_ROOT / "state" / "commits_state.json")
CHAT_HISTORY_FILE = str(PROJECT_ROOT / "state" / "chat_history.json")
LAST_COMMITS_FILE = str(PROJECT_ROOT / "state" / "last_commits.json")
LAST_REPLY_TS_FILE = str(PROJECT_ROOT / "state" / "last_reply_ts.json")
CHAT_HISTORY_LIMIT = 30

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
    """Return only commits whose state is 'unpublished' or not in state_dict."""
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


def load_chat_history(path: str = CHAT_HISTORY_FILE) -> list[dict]:
    """Load Monika chat history: [{"role": ..., "content": ...}]."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_chat_history(history: list[dict], path: str = CHAT_HISTORY_FILE) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def append_chat_message(role: str, text: str, path: str = CHAT_HISTORY_FILE) -> None:
    """Append one message to the chat history, trimming to CHAT_HISTORY_LIMIT."""
    history = load_chat_history(path)
    history.append({"role": role, "content": text})
    history = history[-CHAT_HISTORY_LIMIT:]
    save_chat_history(history, path)


def load_last_commits(path: str = LAST_COMMITS_FILE) -> list[dict]:
    """Load the most recent known commits (Monika's chat context)."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_last_commits(commits: list[dict], path: str = LAST_COMMITS_FILE) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(commits, f, ensure_ascii=False, indent=2)


def load_last_reply_ts(path: str = LAST_REPLY_TS_FILE) -> float:
    """Load the unix timestamp of the last discussion-group reply."""
    if not os.path.exists(path):
        return 0.0
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return float(data.get("ts", 0.0))
    except (json.JSONDecodeError, IOError, TypeError, ValueError):
        return 0.0


def save_last_reply_ts(ts: float, path: str = LAST_REPLY_TS_FILE) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"ts": ts}, f)

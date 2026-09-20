# -*- coding: utf-8 -*-
import pytest
import os
import json
from monikanews.state import (
    load_commits_state, save_commits_state,
    get_unpublished_commits, mark_published, mark_ignored,
    get_last_timestamp, set_last_timestamp,
    STATE_FILE,
)


@pytest.mark.asyncio
async def test_load_commits_state_empty():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    result = load_commits_state()
    assert result == {"last_timestamp": ""}


def test_save_and_load_commits_state():
    state = {
        "last_timestamp": "2026-09-20T15:00:00Z",
        "FQingLars/Monika-IT-bot": {"abc123def45678901234567890abcdef": "published"},
    }
    save_commits_state(state)
    result = load_commits_state()
    assert result == state
    os.remove(STATE_FILE)


def test_get_last_timestamp():
    state = {"last_timestamp": "2026-09-20T15:00:00Z"}
    assert get_last_timestamp(state) == "2026-09-20T15:00:00Z"


def test_set_last_timestamp():
    state = {}
    set_last_timestamp(state, "2026-09-20T16:00:00Z")
    assert state["last_timestamp"] == "2026-09-20T16:00:00Z"


def test_get_unpublished_commits():
    commits = [
        {"sha": "abc123def45678901234567890abcdef", "repo": "FQingLars/Monika-IT-bot"},
        {"sha": "def456new789abcdef0123456789abcdef", "repo": "FQingLars/Monika-IT-bot"},
    ]
    state = {"FQingLars/Monika-IT-bot": {"abc123def45678901234567890abcdef": "published"}}
    result = get_unpublished_commits(commits, state)
    assert len(result) == 1
    assert result[0]["sha"] == "def456new789abcdef0123456789abcdef"


def test_get_unpublished_not_in_state():
    commits = [{"sha": "abc123def45678901234567890abcdef", "repo": "FQingLars/Monika-IT-bot"}]
    result = get_unpublished_commits(commits, {})
    assert len(result) == 1


def test_get_unpublished_ignored():
    commits = [{"sha": "abc123def45678901234567890abcdef", "repo": "FQingLars/Monika-IT-bot"}]
    state = {"FQingLars/Monika-IT-bot": {"abc123def45678901234567890abcdef": "ignored"}}
    result = get_unpublished_commits(commits, state)
    assert len(result) == 0


def test_mark_published():
    state = {}
    commit = {"sha": "abc123def45678901234567890abcdef", "repo": "FQingLars/Monika-IT-bot"}
    mark_published(state, commit)
    assert state["FQingLars/Monika-IT-bot"]["abc123def45678901234567890abcdef"] == "published"


def test_mark_ignored():
    state = {}
    commit = {"sha": "abc123def45678901234567890abcdef", "repo": "FQingLars/Monika-IT-bot"}
    mark_ignored(state, commit)
    assert state["FQingLars/Monika-IT-bot"]["abc123def45678901234567890abcdef"] == "ignored"


@pytest.mark.asyncio
async def test_save_and_load_json_file():
    state = {
        "last_timestamp": "2026-09-20T15:00:00Z",
        "FQingLars/Monika-IT-bot": {"abc123def45678901234567890abcdef": "published"},
    }
    save_commits_state(state)
    assert os.path.exists(STATE_FILE)
    with open(STATE_FILE, "r") as f:
        data = json.load(f)
    assert data == state
    os.remove(STATE_FILE)

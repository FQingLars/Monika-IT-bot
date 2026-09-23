# -*- coding: utf-8 -*-
import json
import os

import pytest

from monikanews.state import (
    CHAT_HISTORY_FILE,
    LAST_COMMITS_FILE,
    STATE_FILE,
    append_chat_message,
    get_last_timestamp,
    get_unpublished_commits,
    load_chat_history,
    load_commits_state,
    load_last_commits,
    mark_ignored,
    mark_published,
    save_chat_history,
    save_commits_state,
    save_last_commits,
    set_last_timestamp,
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
    assert load_commits_state() == state
    os.remove(STATE_FILE)


def test_get_last_timestamp():
    assert get_last_timestamp({"last_timestamp": "2026-09-20T15:00:00Z"}) == "2026-09-20T15:00:00Z"


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
    assert len(get_unpublished_commits(commits, {})) == 1


def test_get_unpublished_ignored():
    commits = [{"sha": "abc123def45678901234567890abcdef", "repo": "FQingLars/Monika-IT-bot"}]
    state = {"FQingLars/Monika-IT-bot": {"abc123def45678901234567890abcdef": "ignored"}}
    assert len(get_unpublished_commits(commits, state)) == 0


def test_mark_published():
    state = {}
    mark_published(state, {"sha": "abc123def45678901234567890abcdef", "repo": "FQingLars/Monika-IT-bot"})
    assert state["FQingLars/Monika-IT-bot"]["abc123def45678901234567890abcdef"] == "published"


def test_mark_ignored():
    state = {}
    mark_ignored(state, {"sha": "abc123def45678901234567890abcdef", "repo": "FQingLars/Monika-IT-bot"})
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
        assert json.load(f) == state
    os.remove(STATE_FILE)


def test_chat_history_roundtrip():
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)
    assert load_chat_history() == []
    save_chat_history([{"role": "user", "content": "привет"}])
    assert load_chat_history() == [{"role": "user", "content": "привет"}]
    os.remove(CHAT_HISTORY_FILE)


def test_append_chat_message_trims_to_limit():
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)
    for i in range(35):
        append_chat_message("user", f"msg {i}")
    history = load_chat_history()
    assert len(history) == 30
    assert history[-1]["content"] == "msg 34"
    os.remove(CHAT_HISTORY_FILE)


def test_last_commits_roundtrip():
    if os.path.exists(LAST_COMMITS_FILE):
        os.remove(LAST_COMMITS_FILE)
    assert load_last_commits() == []
    save_last_commits([{"sha": "abc", "repo": "r"}])
    assert load_last_commits() == [{"sha": "abc", "repo": "r"}]
    os.remove(LAST_COMMITS_FILE)


def test_last_reply_ts_roundtrip():
    import os
    from monikanews.state import LAST_REPLY_TS_FILE, load_last_reply_ts, save_last_reply_ts
    if os.path.exists(LAST_REPLY_TS_FILE):
        os.remove(LAST_REPLY_TS_FILE)
    assert load_last_reply_ts() == 0.0
    save_last_reply_ts(1727123456.5)
    assert load_last_reply_ts() == 1727123456.5
    os.remove(LAST_REPLY_TS_FILE)

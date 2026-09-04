import pytest
from backend.router.session_manager import SessionManager


def test_session_manager_create():
    manager = SessionManager()
    session_id = manager.create_session()
    
    assert session_id is not None
    assert isinstance(session_id, str)
    assert manager.get_history(session_id) == []


def test_session_manager_add_message():
    manager = SessionManager()
    session_id = manager.create_session()
    
    manager.add_message(session_id, "user", "Hello there")
    manager.add_message(session_id, "assistant", "Hi!")
    
    history = manager.get_history(session_id)
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "Hello there"}
    assert history[1] == {"role": "assistant", "content": "Hi!"}


def test_session_manager_sliding_window():
    manager = SessionManager(max_history_messages=3)
    session_id = manager.create_session()
    
    manager.add_message(session_id, "user", "Msg 1")
    manager.add_message(session_id, "assistant", "Reply 1")
    manager.add_message(session_id, "user", "Msg 2")
    manager.add_message(session_id, "assistant", "Reply 2")
    
    # We added 4 messages, max is 3. It should keep the last 3.
    history = manager.get_history(session_id)
    assert len(history) == 3
    assert history[0]["content"] == "Reply 1"
    assert history[1]["content"] == "Msg 2"
    assert history[2]["content"] == "Reply 2"


def test_session_manager_clear():
    manager = SessionManager()
    session_id = manager.create_session()
    
    manager.add_message(session_id, "user", "Hello")
    assert len(manager.get_history(session_id)) == 1
    
    manager.clear_session(session_id)
    assert len(manager.get_history(session_id)) == 0

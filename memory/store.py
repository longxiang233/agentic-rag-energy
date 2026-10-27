import time

MAX_TURNS = 10

_sessions = {}   # {session_id: {"messages": [...], "created_at": ts, "updated_at": ts}}

def get_or_create(session_id: str) -> dict:
    if session_id not in _sessions:
        now = time.time()
        _sessions[session_id] = {
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
    return _sessions[session_id]

def get_history(session_id: str) -> list:
    session = get_or_create(session_id)
    return session["messages"][-MAX_TURNS * 2:]

def save_message(session_id: str, message) -> None:
    session = get_or_create(session_id)
    session["messages"].append(message)
    session["updated_at"] = time.time()

def clear(session_id: str) -> None:
    if session_id in _sessions:
        del _sessions[session_id]

def list_sessions() -> list:
    return list(_sessions.keys())
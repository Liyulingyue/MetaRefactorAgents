import os
import json
import threading
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict


SESSION_FILE_MAX_SIZE = 100 * 1024


@dataclass
class ChatSession:
    chat_id: str
    history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    message_count: int = 0
    busy: bool = False


class SessionManager:
    """
    Manages per-chat_id conversation histories with append-only file persistence.
    Thread-safe singleton.

    File format: NDJSON (one JSON object per line)
      sessions/{chat_id}.ndjson          - current active session
      sessions/{chat_id}_YYYYMMDD.ndjson - archived sessions

    Each line is a message dict. Compaction summary is also written as a line
    with role="system" and type="summary".
    """

    _instance: Optional["SessionManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._sessions: Dict[str, ChatSession] = {}
                    cls._instance._sessions_lock = threading.Lock()
                    cls._instance._chat_locks: Dict[str, threading.Lock] = {}
                    cls._instance._chat_locks_lock = threading.Lock()
                    cls._instance._storage_path = None
        return cls._instance

    def _init(self) -> None:
        if self._storage_path is None:
            from .config import settings
            self._storage_path = settings.SESSION_STORAGE_PATH
            os.makedirs(self._storage_path, exist_ok=True)

    def _session_file(self, chat_id: str, suffix: str = "") -> str:
        self._init()
        safe_id = chat_id.replace("/", "_").replace("\\", "_")
        date_suffix = time.strftime("%Y%m%d") if suffix else ""
        name = f"{safe_id}_{date_suffix}.ndjson" if date_suffix else f"{safe_id}.ndjson"
        return os.path.join(self._storage_path, name)

    def _current_file(self, chat_id: str) -> str:
        return self._session_file(chat_id)

    def _archived_files(self, chat_id: str) -> List[str]:
        self._init()
        safe_id = chat_id.replace("/", "_").replace("\\", "_")
        prefix = safe_id + "_"
        try:
            files = [
                os.path.join(self._storage_path, f)
                for f in os.listdir(self._storage_path)
                if f.startswith(prefix) and f.endswith(".ndjson")
            ]
            return sorted(files)
        except Exception:
            return []

    def _load_from_file(self, filepath: str) -> List[Dict[str, Any]]:
        messages = []
        if not os.path.exists(filepath):
            return messages
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        messages.append(json.loads(line))
        except Exception as e:
            print(f"⚠️ Failed to load session {filepath}: {e}")
        return messages

    def get_chat_lock(self, chat_id: str) -> threading.Lock:
        with self._chat_locks_lock:
            if chat_id not in self._chat_locks:
                self._chat_locks[chat_id] = threading.Lock()
            return self._chat_locks[chat_id]

    def _append_to_file(self, chat_id: str, entry: Dict[str, Any]) -> bool:
        self._init()
        filepath = self._current_file(chat_id)
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            if os.path.getsize(filepath) > SESSION_FILE_MAX_SIZE:
                self._archive_session(chat_id)
            return True
        except Exception as e:
            print(f"⚠️ Failed to append to session {chat_id}: {e}")
            return False

    def _archive_session(self, chat_id: str) -> None:
        filepath = self._current_file(chat_id)
        if not os.path.exists(filepath):
            return
        archive_path = self._session_file(chat_id, suffix=time.strftime("%Y%m%d"))
        try:
            with open(filepath, "r", encoding="utf-8") as src:
                content = src.read()
            with open(archive_path, "w", encoding="utf-8") as dst:
                dst.write(content)
            os.remove(filepath)
            print(f"📦 Session {chat_id} archived to {archive_path}")
        except Exception as e:
            print(f"⚠️ Failed to archive session {chat_id}: {e}")

    def get_session(self, chat_id: str) -> ChatSession:
        self._init()
        with self._sessions_lock:
            if chat_id not in self._sessions:
                messages = self._load_from_file(self._current_file(chat_id))
                session = ChatSession(chat_id=chat_id)
                session.history = messages
                session.message_count = sum(1 for m in messages if m.get("role") != "system")
                self._sessions[chat_id] = session
            return self._sessions[chat_id]

    def get_history(self, chat_id: str) -> List[Dict[str, Any]]:
        return self.get_session(chat_id).history

    def append_message(self, chat_id: str, role: str, content: str) -> None:
        session = self.get_session(chat_id)
        entry = {"role": role, "content": content, "ts": time.time()}
        session.history.append(entry)
        session.last_active = time.time()
        session.message_count += 1
        self._append_to_file(chat_id, entry)

    def append_summary(self, chat_id: str, summary_text: str) -> None:
        session = self.get_session(chat_id)
        entry = {"role": "system", "type": "summary", "content": summary_text, "ts": time.time()}
        session.history.append(entry)
        session.last_active = time.time()
        self._append_to_file(chat_id, entry)

    def append_assistant(
        self, chat_id: str, content: str, tool_calls: Optional[List[Dict]] = None
    ) -> None:
        entry: Dict[str, Any] = {"role": "assistant", "content": content, "ts": time.time()}
        if tool_calls:
            entry["tool_calls"] = tool_calls
        session = self.get_session(chat_id)
        session.history.append(entry)
        session.last_active = time.time()
        self._append_to_file(chat_id, entry)

    def append_tool(
        self, chat_id: str, tool_call_id: str, name: str, content: str
    ) -> None:
        entry = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": name,
            "content": content,
            "ts": time.time(),
        }
        session = self.get_session(chat_id)
        session.history.append(entry)
        session.last_active = time.time()
        self._append_to_file(chat_id, entry)

    def set_history(self, chat_id: str, history: List[Dict[str, Any]]) -> None:
        session = self.get_session(chat_id)
        session.history = history
        session.last_active = time.time()

    def clear_session(self, chat_id: str) -> None:
        with self._sessions_lock:
            if chat_id in self._sessions:
                del self._sessions[chat_id]
        filepath = self._current_file(chat_id)
        if os.path.exists(filepath):
            os.remove(filepath)
        for archived in self._archived_files(chat_id):
            try:
                os.remove(archived)
            except Exception:
                pass

    def list_sessions(self) -> List[str]:
        self._init()
        result = []
        try:
            for f in os.listdir(self._storage_path):
                if f.endswith(".ndjson") and "_20" not in f:
                    result.append(f[:-6])
        except Exception:
            pass
        return result


def get_session_manager() -> SessionManager:
    return SessionManager()

"""Session state for the Discord bot.

Tracks theme suggestion messages and active modification threads in one
object so bot.py no longer owns raw module-level dicts (R5a). An optional
persistence seam writes every mutation to a store (SQLite, #52) and reloads
state from it at startup, so tracking survives restarts.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Protocol


class SessionStore(Protocol):
    """Persistence contract for session tracking (#52)."""

    def load_suggestions(self) -> Dict[int, Dict[str, Any]]: ...

    def load_threads(self) -> Dict[int, Dict[str, Any]]: ...

    def save_suggestion(self, message_id: int, info: Dict[str, Any]) -> None: ...

    def delete_suggestion(self, message_id: int) -> None: ...

    def save_thread(self, thread_id: int, info: Dict[str, Any]) -> None: ...

    def delete_thread(self, thread_id: int) -> None: ...


class SessionState:
    """Tracks theme suggestion messages and active modification threads."""

    def __init__(self, persistence: Optional[SessionStore] = None) -> None:
        self._persistence = persistence
        if persistence is not None:
            self._suggestions: Dict[int, Dict[str, Any]] = (
                persistence.load_suggestions()
            )
            self._threads: Dict[int, Dict[str, Any]] = persistence.load_threads()
        else:
            self._suggestions = {}
            self._threads = {}
        self._messages_with_threads: set = {
            info["message_id"] for info in self._threads.values()
        }

    @property
    def persistence(self) -> Optional[SessionStore]:
        """The persistence seam, when one is configured."""
        return self._persistence

    def register_suggestion(self, message_id: int, theme_name: str) -> None:
        self._suggestions[message_id] = {
            "theme_name": theme_name,
            "timestamp": datetime.now(timezone.utc),
            "locked": False,
        }
        if self._persistence is not None:
            self._persistence.save_suggestion(message_id, self._suggestions[message_id])

    def get_suggestion(self, message_id: int) -> Optional[Dict[str, Any]]:
        return self._suggestions.get(message_id)

    def has_suggestion(self, message_id: int) -> bool:
        return message_id in self._suggestions

    def lock_suggestion(self, message_id: int) -> None:
        info = self._suggestions.get(message_id)
        if info is None:
            return
        info["locked"] = True
        if self._persistence is not None:
            self._persistence.save_suggestion(message_id, info)

    def is_locked(self, message_id: int) -> bool:
        info = self._suggestions.get(message_id)
        return True if info is None else bool(info["locked"])

    def remove_suggestion(self, message_id: int) -> None:
        info = self._suggestions.pop(message_id, None)
        if info is not None and self._persistence is not None:
            self._persistence.delete_suggestion(message_id)

    def register_thread(
        self, thread_id: int, theme_name: str, user_id: int, message_id: int
    ) -> None:
        self._threads[thread_id] = {
            "theme_name": theme_name,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc),
            "message_id": message_id,
        }
        self._messages_with_threads.add(message_id)
        if self._persistence is not None:
            self._persistence.save_thread(thread_id, self._threads[thread_id])

    def get_thread(self, thread_id: int) -> Optional[Dict[str, Any]]:
        return self._threads.get(thread_id)

    def has_thread(self, thread_id: int) -> bool:
        return thread_id in self._threads

    def message_has_active_thread(self, message_id: int) -> bool:
        return message_id in self._messages_with_threads

    def remove_thread(self, thread_id: int) -> None:
        info = self._threads.pop(thread_id, None)
        if info is None:
            return
        self._messages_with_threads.discard(info.get("message_id"))
        if self._persistence is not None:
            self._persistence.delete_thread(thread_id)

    def inactive_threads(self, cutoff: timedelta) -> List[int]:
        now = datetime.now(timezone.utc)
        return [
            thread_id
            for thread_id, info in self._threads.items()
            if now - info["created_at"] >= cutoff
        ]


@dataclass
class VoteDecision:
    """Outcome of a vote-lock policy evaluation."""

    allowed: bool
    should_lock: bool


class VoteLockPolicy:
    """The 2-hour voting rule as a testable policy (R5b).

    Durability across restarts was added in #52: timestamps now come from
    the persisted session state.
    """

    def __init__(self, lock_after: timedelta = timedelta(hours=2)) -> None:
        self._lock_after = lock_after

    def evaluate(self, state: "SessionState", message_id: int) -> VoteDecision:
        info = state._suggestions.get(message_id)
        if info is None:
            return VoteDecision(allowed=False, should_lock=False)
        if info["locked"]:
            return VoteDecision(allowed=False, should_lock=False)
        elapsed = datetime.now(timezone.utc) - info["timestamp"]
        if elapsed >= self._lock_after:
            return VoteDecision(allowed=False, should_lock=True)
        return VoteDecision(allowed=True, should_lock=False)

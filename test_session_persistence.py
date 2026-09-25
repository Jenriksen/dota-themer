"""Tests for SessionState persistence across restarts (#52).A SessionState backed by SqliteSessionStore reloads suggestions andthreads from SQLite, so message/thread tracking survives a restart."""

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import storage
from session_state import SessionState, VoteDecision, VoteLockPolicy


class SqliteSessionPersistenceTestCase(unittest.TestCase):
    """Hermetic fixture: every test gets a fresh temp database file."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = Path(self.tmp.name) / "dota.db"

    def make_state(self):
        return SessionState(persistence=storage.SqliteSessionStore(self.db_path))

    def restart(self, state):
        """Simulate a restart: new objects over the same database file."""
        state2 = self.make_state()
        return state2

    def test_suggestion_survives_restart(self):
        state = self.make_state()
        state.register_suggestion(message_id=101, theme_name="Carry Duo")

        restarted = self.restart(state)

        info = restarted.get_suggestion(message_id=101)
        self.assertIsNotNone(info)
        self.assertEqual(info["theme_name"], "Carry Duo")
        self.assertFalse(info["locked"])
        self.assertIsInstance(info["timestamp"], datetime)

    def test_locked_flag_survives_restart(self):
        state = self.make_state()
        state.register_suggestion(message_id=101, theme_name="Carry Duo")
        state.lock_suggestion(101)

        restarted = self.restart(state)

        self.assertTrue(restarted.is_locked(101))
        decision = VoteLockPolicy().evaluate(restarted, message_id=101)
        self.assertFalse(decision.allowed)

    def test_removed_suggestion_stays_removed(self):
        state = self.make_state()
        state.register_suggestion(message_id=101, theme_name="Carry Duo")
        state.remove_suggestion(101)

        restarted = self.restart(state)

        self.assertFalse(restarted.has_suggestion(101))

    def test_thread_survives_restart(self):
        state = self.make_state()
        state.register_suggestion(message_id=101, theme_name="Carry Duo")
        state.register_thread(
            thread_id=55, theme_name="Carry Duo", user_id=42, message_id=101
        )

        restarted = self.restart(state)

        info = restarted.get_thread(thread_id=55)
        self.assertIsNotNone(info)
        self.assertEqual(info["theme_name"], "Carry Duo")
        self.assertEqual(info["user_id"], 42)
        self.assertEqual(info["message_id"], 101)
        self.assertIsInstance(info["created_at"], datetime)
        self.assertTrue(restarted.message_has_active_thread(101))

    def test_removed_thread_stays_removed(self):
        state = self.make_state()
        state.register_suggestion(message_id=101, theme_name="Carry Duo")
        state.register_thread(
            thread_id=55, theme_name="Carry Duo", user_id=42, message_id=101
        )
        state.remove_thread(55)

        restarted = self.restart(state)

        self.assertFalse(restarted.has_thread(55))
        self.assertFalse(restarted.message_has_active_thread(101))

    def test_vote_window_survives_restart(self):
        """A pre-restart timestamp keeps its original vote window."""
        state = self.make_state()
        state.register_suggestion(message_id=101, theme_name="Carry Duo")
        stale = datetime.now(timezone.utc) - timedelta(hours=3)
        state._suggestions[101]["timestamp"] = stale
        state._persistence.save_suggestion(101, state._suggestions[101])

        restarted = self.restart(state)

        decision = VoteLockPolicy().evaluate(restarted, message_id=101)
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.should_lock)


class TestSessionStoreOnlyUsedWhenInjected(unittest.TestCase):
    """Without a persistence seam, SessionState stays purely in-memory."""

    def test_plain_state_is_in_memory(self):
        state = SessionState()
        state.register_suggestion(message_id=1, theme_name="T")
        self.assertIsNone(state.persistence)
        self.assertEqual(state._suggestions, {1: state._suggestions[1]})


if __name__ == "__main__":
    unittest.main()

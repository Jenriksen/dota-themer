import unittest
from datetime import datetime, timedelta, timezone

from session_state import SessionState


class TestThemeSuggestionTracking(unittest.TestCase):
    """SessionState tracks theme suggestion messages."""

    def setUp(self):
        self.state = SessionState()

    def test_register_and_get_suggestion(self):
        """Registering a suggestion stores theme_name/timestamp/locked."""
        self.state.register_suggestion(message_id=101, theme_name="Carry Duo")
        info = self.state.get_suggestion(message_id=101)
        self.assertIsNotNone(info)
        self.assertEqual(info["theme_name"], "Carry Duo")
        self.assertFalse(info["locked"])
        self.assertIn("timestamp", info)

    def test_get_suggestion_unknown_message_returns_none(self):
        """Unknown message_ids return None instead of raising."""
        self.assertIsNone(self.state.get_suggestion(message_id=999))

    def test_has_suggestion(self):
        """has_suggestion reports membership."""
        self.assertFalse(self.state.has_suggestion(101))
        self.state.register_suggestion(message_id=101, theme_name="T")
        self.assertTrue(self.state.has_suggestion(101))

    def test_remove_suggestion(self):
        """Removing a suggestion forgets it, unknown ids are safe."""
        self.state.register_suggestion(message_id=101, theme_name="T")
        self.state.remove_suggestion(101)
        self.assertFalse(self.state.has_suggestion(101))
        self.state.remove_suggestion(101)


class TestVoteLock(unittest.TestCase):
    """SessionState owns the 2-hour voting lock rule."""

    def setUp(self):
        self.state = SessionState()

    def test_fresh_suggestion_is_unlocked(self):
        """A just-registered suggestion is not locked and is votable."""
        self.state.register_suggestion(message_id=1, theme_name="T")
        self.assertFalse(self.state.is_locked(1))

    def test_locked_flag_locks_voting(self):
        """An explicitly locked suggestion refuses further votes."""
        self.state.register_suggestion(message_id=1, theme_name="T")
        self.state.lock_suggestion(1)
        self.assertTrue(self.state.is_locked(1))

    def test_lock_is_idempotent(self):
        """Locking an already-locked suggestion is safe."""
        self.state.register_suggestion(message_id=1, theme_name="T")
        self.state.lock_suggestion(1)
        self.state.lock_suggestion(1)
        self.assertTrue(self.state.is_locked(1))

    def test_lock_unknown_suggestion_is_safe(self):
        """Locking an unregistered message_id does not raise."""
        self.state.lock_suggestion(42)

    def test_is_locked_unknown_message_returns_true(self):
        """Unknown messages are treated as locked (never votable)."""
        self.assertTrue(self.state.is_locked(999))


class TestModificationThreadTracking(unittest.TestCase):
    """SessionState tracks active modification threads per message."""

    def setUp(self):
        self.state = SessionState()
        self.state.register_suggestion(message_id=1, theme_name="Carry Duo")

    def test_register_thread(self):
        """Registering a thread marks the message as having a thread."""
        self.state.register_thread(
            thread_id=55, theme_name="Carry Duo", user_id=7, message_id=1
        )
        info = self.state.get_thread(thread_id=55)
        self.assertEqual(info["theme_name"], "Carry Duo")
        self.assertEqual(info["user_id"], 7)
        self.assertEqual(info["message_id"], 1)
        self.assertIn("created_at", info)
        self.assertTrue(self.state.message_has_active_thread(1))

    def test_get_thread_unknown_returns_none(self):
        """Unknown thread_ids return None instead of raising."""
        self.assertIsNone(self.state.get_thread(thread_id=999))

    def test_remove_thread(self):
        """Removing a thread unmarks its message and forgets it."""
        self.state.register_thread(
            thread_id=55, theme_name="T", user_id=7, message_id=1
        )
        self.state.remove_thread(55)
        self.assertIsNone(self.state.get_thread(thread_id=55))
        self.assertFalse(self.state.message_has_active_thread(1))

    def test_remove_thread_unknown_is_safe(self):
        """Removing an unregistered thread does not raise."""
        self.state.remove_thread(999)

    def test_has_thread(self):
        """has_thread reports membership."""
        self.assertFalse(self.state.has_thread(55))
        self.state.register_thread(
            thread_id=55, theme_name="T", user_id=7, message_id=1
        )
        self.assertTrue(self.state.has_thread(55))


class TestInactiveThreadSweep(unittest.TestCase):
    """SessionState identifies threads inactive past a cutoff."""

    def setUp(self):
        self.state = SessionState()

    def test_fresh_thread_is_not_inactive(self):
        """A thread created now is not inactive at the 10-minute cutoff."""
        self.state.register_suggestion(message_id=1, theme_name="T")
        self.state.register_thread(
            thread_id=55, theme_name="T", user_id=7, message_id=1
        )
        self.assertEqual(self.state.inactive_threads(cutoff=timedelta(minutes=10)), [])

    def test_old_thread_is_inactive(self):
        """A thread created 11 minutes ago is inactive at 10 minutes."""
        self.state.register_suggestion(message_id=1, theme_name="T")
        self.state.register_thread(
            thread_id=55, theme_name="T", user_id=7, message_id=1
        )
        self.state._threads[55]["created_at"] = datetime.now(timezone.utc) - timedelta(
            minutes=11
        )
        inactive = self.state.inactive_threads(cutoff=timedelta(minutes=10))
        self.assertEqual(inactive, [55])

    def test_inactive_threads_do_not_include_valid_ones(self):
        """Mixing old and fresh threads reports only the old ones."""
        self.state.register_suggestion(message_id=1, theme_name="T")
        self.state.register_thread(
            thread_id=55, theme_name="T", user_id=7, message_id=1
        )
        self.state.register_thread(
            thread_id=56, theme_name="T", user_id=7, message_id=1
        )
        self.state._threads[55]["created_at"] = datetime.now(timezone.utc) - timedelta(
            minutes=12
        )
        inactive = self.state.inactive_threads(cutoff=timedelta(minutes=10))
        self.assertEqual(inactive, [55])


if __name__ == "__main__":
    unittest.main()

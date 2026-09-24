import unittest

import thread_commands


class TestIsExitCommand(unittest.TestCase):
    """parse_exit detects end-of-session commands."""

    def test_exit_words(self):
        for word in ["done", "cancel", "exit", "quit"]:
            with self.subTest(word=word):
                self.assertTrue(thread_commands.is_exit_command(word))
                self.assertTrue(thread_commands.is_exit_command(word.upper()))
                self.assertTrue(thread_commands.is_exit_command(f"  {word}  "))

    def test_non_exit_content(self):
        self.assertFalse(thread_commands.is_exit_command("add axe"))
        self.assertFalse(thread_commands.is_exit_command(""))
        self.assertFalse(thread_commands.is_exit_command("don"))


class TestParseModification(unittest.TestCase):
    """parse_modification extracts action and hero names from thread input."""

    def test_plus_prefix(self):
        result = thread_commands.parse_modification("+ axe")
        self.assertIsNotNone(result)
        self.assertEqual(result.action, "add")
        self.assertEqual(result.hero_names, ["axe"])

    def test_minus_prefix(self):
        result = thread_commands.parse_modification("-axe")
        self.assertIsNotNone(result)
        self.assertEqual(result.action, "remove")
        self.assertEqual(result.hero_names, ["axe"])

    def test_add_word(self):
        result = thread_commands.parse_modification("Add axe, Zeus")
        self.assertIsNotNone(result)
        self.assertEqual(result.action, "add")
        self.assertEqual(result.hero_names, ["axe,", "Zeus"])

    def test_remove_word(self):
        result = thread_commands.parse_modification("remove axe")
        self.assertIsNotNone(result)
        self.assertEqual(result.action, "remove")
        self.assertEqual(result.hero_names, ["axe"])

    def test_quoted_hero_names_are_kept_whole(self):
        result = thread_commands.parse_modification('add "lord of hell" axe')
        self.assertIsNotNone(result)
        self.assertEqual(result.action, "add")
        self.assertEqual(result.hero_names, ["lord of hell", "axe"])

    def test_quotes_with_partial_matches_still_split(self):
        result = thread_commands.parse_modification('add "lord of hell" axe')
        self.assertIsNotNone(result)
        self.assertEqual(result.hero_names, ["lord of hell", "axe"])

    def test_unrecognized_content_returns_none(self):
        self.assertIsNone(thread_commands.parse_modification("hello world"))
        self.assertIsNone(thread_commands.parse_modification(""))

    def test_bare_prefix_yields_empty_hero_names(self):
        result = thread_commands.parse_modification("+")
        self.assertIsNotNone(result)
        self.assertEqual(result.action, "add")
        self.assertEqual(result.hero_names, [])
        result = thread_commands.parse_modification("remove")
        self.assertIsNotNone(result)
        self.assertEqual(result.action, "remove")
        self.assertEqual(result.hero_names, [])

    def test_dataclass_fields(self):
        result = thread_commands.parse_modification("+axe")
        self.assertEqual(result.action, "add")
        self.assertEqual(result.hero_names, ["axe"])


if __name__ == "__main__":
    unittest.main()

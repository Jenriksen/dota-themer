"""Tests for the presentation module (R4a: extracted message rendering)."""

import unittest

import presentation


class TestRenderThemeSuggestion(unittest.TestCase):
    """render_theme_suggestion produces the Discord theme message."""

    def test_full_suggestion(self):
        """Theme, description, heroes, feedback, and footer all render."""
        msg = presentation.render_theme_suggestion(
            theme_name="Undead Heroes",
            description="Undead or skeletal heroes",
            heroes_display="Abaddon (3,4), Undying (3,4,5)",
            hero_count=2,
            feedback_score=5,
        )
        self.assertEqual(
            msg,
            "**Theme:** Undead Heroes\n"
            "**Description:** Undead or skeletal heroes\n"
            "**Heroes:** Abaddon (3,4), Undying (3,4,5)\n"
            "**Feedback:** 5 \U0001f44d\U0001f44e\n"
            "*(2 heroes match this theme)*\n"
            "\n"
            "React with \U0001f44d to upvote this theme, or \U0001f44e to downvote it!"
            " (Voting locks after 2 hours)",
        )

    def test_empty_description_is_omitted(self):
        """No description line when the description is empty."""
        msg = presentation.render_theme_suggestion(
            theme_name="T",
            description="",
            heroes_display="Axe (3)",
            hero_count=1,
            feedback_score=0,
        )
        self.assertNotIn("Description", msg)
        self.assertIn("**Theme:** T", msg)


class TestRenderModificationInstructions(unittest.TestCase):
    """render_modification_instructions produces the thread how-to message."""

    def test_instructions_contain_theme_heroes_and_commands(self):
        """Instructions name the theme, its heroes, and the modify syntax."""
        msg = presentation.render_modification_instructions(
            theme_name="Carry Duo",
            heroes_list="Axe, Zeus",
        )
        self.assertIn("**Theme:** Carry Duo", msg)
        self.assertIn("**Current Heroes:** Axe, Zeus", msg)
        self.assertIn('"Add HeroName"', msg)
        self.assertIn('"Remove HeroName"', msg)
        self.assertIn('"Done", "Cancel", "Exit", or "Quit"', msg)


if __name__ == "__main__":
    unittest.main()

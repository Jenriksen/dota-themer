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
            heroes_display="- Abaddon (pos 3,4) - winrate 51.2%\n- Undying (pos 3,4,5) - winrate 52.0%",
            hero_count=2,
            feedback_score=5,
        )
        self.assertEqual(
            msg,
            "**Theme:** Undead Heroes\n"
            "**Description:** Undead or skeletal heroes\n"
            "**Heroes:**\n"
            "- Abaddon (pos 3,4) - winrate 51.2%\n"
            "- Undying (pos 3,4,5) - winrate 52.0%\n"
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


class TestRenderLaneDuoSuggestions(unittest.TestCase):
    """render_lane_duo_suggestions produces the duo block."""

    def test_duo_block_renders_lane_heroes_and_winrate(self):
        duos = [
            {
                "lane": "Safelane",
                "hero1": "Crystal Maiden",
                "hero2": "Juggernaut",
                "games": 30.0,
                "winrate": 66.7,
            },
        ]
        msg = presentation.render_lane_duo_suggestions(duos)
        self.assertEqual(
            msg,
            "**Suggested lane duos:**\n"
            "Safelane: Crystal Maiden + Juggernaut (67% over ~30 games)",
        )

    def test_no_duos_renders_empty_string(self):
        self.assertEqual(presentation.render_lane_duo_suggestions([]), "")

    def test_suggestion_can_embed_the_duo_block(self):
        """render_theme_suggestion inserts the block before feedback."""
        msg = presentation.render_theme_suggestion(
            theme_name="T",
            description="",
            heroes_display="Axe (pos 3,4)",
            hero_count=1,
            feedback_score=0,
            lane_duos_display="**Suggested lane duos:**\nOfflane: Axe + Chen (55% over ~22 games)",
        )
        self.assertIn(
            "Axe (pos 3,4)\n**Suggested lane duos:**\n"
            "Offlane: Axe + Chen (55% over ~22 games)\n**Feedback:**",
            msg,
        )

    def test_suggestion_without_duos_is_unchanged(self):
        """No lane_duos_display means no duo lines in the message."""
        msg = presentation.render_theme_suggestion(
            theme_name="T",
            description="",
            heroes_display="Axe (pos 3,4)",
            hero_count=1,
            feedback_score=0,
        )
        self.assertNotIn("Suggested lane duos", msg)


class TestRenderSuggestionEmbedData(unittest.TestCase):
    """render_suggestion_embed_data produces embed fields for M4.3."""

    def test_embed_data_structure(self):
        data = presentation.render_suggestion_embed_data(
            theme_name="Undead Heroes",
            description="Undead or skeletal heroes",
            heroes_display="- [Axe](https://www.dota2.com/hero/axe) (pos 3,4)",
            hero_count=1,
            feedback_score=5,
            thumbnail_url="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/axe.png",
            footer="Theme of the day for 2026-10-24 (UTC)",
        )
        self.assertEqual(data["title"], "Undead Heroes")
        self.assertIn("Undead or skeletal heroes", data["description"])
        self.assertIn("1 heroes match this theme", data["description"])
        self.assertEqual(data["fields"][0], ("Heroes", "- [Axe](https://www.dota2.com/hero/axe) (pos 3,4)", False))
        self.assertIn("Feedback: 5", data["footer"])
        self.assertIn("Theme of the day for 2026-10-24 (UTC)", data["footer"])
        self.assertTrue(data["thumbnail"].endswith("/axe.png"))

    def test_embed_data_without_optional_parts(self):
        data = presentation.render_suggestion_embed_data(
            theme_name="T",
            description="",
            heroes_display="Axe (pos 3,4)",
            hero_count=1,
            feedback_score=0,
        )
        self.assertEqual(data["title"], "T")
        self.assertNotIn("Theme of the day", data["footer"])
        self.assertIsNone(data["thumbnail"])
        self.assertEqual(len(data["fields"]), 1)

    def test_embed_data_includes_lane_duos_field(self):
        data = presentation.render_suggestion_embed_data(
            theme_name="T",
            description="",
            heroes_display="Axe (pos 3,4)",
            hero_count=1,
            feedback_score=0,
            lane_duos_display="**Suggested lane duos:**\nOfflane: Axe + Chen (55% over ~22 games)",
        )
        self.assertEqual(len(data["fields"]), 2)
        self.assertEqual(data["fields"][1][0], "Suggested lane duos")
        self.assertEqual(
            data["fields"][1][1], "Offlane: Axe + Chen (55% over ~22 games)"
        )


if __name__ == "__main__":
    unittest.main()

"""
Expand heroes.json to include all Dota 2 heroes.
This script contains manually compiled data for all heroes.
"""

import json
from pathlib import Path

# Complete list of Dota 2 heroes with positions
# Positions based on Dota 2 meta and common usage
COMPLETE_HEROES = [
    # Existing heroes (keep for reference)
    {"id": "npc_dota_hero_antimage", "name": "Anti-Mage", "primary_role": "Carry", "positions": [1, 2], "positions_display": "1,2"},
    {"id": "npc_dota_hero_axe", "name": "Axe", "primary_role": "Initiator", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_bane", "name": "Bane", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_bloodseeker", "name": "Bloodseeker", "primary_role": "Carry", "positions": [1, 3], "positions_display": "1,3"},
    {"id": "npc_dota_hero_bristleback", "name": "Bristleback", "primary_role": "Initiator", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_centaur", "name": "Centaur Warrunner", "primary_role": "Initiator", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_chaos_knight", "name": "Chaos Knight", "primary_role": "Carry", "positions": [1, 3], "positions_display": "1,3"},
    {"id": "npc_dota_hero_rattletrap", "name": "Clockwerk", "primary_role": "Initiator", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_crystal_maiden", "name": "Crystal Maiden", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_dark_seer", "name": "Dark Seer", "primary_role": "Initiator", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_dazzle", "name": "Dazzle", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_death_prophet", "name": "Death Prophet", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_disruptor", "name": "Disruptor", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_doombringer", "name": "Doom Bringer", "primary_role": "Initiator", "positions": [1, 3], "positions_display": "1,3"},
    {"id": "npc_dota_hero_dragon_knight", "name": "Dragon Knight", "primary_role": "Carry", "positions": [1, 3], "positions_display": "1,3"},
    {"id": "npc_dota_hero_drow_ranger", "name": "Drow Ranger", "primary_role": "Carry", "positions": [1, 2], "positions_display": "1,2"},
    {"id": "npc_dota_hero_earthshaker", "name": "Earthshaker", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_juggernaut", "name": "Juggernaut", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_keeper_of_the_light", "name": "Keeper of the Light", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_kunkka", "name": "Kunkka", "primary_role": "Carry", "positions": [1, 3], "positions_display": "1,3"},
    {"id": "npc_dota_hero_legion_commander", "name": "Legion Commander", "primary_role": "Carry", "positions": [1, 3, 4], "positions_display": "1,3,4"},
    {"id": "npc_dota_hero_lichen", "name": "Lich", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_life_stealer", "name": "Lifestealer", "primary_role": "Carry", "positions": [1], "positions_display": "1"},
    {"id": "npc_dota_hero_lina", "name": "Lina", "primary_role": "Support", "positions": [2, 4], "positions_display": "2,4"},
    {"id": "npc_dota_hero_lion", "name": "Lion", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_luna", "name": "Luna", "primary_role": "Carry", "positions": [1, 2], "positions_display": "1,2"},
    {"id": "npc_dota_hero_mirana", "name": "Mirana", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_nevermore", "name": "Shadow Fiend", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_morphling", "name": "Morphling", "primary_role": "Carry", "positions": [1, 2], "positions_display": "1,2"},
    {"id": "npc_dota_hero_phantom_assassin", "name": "Phantom Assassin", "primary_role": "Carry", "positions": [1, 2], "positions_display": "1,2"},
    {"id": "npc_dota_hero_phantom_lancer", "name": "Phantom Lancer", "primary_role": "Carry", "positions": [1, 3], "positions_display": "1,3"},
    {"id": "npc_dota_hero_puck", "name": "Puck", "primary_role": "Initiator", "positions": [2, 3], "positions_display": "2,3"},
    {"id": "npc_dota_hero_pudge", "name": "Pudge", "primary_role": "Initiator", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_razor", "name": "Razor", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_riki", "name": "Riki", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_sand_king", "name": "Sand King", "primary_role": "Initiator", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_shadow_shaman", "name": "Shadow Shaman", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_slardar", "name": "Slardar", "primary_role": "Carry", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_snapfire", "name": "Snapfire", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_sniper", "name": "Sniper", "primary_role": "Carry", "positions": [1, 2], "positions_display": "1,2"},
    {"id": "npc_dota_hero_spirit_breaker", "name": "Spirit Breaker", "primary_role": "Carry", "positions": [1, 4], "positions_display": "1,4"},
    {"id": "npc_dota_hero_storm_spirit", "name": "Storm Spirit", "primary_role": "Carry", "positions": [1, 2], "positions_display": "1,2"},
    {"id": "npc_dota_hero_sven", "name": "Sven", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_tidehunter", "name": "Tidehunter", "primary_role": "Initiator", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_shredder", "name": "Timbersaw", "primary_role": "Initiator", "positions": [2, 3], "positions_display": "2,3"},
    {"id": "npc_dota_hero_tinker", "name": "Tinker", "primary_role": "Carry", "positions": [1, 2], "positions_display": "1,2"},
    {"id": "npc_dota_hero_tiny", "name": "Tiny", "primary_role": "Carry", "positions": [1, 2, 4], "positions_display": "1,2,4"},
    {"id": "npc_dota_hero_vengefulspirit", "name": "Vengeful Spirit", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_viper", "name": "Viper", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_warlock", "name": "Warlock", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_windrunner", "name": "Windranger", "primary_role": "Carry", "positions": [1, 2, 4], "positions_display": "1,2,4"},
    {"id": "npc_dota_hero_zuus", "name": "Zeus", "primary_role": "Support", "positions": [2, 4], "positions_display": "2,4"},
]

# Missing heroes to add
MISSING_HEROES = [
    {"id": "npc_dota_hero_abaddon", "name": "Abaddon", "primary_role": "Support", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_alchemist", "name": "Alchemist", "primary_role": "Carry", "positions": [1, 3], "positions_display": "1,3"},
    {"id": "npc_dota_hero_ancient_apparition", "name": "Ancient Apparition", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_arc_warden", "name": "Arc Warden", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_beastmaster", "name": "Beastmaster", "primary_role": "Initiator", "positions": [1, 3, 4], "positions_display": "1,3,4"},
    {"id": "npc_dota_hero_brewmaster", "name": "Brewmaster", "primary_role": "Initiator", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_broodmother", "name": "Broodmother", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_bounty_hunter", "name": "Bounty Hunter", "primary_role": "Carry", "positions": [1, 2, 4], "positions_display": "1,2,4"},
    {"id": "npc_dota_hero_chen", "name": "Chen", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_clinkz", "name": "Clinkz", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_dawnbreaker", "name": "Dawnbreaker", "primary_role": "Carry", "positions": [1, 3], "positions_display": "1,3"},
    {"id": "npc_dota_hero_dark_willow", "name": "Dark Willow", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_enchantress", "name": "Enchantress", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_ember_spirit", "name": "Ember Spirit", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_furion", "name": "Furion", "primary_role": "Carry", "positions": [1, 2, 5], "positions_display": "1,2,5"},
    {"id": "npc_dota_hero_grimstroke", "name": "Grimstroke", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_gyrocopter", "name": "Gyrocopter", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_hoodwink", "name": "Hoodwink", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_huskar", "name": "Huskar", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_invoker", "name": "Invoker", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_jakiro", "name": "Jakiro", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_wisp", "name": "Io", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_lone_druid", "name": "Lone Druid", "primary_role": "Carry", "positions": [1, 3, 5], "positions_display": "1,3,5"},
    {"id": "npc_dota_hero_lycan", "name": "Lycan", "primary_role": "Carry", "positions": [1, 3, 4], "positions_display": "1,3,4"},
    {"id": "npc_dota_hero_magnataur", "name": "Magnus", "primary_role": "Initiator", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_meepo", "name": "Meepo", "primary_role": "Carry", "positions": [1, 2, 4], "positions_display": "1,2,4"},
    {"id": "npc_dota_hero_mars", "name": "Mars", "primary_role": "Carry", "positions": [1, 3], "positions_display": "1,3"},
    {"id": "npc_dota_hero_monkey_king", "name": "Monkey King", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_necrolyte", "name": "Necrophos", "primary_role": "Carry", "positions": [1, 2], "positions_display": "1,2"},
    {"id": "npc_dota_hero_naga_siren", "name": "Naga Siren", "primary_role": "Carry", "positions": [1, 2, 4], "positions_display": "1,2,4"},
    {"id": "npc_dota_hero_furion", "name": "Nature's Prophet", "primary_role": "Carry", "positions": [1, 2, 5], "positions_display": "1,2,5"},
    {"id": "npc_dota_hero_nyx_assassin", "name": "Nyx Assassin", "primary_role": "Initiator", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_ogre_magi", "name": "Ogre Magi", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_omniknight", "name": "Omniknight", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_oracle", "name": "Oracle", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_outworld_devourer", "name": "Outworld Devourer", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_pangolier", "name": "Pangolier", "primary_role": "Initiator", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_phoenix", "name": "Phoenix", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_pugna", "name": "Pugna", "primary_role": "Support", "positions": [2, 4, 5], "positions_display": "2,4,5"},
    {"id": "npc_dota_hero_queenofpain", "name": "Queen of Pain", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_rubick", "name": "Rubick", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_skywrath_mage", "name": "Skywrath Mage", "primary_role": "Support", "positions": [2, 4, 5], "positions_display": "2,4,5"},
    {"id": "npc_dota_hero_slark", "name": "Slark", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_silencer", "name": "Silencer", "primary_role": "Carry", "positions": [1, 2, 5], "positions_display": "1,2,5"},
    {"id": "npc_dota_hero_templar_assassin", "name": "Templar Assassin", "primary_role": "Carry", "positions": [1, 2, 4], "positions_display": "1,2,4"},
    {"id": "npc_dota_hero_terrorblade", "name": "Terrorblade", "primary_role": "Carry", "positions": [1, 5], "positions_display": "1,5"},
    {"id": "npc_dota_hero_tidehunter", "name": "Tidehunter", "primary_role": "Initiator", "positions": [3, 4], "positions_display": "3,4"},
    {"id": "npc_dota_hero_techies", "name": "Techies", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_treant", "name": "Treant Protector", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_troll_warlord", "name": "Troll Warlord", "primary_role": "Carry", "positions": [1, 2], "positions_display": "1,2"},
    {"id": "npc_dota_hero_undying", "name": "Undying", "primary_role": "Support", "positions": [3, 4, 5], "positions_display": "3,4,5"},
    {"id": "npc_dota_hero_ursa", "name": "Ursa", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_venomancer", "name": "Venomancer", "primary_role": "Support", "positions": [3, 4, 5], "positions_display": "3,4,5"},
    {"id": "npc_dota_hero_void_spirit", "name": "Void Spirit", "primary_role": "Carry", "positions": [1, 2, 3], "positions_display": "1,2,3"},
    {"id": "npc_dota_hero_winter_wyvern", "name": "Winter Wyvern", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_witch_doctor", "name": "Witch Doctor", "primary_role": "Support", "positions": [4, 5], "positions_display": "4,5"},
    {"id": "npc_dota_hero_wraith_king", "name": "Wraith King", "primary_role": "Carry", "positions": [1], "positions_display": "1"},
    {"id": "npc_dota_hero_underlord", "name": "Underlord", "primary_role": "Initiator", "positions": [3, 4], "positions_display": "3,4"},
]


def expand_heroes():
    """Expand heroes.json with all Dota 2 heroes."""
    DATA_DIR = Path(__file__).parent.parent / "data"
    heroes_path = DATA_DIR / "heroes.json"
    
    # Load existing
    with open(heroes_path, "r") as f:
        existing = json.load(f)
    
    existing_ids = {h["id"] for h in existing}
    
    # Add missing
    added = []
    for hero in MISSING_HEROES:
        if hero["id"] not in existing_ids:
            existing.append(hero)
            added.append(hero["name"])
            existing_ids.add(hero["id"])
    
    # Sort by name
    existing.sort(key=lambda h: h["name"])
    
    # Save
    with open(heroes_path, "w") as f:
        json.dump(existing, f, indent=2)
    
    print(f"Total: {len(existing)} heroes")
    print(f"Added: {len(added)} heroes - {', '.join(added[:10])}...")


if __name__ == "__main__":
    expand_heroes()

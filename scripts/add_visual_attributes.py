#!/usr/bin/env python3
"""
Script to add visual attributes to all heroes in heroes.json.

Visual attributes include:
- colors: Primary color scheme (list of strings)
- features: Distinguishing visual features (list of strings)
- Boolean flags: has_hair, has_horns, has_wings, has_tail, has_beard, 
  has_hat, has_mask, has_staff, has_sword
"""

import json
from pathlib import Path

# Load heroes
DATA_DIR = Path(__file__).parent.parent / "data"
HEROES_FILE = DATA_DIR / "heroes.json"

with open(HEROES_FILE, 'r') as f:
    heroes = json.load(f)

# Comprehensive visual attributes for all 121 heroes
VISUAL_ATTRIBUTES = {
    "abaddon": {
        "colors": ["white", "black"],
        "features": ["undead", "glowing_eyes", "cape"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "alchemist": {
        "colors": ["green", "brown"],
        "features": ["beard", "bald", "tanky", "chemical_rage"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "ancient_apparition": {
        "colors": ["white", "blue"],
        "features": ["ghostly", "glowing", "wings", "ethereal"],
        "has_hair": False, "has_horns": False, "has_wings": True,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "antimage": {
        "colors": ["purple", "black"],
        "features": ["bald", "mystical", "mana_burn", "blink"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "arc_warden": {
        "colors": ["green", "blue"],
        "features": ["arcane", "glowing", "duplicate", "spark"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "axe": {
        "colors": ["red", "brown"],
        "features": ["beard", "muscular", "angry", "berserk", "counter_helix"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "bane": {
        "colors": ["purple", "black"],
        "features": ["hooded", "tentacles", "brain", "nightmare", "fiend"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": False, "has_hat": True,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "beastmaster": {
        "colors": ["brown", "green"],
        "features": ["beard", "animal_companions", "horns", "wild", "primal_roar"],
        "has_hair": True, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "bloodseeker": {
        "colors": ["red", "black"],
        "features": ["bald", "blood", "visible_teeth", "thirst", "rupture"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "bounty_hunter": {
        "colors": ["brown", "gold"],
        "features": ["masked", "cape", "bounty", "tracker", "shuriken"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": True, "has_staff": False, "has_sword": True
    },
    "brewmaster": {
        "colors": ["red", "brown"],
        "features": ["beard", "dwarven", "panda", "drunk", "primal_split"],
        "has_hair": True, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "bristleback": {
        "colors": ["green", "brown"],
        "features": ["beard", "quills", "tanky", "porcupine", "warpath"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "broodmother": {
        "colors": ["black", "purple"],
        "features": ["spider", "invisible", "tails", "web", "spawn_spiderlings"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "centaur": {
        "colors": ["brown", "blue"],
        "features": ["horse", "beard", "tanky", "stampede", "return"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "chaos_knight": {
        "colors": ["red", "black"],
        "features": ["armored", "horse", "chaos", "illusion", "reality_rift"],
        "has_hair": True, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "chen": {
        "colors": ["green", "white"],
        "features": ["holy", "serene", "healer", "summoner", "penitence"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": True,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "clinkz": {
        "colors": ["green", "black"],
        "features": ["skeletal", "invisible", "bow", "bone", "strafe"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": False, "has_hat": True,
        "has_mask": True, "has_staff": False, "has_sword": False
    },
    "crystal_maiden": {
        "colors": ["blue", "white"],
        "features": ["ice", "glowing", "hat", "frost", "nova"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": True,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "dark_seer": {
        "colors": ["black", "purple"],
        "features": ["masked", "mystical", "tails", "wall", "vacuum"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": True, "has_staff": True, "has_sword": False
    },
    "dark_willow": {
        "colors": ["purple", "black"],
        "features": ["mystical", "fae", "wings", "shadow", "bedlam"],
        "has_hair": True, "has_horns": False, "has_wings": True,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "dawnbreaker": {
        "colors": ["orange", "gold"],
        "features": ["armored", "sun", "shield", "light", "celestial_hammer"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": True,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "dazzle": {
        "colors": ["white", "gold"],
        "features": ["glowing", "healer", "poor_eyesight", "shadow", "weave"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "death_prophet": {
        "colors": ["white", "blue"],
        "features": ["undead", "ghostly", "carrion", "screech", "silence"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "disruptor": {
        "colors": ["purple", "black"],
        "features": ["electric", "glowing", "masked", "thunder", "glimpse"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": True, "has_staff": False, "has_sword": False
    },
    "doombringer": {
        "colors": ["red", "black"],
        "features": ["demonic", "scary_face", "doom", "infernal", "devour"],
        "has_hair": False, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "dragon_knight": {
        "colors": ["red", "green"],
        "features": ["dragon", "rides_steed", "armored", "beard", "horns", "tails", "fire", "breathe_fire"],
        "has_hair": True, "has_horns": True, "has_wings": False,
        "has_tail": True, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "drow_ranger": {
        "colors": ["black", "white"],
        "features": ["elven", "hooded", "wings", "cape", "frost_arrows", "marksmanship"],
        "has_hair": True, "has_horns": False, "has_wings": True,
        "has_tail": False, "has_beard": False, "has_hat": True,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "earth_spirit": {
        "colors": ["green", "brown"],
        "features": ["stone", "nature", "fast", "rolling", "boulder"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "earthshaker": {
        "colors": ["brown", "orange"],
        "features": ["muscular", "totem", "horns", "earthquake", "fissure"],
        "has_hair": True, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "elder_titan": {
        "colors": ["green", "brown"],
        "features": ["giant", "nature", "ancient", "stomp", "echo_stomp"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "ember_spirit": {
        "colors": ["orange", "red"],
        "features": ["fire", "fast", "flaming", "sleight", "flame_guard"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "enchantress": {
        "colors": ["green", "white"],
        "features": ["nature", "animal_companions", "healer", "enchant", "untouchable"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "furion": {
        "colors": ["green", "brown"],
        "features": ["nature", "tree_hugger", "summoner", "wrath", "treants"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "grimstroke": {
        "colors": ["purple", "black"],
        "features": ["artistic", "masked", "ink", "stroke", "soul_chain"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": True, "has_staff": False, "has_sword": False
    },
    "gyrocopter": {
        "colors": ["brown", "gold"],
        "features": ["flying", "mechanical", "robot", "bombs", "call_down"],
        "has_hair": True, "has_horns": False, "has_wings": True,
        "has_tail": False, "has_beard": True, "has_hat": True,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "hoodwink": {
        "colors": ["green", "brown"],
        "features": ["forest", "hooded", "sneaky", "acorn", "bushwhack"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": True,
        "has_mask": True, "has_staff": False, "has_sword": False
    },
    "huskar": {
        "colors": ["brown", "red"],
        "features": ["tribal", "spears", "berserk", "sacrifice", "inner_fire"],
        "has_hair": True, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "invoker": {
        "colors": ["purple", "gold"],
        "features": ["arcane", "masked", "elements", "tornado", "emp", "alacrity"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": True, "has_staff": False, "has_sword": False
    },
    "jakiro": {
        "colors": ["red", "blue"],
        "features": ["dual_headed", "fire", "ice", "tails", "dragon", "dual_breath"],
        "has_hair": False, "has_horns": False, "has_wings": True,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "juggernaut": {
        "colors": ["blue", "gold"],
        "features": ["bald", "sword", "healing", "omnislash", "blade_fury"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "keeper_of_the_light": {
        "colors": ["white", "gold"],
        "features": ["glowing", "poor_eyesight", "rides_steed", "hat", "illuminate", "chakra"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": True,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "kunkka": {
        "colors": ["blue", "gold"],
        "features": ["pirate", "one_eyed", "sword", "tide", "boat", "torrent"],
        "has_hair": True, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": True,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "legion_commander": {
        "colors": ["red", "gold"],
        "features": ["armored", "cape", "sword", "visible_teeth", "duel", "overwhelming_odds"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "leshrac": {
        "colors": ["green", "purple"],
        "features": ["demonic", "split_personality", "magic", "pulse", "diabolic_edict"],
        "has_hair": False, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "lichen": {
        "colors": ["blue", "white"],
        "features": ["ice", "undead", "frost", "sacrifice", "chain_frost"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "life_stealer": {
        "colors": ["green", "black"],
        "features": ["demonic", "scary_face", "infect", "rage", "open_wounds"],
        "has_hair": False, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "lina": {
        "colors": ["red", "white"],
        "features": ["fire", "hat", "glowing", "poor_eyesight", "laguna_blade", "light_strike"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": True,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "lion": {
        "colors": ["blue", "white"],
        "features": ["maned", "finger_mustache", "magic", "impale", "voodoo"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "lone_druid": {
        "colors": ["green", "brown"],
        "features": ["nature", "animal_companions", "summoner", "bear", "true_form", "savage_roar"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "luna": {
        "colors": ["blue", "white"],
        "features": ["elven", "moon", "wings", "cape", "lucent_beam", "eclipse"],
        "has_hair": True, "has_horns": False, "has_wings": True,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "lycan": {
        "colors": ["brown", "green"],
        "features": ["werewolf", "summoner", "shapeshift", "howl", "wolves"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "magnataur": {
        "colors": ["blue", "silver"],
        "features": ["giant", "magnetic", "shockwave", "reverse_polarity", "skewer"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "mars": {
        "colors": ["red", "gold"],
        "features": ["armored", "spear", "god_of_war", "arena", "gods_rebuke"],
        "has_hair": True, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": True,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "medusa": {
        "colors": ["green", "gold"],
        "features": ["snake_hair", "stone_gaze", "mystic_snake", "mana_shield"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "meepo": {
        "colors": ["green", "brown"],
        "features": ["small", "duplicate", "poof", "earthbind", "ransack"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "mirana": {
        "colors": ["white", "blue"],
        "features": ["elven", "moon", "wings", "arrow", "sacred_arrow", "leap"],
        "has_hair": True, "has_horns": False, "has_wings": True,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "monkey_king": {
        "colors": ["brown", "gold"],
        "features": ["monkey", "masked", "staff", "boundless_strike", "tree_dance"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": True, "has_staff": True, "has_sword": False
    },
    "morphling": {
        "colors": ["blue", "white"],
        "features": ["shapeshift", "wave", "adaptive_strike", "morph", "ethereal"],
        "has_hair": True, "has_horns": False, "has_wings": True,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "muerta": {
        "colors": ["purple", "black"],
        "features": ["skeletal", "gun", "gunslinger", "dead_shot", "the_gunslinger"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": True,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "naga_siren": {
        "colors": ["blue", "green"],
        "features": ["mermaid", "song", "ensnare", "mirror_image", "rip_tide"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "necrolyte": {
        "colors": ["green", "black"],
        "features": ["undead", "sadistic", "heartstopper", "death_pulse", "reapers_scythe"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "nevermore": {
        "colors": ["black", "red"],
        "features": ["demonic", "wings", "scary_face", "shadow", "requiem", "necromastery"],
        "has_hair": False, "has_horns": False, "has_wings": True,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "night_stalker": {
        "colors": ["black", "purple"],
        "features": ["dark", "invisible", "void", "crippling_fear", "hunter_in_the_night"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "nyx_assassin": {
        "colors": ["purple", "black"],
        "features": ["invisible", "spiked", "impale", "mana_burn", "vendetta"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "ogre_magi": {
        "colors": ["green", "brown"],
        "features": ["ogre", "multi_armed", "fire", "bloodlust", "ignite"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "omniknight": {
        "colors": ["white", "gold"],
        "features": ["armored", "healer", "angelic", "purification", "repel"],
        "has_hair": True, "has_horns": False, "has_wings": True,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "oracle": {
        "colors": ["white", "blue"],
        "features": ["mystical", "healer", "false_promise", "fates_edict", "purifying_flames"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "outworld_devourer": {
        "colors": ["black", "purple"],
        "features": ["astral", "intelligence", "arcane_orb", "essence_flux", "sanity_eclipse"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "pangolier": {
        "colors": ["brown", "gold"],
        "features": ["armored", "tail", "rolling", "swash_buckle", "shield_crash"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "phantom_assassin": {
        "colors": ["black", "purple"],
        "features": ["invisible", "blur", "visible_teeth", "stifling_dagger", "coup_de_grace"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "phantom_lancer": {
        "colors": ["blue", "white"],
        "features": ["cape", "illusions", "juxtapose", "doppelganger", "phantom_rush"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": True
    },
    "phoenix": {
        "colors": ["red", "orange"],
        "features": ["fire", "wings", "sun", "supernova", "icarus_dive", "fire_spirits"],
        "has_hair": False, "has_horns": False, "has_wings": True,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "puck": {
        "colors": ["blue", "white"],
        "features": ["fae", "wings", "orb", "illusionary", "phase_shift", "dream_coil"],
        "has_hair": True, "has_horns": False, "has_wings": True,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "pudge": {
        "colors": ["brown", "black"],
        "features": ["fat", "hook", "dismember", "rot", "meat_hook"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "pugna": {
        "colors": ["purple", "black"],
        "features": ["nether", "blast", "ward", "decrepify", "nether_blast"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "pugo": {
        "colors": ["green", "brown"],
        "features": ["small", "nether", "swarm", "nether_blast"],
        "has_hair": False, "has_horns": False, "has_wings": True,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "queenofpain": {
        "colors": ["purple", "black"],
        "features": ["demonic", "wings", "scream", "shadow_strike", "sonic_wave"],
        "has_hair": False, "has_horns": True, "has_wings": True,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "rattletrap": {
        "colors": ["brown", "gold"],
        "features": ["mechanical", "robot", "hookshot", "power_cogs", "rocket_flare"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": True, "has_staff": False, "has_sword": False
    },
    "razor": {
        "colors": ["blue", "white"],
        "features": ["lightning", "storm", "visible_teeth", "plasma_field", "static_link"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "ringmaster": {
        "colors": ["red", "gold"],
        "features": ["circus", "whip", "tiger", "ring_of_fire", "tame_the_beast"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": True, "has_hat": True,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "rubick": {
        "colors": ["purple", "white"],
        "features": ["arcane", "telekinetic", "spell_steal", "fade_bolt", "null_field"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "sand_king": {
        "colors": ["yellow", "brown"],
        "features": ["sand", "burrow", "caustic_finale", "sand_storm", "epicenter"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "shadow_demon": {
        "colors": ["purple", "black"],
        "features": ["demonic", "shadow", "disruption", "soul_catcher", "demonic_purge"],
        "has_hair": False, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "shadow_shaman": {
        "colors": ["purple", "black"],
        "features": ["shaman", "hex", "serpent_ward", "voodoo", "ether_shock"],
        "has_hair": True, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "silencer": {
        "colors": ["purple", "black"],
        "features": ["muted", "intelligence", "last_word", "global_silence", "curse_of_the_silent"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "skywrath_mage": {
        "colors": ["blue", "white"],
        "features": ["dragon", "wings", "mystic_flare", "concussive_shot", "arcane_bolt"],
        "has_hair": True, "has_horns": True, "has_wings": True,
        "has_tail": True, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "slardar": {
        "colors": ["blue", "white"],
        "features": ["fish", "one_eyed", "crush", "slithereen_crush", "bash"],
        "has_hair": False, "has_horns": True, "has_wings": False,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "slark": {
        "colors": ["blue", "black"],
        "features": ["fish", "dark", "pounce", "essence_shift", "shadow_dance"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "snapfire": {
        "colors": ["blue", "white"],
        "features": ["old", "dragon", "rides_steed", "one_eyed", "scatterblast", "firesnap_cookie"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "sniper": {
        "colors": ["green", "brown"],
        "features": ["dwarven", "snipe", "shrapnel", "headshot", "assassinate"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": True,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "spectre": {
        "colors": ["white", "blue"],
        "features": ["ghostly", "spectral", "dispersion", "reality", "haunt"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "spirit_breaker": {
        "colors": ["red", "white"],
        "features": ["rides_steed", "charge", "greater_bash", "empowering_haste", "nether_strike"],
        "has_hair": True, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "stealth_assassin": {
        "colors": ["black", "purple"],
        "features": ["invisible", "blink", "backstab", "permanence", "shadow_walk"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": True, "has_staff": False, "has_sword": True
    },
    "storm_spirit": {
        "colors": ["blue", "white"],
        "features": ["storm", "fast", "electric", "remnant", "ball_lightning", "overload"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "sven": {
        "colors": ["gold", "white"],
        "features": ["armored", "wings", "storm_hammer", "gods_strength", "cleave"],
        "has_hair": True, "has_horns": True, "has_wings": True,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "techies": {
        "colors": ["red", "brown"],
        "features": ["mechanical", "explosive", "land_mines", "suicide", "remote_mines"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": True,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "templar_assassin": {
        "colors": ["blue", "white"],
        "features": ["elven", "cape", "psi_blades", "refraction", "meld"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "terrorblade": {
        "colors": ["black", "red"],
        "features": ["demonic", "wings", "scary_face", "metamorphosis", "sunder", "conjure_image"],
        "has_hair": False, "has_horns": True, "has_wings": True,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": True
    },
    "tidehunter": {
        "colors": ["blue", "black"],
        "features": ["crab", "one_eyed", "anchor", "kraken_shell", "ravage"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "timbersaw": {
        "colors": ["brown", "gold"],
        "features": ["mechanical", "chainsaw", "timber_chain", "whirling_death", "reactive_armor"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "tinker": {
        "colors": ["brown", "gold"],
        "features": ["mechanical", "robot", "laser", "heat_seeking_missile", "march_of_the_machines"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "tiny": {
        "colors": ["brown", "gray"],
        "features": ["stone", "giant", "toss", "avalanche", "grow"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "treant": {
        "colors": ["green", "brown"],
        "features": ["tree", "nature", "roots", "leech_seed", "overgrowth", "living_armor"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "troll_warlord": {
        "colors": ["brown", "gold"],
        "features": ["troll", "axes", "berserk", "whirling_axes", "rampage"],
        "has_hair": True, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "tusk": {
        "colors": ["blue", "white"],
        "features": ["walrus", "ice", "tusks", "snowball", "ice_shards"],
        "has_hair": False, "has_horns": True, "has_wings": False,
        "has_tail": True, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "underlord": {
        "colors": ["black", "purple"],
        "features": ["demonic", "pit", "fire", "atrophy_aura", "firestorm"],
        "has_hair": False, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "undying": {
        "colors": ["green", "black"],
        "features": ["undead", "zombie", "decay", "soul_rip", "tombstone"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "ursa": {
        "colors": ["brown", "black"],
        "features": ["bear", "fur", "enrage", "earthshock", "overpower"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "vengefulspirit": {
        "colors": ["white", "black"],
        "features": ["ghostly", "wings", "swap", "command_aura", "nether_toxin"],
        "has_hair": True, "has_horns": False, "has_wings": True,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "venomancer": {
        "colors": ["green", "black"],
        "features": ["plague", "venom", "ward", "poison_nova", "gale"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "viper": {
        "colors": ["green", "black"],
        "features": ["snake", "venom", "corrosive_skin", "poison_attack", "viper_strike"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "visage": {
        "colors": ["blue", "white"],
        "features": ["ghostly", "familiars", "soul_assumption", "grave_chill", "gravekeepers_cloak"],
        "has_hair": False, "has_horns": False, "has_wings": True,
        "has_tail": False, "has_beard": False, "has_hat": True,
        "has_mask": True, "has_staff": True, "has_sword": False
    },
    "warlock": {
        "colors": ["purple", "black"],
        "features": ["demonic", "golem", "summoner", "fatal_bonds", "shadow_word"],
        "has_hair": True, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": False,
        "has_mask": False, "has_staff": True, "has_sword": False
    },
    "weaver": {
        "colors": ["black", "blue"],
        "features": ["insect", "invisible", "geminate", "swarm", "time_lapse"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "windrunner": {
        "colors": ["blue", "white"],
        "features": ["wind", "wings", "fast", "shackleshot", "powershot", "focus_fire"],
        "has_hair": True, "has_horns": False, "has_wings": True,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "winter_wyvern": {
        "colors": ["blue", "white"],
        "features": ["dragon", "wings", "ice", "arctic_burn", "cold_embrace", "splinter_blast"],
        "has_hair": True, "has_horns": True, "has_wings": True,
        "has_tail": True, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "wisp": {
        "colors": ["blue", "white"],
        "features": ["ethereal", "orb", "fast", "overcharge", "relocate", "tether"],
        "has_hair": False, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": False,
        "has_mask": False, "has_staff": False, "has_sword": False
    },
    "witch_doctor": {
        "colors": ["green", "black"],
        "features": ["voodoo", "masked", "cask", "paralyzing_cask", "voodoo_restoration"],
        "has_hair": True, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": True,
        "has_mask": True, "has_staff": True, "has_sword": False
    },
    "wraith_king": {
        "colors": ["blue", "white"],
        "features": ["skeletal", "king", "reincarnation", "hellfire_blast", "vampiric_aura"],
        "has_hair": False, "has_horns": True, "has_wings": False,
        "has_tail": False, "has_beard": False, "has_hat": True,
        "has_mask": False, "has_staff": True, "has_sword": True
    },
    "zuus": {
        "colors": ["blue", "white"],
        "features": ["god", "lightning", "hat", "glowing", "poor_eyesight", "arc_lightning", "static_field"],
        "has_hair": True, "has_horns": False, "has_wings": False,
        "has_tail": False, "has_beard": True, "has_hat": True,
        "has_mask": False, "has_staff": True, "has_sword": False
    }
}

# Add visual attributes to heroes
for hero in heroes:
    hero_id = hero['id']
    if hero_id in VISUAL_ATTRIBUTES:
        hero['visual_attributes'] = VISUAL_ATTRIBUTES[hero_id]
    else:
        # Default attributes for unknown heroes
        hero['visual_attributes'] = {
            "colors": ["unknown"],
            "features": [],
            "has_hair": False, "has_horns": False, "has_wings": False,
            "has_tail": False, "has_beard": False, "has_hat": False,
            "has_mask": False, "has_staff": False, "has_sword": False
        }
        print(f"WARNING: No visual attributes defined for {hero_id}")

# Save updated heroes
with open(HEROES_FILE, 'w') as f:
    json.dump(heroes, f, indent=2)

print(f"Added visual attributes to {len(heroes)} heroes")

# Verify
with open(HEROES_FILE, 'r') as f:
    updated_heroes = json.load(f)
    
hero_with_attrs = [h for h in updated_heroes if 'visual_attributes' in h]
print(f"Heroes with visual attributes: {len(hero_with_attrs)}")

# Show sample
sample = updated_heroes[0]
print(f"\nSample hero with attributes:")
print(json.dumps(sample, indent=2))

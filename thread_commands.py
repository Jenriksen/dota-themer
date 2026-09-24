"""Parsing for natural-language theme modification commands in threads.

Pure functions, no Discord or repo dependencies (R5c).
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ModificationCommand:
    """A parsed add/remove request from a modification thread."""

    action: str
    hero_names: List[str] = field(default_factory=list)


EXIT_COMMANDS = frozenset({"done", "cancel", "exit", "quit"})


def is_exit_command(content: str) -> bool:
    """Return True when the message ends the modification session."""
    return content.strip().lower() in EXIT_COMMANDS


def _split_hero_names(hero_part: str) -> List[str]:
    """Split the hero portion, honoring double-quoted names."""
    hero_names: List[str] = []
    current = ""
    in_quotes = False
    for char in hero_part:
        if char == '"':
            in_quotes = not in_quotes
        elif char == " " and not in_quotes:
            if current:
                hero_names.append(current)
                current = ""
        else:
            current += char
    if current:
        hero_names.append(current)
    if not any('"' in name for name in hero_names) and '"' not in hero_part:
        hero_names = hero_part.split()
    return hero_names


def parse_modification(content: str) -> Optional[ModificationCommand]:
    """Parse thread input into an action and hero names, or None if not a command."""
    content = content.strip()
    lowered = content.lower()
    if content.startswith("+"):
        action, hero_part = "add", content[1:].strip()
    elif content.startswith("-"):
        action, hero_part = "remove", content[1:].strip()
    elif lowered.startswith("add"):
        action, hero_part = "add", content[3:].strip()
    elif lowered.startswith("remove"):
        action, hero_part = "remove", content[6:].strip()
    else:
        return None
    return ModificationCommand(action=action, hero_names=_split_hero_names(hero_part))

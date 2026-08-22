# Dota Themer - Domain Model

## Glossary

### Party
A group of players selecting heroes together. Size ranges from **1-5 members**, but is **typically 2-4 players** in practice. Since there are 5 positions but parties are often smaller than 5, not all positions can be accounted for.

### Theme
A categorical constraint used to filter heroes for selection. Themes are **statically defined** in a pre-defined list with explicit hero whitelists (e.g., "rides a steed", "blue heroes", "beards", "visible teeth", "poor eyesight"). Each theme definition includes:
- Name
- Optional description
- **Hero whitelist**: Explicit list of hero **internal names/IDs** that match this theme

All heroes selected by a party must match the same theme.

### Hero
A Dota 2 playable character. Each hero has:
- A **unique internal name/ID** (e.g., "npc_dota_hero_keeper_of_the_light", stable for API use)
- A display name (e.g., "Keeper of the Light")
- A **primary role** (e.g., "Support", "Carry", "Initiator") - may inform position mapping later
- A **primary position** and **secondary position(s)** from 1-5 (for MVP: randomly assigned, manually curated later)
- Visual attributes (color, appearance features) - for theme matching
- Source: Initially placeholder data; to be manually curated from Liquipedia later

### Position
The 5 standard Dota 2 roles, numbered 1-5:
- Position 1: Carry / Safelane Core
- Position 2: Midlane
- Position 3: Offlane
- Position 4: Hard Support / Utility
- Position 5: Soft Support / Babysitter

Each hero is viable in 2-3 of these positions (static mapping).

### Lane
A grouping of positions based on map location. Positions that share a lane can have multiple party members assigned to them:
- **Safelane**: Positions 1 (Carry) and 5 (Hard Support)
- **Mid**: Position 2 (Midlaner)
- **Offlane**: Positions 3 (Offlaner/Semi-core) and 4 (Soft Support)

This lane-based grouping informs how heroes are assigned to parties: **prefer configurations with players in pairs of 2**, using mid to cover odd numbers. Examples:
- Party of 2: safelane(2) OR offlane(2)
- Party of 3: safelane(2) + mid(1) OR offlane(2) + mid(1)
- Party of 4: safelane(2) + offlane(2)
- Party of 5: safelane(2) + mid(1) + offlane(2)

### Theme-to-Hero Matching
The relationship between a theme and the heroes that satisfy it. Since all party members must select heroes matching the same theme, the available hero pool for a given party is the set of heroes tagged with that theme.

### Suggestion
The tool's output: a **single theme** and the **list of matching heroes with their viable positions in parentheses**. Example:
```
Theme: Rides a Steed
Heroes: Keeper of the Light (4,5), Snapfire (1,3), Spirit Breaker (1,4)
```
Each hero's positions reflect their viable roles, with primary position first.

---

## Resolved Decisions

- Themes: Static pre-defined list with explicit hero whitelists using internal hero IDs (Q10=C)
- Hero data: Manual curation initially, placeholder random positions for MVP (Q14)
- Position grouping: Lane-based (safelane: 1+5, mid: 2, offlane: 3+4) (Q8 corrected)
- Position subset: Prefer pairs of 2, use mid for odd numbers (Q12)
- Output format: Theme + heroes with positions in parentheses (Q13)
- Hero identifier: Internal name/ID for stability (Q15 implied)

## Open Questions

- [ ] How are themes selected (random? weighted?)?
- [ ] Should we validate themes have enough heroes for party size?
- [ ] Should we filter themes by position coverage?

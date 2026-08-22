# Dota Themer

A tool to make hero selection challenging and fun by suggesting themes and listing matching heroes with their viable positions.

## Domain Model

See [CONTEXT.md](CONTEXT.md) for the full domain model, glossary, and resolved design decisions.

## Features

- **Theme Suggestions**: Randomly selects a theme from a curated list
- **Hero Filtering**: Lists all heroes that match the selected theme
- **Position Information**: Shows each hero's viable positions in parentheses
- **Party Size Support**: Accepts party size input (1-5 players) for future lane-based features

## Data Structure

### Heroes (`data/heroes.json`)
Each hero has:
- `id`: Internal Dota 2 hero ID (e.g., `npc_dota_hero_keeper_of_the_light`)
- `name`: Display name (e.g., "Keeper of the Light")
- `primary_role`: Primary role (e.g., "Support", "Carry", "Initiator")
- `positions`: Array of viable positions (1-5)
- `positions_display`: Comma-separated string of positions for output

### Themes (`data/themes.json`)
Each theme has:
- `name`: Theme name
- `description`: Optional description
- `hero_ids`: Array of hero IDs that match this theme

## Usage

### Command Line
```bash
# With party size (1-5)
python core.py 3

# Default party size is 2
python core.py
```

### Example Output
```
Theme: Rides a Steed
Description: Heroes that ride mounts or animals into battle
Heroes: Chaos Knight (1,3), Dragon Knight (1,3), Keeper of the Light (4,5), Snapfire (4,5), Spirit Breaker (1,4)
(5 heroes match this theme)
```

## Lane-Position Mapping

Based on your requirements:
- **Safelane**: Positions 1 (Carry) + 5 (Hard Support)
- **Mid**: Position 2 (Midlaner)
- **Offlane**: Positions 3 (Offlaner/Semi-core) + 4 (Soft Support)

Party configurations prefer pairs:
- Party of 2: safelane(2) OR offlane(2)
- Party of 3: safelane(2) + mid(1) OR offlane(2) + mid(1)
- Party of 4: safelane(2) + offlane(2)
- Party of 5: safelane(2) + mid(1) + offlane(2)

## Future Enhancements

- [ ] Filter themes by minimum hero count for party size
- [ ] Validate themes have good position coverage
- [ ] Weighted random theme selection
- [ ] Discord bot integration
- [ ] Position-based hero suggestions for balanced teams
- [ ] Custom theme creation
- [ ] Hero data curation from Liquipedia

## Project Structure

```
dota-themer/
├── CONTEXT.md          # Domain model and design decisions
├── README.md           # This file
├── core.py             # Core logic
└── data/
    ├── heroes.json      # Hero definitions
    └── themes.json      # Theme definitions
```

## Testing

Run the core script with different party sizes to verify:
```bash
python core.py 1
python core.py 2
python core.py 3
python core.py 4
python core.py 5
```

Each run should output a random theme with its matching heroes and their positions.

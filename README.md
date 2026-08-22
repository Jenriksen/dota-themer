# Dota Themer

A tool to make hero selection challenging and fun by suggesting themes and listing matching heroes with their viable positions.

## Domain Model

See [CONTEXT.md](CONTEXT.md) for the full domain model, glossary, and resolved design decisions.

## Features

- **Theme Suggestions**: Randomly selects a theme from a curated list
- **Hero Filtering**: Lists all heroes that match the selected theme
- **Position Information**: Shows each hero's viable positions in parentheses
- **Party Size Support**: Accepts party size input (1-5 players) for future lane-based features
- **Discord Bot**: `!theme [party_size]` command for Discord integration

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

### Discord Bot
```bash
# Install dependencies
uv pip install discord.py

# Set your Discord token
export DISCORD_TOKEN='your-bot-token-here'

# Run the bot
python bot.py
```

**Discord Commands:**
- `!theme` or `!theme 3` - Get a theme suggestion (party size optional, default: 2)
- `!tr 3` - Short alias for `!theme 3`
- `!helptheme` - Show help information

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
- [x] Discord bot integration
- [ ] Position-based hero suggestions for balanced teams
- [ ] Custom theme creation
- [ ] Hero data curation from Liquipedia

## Project Structure

```
dota-themer/
├── CONTEXT.md          # Domain model and design decisions
├── README.md           # This file
├── core.py             # Core logic
├── bot.py              # Discord bot
├── test_core.py        # Core unit tests (57 tests)
├── test_bot.py         # Bot unit tests (15 tests)
├── .gitignore          # Git ignore rules
└── data/
    ├── heroes.json      # Hero definitions (46 heroes)
    └── themes.json      # Theme definitions (8 themes)
```

## Testing

### Running Tests
```bash
# Run all tests
python -m unittest discover

# Run specific test files
python -m unittest test_core
python -m unittest test_bot

# Test core CLI functionality
python core.py 1
python core.py 2
python core.py 3
python core.py 4
python core.py 5
```

Each run should output a random theme with its matching heroes and their positions.

### Test Coverage
- **72 total tests** covering:
  - Core functionality (data loading, theme selection, hero filtering)
  - Edge cases (empty inputs, invalid data, boundaries)
  - Error handling (file errors, invalid inputs)
  - Discord bot structure and commands

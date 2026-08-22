# Dota Themer - Next Steps

## Completed ✅

### Domain Modeling (grill-with-docs)
- [x] Conducted 4 rounds of grilling to resolve domain questions
- [x] Created and maintained CONTEXT.md with full glossary
- [x] Resolved all core domain concepts:
  - Party (1-5 members, typically 2-4)
  - Theme (static list with hero whitelists)
  - Hero (internal ID, name, role, positions)
  - Position (1-5 standard Dota 2 roles)
  - Lane (safelane: 1+5, mid: 2, offlane: 3+4)
  - Output format: Theme + heroes with positions in parentheses

### Core Functionality
- [x] Created `data/heroes.json` with 46 heroes
- [x] Created `data/themes.json` with 8 themes
- [x] Implemented `core.py` with theme selection and hero filtering
- [x] Tested with all party sizes (1-5)
- [x] Output matches required format: `HeroName (pos1,pos2)`

### Testing
- [x] Created `test_core.py` with 57 unit tests
- [x] Created `test_bot.py` with 15 unit tests
- [x] Added 14 more tests for enhanced theme selection (86 total)
- [x] Fixed data inconsistency (clockwerk -> rattletrap)
- [x] Added .gitignore for Python artifacts

### Enhanced Theme Selection
- [x] Implemented filter_themes() for party size filtering
- [x] Implemented weighted random selection
- [x] Implemented position coverage validation

### Position-Based Features
- [x] Implemented lane-based hero grouping
- [x] Implemented balanced team suggestions
- [x] Implemented party composition validation

### Data Improvements
- [x] Expanded hero database to 121 heroes (complete Dota 2 roster)

### Discord Bot Integration
- [x] Created `bot.py` using discord.py
- [x] Implemented `!theme [party_size]` command
- [x] Wrapped `get_theme_suggestion()` from core.py
- [x] Added error handling for invalid inputs
- [x] Added `!tr` alias and `!helptheme` command
- [ ] Configure Discord bot token (user action required)
- [ ] Deploy to Discord server (user action required)

### Documentation
- [x] Created CONTEXT.md (domain model)
- [x] Created README.md (usage, structure, examples)
- [x] Updated README.md with Discord bot info
- [x] Updated TODOs.md with progress

---

## Next Steps (Priority Order)

### 1. Enhanced Theme Selection (High Priority)
- [x] Filter themes to ensure minimum hero count for party size
- [x] Add weighted random selection (favor themes with more heroes)
- [x] Validate themes have good position coverage

### 2. Position-Based Features (Medium Priority)
- [x] Implement lane-based hero grouping in output
- [x] Suggest balanced compositions (e.g., for party of 3: 2 safelane + 1 mid)
- [x] Add position validation for party configurations

### 3. Data Improvements (Medium Priority)
- [x] Expand hero database to 121 heroes (complete Dota 2 roster)
- [x] Manually curated hero positions for all heroes
- [ ] Add more themes (current: 8)
- [ ] Add visual attributes to heroes for better theme matching

### 4. Advanced Features (Backlog)
- [ ] Custom theme creation via Discord commands
- [ ] Theme categories (visual, lore, mechanical)
- [ ] Winrate-based position recommendations
- [ ] Team composition validation
- [ ] Multiple theme suggestions per request
- [ ] Theme rotation / daily themes

---

## Quick Start

To run the bot locally:

```bash
# Install dependencies
uv pip install discord.py

# Set your Discord token
export DISCORD_TOKEN='your-bot-token-here'

# Run the bot
python bot.py

# Or test the core functionality
python core.py 3
```

---

## Files to Review
- `CONTEXT.md` - Domain model (complete)
- `core.py` - Core logic (complete, tested)
- `bot.py` - Discord bot (complete, needs token)
- `test_core.py` - Core unit tests (57 tests)
- `test_bot.py` - Bot unit tests (15 tests)
- `data/heroes.json` - Hero data (MVP complete, 46 heroes)
- `data/themes.json` - Theme data (MVP complete, 8 themes)

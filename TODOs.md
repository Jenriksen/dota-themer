# Dota Themer - Next Steps

## Completed Today ✅

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

### Documentation
- [x] Created CONTEXT.md (domain model)
- [x] Created README.md (usage, structure, examples)

---

## Next Steps (Priority Order)

### 1. Discord Bot Integration (High Priority)
- [ ] Create `bot.py` using discord.py
- [ ] Implement `!theme [party_size]` command
- [ ] Wrap `get_theme_suggestion()` from core.py
- [ ] Add error handling for invalid inputs
- [ ] Configure Discord bot token
- [ ] Deploy to Discord server

### 2. Enhanced Theme Selection (Medium Priority)
- [ ] Filter themes to ensure minimum hero count for party size
- [ ] Add weighted random selection (favor themes with more heroes)
- [ ] Validate themes have good position coverage
- [ ] Option: let users request new theme if unhappy with selection

### 3. Position-Based Features (Medium Priority)
- [ ] Implement lane-based hero grouping in output
- [ ] Suggest balanced compositions (e.g., for party of 3: 2 safelane + 1 mid)
- [ ] Add position validation for party configurations

### 4. Data Improvements (Low Priority)
- [ ] Manually curate hero positions from Liquipedia
- [ ] Expand hero database to all Dota 2 heroes (currently ~46)
- [ ] Add more themes (current: 8)
- [ ] Add visual attributes to heroes for better theme matching

### 5. Advanced Features (Backlog)
- [ ] Custom theme creation via Discord commands
- [ ] Theme categories (visual, lore, mechanical)
- [ ] Winrate-based position recommendations
- [ ] Team composition validation
- [ ] Multiple theme suggestions per request
- [ ] Theme rotation / daily themes

---

## Quick Start for Tomorrow

To continue where we left off:

```bash
# Test current core functionality
python core.py 3

# To start Discord bot development:
uv pip install discord.py
```

Then create `bot.py` with basic structure.

---

## Files to Review
- `CONTEXT.md` - Domain model (complete)
- `core.py` - Core logic (complete, tested)
- `data/heroes.json` - Hero data (MVP complete)
- `data/themes.json` - Theme data (MVP complete)

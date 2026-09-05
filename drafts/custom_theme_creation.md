# Custom Theme Creation Feature - Draft

## Overview

This document describes the draft implementation for custom theme creation via Discord commands. The feature allows users to create, modify, and remove themes through Discord bot commands, with all changes persisted to `data/themes.json`.

## Feature Status

**Status:** ✅ IMPLEMENTED AND TESTED

The core functionality for custom theme creation is implemented and tested. The hide/unhide feature has been fully implemented.

## Design Decision: Hide vs Delete

**Users should NOT be able to delete themes, only hide them.**

This design decision has been implemented. Users can now hide themes from suggestions and unhide them later, but cannot permanently delete them.

**Implementation:**
- Added `is_hidden` boolean field to each theme in `themes.json` (backward compatible)
- Changed `!removetheme` to `!hidetheme` command
- Added `!unhidetheme` command
- Added `hide_theme()` and `unhide_theme()` functions in core.py
- Modified `load_themes()` to support `include_hidden` parameter
- Updated `filter_themes()` to filter out hidden themes by default
- Updated `get_theme_suggestion()` and `select_theme()` to exclude hidden themes
- Added `get_all_themes_with_status()` for listing with hidden status
- Updated `!listthemes` to show hidden status (hidden themes marked with "(hidden)")
- Updated help text with new commands

This ensures:
- User-created themes can be hidden but not lost
- Hidden themes can be restored
- No accidental permanent data loss
- Better user experience

## Implemented Components

### 1. Core Functions (`core.py`)

All persistence functions are implemented and tested:

- **`add_theme(theme_name, description, hero_ids)`** (lines 509-590)
  - Creates a new theme with validation
  - Saves to `data/themes.json`
  - Validates: non-empty name, unique name, valid hero IDs
  - Returns: (success: bool, message: str)

- **`update_theme(theme_name, add_hero_ids, remove_hero_ids, new_description)`** (lines 593-681)
  - Adds/removes heroes from existing theme
  - Updates theme description
  - Saves to `data/themes.json`
  - Returns: (success: bool, message: str)

- **`remove_theme(theme_name)`** (lines 684-739)
  - Removes a theme by name
  - Saves to `data/themes.json`
  - Returns: (success: bool, message: str)

- **`get_all_theme_names()`** (lines 742-754)
  - Returns sorted list of all theme names

- **`get_all_hero_names()`** (lines 757-769)
  - Returns mapping of hero name (lowercase) to hero ID

### 2. Discord Bot Commands (`bot.py`)

All commands are implemented:

- **`!addtheme <name> [description] <hero1> [hero2] ...`** (lines 122-192)
  - Creates a new theme
  - Accepts optional description
  - Accepts variable number of hero names/IDs
  - Validates heroes exist
  - Example: `!addtheme "My Custom Theme" "A test theme" antimage juggernaut`

- **`!removetheme <name>`** (lines 195-215)
  - Removes a theme by name
  - Example: `!removetheme "My Custom Theme"`

- **`!updatetheme <name> add <hero1> [hero2] ...`** (lines 218-282)
  - Adds heroes to existing theme
  - Example: `!updatetheme "Red Heroes" add crystal_maiden`

- **`!updatetheme <name> remove <hero1> [hero2] ...`** (lines 218-282)
  - Removes heroes from existing theme
  - Example: `!updatetheme "Red Heroes" remove bloodseeker`

- **`!listthemes`** (lines 285-311)
  - Lists all available themes (paginated)

- **`!listheroes`** (lines 314-342)
  - Lists all available heroes (paginated)

- **`!helptheme`** (lines 70-98)
  - Shows help text with all commands and examples

### 3. Existing Tests (`test_core.py`)

Core functions have unit tests (lines 906+):
- `test_add_theme_valid`
- `test_add_theme_duplicate`
- `test_add_theme_empty_name`
- `test_add_theme_invalid_hero`
- `test_update_theme_add_heroes`
- `test_update_theme_remove_heroes`
- `test_update_theme_nonexistent`
- `test_remove_theme_valid`
- `test_remove_theme_nonexistent`

## Data Structure

### themes.json Format

```json
[
  {
    "name": "Theme Name",
    "description": "Theme description",
    "hero_ids": ["antimage", "juggernaut", "..."]
  }
]
```

### Hero IDs

Hero IDs are short names like:
- `antimage`
- `juggernaut`
- `crystal_maiden`

These match the `id` field in `data/heroes.json`.

## Usage Examples

### Creating a Theme

```
User: !addtheme "My Favorite Heroes" "Heroes I like to play" antimage juggernaut crystal_maiden
Bot: ✅ Theme 'My Favorite Heroes' added successfully with 3 heroes
```

### Adding Heroes to Existing Theme

```
User: !updatetheme "My Favorite Heroes" add phantom_assassin
Bot: ✅ Theme 'My Favorite Heroes' updated successfully. Now has 4 heroes
```

### Removing Heroes from Theme

```
User: !updatetheme "My Favorite Heroes" remove juggernaut
Bot: ✅ Theme 'My Favorite Heroes' updated successfully. Now has 3 heroes
```

### Hiding a Theme

```
User: !hidetheme "My Favorite Heroes"
Bot: ✅ Theme 'My Favorite Heroes' hidden successfully. It will no longer appear in suggestions.
```

### Unhiding a Theme

```
User: !unhidetheme "My Favorite Heroes"
Bot: ✅ Theme 'My Favorite Heroes' unhidden successfully. It will now appear in suggestions.
```

### Listing Themes

```
User: !listthemes
Bot: **Available Themes:**
1. Agility Heroes
2. Animal Companions
3. Beards (hidden)
4. Black Heroes
...
```

Note: Hidden themes are marked with "(hidden)" in the list.

## Implementation Notes

### Hero Name Resolution

The system supports both:
1. Hero names (e.g., `antimage`, `crystal_maiden`)
2. Hero IDs (same as names in current implementation)

The bot uses `core.get_all_hero_names()` which returns a mapping of lowercase hero name to ID.

### Validation

All operations validate:
- Theme names are not empty
- Theme names are unique (case-insensitive)
- Hero IDs exist in the hero database
- Hero IDs are valid

### Persistence

All changes are immediately saved to `data/themes.json`:
- Uses `json.dump()` with indent=2 for readability
- Themes are sorted alphabetically by name before saving
- File is overwritten atomically

## Missing/To-Do

1. **Bot Command Tests**: No tests for the bot commands themselves (only core functions are tested)
2. **Input Validation**: Could improve hero name matching (fuzzy matching?)
3. **Error Messages**: Could be more user-friendly
4. **Categories**: Theme categories not yet implemented (mentioned in ROADMAP)
5. **Permissions**: No permission system (any user can modify themes)
6. **Audit Log**: No logging of who created/modified themes

**Completed:**
- ✅ Hide/UnHide Implementation: Users can hide/unhide themes but cannot delete them

## Testing the Feature

### Manual Testing

1. Start the bot: `python bot.py` (with DISCORD_TOKEN set)
2. In Discord, use the commands above
3. Verify `data/themes.json` is updated

### Running Tests

```bash
# Test core functions
python -m pytest test_core.py::TestThemeManagement -v

# Or run all tests
python -m pytest test_core.py -v
```

## Files Modified

- `core.py` - Added theme management functions
- `bot.py` - Added Discord commands for theme management
- `test_core.py` - Added tests for theme management
- `data/themes.json` - Stores all themes (including user-created ones)

## Next Steps

1. Add tests for bot commands in `test_bot.py`
2. Implement theme categories
3. Add permission system
4. Add confirmation for destructive operations
5. Improve error messages
6. Add audit logging

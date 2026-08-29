# Dota Themer

A tool to make hero selection challenging and fun by suggesting themes and listing matching heroes with their viable positions.

## Domain Model

See [CONTEXT.md](CONTEXT.md) for the full domain model, glossary, and resolved design decisions.
See [ROADMAP.md](ROADMAP.md) for project roadmap, milestones, and future plans.
See [TODOs.md](TODOs.md) for detailed task tracking.

## Features

- **Theme Suggestions**: Randomly selects a theme from a curated list of 71 themes
- **Hero Filtering**: Lists all heroes that match the selected theme
- **Position Information**: Shows each hero's viable positions in parentheses
- **Party Size Support**: Accepts party size input (1-5 players) for lane-based features
- **Enhanced Theme Selection**: Filtered by party size, weighted by hero count, validated for position coverage
- **Position-Based Features**: Lane-based hero grouping, balanced team suggestions
- **Visual Attributes**: Heroes include color schemes, features, and visual characteristics for better theme matching
- **Structured Logging**: JSON and text format logging with configurable levels
- **Discord Bot**: `!theme [party_size]` command for Discord integration

## Data Structure

### Heroes (`data/heroes.json`)
Each hero has:
- `id`: Internal Dota 2 hero ID (e.g., `abaddon`, `juggernaut`)
- `name`: Display name (e.g., "Abaddon", "Juggernaut")
- `primary_role`: Primary role (e.g., "Support", "Carry", "Initiator")
- `positions`: Array of viable positions (1-5)
- `visual_attributes`: Object containing:
  - `colors`: Primary color scheme as array (e.g., `["red", "black"]`)
  - `features`: Distinguishing visual features as array (e.g., `["undead", "glowing_eyes"]`)
  - Boolean flags: `has_hair`, `has_horns`, `has_wings`, `has_tail`, `has_beard`, `has_hat`, `has_mask`, `has_staff`, `has_sword`

### Themes (`data/themes.json`)
Each theme has:
- `name`: Theme name (e.g., "Red Heroes", "Wings", "Bald and Beautiful")
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

## Discord Bot

### Prerequisites
- Python 3.8+
- Discord bot token (get from [Discord Developer Portal](https://discord.com/developers/applications))

### Installation

```bash
# Clone the repository
git clone https://github.com/jenriksen/dota-themer.git
cd dota-themer

# Install dependencies
pip install discord.py
```

### Configuration

```bash
# Windows (Command Prompt)
set DISCORD_TOKEN=your-bot-token-here

# Windows (PowerShell)
$env:DISCORD_TOKEN="your-bot-token-here"

# Linux/macOS
export DISCORD_TOKEN='your-bot-token-here'
```

Or create a `.env` file:
```
DISCORD_TOKEN=your-bot-token-here
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Running the Bot

```bash
# Start the bot
python bot.py
```

**Discord Commands:**
- `!theme` or `!theme 3` - Get a theme suggestion (party size optional, default: 2)
- `!tr 3` - Short alias for `!theme 3`
- `!helptheme` - Show help information

### Optional Logging Configuration

```bash
# JSON format (for production/log aggregation)
set LOG_LEVEL=INFO
set LOG_FORMAT=json
set LOG_FILE=logs/dota-themer.log

# Text format (for development)
set LOG_LEVEL=DEBUG
set LOG_FORMAT=text
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

## Features Status

- [x] Filter themes by minimum hero count for party size
- [x] Validate themes have good position coverage
- [x] Weighted random theme selection
- [x] Discord bot integration
- [x] Position-based hero suggestions for balanced teams
- [x] Hero data with visual attributes for all 121 heroes
- [x] Structured logging (JSON and text formats)
- [x] Enhanced theme library (71 themes)
- [ ] Hero data curation from Liquipedia (automation pending)

## Project Structure

```
dota-themer/
├── CONTEXT.md              # Domain model and design decisions
├── README.md               # This file
├── ROADMAP.md              # Project roadmap and milestones
├── TODOs.md                # Task tracking
├── core.py                 # Core logic
├── bot.py                  # Discord bot
├── logging_config.py       # Structured logging configuration
├── test_core.py            # Core unit tests (86 tests)
├── test_bot.py             # Bot unit tests (15 tests)
├── test_logging.py          # Logging unit tests (30 tests)
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment variables
└── data/
    ├── heroes.json          # Hero definitions (121 heroes)
    └── themes.json          # Theme definitions (71 themes)
└── scripts/
    ├── add_themes.py        # Add new themes to themes.json
    ├── add_visual_attributes.py  # Add visual attributes to heroes
    └── pre-commit-hook.sh   # Git pre-commit hook for Black formatting
```

## Development Setup

### Prerequisites
- Python 3.8+
- Git

### Windows Setup

```cmd
:: Clone the repository
git clone https://github.com/jenriksen/dota-themer.git
cd dota-themer

:: Create virtual environment
python -m venv venv
call venv\Scripts\activate

:: Install dependencies
pip install -r requirements.txt

:: Run tests
python -m unittest discover

:: Run the application
python core.py 3
```

### Linux/macOS Setup

```bash
# Clone the repository
git clone https://github.com/jenriksen/dota-themer.git
cd dota-themer

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m unittest discover

# Run the application
python core.py 3
```

## Code Quality

### Pre-commit Hook

A pre-commit hook is available to ensure all Python code complies with the Black formatter before allowing commits.

**Installation:**

To enable the pre-commit hook, run:

```bash
# Create the symlink
ln -s ../../scripts/pre-commit-hook.sh .git/hooks/pre-commit

# Make sure it's executable
chmod +x .git/hooks/pre-commit
```

Or on Windows (Command Prompt):
```cmd
mklink .git\hooks\pre-commit scripts\pre-commit-hook.sh
```

The hook will automatically check all staged Python files with Black and block the commit if any files need reformatting, with clear instructions on how to fix them.

**Requirements:**
- Black must be installed (`pip install black`)
- The hook requires Black 23.0.0+

**To fix formatting issues:**
```bash
# Run Black on the files that need fixing
black file1.py file2.py

# Or format all Python files
black .

# Then stage and commit again
git add .
git commit -m "Your message"
```

## Testing

### Running Tests

```bash
# Run all tests (120 tests)
python -m unittest discover

# Run specific test files
python -m unittest test_core
python -m unittest test_bot
python -m unittest test_logging

# Run with verbose output
python -m unittest discover -v

# Test core CLI functionality
python core.py 1
python core.py 2
python core.py 3
python core.py 4
python core.py 5
```

Each run outputs a random theme with matching heroes and their positions.

### Test Coverage
- **120 total tests** covering:
  - Core functionality (data loading, theme selection, hero filtering)
  - Enhanced theme selection (filtering, weighting, position coverage)
  - Position-based features (lane grouping, balanced team suggestions)
  - Edge cases (empty inputs, invalid data, boundaries)
  - Error handling (file errors, invalid inputs)
  - Discord bot structure and commands
  - Structured logging configuration
  - Data integrity and consistency

## Deployment for Testing

### Local Testing

The easiest way to test the application locally:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the core application:**
   ```bash
   python core.py 2
   ```

3. **Run the Discord bot for local testing:**
   ```bash
   # Create a test Discord server and bot at https://discord.com/developers/applications
   # Set the token
   export DISCORD_TOKEN=your_test_token
   
   # Run the bot
   python bot.py
   ```

### Using the Provided Scripts

**Add new themes:**
```bash
python scripts/add_themes.py
```

**Add/Update visual attributes for heroes:**
```bash
python scripts/add_visual_attributes.py
```

### Docker Deployment (Optional)

For containerized deployment and testing:

1. **Create a `Dockerfile`:**
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["python", "bot.py"]
   ```

2. **Build and run:**
   ```bash
   docker build -t dota-themer .
   docker run -e DISCORD_TOKEN=your_token dota-themer
   ```

3. **For local testing with a test token:**
   ```bash
   # Create a test.env file with your test token
   echo DISCORD_TOKEN=your_test_token > test.env
   
   # Run with the test environment
   docker run --env-file test.env dota-themer
   ```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DISCORD_TOKEN` | Discord bot token | None | Yes (for bot) |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `LOG_FORMAT` | Log format (`json` or `text`) | `text` | No |
| `LOG_FILE` | Log file path | None | No |
| `ENV` | Environment name | `development` | No |

## Configuration File

Create a `.env` file in the project root for local development:

```bash
# .env
DISCORD_TOKEN=your_bot_token_here
LOG_LEVEL=DEBUG
LOG_FORMAT=text
# LOG_FILE=logs/dota-themer.log
```

## Troubleshooting

### Windows-Specific Issues

**File lock errors in tests:**
If you see `PermissionError: [WinError 32]` during test cleanup, this is a known Windows issue where file handlers remain locked. The test suite now properly closes handlers before cleanup, but if you encounter this in your own code, ensure you call `handler.close()` on all FileHandlers before deleting files.

**Python not found:**
- Ensure Python is in your PATH
- On Windows, use the full path: `py -3 core.py` or `python core.py`
- Or use the Python Launcher for Windows

**Discord.py import errors:**
```bash
pip install discord.py
```

### Common Issues

**Module not found errors:**
```bash
# Make sure you're in the right directory
cd /path/to/dota-themer

# And the module is in your Python path
python -m unittest test_core
```

**JSON decode errors:**
Ensure your data files (`data/heroes.json`, `data/themes.json`) are valid JSON. You can validate them at [jsonlint.com](https://jsonlint.com).

**All tests pass but bot doesn't connect:**
- Verify your Discord token is correct
- Ensure the bot has been added to your server
- Check that the bot has the correct permissions

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests: `python -m unittest discover`
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License

---

**Current Version:** 1.0.0  
**Heroes:** 121 (complete Dota 2 roster)  
**Themes:** 71  
**Tests:** 120  
**Last Updated:** August 2026

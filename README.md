# Dota Themer

A tool to make hero selection challenging and fun by suggesting themes and listing matching heroes with their viable positions.

## Domain Model

See [CONTEXT.md](CONTEXT.md) for the full domain model, glossary, and resolved design decisions.
See [ROADMAP.md](ROADMAP.md) for project roadmap, milestones, and future plans.
See [TODOs.md](TODOs.md) for detailed task tracking.

## Features

- **Theme Suggestions**: Randomly selects a theme from a curated list of 52 themes
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
- `name`: Theme name (e.g., "Red Heroes", "Wings", "Bald Heroes")
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

# Install uv (https://docs.astral.sh/uv/)
pip install uv

# Create a virtual environment and install dependencies
# (requirements.txt is the canonical dependency list)
uv venv
uv pip install -r requirements.txt
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
- `!theme [party_size]` - Get a theme suggestion (party size 1-5, default: 2)
- `!tr [party_size]` - Short alias for `!theme` (also defaults to party size 2)
- `!helptheme` - Show help information
- `!addtheme <name> [description] <hero1> [hero2] ...` - Create a new theme
- `!updatetheme <name> add|remove <hero1> [hero2] ...` - Add or remove heroes from a theme
- `!hidetheme <name>` - Hide a theme from suggestions
- `!unhidetheme <name>` - Make a hidden theme visible again
- `!listthemes` - List all themes including hidden status
- `!listheroes` - List all available heroes
- React with 👍/👎 on a theme suggestion to vote; react with ❓ to open an interactive modification thread

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
- [x] Hero data with visual attributes for all 120 heroes
- [x] Structured logging (JSON and text formats)
- [x] Enhanced theme library (52 themes)
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
├── test_core.py            # Core unit tests (104 tests)
├── test_bot.py             # Bot unit tests (15 tests)
├── test_logging.py          # Logging unit tests (21 tests)
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment variables
└── data/
    ├── heroes.json          # Hero definitions (120 heroes, seed data)
    └── themes.json          # Theme definitions (52 themes, seed data)
└── scripts/
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

:: Install uv (skip if already installed)
pip install uv

:: Create virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt

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

# Install uv (skip if already installed)
pip install uv

# Create virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt

# Run tests
python -m unittest discover

# Run the application
python core.py 3
```

## Code Quality

### Pre-commit Hook

A pre-commit hook is available to ensure code quality before allowing commits. It performs the following checks:

1. **Code Formatting**: Verifies all staged Python files comply with Black and isort formatting
2. **Version Check**: Ensures `__version__.py` has been incremented compared to the main branch

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

Or on Windows (PowerShell):
```powershell
# Create the hooks directory if it doesn't exist
if (-not (Test-Path .git\hooks)) { New-Item -ItemType Directory -Path .git\hooks | Out-Null }
# Copy the pre-commit hook
Copy-Item scripts\pre-commit-hook.sh .git\hooks\pre-commit
```

The hook will automatically check all staged Python files with Black and isort, and verify version increment, blocking the commit if any checks fail with clear instructions on how to fix them.

**Requirements:**
- Black must be installed (`pip install black`)
- isort must be installed (`pip install isort`)
- Python must be installed and available in PATH
- The hook requires Black 23.0.0+

**Checks Performed:**

**1. Formatting Check (Black & isort):**
- Verifies all staged `.py` files comply with Black code formatting
- Verifies all imports are correctly sorted with isort

**2. Version Check:**
- Compares the version in `__version__.py` against the main branch
- Blocks commit if the version is lower than the main branch version
- Allows any version if main doesn't have `__version__.py` (first version)
- Uses semantic versioning comparison (MAJOR.MINOR.PATCH)

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

**To fix version issues:**
```bash
# Update the version in __version__.py to be higher than main branch
# For example, if main is 1.0.0, change to 1.0.1 or 1.1.0 or 2.0.0
# Then stage and commit again
git add __version__.py
git commit -m "Bump version to X.Y.Z"
```

**Bypassing the Hook:**

In rare cases, you can bypass the pre-commit hook with:
```bash
git commit --no-verify -m "Your message"
```

However, this is not recommended as it may introduce formatting issues or version regressions.

## Testing

### Running Tests

```bash
# Run all tests (140 tests)
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
- **140 total tests** covering:
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
   uv venv
   uv pip install -r requirements.txt
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

### Docker Deployment (Optional)

The repository includes a production-ready **multi-stage Dockerfile** and **docker-compose.yml** for containerized deployment.

**Using docker-compose (recommended for local development):**

1. Create a `.env` file with your Discord token:
   ```bash
   echo DISCORD_TOKEN=your_bot_token_here > .env
   ```

2. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

3. View logs:
   ```bash
   docker-compose logs -f dota-themer
   ```

**Manual Docker build:**
```bash
docker build -t dota-themer .
docker run -e DISCORD_TOKEN=your_token -e LOG_LEVEL=INFO dota-themer
```

### Railway Deployment (Recommended for 24/7 Hosting)

[Railway](https://railway.app/) provides free hosting perfect for Discord bots:

**Prerequisites:**
- Railway account
- GitHub account connected to Railway
- Discord bot token
- Bot added to your server

**Steps:**

1. **Create new project:**
   - Go to [Railway.app](https://railway.app/)
   - Click **"New Project"** → **"Deploy from GitHub repo"**
   - Select `Jenriksen/dota-themer` repository
   - Select `main` branch

2. **Configure environment variables:**
   - Go to **Variables** tab
   - Add `DISCORD_TOKEN=your_bot_token_here`
   - Optionally add `LOG_LEVEL=INFO`, `LOG_FORMAT=json`

3. **Enable auto-deploy:**
   - Railway will automatically redeploy on every push to main
   - ✅ Enable auto-deploy for seamless updates

4. **Deploy:**
   - Click **"Deploy"**
   - Wait ~2-5 minutes for build to complete

5. **Verify:**
   - Check **Logs** tab for startup messages
   - In Discord, verify bot shows as "Online"
   - Test with `!theme` command

**Free Tier:** ✅ Yes - Railway's free tier is sufficient for a single Discord bot

**Note:** Since Railway auto-deploys from main, always use feature branches and merge via PRs.

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DISCORD_TOKEN` | Discord bot token | None | Yes (for bot) |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `LOG_FORMAT` | Log format (`json` or `text`) | `text` | No |
| `LOG_FILE` | Log file path | None | No |
| `ENV` | Environment name | `development` | No |
| `DOTA_THEMER_DATA_DIR` | Directory for `dota.db` and the JSON seed files | `./data` | No |
| `DOTA_THEMER_S3_BUCKET` | S3 bucket for database snapshots (enables snapshot push/pull) | None | No |
| `DOTA_THEMER_S3_PREFIX` | S3 key prefix for database snapshots | None | No |

### Discord Bot Permissions

Your bot requires these **permissions** in the Discord Developer Portal:

**Text Permissions:**
- ✅ **Send Messages** - Post theme suggestions
- ✅ **Embed Links** - Format messages with rich content
- ✅ **Add Reactions** - Add/remove 👍, 👎, ❓, ✅, 🔒 reactions
- ✅ **Read Message History** - Read thread messages
- ✅ **Create Public Threads** - Create modification threads
- ✅ **Send Messages in Threads** - Reply in threads
- ✅ **Manage Threads** - Archive inactive threads

**OAuth2 Scopes:**
- ✅ **bot** - Required for all bots

**Permission Bitmask:** `274877955104` (includes all above)

**How to set up:**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application → **Bot** → **Permissions**
3. Enable all permissions listed above
4. Generate invite URL and add bot to your server

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
The JSON seed files (`data/heroes.json`, `data/themes.json`) are imported into `data/dota.db` on first use; a decode error at startup means one of them is malformed. You can validate them at [jsonlint.com](https://jsonlint.com).

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

**Current Version:** 1.0.1  
**Heroes:** 120 (complete Dota 2 roster)  
**Themes:** 52  
**Tests:** 140

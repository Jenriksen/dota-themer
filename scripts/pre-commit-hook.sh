#!/bin/sh
# Dota Themer - Pre-commit hook for Black formatter
# 
# This script can be used as a Git pre-commit hook to ensure all Python files
# comply with Black formatting before allowing a commit.
#
# INSTALLATION:
# 1. Make this script executable:
#    chmod +x scripts/pre-commit-hook.sh
#
# 2. Create a symlink in your .git/hooks directory:
#    ln -s ../../scripts/pre-commit-hook.sh .git/hooks/pre-commit
#
# OR copy it directly:
#    cp scripts/pre-commit-hook.sh .git/hooks/pre-commit
#    chmod +x .git/hooks/pre-commit
#
# This ensures code is not pushed until it complies with Black formatter.

# Check if this is an initial commit (no parent)
if [ -z "$(git rev-parse --verify HEAD 2>/dev/null)" ]; then
    # Initial commit, skip Black check
    exit 0
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${YELLOW}Running pre-commit hook: Black formatter check...${NC}"
echo ""

# Check if Black is installed
if ! command -v black >/dev/null 2>&1; then
    echo -e "${RED}ERROR: Black is not installed.${NC}"
    echo ""
    echo "Please install Black with:"
    echo "  pip install black"
    echo ""
    echo "Or run it in a virtual environment:"
    echo "  python -m pip install black"
    echo ""
    exit 1
fi

# Get the project root (where this script is located)
# Navigate up from .git/hooks/pre-commit to project root
PROJECT_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$PROJECT_ROOT"

# Get list of staged Python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.py$')

if [ -z "$STAGED_FILES" ]; then
    # No Python files staged, allow commit
    echo -e "${GREEN}No Python files staged for commit.${NC}"
    echo ""
    exit 0
fi

echo "Checking Black formatting for staged Python files:"
echo ""

# Run Black in check mode on all staged Python files
BLACK_OUTPUT=$(black --check $STAGED_FILES 2>&1)
BLACK_EXIT_CODE=$?

if [ $BLACK_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}All Python files are properly formatted with Black.${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}Black formatting check failed.${NC}"
    echo ""
    echo "The following files need to be reformatted with Black:"
    echo ""
    echo "$BLACK_OUTPUT"
    echo ""
    echo "To fix, run:"
    echo "  black $STAGED_FILES"
    echo ""
    echo "Then stage the changes and try committing again."
    echo ""
    exit 1
fi

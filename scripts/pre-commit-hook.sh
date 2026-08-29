#!/bin/sh
# Dota Themer - Pre-commit hook for code formatting
# 
# This script can be used as a Git pre-commit hook to ensure all Python files
# comply with Black and isort formatting before allowing a commit.
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
# This ensures code is not committed until it complies with Black and isort.

# Check if this is an initial commit (no parent)
if [ -z "$(git rev-parse --verify HEAD 2>/dev/null)" ]; then
    # Initial commit, skip formatting checks
    exit 0
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${YELLOW}Running pre-commit hook: Code formatting checks...${NC}"
echo ""

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

# Function to run a formatting check
run_check() {
    local checker_name=$1
    local checker_cmd=$2
    local install_instructions=$3
    
    # Check if the tool is installed
    if ! command -v "$checker_name" >/dev/null 2>&1; then
        echo -e "${RED}ERROR: $checker_name is not installed.${NC}"
        echo ""
        echo "$install_instructions"
        echo ""
        return 1
    fi
    
    # Run the check
    echo "Checking $checker_name formatting for staged Python files:"
    OUTPUT=$($checker_cmd $STAGED_FILES 2>&1)
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}All Python files pass $checker_name check.${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}$checker_name formatting check failed.${NC}"
        echo ""
        echo "$OUTPUT"
        echo ""
        return 1
    fi
}

# Run isort check first
if ! run_check "isort" "isort --check --verbose" "Please install isort with:\n  pip install isort"; then
    echo "To fix, run:"
    echo "  isort $STAGED_FILES"
    echo ""
    echo "Then stage the changes and try committing again."
    echo ""
    exit 1
fi

# Run Black check
if ! run_check "Black" "black --check --verbose" "Please install Black with:\n  pip install black"; then
    echo "To fix, run:"
    echo "  black $STAGED_FILES"
    echo ""
    echo "Then stage the changes and try committing again."
    echo ""
    exit 1
fi

echo -e "${GREEN}All formatting checks passed!${NC}"
echo ""
exit 0

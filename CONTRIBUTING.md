# Contributing to Dota Themer

Thank you for your interest in contributing to Dota Themer! This document outlines our development practices and guidelines.

## Development Philosophy

**All code changes MUST follow Test-Driven Development (TDD) with the red-green-refactor pattern.**

This is a non-negotiable requirement for this project. Pull requests that do not follow TDD will be rejected.

---

## TDD Rules (Required)

### The Red-Green-Refactor Loop

Every feature, bug fix, or enhancement **must** follow this exact sequence:

1. **RED**: Write a failing test first
   - The test must fail for the right reason (assertion failure)
   - No syntax errors - the test must be valid code
   - Test only ONE thing at a time
   - The test name should read like a specification

2. **GREEN**: Write only enough code to make the test pass
   - No more, no less
   - Don't anticipate future requirements
   - Don't add speculative features
   - Keep it simple and minimal

3. **REFACTOR**: Improve the design
   - After the test passes, refactor both code and tests
   - Tests must continue to pass
   - This is when you apply DRY, improve naming, etc.
   - Refactoring happens AFTER the test passes, not during

**Repeat this loop for each vertical slice of functionality.**

### Vertical Slices vs Horizontal Slices

✅ **DO**: Vertical slices (one test → one implementation → repeat)
- Each slice delivers end-to-end value
- Tests respond to what the last cycle taught you
- You discover the interface as you go

❌ **DON'T**: Horizontal slices (all tests first, then all implementation)
- Tests verify imagined behavior, not real behavior
- Tests become insensitive to real changes
- You commit to test structure before understanding implementation

---

## What Makes a Good Test

### Test at Seams

A **seam** is a public boundary where you can observe behavior without reaching inside.

**✅ Test at these seams:**
- Public module interfaces (e.g., `core.get_theme_suggestion()`)
- Discord bot commands (e.g., `!theme`, `!addtheme`)
- CLI entry points (e.g., `core.py` main function)
- Public API endpoints

**❌ Never test at:**
- Private methods or internal functions
- Implementation details (e.g., how a function internally processes data)
- Database queries directly (test through the public interface instead)

### Test Naming

Test names should read like specifications using the project's domain language:

```python
# ✅ Good - reads like a spec
def test_add_theme_adds_new_theme_to_file():
    def test_user_can_create_theme_via_discord():
    def test_get_theme_suggestion_returns_valid_theme():

# ❌ Bad - implementation-focused
def test_add_theme_function():
    def test_themes_list_length():
    def test_internal_processing():
```

Use the vocabulary from [CONTEXT.md](CONTEXT.md) in your test names.

### Test Structure

Each test should follow the Arrange-Act-Assert pattern:

```python
# Arrange - set up the test
heroes = [{"id": "antimage", "name": "Anti-Mage"}]

# Act - perform the action
theme = {"name": "Test Theme", "hero_ids": ["antimage"]}
success, message = core.add_theme(
    theme["name"], theme.get("description", ""), theme["hero_ids"]
)

# Assert - verify the outcome
assert success is True
assert "added successfully" in message
```

---

## Anti-Patterns (Forbidden)

### 1. Implementation-Coupled Tests

Tests that break when you refactor but behavior hasn't changed.

```python
# ❌ BAD: Testing internal structure
def test_add_theme_calls_load_themes():
    with patch('core.load_themes') as mock_load:
        core.add_theme("Test", "", [])
        mock_load.assert_called()  # Tests HOW, not WHAT

# ✅ GOOD: Testing behavior
def test_add_theme_adds_new_theme():
    themes_before = core.get_all_theme_names()
    core.add_theme("New Theme", "", ["antimage"])
    themes_after = core.get_all_theme_names()
    assert "New Theme" in themes_after
```

### 2. Tautological Tests

Tests that pass by construction and can never fail:

```python
# ❌ BAD: Always passes, tests nothing
def test_add_returns_correct_value():
    result = add(1, 2)
    assert result == 1 + 2  # Recomputes the same way

# ✅ GOOD: Tests against independent truth
def test_add_returns_expected_value():
    assert add(1, 2) == 3
```

### 3. Testing Private/Internal Methods

Never test methods that start with `_` (private by convention):

```python
# ❌ BAD: Testing private method
def test__validate_theme_name():
    assert core._validate_theme_name("Test") is True

# ✅ GOOD: Test through public interface
def test_add_theme_rejects_empty_name():
    success, message = core.add_theme("", "")
    assert success is False
```

---

## Before You Start

### 1. Confirm the Seam

Before writing ANY test, we must agree on:
- What is the public interface being tested?
- Where is the seam (boundary) for this test?
- What behavior are we verifying?

**Example discussion:**
```
User: "I want to add a feature to list all themes via Discord."
You: "The seam should be the Discord command `!listthemes`. We'll test:
     1. The command exists and is registered
     2. It returns the list of theme names
     3. It handles errors gracefully"
```

### 2. One Slice at a Time

Don't try to implement everything at once. Break features into the smallest possible vertical slices:

```
# For "user can add themes via Discord":

# Slice 1: Command registration
TEST: !addtheme command exists
CODE: Register the command in bot.py

# Slice 2: Parse theme name
TEST: !addtheme "My Theme" extracts "My Theme" as name
CODE: Parse first argument as theme name

# Slice 3: Parse description (optional)
TEST: !addtheme "My Theme" "desc" extracts "desc" as description
CODE: Parse second argument as description if present

# Slice 4: Parse hero list
TEST: !addtheme "My Theme" hero1 hero2 extracts heroes
CODE: Parse remaining arguments as hero names

# Slice 5: Full integration
TEST: !addtheme creates theme with all provided info
CODE: Wire up all the parsed data to add_theme function
```

---

## Development Workflow

### For New Features

1. Open an issue describing the feature
2. Break the feature into vertical slices (with the maintainer)
3. For each slice:
   - Write the failing test (RED)
   - Run tests: `python -m unittest` (should fail)
   - Implement minimal code (GREEN)
   - Run tests: `python -m unittest` (should pass)
   - Refactor if needed (REFACTOR)
   - Run tests: `python -m unittest` (must still pass)
4. All tests must pass before merging

### For Bug Fixes

1. Write a test that reproduces the bug (RED - it should fail)
2. Implement the fix (GREEN - test now passes)
3. Refactor if needed (REFACTOR - test still passes)

### For Refactoring

1. All existing tests must pass before refactoring
2. Write new tests for any new behavior (follow RED-GREEN-REFACTOR)
3. Refactor in small, testable steps
4. Run tests after every change

---

## Code Review Checklist

When reviewing code, verify:

- [ ] Every feature/bug fix follows RED-GREEN-REFACTOR
- [ ] Tests are at public seams, not implementation details
- [ ] Test names read like specifications
- [ ] No tautological tests
- [ ] No tests of private methods
- [ ] All tests pass: `python -m unittest discover`
- [ ] All formatting passes: `black --check .` and `isort --check .`
- [ ] Code follows the pre-commit hook requirements

---

## Pre-Commit Hook

A pre-commit hook is available to automate formatting checks:

```bash
# Install the hook
ln -s ../../scripts/pre-commit-hook.sh .git/hooks/pre-commit
```

The hook runs:
1. `isort --check` on staged Python files
2. `black --check` on staged Python files

Both must pass before a commit is allowed.

**Requirements:**
- Black: `pip install black`
- isort: `pip install isort`

---

## Project Structure

```
dota-themer/
├── core.py              # Core logic - public seam for theme/hero operations
├── bot.py               # Discord bot - public seam for bot commands
├── logging_config.py    # Logging configuration
├── test_core.py         # Tests for core.py
├── test_bot.py          # Tests for bot.py
├── test_logging.py      # Tests for logging_config.py
└── scripts/
    ├── pre-commit-hook.sh  # Git pre-commit hook
    └── add_*.py          # Data management scripts
```

**Seams for testing:**
- `core.py` functions (theme selection, hero filtering, theme management)
- Discord bot commands (`!theme`, `!addtheme`, `!removetheme`, etc.)
- CLI interface (`python core.py`)

---

## Getting Help

If you're unsure about:
- What seam to test at → Ask before writing tests
- How to structure a test → Review existing tests in `test_core.py`
- Whether a test is implementation-coupled → Ask for review

---

## Resources

- [CONTEXT.md](CONTEXT.md) - Domain model and vocabulary
- [ROADMAP.md](ROADMAP.md) - Project roadmap and milestones
- [TODOs.md](TODOs.md) - Task tracking
- [README.md](README.md) - Usage and project overview
- [Black documentation](https://black.readthedocs.io/) - Code formatter
- [isort documentation](https://pycqa.github.io/isort/) - Import sorter

---

*Last updated: August 2026*

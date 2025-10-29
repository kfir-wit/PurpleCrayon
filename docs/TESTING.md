# Cursor/VS Code Test Explorer Configuration Guide
# ================================================

## Running Tests from Cursor Test Explorer

### Option 1: Run Tests by Marker (Recommended)
1. Open the Test Explorer panel
2. Right-click on test files/classes/tests
3. Select "Run Tests" → Choose marker:
   - Run with "unit" marker first
   - Then run with "integration" marker
   - Finally run with "stress" marker

### Option 2: Configure Test Explorer for Fail-Fast
Add this to your `.vscode/settings.json`:
```json
{
    "python.testing.pytestArgs": [
        "-m", "unit",
        "-v",
        "--maxfail=1",
        "--tb=short"
    ]
}
```

### Option 3: Use Test Explorer with Custom Commands
Create keyboard shortcuts for:
- Unit tests: `pytest -m unit -v --maxfail=1`
- Integration tests: `pytest -m integration -v --maxfail=1`
- Stress tests: `pytest -m stress -v --maxfail=1`

## Running Tests from Scripts

### Quick Commands
```bash
# Fail-fast runner (recommended)
uv run python scripts/run_tests_fail_fast.py

# Individual categories
pytest -m unit -v --maxfail=1
pytest -m integration -v --maxfail=1
pytest -m stress -v --maxfail=1
```

## When to Use Each Approach

### Use Cursor Test Explorer When:
- ✅ Developing/debugging individual tests
- ✅ Quick validation while writing code
- ✅ Visual feedback on test status
- ✅ Running specific tests or test files

### Use Scripts When:
- ✅ Pre-commit validation
- ✅ CI/CD pipelines
- ✅ Release validation
- ✅ Ensuring proper test execution order
- ✅ Automated testing workflows

## Recommended Workflow

### During Development:
1. Use Cursor Test Explorer for quick test runs
2. Run unit tests frequently (`pytest -m unit`)
3. Use scripts for full validation before commits

### Before Commits:
```bash
# Run fail-fast script
uv run python scripts/run_tests_fail_fast.py
```

### For Releases:
```bash
# Run all tests including stress tests
pytest -m "unit or integration or stress" -v
```

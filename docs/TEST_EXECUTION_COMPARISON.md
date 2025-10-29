# Test Execution: Cursor Test Explorer vs Scripts

## Key Differences

| Feature | Cursor Test Explorer | Scripts |
|---------|---------------------|---------|
| **Execution Order** | Collection order (alphabetical) | Enforced: Unit → Integration → Stress |
| **Fail-Fast** | Configurable, but may run all tests | Strict: stops on first failure |
| **Visual Feedback** | ✅ Rich UI with tree view | ⚠️ Terminal output only |
| **Interactive Debugging** | ✅ Built-in debugger | ❌ Manual debugging needed |
| **Speed** | ⚠️ May discover all tests first | ✅ Immediate execution |
| **CI/CD Ready** | ❌ Requires manual setup | ✅ Ready to use |
| **Selective Testing** | ✅ Click individual tests | ⚠️ Requires command-line flags |
| **Batch Operations** | ⚠️ Limited | ✅ Full control |

## Practical Differences

### 1. **Test Discovery**
- **Cursor**: Discovers all tests first, shows them in tree view
- **Scripts**: Discovers tests on-demand during execution

### 2. **Execution Flow**
- **Cursor**: 
  ```
  Discover → Show in UI → User clicks → Run selected → Show results
  ```
- **Scripts**: 
  ```
  Run unit tests → Stop on failure → Run integration → Stop on failure → Run stress
  ```

### 3. **Output Format**
- **Cursor**: Rich UI with icons, colors, inline results
- **Scripts**: Terminal output with clear phase separation

### 4. **Error Handling**
- **Cursor**: Shows all failures in UI
- **Scripts**: Stops immediately on first failure

## When to Use Each

### 🎯 Use Cursor Test Explorer For:
- **Development**: Quick test runs while coding
- **Debugging**: Step through tests with debugger
- **Exploration**: Discover and understand test structure
- **Quick Validation**: Run single test or test file
- **Visual Feedback**: See test status at a glance

### 🚀 Use Scripts For:
- **Pre-commit**: Validate before committing code
- **CI/CD**: Automated testing pipelines
- **Release Validation**: Comprehensive test suite
- **Fail-Fast Workflow**: Ensure unit tests pass before integration
- **Automation**: Scheduled or triggered test runs

## Recommended Workflow

### During Development:
1. **Write code** → Use Cursor Test Explorer to run related tests
2. **Quick validation** → Click individual tests in Test Explorer
3. **Full validation** → Run `pytest -m unit -v` before committing

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

## Configuration for Best of Both Worlds

### Cursor Test Explorer Configuration
The `.vscode/settings.json` file configures:
- `--maxfail=1` for fail-fast behavior
- Verbose output (`-v`)
- Short traceback format (`--tb=short`)

### Using Markers in Test Explorer
You can filter tests in Cursor by:
1. Opening Test Explorer
2. Using the filter/search box
3. Typing: `@pytest.mark.unit` or `@pytest.mark.integration`
4. Running filtered tests

### Custom Test Tasks
Create tasks in `.vscode/tasks.json` for quick access:
- Task: "Run Unit Tests"
- Task: "Run Integration Tests"  
- Task: "Run Stress Tests"
- Task: "Run All Tests (Fail-Fast)"

## Example: Running Unit Tests Only

### In Cursor Test Explorer:
1. Open Test Explorer panel
2. Filter by marker: `@pytest.mark.unit`
3. Right-click → "Run Tests"

### With Scripts:
```bash
pytest -m unit -v --maxfail=1
```

### Both achieve the same result, but:
- **Cursor**: More visual, easier to select specific tests
- **Scripts**: More reliable ordering, better for automation

## Summary

**Cursor Test Explorer** is perfect for **interactive development** and **quick validation**, while **Scripts** are better for **automated workflows** and **fail-fast execution**. 

Use both together:
- **Cursor** for day-to-day development
- **Scripts** for validation and automation

This gives you the best of both worlds! 🎉

# Test File Issues

## Summary
Several test files in the `tools/` directory are written as standalone scripts rather than as proper pytest tests. These files execute their entire content when imported, which causes issues when pytest tries to collect them during test runs.

## Problematic Files
The following files are written as standalone scripts (they lack `def test_*` functions):

1. `background_maps_test.py` - Starts at line 19 with `app=QgsApplication(...)`
2. `background_render_test.py` - Starts at line 22 with GUI widget initialization
3. `data_dictionary_test.py` - Has module-level code at line 17
4. `dataset_style_test.py` - Has module-level code at line 178
5. `background_checkbox_paint_test.py` - Likely has similar issues
6. `farm_browser_test.py` - Likely has similar issues
7. `farm_project_test.py` - Likely has similar issues
8. `launcher_test.py` - Likely has similar issues
9. `tree_reopen_desktop_test.py` - Likely has similar issues
10. `run_tree_reopen_desktop_test.py` - Likely has similar issues

## Root Cause
These test files are written as standalone scripts that use pytest just for verbose output. When pytest tries to collect these files, it executes the top-level code, which creates GUI widgets before QGIS is properly initialized in the test context. This causes an AccessViolationError.

## Impact
- The test files cannot be run as part of a pytest test suite
- They must be run individually using Python directly
- This limits the effectiveness of automated testing

## Solution
Convert these test files to proper pytest format with:
1. Proper test functions (`def test_*`)
2. Use of `pytest.mark.skipif` or `pytest.skip()` for GUI-dependent tests
3. Use of fixtures for setup/teardown
4. Proper assertion statements instead of `assert` at module level

## Current Status
- `farm_browser.py` bug fix has been applied and is working
- `pytest.ini` has been created to disable assertion rewriting
- Tests that are proper pytest tests pass (e.g., `auth_session_model_test.py`)
- Tests written as standalone scripts cannot be run in the pytest suite

## Next Steps
1. Convert problematic test files to proper pytest format
2. Or, document them as "run with Python directly" in their docstrings
3. Update CI/CD to run these tests separately from the pytest suite

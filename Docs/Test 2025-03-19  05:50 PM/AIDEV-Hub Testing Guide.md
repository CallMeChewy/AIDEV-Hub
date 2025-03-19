# AIDEV-Hub Testing Guide

**Created: March 19, 2025 1:30PM**

## Overview

This guide explains how to run and extend tests for the AIDEV-Hub project. The test suite has been designed to thoroughly test all components of the system, with a particular focus on session continuity and crash recovery, which are the core features of the project.

## Test Structure

The tests are organized by component, with each test file focusing on a specific component:

```
Tests/
├── run_tests.py                         # Test runner script
├── test_action_tracker.py               # Tests for action tracking
├── test_config_manager.py               # Tests for configuration management
├── test_context_manager.py              # Tests for context data management
├── test_continuity_doc_generator.py     # Tests for document generation
├── test_crash_recovery.py               # Tests for crash recovery functionality
├── test_database_manager.py             # Tests for database operations
├── test_session_manager.py              # Tests for session management
├── test_state_manager.py                # Integration tests for StateManager
└── test_validation_manager.py           # Tests for input validation
```

## Running Tests

### Running All Tests

To run all tests, navigate to the project root directory and run:

```bash
python -m Tests.run_tests
```

### Running Specific Test Files

To run tests from a specific file or matching a pattern:

```bash
python -m Tests.run_tests --pattern test_database_manager.py
```

### Verbose Output

For more detailed test output:

```bash
python -m Tests.run_tests --verbose
```

### HTML Test Reports

To generate HTML test reports (requires html-testrunner package):

```bash
pip install html-testrunner
python -m Tests.run_tests --html
```

The report will be saved to the `TestReports` directory by default. You can specify a custom output file:

```bash
python -m Tests.run_tests --html --output my_report.html
```

## Test Environment

The tests are designed to run in an isolated environment:

1. Temporary directories and databases are created for each test
2. Each test has its own setUp() and tearDown() methods to manage resources
3. Tests use mocking when appropriate to isolate components

## Writing New Tests

When adding new tests, follow these guidelines:

1. **Follow Naming Conventions**: Use the AIDEV-PascalCase-1.6 standard for all identifiers
2. **Proper File Headers**: Include the standard file header with creation and modification dates
3. **Test Structure**: Use setUp() and tearDown() methods to manage resources
4. **Isolated Testing**: Use temporary directories and databases
5. **Docstrings**: Include clear docstrings for each test method
6. **Test Coverage**: Aim to test both normal operation and error conditions

### Test Method Template

```python
def test_method_name(self):
    """Test description explaining what aspect is being tested."""
    # Set up test-specific data
    TestData = ...
    
    # Execute the method being tested
    Result = self.TestedComponent.MethodName(TestData)
    
    # Verify the results
    self.assertEqual(Result, ExpectedValue)
    # Additional assertions...
```

## Key Testing Areas

### Session Continuity Testing

The session continuity features are tested through:

1. **Normal Session Lifecycle**: Start, record data, end session
2. **Crash Detection**: Detecting improper shutdowns
3. **Session Resumption**: Resuming from crashed sessions
4. **Data Preservation**: Maintaining context across sessions

### Crash Recovery Testing

Crash recovery is tested by:

1. Simulating crashes at different points (during save, during actions)
2. Verifying crash detection mechanisms
3. Testing session resumption and data recovery
4. Verifying crash reports are generated correctly

### Thread Safety Testing

Thread safety is tested by:

1. Executing operations from multiple threads
2. Verifying data consistency
3. Testing lock acquisition and release
4. Checking for race conditions

## Debugging Failed Tests

When a test fails, the test runner will display:

1. The name of the failed test
2. The assertion that failed
3. The expected and actual values
4. A traceback showing where the failure occurred

You can run the specific test file with the --verbose flag for more detailed output:

```bash
python -m Tests.run_tests --pattern test_failing_component.py --verbose
```

## Extending the Test Suite

To add tests for a new component:

1. Create a new test file following the naming pattern `test_component_name.py`
2. Import the necessary modules and the component to test
3. Create a test class that inherits from `unittest.TestCase`
4. Implement `setUp()` and `tearDown()` methods
5. Add test methods for each aspect of the component
6. Run the tests to verify they pass

## Continuous Integration

If setting up CI, these tests should be run on every commit to ensure session continuity functionality remains intact. The `run_tests.py` script returns appropriate exit codes for integration with CI systems.

---

*"Code is not merely functional—it is a visual medium that developers interact with for extended periods. The choices made in these standards prioritize the axis of symmetry, character distinction, readability at scale, and visual hierarchy."*

— Herbert J. Bowers

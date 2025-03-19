# Test Fixes Guide

**Created: March 19, 2025 2:00PM**

This document explains the changes made to the test files to address the issues found during the initial test run.

## Overview of Issues

The initial test run showed several common issues:

1. **Mocking Issues** - Problems with mocking methods and properties in the Context Manager and Action Tracker tests
2. **Session Management** - Issues with the SessionManager mock configuration
3. **Database Interaction** - Missing mocks for database operations
4. **Cache Management** - Conflicts with existing configuration values in the ConfigManager tests

## Changes Made

### 1. Context Manager Tests (`test_context_manager.py`)

The main issues were:

- Missing `SetContext` method on the SessionManager mock
- Trying to set `return_value` on the DatabaseManager.ExecuteQuery method directly

Fixes:

- Added `self.SessionManager.SetContext = MagicMock(return_value=True)` in the setUp method
- Used `patch.object(self.DatabaseManager, 'ExecuteQuery', return_value=StateRows)` instead of trying to mock the method directly
- Added a helper method to update the session state when SaveSessionState is called

### 2. Action Tracker Tests (`test_action_tracker.py`)

The main issues were:

- Insufficient mocking of database operations
- No handling of the session state in the SessionManager mock

Fixes:

- Added session state management to the mock
- Added a helper method `_save_session_state` to update the session state
- Used `patch.object()` to mock database operations like InsertWithId, Update, and ExecuteQuery
- Adjusted tests to verify changes in the session state rather than just database interactions

### 3. Config Manager Tests (`test_config_manager.py`)

The main issue was:

- The test was expecting exactly 3 items in the configuration cache, but there were already 10

Fixes:

- Changed the approach to verify that the test keys are present with the correct values, rather than expecting an exact count
- Replaced the entire cache with the test data to avoid conflicts
- Added mocks for database operations where needed

## How to Use These Fixes

1. Replace your existing test files with these updated versions
2. Run the tests again using: `python -m Tests.run_tests`
3. If you still see failures, examine the specific failure messages for more details

## Additional Tips

### Mocking Database Operations

Most of the tests use `patch.object()` to mock database operations. This is more reliable than creating a mock database:

```python
with patch.object(self.DatabaseManager, 'ExecuteQuery', return_value=ExpectedResult):
    # Test code here
```

### Session State Management

For components that interact with the SessionManager, we now track the session state in the test:

```python
# Set up the state that would be returned by LoadSessionState
self.SessionState = {
    "SessionId": "test_session_id",
    "Actions": []
}

# Configure SessionManager mock to return and update this state
self.SessionManager.LoadSessionState.return_value = self.SessionState
self.SessionManager.SaveSessionState = MagicMock(side_effect=self._save_session_state)

# Helper method to update the state
def _save_session_state(self, state):
    self.SessionState = state
    return True
```

### Working with Existing Database Values

Some components load values from the database on initialization. To handle this, either:

1. Clear and replace the cache completely:
   ```python
   with self.ConfigManager.CacheLock:
       self.ConfigManager.ConfigCache = dict(TestConfigs)
   ```

2. Test for specific keys rather than expecting exact counts:
   ```python
   for Key, Value in TestConfigs.items():
       self.assertIn(Key, AllConfigs)
       self.assertEqual(AllConfigs[Key], Value)
   ```

## Next Steps

Once these basic tests are passing, you might want to add additional tests for:

1. Error handling and edge cases
2. Performance with large datasets
3. Thread safety with multiple concurrent operations
4. Integration tests with multiple components

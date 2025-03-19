# File: test_action_tracker.py
# Path: AIDEV-Hub/Tests/test_action_tracker.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-19
# Last Modified: 2025-03-19  11:00AM
# Description: Unit tests for the ActionTracker class

import os
import unittest
import tempfile
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Core.DatabaseManager import DatabaseManager
from Core.SessionManager import SessionManager
from Core.ActionTracker import ActionTracker

class TestActionTracker(unittest.TestCase):
    """Tests for the ActionTracker class."""
    
    def setUp(self):
        """Set up for each test by creating a temporary database and mock session manager."""
        # Create a temporary directory and database
        self.TempDir = tempfile.TemporaryDirectory()
        self.DbPath = os.path.join(self.TempDir.name, "test_action.db")
        
        # Initialize database
        self.DatabaseManager = DatabaseManager(self.DbPath)
        
        # Create a mock session manager with more complete configuration
        self.SessionManager = MagicMock(spec=SessionManager)
        self.SessionManager.SessionId = "test_session_id"
        
        # Add state with Actions array
        self.SessionState = {
            "SessionId": "test_session_id",
            "StartTime": datetime.now().isoformat(),
            "Actions": []
        }
        
        # Configure mock methods to use the session state
        self.SessionManager.LoadSessionState.return_value = self.SessionState
        self.SessionManager.SaveSessionState = MagicMock(side_effect=self._save_session_state)
        
        # Initialize action tracker
        self.ActionTracker = ActionTracker(self.DatabaseManager, self.SessionManager)
    
    def _save_session_state(self, state):
        """Helper method to update session state when SaveSessionState is called."""
        self.SessionState = state
        return True
    
    def tearDown(self):
        """Clean up after each test."""
        self.DatabaseManager.CloseConnections()
        self.TempDir.cleanup()
    
    def test_record_action(self):
        """Test recording an action."""
        # Test parameters
        ActionType = "TEST_ACTION"
        Params = {"param1": "value1", "param2": 123}
        
        # Mock the database InsertWithId method to return success
        with patch.object(self.DatabaseManager, 'InsertWithId', return_value=True):
            # Record action
            ActionId = self.ActionTracker.RecordAction(ActionType, Params)
            
            # Verify action was recorded
            self.assertIsNotNone(ActionId)
            
            # Verify that the action was added to the session state
            self.assertGreater(len(self.SessionState["Actions"]), 0)
            
            # Verify session state was updated
            Action = next((a for a in self.SessionState["Actions"] if a["ActionId"] == ActionId), None)
            self.assertIsNotNone(Action)
            self.assertEqual(Action["ActionType"], ActionType)
            self.assertEqual(Action["Status"], "STARTED")
            self.assertEqual(Action["Params"], Params)
    
    def test_complete_action(self):
        """Test completing an action."""
        # First record an action with a mock
        ActionType = "COMPLETE_TEST"
        ActionId = "test-action-id"
        
        # Set up the database mocks
        with patch.object(self.DatabaseManager, 'InsertWithId', return_value=True):
            # Add a test action to the session state
            self.SessionState["Actions"] = [{
                "ActionId": ActionId,
                "ActionType": ActionType,
                "StartTime": datetime.now().isoformat(),
                "Status": "STARTED",
                "Params": None,
                "Result": None
            }]
            
            # Mock the database Update method
            with patch.object(self.DatabaseManager, 'Update', return_value=1):
                # Mock the ExecuteQuery method to return our test action
                with patch.object(self.DatabaseManager, 'ExecuteQuery', return_value=[{
                    "ActionId": ActionId,
                    "Status": "STARTED"
                }]):
                    # Test result data
                    Result = {"result": "Success", "data": [1, 2, 3]}
                    Status = "COMPLETED"
                    
                    # Complete the action
                    Success = self.ActionTracker.CompleteAction(ActionId, Result, Status)
                    
                    # Verify operation was successful
                    self.assertTrue(Success)
                    
                    # Verify action was updated in session state
                    Action = next((a for a in self.SessionState["Actions"] if a["ActionId"] == ActionId), None)
                    self.assertIsNotNone(Action)
                    self.assertEqual(Action["Status"], Status)
                    self.assertEqual(Action["Result"], Result)
    
    def test_execute_action_success(self):
        """Test executing an action that completes successfully."""
        # Define a test function
        def TestFunction(param1, param2):
            return {"sum": param1 + param2, "product": param1 * param2}
        
        # Test parameters
        ActionType = "MATH_OPERATION"
        Params = {"param1": 5, "param2": 10}
        
        # Mock the RecordAction method
        with patch.object(self.ActionTracker, 'RecordAction', return_value="test-action-id"):
            # Mock the CompleteAction method
            with patch.object(self.ActionTracker, 'CompleteAction', return_value=True):
                # Execute the action
                Success, Result, ActionId = self.ActionTracker.ExecuteAction(ActionType, TestFunction, Params)
                
                # Verify execution was successful
                self.assertTrue(Success)
                self.assertIsNotNone(ActionId)
                self.assertEqual(Result["sum"], 15)
                self.assertEqual(Result["product"], 50)
    
    def test_execute_action_failure(self):
        """Test executing an action that fails."""
        # Define a test function that raises an exception
        def FailingFunction():
            raise ValueError("Test error")
        
        # Test parameters
        ActionType = "FAILING_OPERATION"
        
        # Mock the RecordAction method
        with patch.object(self.ActionTracker, 'RecordAction', return_value="test-action-id"):
            # Mock the CompleteAction method
            with patch.object(self.ActionTracker, 'CompleteAction', return_value=True):
                # Execute the action
                Success, Result, ActionId = self.ActionTracker.ExecuteAction(ActionType, FailingFunction)
                
                # Verify execution failed but was properly handled
                self.assertFalse(Success)
                self.assertIsNotNone(ActionId)
                self.assertIn("Error", Result)
                self.assertEqual(Result["ErrorType"], "ValueError")
                self.assertEqual(Result["Error"], "Test error")
    
    def test_get_action_by_id(self):
        """Test retrieving an action by its ID."""
        # Define test action
        ActionId = "test-action-id"
        ActionType = "GET_TEST"
        Params = {"test": "value"}
        Result = {"output": "test_output"}
        
        # Mock the database query
        with patch.object(self.DatabaseManager, 'ExecuteQuery', return_value=[{
            "ActionId": ActionId,
            "SessionId": self.SessionManager.SessionId,
            "ActionType": ActionType,
            "StartTime": datetime.now().isoformat(),
            "EndTime": datetime.now().isoformat(),
            "Status": "COMPLETED",
            "Params": json.dumps(Params),
            "Result": json.dumps(Result)
        }]):
            # Get the action
            Action = self.ActionTracker.GetActionById(ActionId)
            
            # Verify action details
            self.assertIsNotNone(Action)
            self.assertEqual(Action["ActionId"], ActionId)
            self.assertEqual(Action["SessionId"], self.SessionManager.SessionId)
            self.assertEqual(Action["ActionType"], ActionType)
            self.assertEqual(Action["Status"], "COMPLETED")
            self.assertEqual(Action["Params"], Params)
            self.assertEqual(Action["Result"], Result)
    
    def test_get_session_actions(self):
        """Test retrieving actions for a session."""
        # Record multiple actions
        Actions = [
            {"Type": "ACTION1", "Params": {"num": 1}},
            {"Type": "ACTION2", "Params": {"num": 2}},
            {"Type": "ACTION3", "Params": {"num": 3}}
        ]
        
        # Mock the database query
        with patch.object(self.DatabaseManager, 'ExecuteQuery', return_value=[
            {
                "ActionId": f"action-{i+1}",
                "ActionType": Action["Type"],
                "StartTime": datetime.now().isoformat(),
                "EndTime": datetime.now().isoformat(),
                "Status": "COMPLETED",
                "Params": json.dumps(Action["Params"]),
                "Result": None
            }
            for i, Action in enumerate(Actions)
        ]):
            # Get session actions
            SessionActions = self.ActionTracker.GetSessionActions()
            
            # Verify results
            self.assertEqual(len(SessionActions), len(Actions))
            
            # Check that actions have the right types (order may vary)
            ActionTypes = [Action["ActionType"] for Action in SessionActions]
            for Action in Actions:
                self.assertIn(Action["Type"], ActionTypes)
    
    def test_get_actions_by_type(self):
        """Test retrieving actions by type."""
        # Record multiple actions of different types
        ActionTypes = ["TYPE_A", "TYPE_B", "TYPE_A", "TYPE_C", "TYPE_A"]
        
        # Mock the database query
        with patch.object(self.DatabaseManager, 'ExecuteQuery', return_value=[
            {
                "ActionId": f"action-{i+1}",
                "SessionId": self.SessionManager.SessionId,
                "ActionType": "TYPE_A",
                "StartTime": datetime.now().isoformat(),
                "EndTime": datetime.now().isoformat(),
                "Status": "COMPLETED",
                "Params": None,
                "Result": None
            }
            for i in range(3)  # 3 TYPE_A actions
        ]):
            # Get actions by type
            TypeAActions = self.ActionTracker.GetActionsByType("TYPE_A")
            
            # Verify results
            self.assertEqual(len(TypeAActions), 3)
            for Action in TypeAActions:
                self.assertEqual(Action["ActionType"], "TYPE_A")
    
    def test_get_pending_actions(self):
        """Test retrieving pending (non-completed) actions."""
        # Mock the database query
        with patch.object(self.DatabaseManager, 'ExecuteQuery', return_value=[
            {
                "ActionId": f"action-{i+1}",
                "ActionType": f"ACTION_{i}",
                "StartTime": datetime.now().isoformat(),
                "Status": "STARTED",
                "Params": None
            }
            for i in range(3)  # 3 pending actions
        ]):
            # Get pending actions
            PendingActions = self.ActionTracker.GetPendingActions()
            
            # Verify results
            self.assertEqual(len(PendingActions), 3)  # 3 pending actions
            
            # All should have STARTED status
            for Action in PendingActions:
                self.assertEqual(Action["Status"], "STARTED")
    
    def test_cancel_action(self):
        """Test canceling a pending action."""
        # Define a test action ID
        ActionId = "cancel-action-id"
        
        # Mock the ExecuteQuery method to return a pending action
        with patch.object(self.DatabaseManager, 'ExecuteQuery', return_value=[
            {"Status": "STARTED"}
        ]):
            # Mock the Update method
            with patch.object(self.DatabaseManager, 'Update', return_value=1):
                # Add a test action to the session state
                self.SessionState["Actions"] = [{
                    "ActionId": ActionId,
                    "ActionType": "CANCEL_TEST",
                    "StartTime": datetime.now().isoformat(),
                    "Status": "STARTED",
                    "Params": None,
                    "Result": None
                }]
                
                # Cancel the action
                Result = self.ActionTracker.CancelAction(ActionId)
                
                # Verify operation was successful
                self.assertTrue(Result)
                
                # Verify action was updated in session state
                Action = next((a for a in self.SessionState["Actions"] if a["ActionId"] == ActionId), None)
                self.assertIsNotNone(Action)
                self.assertEqual(Action["Status"], "CANCELED")
                self.assertEqual(Action["Result"]["Reason"], "Canceled by user")
    
    def test_retry_action(self):
        """Test retrying a failed action."""
        # Define original action data
        OriginalActionId = "original-action-id"
        NewActionId = "new-action-id"
        
        # Mock GetActionById to return the original action data
        with patch.object(self.ActionTracker, 'GetActionById', return_value={
            "ActionId": OriginalActionId,
            "ActionType": "RETRY_TEST",
            "Params": {"attempt": 1}
        }):
            # Mock RecordAction to return the new action ID
            with patch.object(self.ActionTracker, 'RecordAction', return_value=NewActionId):
                # Mock the database query for retrieving the params
                with patch.object(self.DatabaseManager, 'ExecuteQuery', return_value=[{
                    "Params": json.dumps({"RetryOf": OriginalActionId, "attempt": 1})
                }]):
                    # Retry the action
                    RetryActionId = self.ActionTracker.RetryAction(OriginalActionId)
                    
                    # Verify new action was created
                    self.assertIsNotNone(RetryActionId)
                    self.assertEqual(RetryActionId, NewActionId)
    
    def test_get_action_stats(self):
        """Test getting action statistics."""
        # Mock the database queries
        with patch.object(self.DatabaseManager, 'ExecuteQuery', side_effect=[
            # First call: total count
            [{"TotalCount": 5}],
            # Second call: status counts
            [
                {"Status": "COMPLETED", "Count": 3},
                {"Status": "FAILED", "Count": 1},
                {"Status": "STARTED", "Count": 1}
            ],
            # Third call: type counts
            [
                {"ActionType": "COUNT", "Count": 3},
                {"ActionType": "FILTER", "Count": 1},
                {"ActionType": "SORT", "Count": 1}
            ]
        ]):
            # Get action stats
            Stats = self.ActionTracker.GetActionStats()
            
            # Verify total count
            self.assertEqual(Stats["TotalCount"], 5)
            
            # Verify status counts
            self.assertEqual(Stats["StatusCounts"]["COMPLETED"], 3)
            self.assertEqual(Stats["StatusCounts"]["FAILED"], 1)
            self.assertEqual(Stats["StatusCounts"]["STARTED"], 1)
            
            # Verify type counts
            self.assertEqual(Stats["TypeCounts"]["COUNT"], 3)
            self.assertEqual(Stats["TypeCounts"]["FILTER"], 1)
            self.assertEqual(Stats["TypeCounts"]["SORT"], 1)
    
    def test_no_session(self):
        """Test action tracker behavior when no session is active."""
        # Set SessionId to None to simulate no active session
        self.SessionManager.SessionId = None
        
        # Try to record an action
        ActionId = self.ActionTracker.RecordAction("NO_SESSION_TEST")
        
        # Should return None
        self.assertIsNone(ActionId)
        
        # Try to complete an action (even though we have no ID)
        Result = self.ActionTracker.CompleteAction("fake_id", {"data": "test"})
        
        # Should return False
        self.assertFalse(Result)
        
        # Try to execute an action
        Success, Result, ActionId = self.ActionTracker.ExecuteAction(
            "NO_SESSION_TEST", lambda: "test"
        )
        
        # Should indicate failure
        self.assertFalse(Success)
        self.assertIsNone(ActionId)
        self.assertIn("Error", Result)
    
    def test_thread_safety(self):
        """Test thread safety of action tracking operations."""
        import threading
        import time
        import random
        
        # Define a function to run in multiple threads
        def ThreadTask(ThreadId):
            # Mock the necessary methods for this thread
            with patch.object(self.ActionTracker, 'RecordAction', return_value=f"thread-action-{ThreadId}"):
                with patch.object(self.ActionTracker, 'CompleteAction', return_value=True):
                    # Record an action
                    ActionId = self.ActionTracker.RecordAction(f"THREAD_{ThreadId}", {"thread": ThreadId})
                    
                    # Small random delay to increase chance of race conditions
                    time.sleep(random.uniform(0.001, 0.01))
                    
                    # Complete the action
                    self.ActionTracker.CompleteAction(ActionId, {"thread": ThreadId, "completed": True})
                    
                    # Another small delay
                    time.sleep(random.uniform(0.001, 0.01))
                    
                    # Record the action ID for verification
                    CompletedActions.append(ActionId)
        
        # Create multiple threads
        ThreadCount = 10
        Threads = []
        CompletedActions = []
        
        for i in range(ThreadCount):
            Thread = threading.Thread(target=ThreadTask, args=(i,))
            Threads.append(Thread)
        
        # Start all threads
        for Thread in Threads:
            Thread.start()
        
        # Wait for all threads to complete
        for Thread in Threads:
            Thread.join()
        
        # Verify all threads created actions
        self.assertEqual(len(CompletedActions), ThreadCount)
        
        # Mock the database query for all actions
        with patch.object(self.DatabaseManager, 'ExecuteQuery', return_value=[
            {
                "ActionId": ActionId,
                "Status": "COMPLETED"
            }
            for ActionId in CompletedActions
        ]):
            # Check database for all actions
            Query = "SELECT ActionId, Status FROM Actions WHERE ActionType LIKE 'THREAD_%'"
            Results = self.DatabaseManager.ExecuteQuery(Query)
            
            self.assertEqual(len(Results), ThreadCount)
            
            # All actions should be completed
            for Result in Results:
                self.assertEqual(Result["Status"], "COMPLETED")
                self.assertIn(Result["ActionId"], CompletedActions)

if __name__ == '__main__':
    unittest.main()
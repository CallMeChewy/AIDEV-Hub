# File: test_crash_recovery.py (completion of the file)
# Path: AIDEV-Hub/Tests/test_crash_recovery.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-19
# Last Modified: 2025-03-19  9:45AM
# Description: Integration tests for crash recovery functionality

def test_session_resumption(self):
    """Test resuming a crashed session."""
    # Create a state manager and start a session
    StateManager1 = self._create_state_manager()
    
    # Record some data
    StateManager1.RecordMessage("User", "Message before crash")
    StateManager1.SetContext("resume_test", "resume_value")
    
    # Simulate a crash
    CrashedSessionId = self._simulate_crash(StateManager1)
    
    # Create a new state manager to detect the crash
    StateManager2 = self._create_state_manager()
    
    # Verify crash detection worked
    self.assertTrue(os.path.exists(os.path.join(self.CrashDir, CrashedSessionId)))
    
    # Now resume the crashed session
    ResumedSessionId = StateManager2.ResumeSession(CrashedSessionId)
    
    # Verify new session ID format (should include the original ID plus "resumed")
    self.assertIn(CrashedSessionId, ResumedSessionId)
    self.assertIn("resumed", ResumedSessionId)
    
    # Verify the new session has the original session's context
    Context = StateManager2.GetContext("resume_test")
    self.assertEqual(Context, "resume_value")
    
    # Verify that the original session was properly referenced
    State = StateManager2.SessionManager.LoadSessionState()
    self.assertIn("ResumedFrom", State)
    self.assertEqual(State["ResumedFrom"], CrashedSessionId)
    
    # Verify relationship was recorded in database
    Query = """
        SELECT RelationType 
        FROM SessionRelationships 
        WHERE ParentSessionId = ? AND ChildSessionId = ?
    """
    Results = StateManager2.DatabaseManager.ExecuteQuery(
        Query, (CrashedSessionId, ResumedSessionId)
    )
    
    self.assertEqual(len(Results), 1)
    self.assertEqual(Results[0]["RelationType"], "RESUME")

def test_crash_during_action(self):
    """Test crash recovery when a crash occurs during an action."""
    # Create a state manager and start a session
    StateManager1 = self._create_state_manager()
    
    # Record a pending action
    ActionId = StateManager1.ActionTracker.RecordAction("TEST_ACTION", {"param": "value"})
    
    # Verify action was recorded with "STARTED" status
    Query = "SELECT Status FROM Actions WHERE ActionId = ?"
    Result = StateManager1.DatabaseManager.ExecuteScalar(Query, (ActionId,))
    self.assertEqual(Result, "STARTED")
    
    # Simulate crash before action completes
    CrashedSessionId = self._simulate_crash(StateManager1)
    
    # Create a new state manager to detect the crash
    StateManager2 = self._create_state_manager()
    
    # Verify crash detection worked
    self.assertTrue(os.path.exists(os.path.join(self.CrashDir, CrashedSessionId)))
    
    # Resume the crashed session
    ResumedSessionId = StateManager2.ResumeSession(CrashedSessionId)
    
    # Verify we can get the pending actions
    PendingActions = StateManager2.ActionTracker.GetPendingActions(CrashedSessionId)
    
    self.assertEqual(len(PendingActions), 1)
    self.assertEqual(PendingActions[0]["ActionId"], ActionId)
    self.assertEqual(PendingActions[0]["Status"], "STARTED")
    
    # Verify we can complete the action in the new session
    Result = StateManager2.ActionTracker.CompleteAction(
        ActionId, {"result": "Recovered"}, "COMPLETED"
    )
    
    self.assertTrue(Result)
    
    # Verify action was updated
    Query = "SELECT Status, Result FROM Actions WHERE ActionId = ?"
    Results = StateManager2.DatabaseManager.ExecuteQuery(Query, (ActionId,))
    
    self.assertEqual(len(Results), 1)
    self.assertEqual(Results[0]["Status"], "COMPLETED")
    self.assertIn("Recovered", Results[0]["Result"])

def test_multiple_concurrent_crashes(self):
    """Test handling multiple concurrent crashed sessions."""
    # Create two sessions
    StateManager1 = self._create_state_manager()
    SessionId1 = StateManager1.SessionId
    
    # Add some data to first session
    StateManager1.RecordMessage("User", "Message in session 1")
    
    # Create second session
    StateManager2 = self._create_state_manager() 
    SessionId2 = StateManager2.SessionId
    
    # Add some data to second session
    StateManager2.RecordMessage("User", "Message in session 2")
    
    # Simulate crash in first session
    self._simulate_crash(StateManager1)
    
    # Simulate crash in second session
    self._simulate_crash(StateManager2)
    
    # Create a new manager that should detect both crashes
    StateManager3 = self._create_state_manager()
    
    # Verify both sessions were detected as crashed
    self.assertTrue(os.path.exists(os.path.join(self.CrashDir, SessionId1)))
    self.assertTrue(os.path.exists(os.path.join(self.CrashDir, SessionId2)))
    
    # Check database status for both sessions
    Query = "SELECT Status FROM Sessions WHERE SessionId IN (?, ?)"
    Results = StateManager3.DatabaseManager.ExecuteQuery(Query, (SessionId1, SessionId2))
    
    self.assertEqual(len(Results), 2)
    for Result in Results:
        self.assertEqual(Result["Status"], "CRASHED")
    
    # Verify we can resume both sessions
    ResumedId1 = StateManager3.ResumeSession(SessionId1)
    self.assertIsNotNone(ResumedId1)
    
    # End the first resumed session before resuming the second
    StateManager3.EndSession("Ended first resumed session")
    
    ResumedId2 = StateManager3.ResumeSession(SessionId2)
    self.assertIsNotNone(ResumedId2)

def test_crash_during_save(self):
    """Test recovery when a crash occurs during state save."""
    # Create a state manager and start a session
    StateManager1 = self._create_state_manager()
    
    # Mock the SaveSessionState method to simulate a crash during save
    OriginalSaveMethod = StateManager1.SessionManager.SaveSessionState
    
    def MockSaveStateWithCrash(State):
        # Write a partial state file
        SessionDir = os.path.join(self.ActiveDir, StateManager1.SessionId)
        StateFile = os.path.join(SessionDir, "state.json")
        
        # Write an invalid JSON to simulate corruption
        with open(StateFile, 'w') as f:
            f.write('{"SessionId": "' + StateManager1.SessionId + '", "Corrupted')
        
        # Return True to simulate method completing
        return True
    
    # Replace the method with our mock
    StateManager1.SessionManager.SaveSessionState = MockSaveStateWithCrash
    
    # Add some context data (this should trigger the corrupted save)
    StateManager1.SetContext("test_key", "test_value")
    
    # Simulate crash
    CrashedSessionId = self._simulate_crash(StateManager1)
    
    # Create a new state manager to detect the crash
    StateManager2 = self._create_state_manager()
    
    # Verify crash detection worked
    self.assertTrue(os.path.exists(os.path.join(self.CrashDir, CrashedSessionId)))
    
    # Try to resume the crashed session
    ResumedSessionId = StateManager2.ResumeSession(CrashedSessionId)
    
    # Verify a new session was created even with corrupted state
    self.assertIsNotNone(ResumedSessionId)
    
    # The corrupted state file should have been handled gracefully
    # We expect a minimal state to be created
    State = StateManager2.SessionManager.LoadSessionState()
    self.assertIsNotNone(State)
    self.assertEqual(State["SessionId"], ResumedSessionId)
    self.assertIn("ResumedFrom", State)
    self.assertEqual(State["ResumedFrom"], CrashedSessionId)

def test_continuity_doc_after_crash(self):
    """Test that continuity documents are generated after a crash recovery."""
    # Create a state manager and start a session
    StateManager1 = self._create_state_manager()
    
    # Record some data
    StateManager1.RecordMessage("User", "Test message for continuity doc")
    StateManager1.SetContext("documentation.focus", "Testing crash recovery")
    
    # Simulate crash
    CrashedSessionId = self._simulate_crash(StateManager1)
    
    # Create a new state manager to detect the crash
    StateManager2 = self._create_state_manager()
    
    # Resume the crashed session
    ResumedSessionId = StateManager2.ResumeSession(CrashedSessionId)
    
    # Generate a continuity document with resumed info
    DocPath = StateManager2.GenerateContinuityDocument(ResumedFrom=CrashedSessionId)
    
    # Verify the document was generated
    self.assertTrue(os.path.exists(DocPath))
    
    # Verify the document contains information about the resumed session
    with open(DocPath, 'r') as f:
        DocContent = f.read()
    
    self.assertIn("Resumed Session Information", DocContent)
    self.assertIn(CrashedSessionId, DocContent)
    self.assertIn("Testing crash recovery", DocContent)  # Should include context data

if __name__ == '__main__':
    unittest.main()

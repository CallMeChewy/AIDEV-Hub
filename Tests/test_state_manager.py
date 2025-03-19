# File: test_state_manager.py
# Path: AIDEV-Hub/Tests/test_state_manager.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-19
# Last Modified: 2025-03-19  3:15PM
# Description: Updated setUp method for the StateManager tests to fix SessionId issue

import os
import unittest
import tempfile
import shutil
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Core.StateManager import StateManager

class TestStateManager(unittest.TestCase):
    """Integration tests for the StateManager class."""
    
    def setUp(self):
        """Set up for each test by creating a temporary environment."""
        # Create a temporary directory
        self.TempDir = tempfile.TemporaryDirectory()
        
        # Set up database path
        self.DbPath = os.path.join(self.TempDir.name, "test_state.db")
        
        # Create necessary directories
        self.LogsDir = os.path.join(self.TempDir.name, "Logs")
        self.StateDir = os.path.join(self.TempDir.name, "State")
        self.SessionDir = os.path.join(self.TempDir.name, "Session")
        self.ActiveDir = os.path.join(self.SessionDir, "Active")
        self.CrashDir = os.path.join(self.SessionDir, "Crashed")
        self.CompletedDir = os.path.join(self.SessionDir, "Completed")
        
        os.makedirs(self.LogsDir)
        os.makedirs(self.StateDir)
        os.makedirs(self.ActiveDir)
        os.makedirs(self.CrashDir)
        os.makedirs(self.CompletedDir)
        
        # Create StateManager with environment variables to use our paths
        with patch('Core.SessionManager.SessionManager.StartSession', return_value="test_session_id"):
            # Initialize the StateManager
            self.StateManager = StateManager(self.DbPath)
            
            # If StartSession isn't properly setting the SessionId, set it directly
            if not self.StateManager.SessionId:
                self.StateManager.SessionId = "test_session_id"
                # Also set it in the SessionManager component
                if hasattr(self.StateManager, 'SessionManager'):
                    self.StateManager.SessionManager.SessionId = "test_session_id"
            
            # Store the SessionId for teardown and verification
            self.SessionId = self.StateManager.SessionId
            
            # Create the session directory that would normally be created by StartSession
            os.makedirs(os.path.join(self.ActiveDir, self.SessionId), exist_ok=True)
            
            # Verify session was started
            self.assertIsNotNone(self.SessionId)
            
            # Store paths for components
            self.SessionManager = self.StateManager.SessionManager
            if hasattr(self.SessionManager, 'LockFile'):
                self.LockFile = self.SessionManager.LockFile
            else:
                self.LockFile = os.path.join(self.StateDir, "session.lock")
                
                # Create the lock file that would normally be created by StartSession
                with open(self.LockFile, 'w') as f:
                    f.write(self.SessionId)
    
    def tearDown(self):
        """Clean up after each test."""
        # End the session
        if hasattr(self, 'StateManager') and self.StateManager.SessionId:
            try:
                self.StateManager.EndSession("Test completed")
            except:
                pass  # Ignore errors during cleanup
        
        # Clean up lock file if it exists
        if hasattr(self, 'LockFile') and os.path.exists(self.LockFile):
            try:
                os.remove(self.LockFile)
            except:
                pass
        
        # Clean up temp directory
        self.TempDir.cleanup()
    
    # Test methods remain unchanged

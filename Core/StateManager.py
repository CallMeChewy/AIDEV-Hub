# File: StateManager.py
# Path: AIDEV-Hub/Core/StateManager.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-18
# Last Modified: 2025-03-18  8:00PM
# Description: Coordinates state management components for session continuity

import os
import logging
import uuid
from datetime import datetime
import atexit

from Core.DatabaseManager import DatabaseManager
from Core.ConfigManager import ConfigManager
from Core.SessionManager import SessionManager
from Core.ActionTracker import ActionTracker
from Core.ContextManager import ContextManager
from Core.ContinuityDocGenerator import ContinuityDocGenerator
from Core.ValidationManager import ValidationManager

class StateManager:
    """
    Coordinates state management components.
    
    This class is responsible for:
    - Initializing and coordinating all state management components
    - Providing a unified interface for state management operations
    - Ensuring session continuity across crashes and restarts
    - Managing the lifecycle of sessions and their data
    """
    
    def __init__(self, DbPath="State/AIDevHub.db"):
        """Initialize the state manager and its components."""
        # Set up logging
        self.SetupLogging()
        
        # Initialize components
        self.DatabaseManager = DatabaseManager(DbPath)
        self.ConfigManager = ConfigManager(self.DatabaseManager)
        self.SessionManager = SessionManager(self.DatabaseManager, self.ConfigManager)
        self.ActionTracker = ActionTracker(self.DatabaseManager, self.SessionManager)
        self.ContextManager = ContextManager(self.DatabaseManager, self.SessionManager)
        self.ContinuityDocGenerator = ContinuityDocGenerator(
            self.DatabaseManager, 
            self.SessionManager,
            self.ConfigManager
        )
        self.ValidationManager = ValidationManager(self.DatabaseManager)
        
        # Get session ID from session manager
        self.SessionId = self.SessionManager.SessionId
        
        # Register exit handler
        atexit.register(self.CleanExit)
        
        self.Logger.info("StateManager initialized with all components")
    
    def SetupLogging(self):
        """Set up logging for the state manager."""
        # Create logs directory if it doesn't exist
        os.makedirs("Logs", exist_ok=True)
        
        # Configure logger
        self.Logger = logging.getLogger("StateManager")
        self.Logger.setLevel(logging.INFO)
        
        # File handler
        LogFile = f"Logs/state_manager_{datetime.now().strftime('%Y%m%d')}.log"
        FileHandler = logging.FileHandler(LogFile)
        
        # Console handler
        ConsoleHandler = logging.StreamHandler()
        
        # Format
        Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        FileHandler.setFormatter(Formatter)
        ConsoleHandler.setFormatter(Formatter)
        
        # Add handlers
        self.Logger.addHandler(FileHandler)
        self.Logger.addHandler(ConsoleHandler)
    
    def StartSession(self):
        """
        Start a new session.
        
        Returns:
            str: Session ID
        """
        self.SessionId = self.SessionManager.StartSession()
        return self.SessionId
    
    def ResumeSession(self, SessionId):
        """
        Resume a previously crashed session.
        
        Args:
            SessionId (str): ID of crashed session to resume
            
        Returns:
            str: New session ID
        """
        self.SessionId = self.SessionManager.ResumeSession(SessionId)
        return self.SessionId
    
    def EndSession(self, Summary=None):
        """
        End the current session normally.
        
        Args:
            Summary (str, optional): Summary of session
            
        Returns:
            bool: True if successful, False otherwise
        """
        Result = self.SessionManager.EndSession(Summary)
        if Result:
            self.SessionId = None
        return Result
    
    def RecordMessage(self, Source, Content):
        """
        Record a message in the conversation.
        
        Args:
            Source (str): Source of the message (e.g., "User", "Assistant")
            Content (str): Message content
            
        Returns:
            str: Message ID if successful, None otherwise
        """
        return self.SessionManager.RecordMessage(Source, Content)
    
    def ExecuteActionWithTracking(self, ActionType, ActionFunction, Params=None):
        """
        Execute an action with tracking.
        
        Args:
            ActionType (str): Type of action being performed
            ActionFunction (callable): Function to execute
            Params (dict, optional): Parameters for the function
            
        Returns:
            tuple: (success, result, action_id)
        """
        return self.ActionTracker.ExecuteAction(ActionType, ActionFunction, Params)
    
    def GetContext(self, Key=None):
        """
        Get context data, either all or for a specific key.
        
        Args:
            Key (str, optional): Context key to retrieve, or None for all
            
        Returns:
            any: Context value or dict of all context values
        """
        return self.ContextManager.GetContext(Key)
    
    def SetContext(self, Key, Value):
        """
        Set context data for a specific key.
        
        Args:
            Key (str): Context key
            Value (any): Context value
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.ContextManager.SetContext(Key, Value)
    
    def ClearContext(self, Key=None):
        """
        Clear context data, either all or for a specific key.
        
        Args:
            Key (str, optional): Context key to clear, or None for all
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.ContextManager.ClearContext(Key)
    
    def GetNamespacedContext(self, Namespace, Key=None):
        """
        Get context data within a namespace.
        
        Args:
            Namespace (str): Context namespace
            Key (str, optional): Context key within the namespace, or None for all
            
        Returns:
            any: Context value or dict of all namespace context values
        """
        return self.ContextManager.GetNamespacedContext(Namespace, Key)
    
    def SetNamespacedContext(self, Namespace, Key, Value):
        """
        Set context data within a namespace.
        
        Args:
            Namespace (str): Context namespace
            Key (str): Context key within the namespace
            Value (any): Context value
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.ContextManager.SetNamespacedContext(Namespace, Key, Value)
    
    def GenerateContinuityDocument(self, ResumedFrom=None, Final=False):
        """
        Generate a session continuity document.
        
        Args:
            ResumedFrom (str, optional): ID of session being resumed
            Final (bool, optional): Whether this is a final document for a completed session
            
        Returns:
            str: Path to the generated document
        """
        return self.ContinuityDocGenerator.GenerateContinuityDocument(ResumedFrom, Final)
    
    def GenerateCrashReport(self, SessionId):
        """
        Generate a crash report for a crashed session.
        
        Args:
            SessionId (str): ID of crashed session
            
        Returns:
            str: Path to the generated report
        """
        return self.ContinuityDocGenerator.GenerateCrashReport(SessionId)
    
    def GetSessionInfo(self, SessionId=None):
        """
        Get information about a session.
        
        Args:
            SessionId (str, optional): Session ID to get info for (defaults to current)
            
        Returns:
            dict: Session information
        """
        return self.SessionManager.GetSessionInfo(SessionId)
    
    def GetSessionHistory(self, Limit=10):
        """
        Get a list of recent sessions.
        
        Args:
            Limit (int, optional): Maximum number of sessions to retrieve
            
        Returns:
            list: List of session dictionaries
        """
        return self.SessionManager.GetSessionHistory(Limit)
    
    def GetSessionMessages(self, SessionId=None, Limit=50):
        """
        Get messages from a session.
        
        Args:
            SessionId (str, optional): Session ID to get messages from (defaults to current)
            Limit (int, optional): Maximum number of messages to retrieve
            
        Returns:
            list: List of message dictionaries
        """
        return self.SessionManager.GetSessionMessages(SessionId, Limit)
    
    def ValidateInput(self, Input, RuleType):
        """
        Validate input against a rule type.
        
        Args:
            Input (str): Input to validate
            RuleType (str): Type of rule to validate against
            
        Returns:
            tuple: (is_valid, error_message)
        """
        return self.ValidationManager.ValidateInput(Input, RuleType)
    
    def ValidateField(self, FieldName, Value):
        """
        Validate a specific field's value.
        
        Args:
            FieldName (str): Name of the field to validate
            Value (str): Value to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        return self.ValidationManager.ValidateField(FieldName, Value)
    
    def GetConfig(self, Key, DefaultValue=None):
        """
        Get a configuration value.
        
        Args:
            Key (str): Configuration key
            DefaultValue (Any, optional): Default value if key doesn't exist
            
        Returns:
            Any: Configuration value
        """
        return self.ConfigManager.GetConfig(Key, DefaultValue)
    
    def SetConfig(self, Key, Value, Type="TEXT", Description=None):
        """
        Set a configuration value.
        
        Args:
            Key (str): Configuration key
            Value (Any): Configuration value
            Type (str, optional): Value type (INTEGER, BOOLEAN, TEXT, FLOAT, JSON)
            Description (str, optional): Description of the configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.ConfigManager.SetConfig(Key, Value, Type, Description)
    
    def BackupState(self, BackupPath=None):
        """
        Create a backup of the current state.
        
        Args:
            BackupPath (str, optional): Path for the backup file
            
        Returns:
            str: Path to the backup file
        """
        # Backup the database
        if not BackupPath:
            Timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            BackupPath = f"State/Backup/state_backup_{Timestamp}"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(BackupPath), exist_ok=True)
        
        # Backup database
        DbBackupPath = f"{BackupPath}.db"
        self.DatabaseManager.CreateBackup(DbBackupPath)
        
        # Generate a continuity document
        DocPath = f"{BackupPath}_continuity.md"
        self.ContinuityDocGenerator.GenerateContinuityDocument(Final=False)
        
        self.Logger.info(f"State backup created at {BackupPath}")
        return BackupPath
    
    def CleanExit(self):
        """Clean up on normal exit."""
        # Let the session manager handle its exit logic
        if hasattr(self, 'SessionManager'):
            self.SessionManager.CleanExit()
        
        # Close database connections
        if hasattr(self, 'DatabaseManager'):
            self.DatabaseManager.CloseConnections()
            
        self.Logger.info("StateManager clean exit complete")

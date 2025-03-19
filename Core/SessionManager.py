# File: SessionManager.py
# Path: AIDEV-Hub/Core/SessionManager.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-18
# Last Modified: 2025-03-18  7:00PM
# Description: Manages session lifecycle and state persistence

import os
import json
import uuid
import shutil
import logging
import atexit
import threading
from datetime import datetime

class SessionManager:
    """
    Manages session lifecycle and state.
    
    This class is responsible for:
    - Starting, resuming, and ending sessions
    - Tracking session status
    - Managing session directories
    - Handling crash detection and recovery
    - Recording session messages
    """
    
    def __init__(self, DatabaseManager, ConfigManager):
        """Initialize the session manager."""
        self.DatabaseManager = DatabaseManager
        self.ConfigManager = ConfigManager
        self.SessionId = None
        self.LockFile = "State/session.lock"
        self.SessionLock = threading.RLock()
        
        # Set up logging
        self.Logger = logging.getLogger("SessionManager")
        self.Logger.setLevel(logging.INFO)
        
        # Create necessary directories
        self.EnsureDirectoriesExist()
        
        # Check for crashed sessions
        self.CheckForCrashedSessions()
        
        # Register exit handler for crash detection
        atexit.register(self.CleanExit)
        
        self.Logger.info("SessionManager initialized")
    
    def EnsureDirectoriesExist(self):
        """Create necessary directories if they don't exist."""
        # Get directory paths from config or use defaults
        self.ActiveSessionDir = self.ConfigManager.GetConfig("ACTIVE_SESSION_DIR", "Session/Active")
        self.CrashSessionDir = self.ConfigManager.GetConfig("CRASH_SESSION_DIR", "Session/Crashed")
        self.CompletedSessionDir = self.ConfigManager.GetConfig("COMPLETED_SESSION_DIR", "Session/Completed")
        
        # Create directories
        os.makedirs(self.ActiveSessionDir, exist_ok=True)
        os.makedirs(self.CrashSessionDir, exist_ok=True)
        os.makedirs(self.CompletedSessionDir, exist_ok=True)
        os.makedirs("Session/Temp", exist_ok=True)
        
        self.Logger.info("Session directories created")
    
    def CheckForCrashedSessions(self):
        """Check for and recover any crashed sessions."""
        # Check if a lock file exists
        if os.path.exists(self.LockFile):
            self.Logger.warning("Lock file found, checking for crashed sessions")
            
            with open(self.LockFile, 'r') as f:
                CrashedSessionId = f.read().strip()
            
            # Check if the session directory exists
            CrashedSessionDir = f"{self.ActiveSessionDir}/{CrashedSessionId}"
            if os.path.exists(CrashedSessionDir):
                self.Logger.warning(f"Found crashed session: {CrashedSessionId}")
                
                # Move to crashed sessions directory
                CrashedDir = f"{self.CrashSessionDir}/{CrashedSessionId}"
                os.makedirs(os.path.dirname(CrashedDir), exist_ok=True)
                shutil.move(CrashedSessionDir, CrashedDir)
                
                # Update database status
                self.UpdateSessionStatus(CrashedSessionId, "CRASHED")
                
                self.Logger.info(f"Crashed session {CrashedSessionId} recovered")
            
            # Remove lock file
            os.remove(self.LockFile)
            self.Logger.info("Lock file removed")
    
    def UpdateSessionStatus(self, SessionId, Status):
        """
        Update the status of a session in the database.
        
        Args:
            SessionId (str): Session ID to update
            Status (str): New status (ACTIVE, COMPLETED, CRASHED, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            Query = "UPDATE Sessions SET Status = ? WHERE SessionId = ?"
            RowsAffected = self.DatabaseManager.ExecuteNonQuery(Query, (Status, SessionId))
            
            self.Logger.info(f"Updated session {SessionId} status to {Status}")
            return RowsAffected > 0
        except Exception as e:
            self.Logger.error(f"Error updating session status: {e}")
            return False
    
    def CreateLockFile(self):
        """Create a lock file for crash detection."""
        with open(self.LockFile, 'w') as f:
            f.write(self.SessionId)
        self.Logger.info(f"Lock file created for session {self.SessionId}")
    
    def StartSession(self):
        """
        Start a new session.
        
        Returns:
            str: Session ID
        """
        with self.SessionLock:
            # End current session if active
            if self.SessionId:
                self.EndSession("Ended to start new session")
            
            # Generate new session ID
            self.SessionId = datetime.now().strftime("%Y%m%d%H%M%S")
            StartTime = datetime.now().isoformat()
            
            # Create session in database
            ColumnDict = {
                "SessionId": self.SessionId,
                "StartTime": StartTime,
                "Status": "ACTIVE"
            }
            
            self.DatabaseManager.InsertWithId("Sessions", ColumnDict)
            
            # Create session directory
            SessionDir = f"{self.ActiveSessionDir}/{self.SessionId}"
            os.makedirs(SessionDir, exist_ok=True)
            
            # Create lock file
            self.CreateLockFile()
            
            # Initialize state file
            self.SaveSessionState({
                "SessionId": self.SessionId,
                "StartTime": StartTime,
                "Messages": [],
                "Context": {},
                "LastModified": StartTime
            })
            
            self.Logger.info(f"Session {self.SessionId} started")
            
            # Log to database
            self.DatabaseManager.LogToDatabase(
                "INFO",
                "SessionManager",
                f"Session {self.SessionId} started",
                self.SessionId
            )
            
            return self.SessionId
    
    def ResumeSession(self, SessionId):
        """
        Resume a previously crashed session.
        
        Args:
            SessionId (str): ID of crashed session to resume
            
        Returns:
            str: New session ID
        """
        with self.SessionLock:
            # Check if the crashed session exists
            CrashedDir = f"{self.CrashSessionDir}/{SessionId}"
            if not os.path.exists(CrashedDir):
                self.Logger.error(f"Crashed session {SessionId} not found")
                return None
            
            # End current session if active
            if self.SessionId:
                self.EndSession("Ended to resume crashed session")
            
            # Create new session with reference to crashed one
            self.SessionId = SessionId + "_resumed_" + datetime.now().strftime("%Y%m%d%H%M%S")
            StartTime = datetime.now().isoformat()
            
            # Create session in database
            ColumnDict = {
                "SessionId": self.SessionId,
                "StartTime": StartTime,
                "Status": "ACTIVE"
            }
            
            self.DatabaseManager.InsertWithId("Sessions", ColumnDict)
            
            # Record relationship to crashed session
            RelationDict = {
                "ParentSessionId": SessionId,
                "ChildSessionId": self.SessionId,
                "RelationType": "RESUME"
            }
            
            self.DatabaseManager.InsertWithId("SessionRelationships", RelationDict)
            
            # Create session directory
            SessionDir = f"{self.ActiveSessionDir}/{self.SessionId}"
            os.makedirs(SessionDir, exist_ok=True)
            
            # Create lock file
            self.CreateLockFile()
            
            # Load state from crashed session
            StateFile = f"{CrashedDir}/state.json"
            if os.path.exists(StateFile):
                try:
                    with open(StateFile, 'r') as f:
                        CrashedState = json.load(f)
                    
                    # Initialize new state based on crashed session
                    NewState = dict(CrashedState)
                    NewState["OriginalSessionId"] = CrashedState["SessionId"]
                    NewState["SessionId"] = self.SessionId
                    NewState["StartTime"] = StartTime
                    NewState["ResumedFrom"] = SessionId
                    NewState["LastModified"] = StartTime
                    
                    # Save the new state
                    self.SaveSessionState(NewState)
                except Exception as e:
                    self.Logger.error(f"Error loading state from crashed session: {e}")
                    
                    # Create minimal state
                    self.SaveSessionState({
                        "SessionId": self.SessionId,
                        "StartTime": StartTime,
                        "Messages": [],
                        "Context": {},
                        "ResumedFrom": SessionId,
                        "LastModified": StartTime
                    })
            else:
                # Create minimal state
                self.SaveSessionState({
                    "SessionId": self.SessionId,
                    "StartTime": StartTime,
                    "Messages": [],
                    "Context": {},
                    "ResumedFrom": SessionId,
                    "LastModified": StartTime
                })
            
            self.Logger.info(f"Resumed session {SessionId} as new session {self.SessionId}")
            
            # Log to database
            self.DatabaseManager.LogToDatabase(
                "INFO",
                "SessionManager",
                f"Resumed session {SessionId} as new session {self.SessionId}",
                self.SessionId,
                {"ResumedFrom": SessionId}
            )
            
            return self.SessionId
    
    def EndSession(self, Summary=None):
        """
        End the current session normally.
        
        Args:
            Summary (str, optional): Summary of session
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.SessionLock:
            if not self.SessionId:
                self.Logger.warning("No active session to end")
                return False
            
            try:
                # Update session in database
                EndTime = datetime.now().isoformat()
                
                UpdateDict = {
                    "EndTime": EndTime,
                    "Status": "COMPLETED"
                }
                
                if Summary:
                    UpdateDict["Summary"] = Summary
                
                WhereClause = "SessionId = ?"
                WhereParams = (self.SessionId,)
                
                self.DatabaseManager.Update("Sessions", UpdateDict, WhereClause, WhereParams)
                
                # Update state file
                StateFile = f"{self.ActiveSessionDir}/{self.SessionId}/state.json"
                if os.path.exists(StateFile):
                    try:
                        with open(StateFile, 'r') as f:
                            State = json.load(f)
                        
                        # Update state
                        State["EndTime"] = EndTime
                        State["Status"] = "COMPLETED"
                        State["LastModified"] = EndTime
                        
                        if Summary:
                            State["Summary"] = Summary
                        
                        # Save updated state
                        with open(StateFile, 'w') as f:
                            json.dump(State, f, indent=2)
                    except Exception as e:
                        self.Logger.error(f"Error updating state file: {e}")
                
                # Move session directory to completed
                ActiveDir = f"{self.ActiveSessionDir}/{self.SessionId}"
                CompletedDir = f"{self.CompletedSessionDir}/{self.SessionId}"
                
                if os.path.exists(ActiveDir):
                    os.makedirs(os.path.dirname(CompletedDir), exist_ok=True)
                    shutil.move(ActiveDir, CompletedDir)
                
                # Remove lock file if it exists
                if os.path.exists(self.LockFile):
                    os.remove(self.LockFile)
                
                # Log to database
                self.DatabaseManager.LogToDatabase(
                    "INFO",
                    "SessionManager",
                    f"Session {self.SessionId} ended",
                    self.SessionId,
                    {"Summary": Summary} if Summary else None
                )
                
                SessionId = self.SessionId
                self.SessionId = None
                
                self.Logger.info(f"Session {SessionId} ended")
                return True
            except Exception as e:
                self.Logger.error(f"Error ending session: {e}")
                return False
    
    def SaveSessionState(self, State):
        """
        Save session state to a file.
        
        Args:
            State (dict): State data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.SessionId:
                self.Logger.warning("No active session to save state for")
                return False
            
            # Update last modified timestamp
            State["LastModified"] = datetime.now().isoformat()
            
            # Save to file
            StateFile = f"{self.ActiveSessionDir}/{self.SessionId}/state.json"
            with open(StateFile, 'w') as f:
                json.dump(State, f, indent=2)
            
            # Create snapshot in database
            SnapshotId = str(uuid.uuid4())
            
            ColumnDict = {
                "SnapshotId": SnapshotId,
                "SessionId": self.SessionId,
                "Timestamp": State["LastModified"],
                "StateData": json.dumps(State)
            }
            
            self.DatabaseManager.InsertWithId("StateSnapshots", ColumnDict)
            
            self.Logger.debug(f"State saved for session {self.SessionId}")
            return True
        except Exception as e:
            self.Logger.error(f"Error saving session state: {e}")
            return False
    
    def LoadSessionState(self):
        """
        Load current session state from file.
        
        Returns:
            dict: Session state or None if not found
        """
        try:
            if not self.SessionId:
                self.Logger.warning("No active session to load state for")
                return None
            
            StateFile = f"{self.ActiveSessionDir}/{self.SessionId}/state.json"
            if os.path.exists(StateFile):
                with open(StateFile, 'r') as f:
                    return json.load(f)
            else:
                self.Logger.warning(f"State file not found for session {self.SessionId}")
                return None
        except Exception as e:
            self.Logger.error(f"Error loading session state: {e}")
            return None
    
    def RecordMessage(self, Source, Content):
        """
        Record a message in the conversation.
        
        Args:
            Source (str): Source of the message (e.g., "User", "Assistant")
            Content (str): Message content
            
        Returns:
            str: Message ID if successful, None otherwise
        """
        try:
            if not self.SessionId:
                self.Logger.warning("No active session to record message for")
                return None
            
            MessageId = str(uuid.uuid4())
            Timestamp = datetime.now().isoformat()
            
            # Add to database
            ColumnDict = {
                "MessageId": MessageId,
                "SessionId": self.SessionId,
                "Timestamp": Timestamp,
                "Source": Source,
                "Content": Content
            }
            
            self.DatabaseManager.InsertWithId("Conversations", ColumnDict)
            
            # Add to current state
            State = self.LoadSessionState()
            if State:
                if "Messages" not in State:
                    State["Messages"] = []
                
                Message = {
                    "MessageId": MessageId,
                    "Timestamp": Timestamp,
                    "Source": Source,
                    "Content": Content
                }
                
                State["Messages"].append(Message)
                self.SaveSessionState(State)
            
            self.Logger.info(f"Message recorded from {Source} with ID {MessageId}")
            return MessageId
        except Exception as e:
            self.Logger.error(f"Error recording message: {e}")
            return None
    
    def GetSessionMessages(self, SessionId=None, Limit=50):
        """
        Get messages from a session.
        
        Args:
            SessionId (str, optional): Session ID to get messages from (defaults to current)
            Limit (int, optional): Maximum number of messages to retrieve
            
        Returns:
            list: List of message dictionaries
        """
        try:
            if not SessionId and not self.SessionId:
                self.Logger.warning("No session specified")
                return []
            
            TargetSessionId = SessionId if SessionId else self.SessionId
            
            Query = """
                SELECT MessageId, Timestamp, Source, Content
                FROM Conversations
                WHERE SessionId = ?
                ORDER BY Timestamp ASC
                LIMIT ?
            """
            
            Messages = self.DatabaseManager.ExecuteQuery(Query, (TargetSessionId, Limit))
            
            return Messages
        except Exception as e:
            self.Logger.error(f"Error getting session messages: {e}")
            return []
    
    def GetSessionInfo(self, SessionId=None):
        """
        Get information about a session.
        
        Args:
            SessionId (str, optional): Session ID to get info for (defaults to current)
            
        Returns:
            dict: Session information
        """
        try:
            if not SessionId and not self.SessionId:
                self.Logger.warning("No session specified")
                return None
            
            TargetSessionId = SessionId if SessionId else self.SessionId
            
            Query = """
                SELECT SessionId, StartTime, EndTime, Status, Summary
                FROM Sessions
                WHERE SessionId = ?
            """
            
            Sessions = self.DatabaseManager.ExecuteQuery(Query, (TargetSessionId,))
            
            if Sessions:
                Session = Sessions[0]
                
                # Get message count
                CountQuery = """
                    SELECT COUNT(*) as MessageCount
                    FROM Conversations
                    WHERE SessionId = ?
                """
                
                CountResult = self.DatabaseManager.ExecuteQuery(CountQuery, (TargetSessionId,))
                MessageCount = CountResult[0]["MessageCount"] if CountResult else 0
                
                # Add message count to result
                Session["MessageCount"] = MessageCount
                
                # Check if this is a resumed session
                RelationQuery = """
                    SELECT ParentSessionId
                    FROM SessionRelationships
                    WHERE ChildSessionId = ? AND RelationType = 'RESUME'
                """
                
                RelationResult = self.DatabaseManager.ExecuteQuery(RelationQuery, (TargetSessionId,))
                if RelationResult:
                    Session["ResumedFrom"] = RelationResult[0]["ParentSessionId"]
                
                return Session
            
            return None
        except Exception as e:
            self.Logger.error(f"Error getting session info: {e}")
            return None
    
    def GetSessionHistory(self, Limit=10):
        """
        Get a list of recent sessions.
        
        Args:
            Limit (int, optional): Maximum number of sessions to retrieve
            
        Returns:
            list: List of session dictionaries
        """
        try:
            Query = """
                SELECT SessionId, StartTime, EndTime, Status, Summary
                FROM Sessions
                ORDER BY StartTime DESC
                LIMIT ?
            """
            
            Sessions = self.DatabaseManager.ExecuteQuery(Query, (Limit,))
            
            return Sessions
        except Exception as e:
            self.Logger.error(f"Error getting session history: {e}")
            return []
    
    def GetCrashedSessions(self):
        """
        Get a list of crashed sessions.
        
        Returns:
            list: List of crashed session dictionaries
        """
        try:
            Query = """
                SELECT SessionId, StartTime, EndTime, Status, Summary
                FROM Sessions
                WHERE Status = 'CRASHED'
                ORDER BY StartTime DESC
            """
            
            Sessions = self.DatabaseManager.ExecuteQuery(Query)
            
            return Sessions
        except Exception as e:
            self.Logger.error(f"Error getting crashed sessions: {e}")
            return []
    
    def CleanExit(self):
        """Clean up on normal exit."""
        if self.SessionId:
            self.Logger.info(f"Clean exit for session {self.SessionId}")
            
            # Remove lock file if it exists
            if os.path.exists(self.LockFile):
                os.remove(self.LockFile)
                self.Logger.info("Lock file removed during clean exit")
    
    def GetSessionStateSnapshots(self, SessionId=None, Limit=10):
        """
        Get state snapshots for a session.
        
        Args:
            SessionId (str, optional): Session ID to get snapshots for (defaults to current)
            Limit (int, optional): Maximum number of snapshots to retrieve
            
        Returns:
            list: List of snapshot dictionaries
        """
        try:
            if not SessionId and not self.SessionId:
                self.Logger.warning("No session specified")
                return []
            
            TargetSessionId = SessionId if SessionId else self.SessionId
            
            Query = """
                SELECT SnapshotId, SessionId, Timestamp
                FROM StateSnapshots
                WHERE SessionId = ?
                ORDER BY Timestamp DESC
                LIMIT ?
            """
            
            Snapshots = self.DatabaseManager.ExecuteQuery(Query, (TargetSessionId, Limit))
            
            return Snapshots
        except Exception as e:
            self.Logger.error(f"Error getting session state snapshots: {e}")
            return []
    
    def GetSessionStateSnapshot(self, SnapshotId):
        """
        Get a specific state snapshot.
        
        Args:
            SnapshotId (str): ID of the snapshot to retrieve
            
        Returns:
            dict: State snapshot
        """
        try:
            Query = """
                SELECT SnapshotId, SessionId, Timestamp, StateData
                FROM StateSnapshots
                WHERE SnapshotId = ?
            """
            
            Snapshots = self.DatabaseManager.ExecuteQuery(Query, (SnapshotId,))
            
            if Snapshots:
                Snapshot = Snapshots[0]
                
                # Parse state data
                if "StateData" in Snapshot:
                    try:
                        Snapshot["State"] = json.loads(Snapshot["StateData"])
                        # Remove the raw data to avoid duplication
                        del Snapshot["StateData"]
                    except:
                        pass
                
                return Snapshot
            
            return None
        except Exception as e:
            self.Logger.error(f"Error getting state snapshot: {e}")
            return None
    
    def GetCurrentSessionState(self):
        """
        Get the current session state.
        
        Returns:
            dict: Current session state or None if no active session
        """
        if not self.SessionId:
            return None
        
        return self.LoadSessionState()
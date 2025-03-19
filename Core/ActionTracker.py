# File: ActionTracker.py
# Path: AIDEV-Hub/Core/ActionTracker.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-18
# Last Modified: 2025-03-18  7:15PM
# Description: Tracks and manages actions within sessions

import uuid
import json
import logging
import threading
from datetime import datetime

class ActionTracker:
    """
    Tracks and manages actions within sessions.
    
    This class is responsible for:
    - Recording actions and their parameters
    - Tracking action execution status
    - Associating actions with sessions
    - Providing execution history
    """
    
    def __init__(self, DatabaseManager, SessionManager):
        """Initialize the action tracker."""
        self.DatabaseManager = DatabaseManager
        self.SessionManager = SessionManager
        self.ActionLock = threading.RLock()
        
        # Set up logging
        self.Logger = logging.getLogger("ActionTracker")
        self.Logger.setLevel(logging.INFO)
        
        self.Logger.info("ActionTracker initialized")
    
    def RecordAction(self, ActionType, Params=None):
        """
        Record an action and its parameters.
        
        Args:
            ActionType (str): Type of action being performed
            Params (dict, optional): Parameters for the action
            
        Returns:
            str: Action ID if successful, None otherwise
        """
        try:
            SessionId = self.SessionManager.SessionId
            if not SessionId:
                self.Logger.warning("No active session to record action for")
                return None
            
            ActionId = str(uuid.uuid4())
            StartTime = datetime.now().isoformat()
            
            # Add to database
            ColumnDict = {
                "ActionId": ActionId,
                "SessionId": SessionId,
                "ActionType": ActionType,
                "StartTime": StartTime,
                "Status": "STARTED",
                "Params": json.dumps(Params) if Params else None
            }
            
            with self.ActionLock:
                self.DatabaseManager.InsertWithId("Actions", ColumnDict)
            
            # Update session state
            State = self.SessionManager.LoadSessionState()
            if State:
                if "Actions" not in State:
                    State["Actions"] = []
                
                Action = {
                    "ActionId": ActionId,
                    "ActionType": ActionType,
                    "StartTime": StartTime,
                    "Status": "STARTED",
                    "Params": Params,
                    "Result": None
                }
                
                State["Actions"].append(Action)
                self.SessionManager.SaveSessionState(State)
            
            self.Logger.info(f"Action {ActionType} recorded with ID {ActionId}")
            
            # Log to database
            self.DatabaseManager.LogToDatabase(
                "INFO",
                "ActionTracker",
                f"Action {ActionType} started",
                SessionId,
                {"ActionId": ActionId, "Params": Params}
            )
            
            return ActionId
        except Exception as e:
            self.Logger.error(f"Error recording action: {e}")
            return None
    
    def CompleteAction(self, ActionId, Result=None, Status="COMPLETED"):
        """
        Mark an action as completed with its result.
        
        Args:
            ActionId (str): ID of the action to complete
            Result (any, optional): Result of the action
            Status (str, optional): Status of the action (COMPLETED, FAILED, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            SessionId = self.SessionManager.SessionId
            if not SessionId:
                self.Logger.warning("No active session to complete action for")
                return False
            
            EndTime = datetime.now().isoformat()
            
            # Update database
            UpdateDict = {
                "EndTime": EndTime,
                "Status": Status,
                "Result": json.dumps(Result) if Result is not None else None
            }
            
            WhereClause = "ActionId = ?"
            WhereParams = (ActionId,)
            
            with self.ActionLock:
                self.DatabaseManager.Update("Actions", UpdateDict, WhereClause, WhereParams)
            
            # Update session state
            State = self.SessionManager.LoadSessionState()
            if State and "Actions" in State:
                for Action in State["Actions"]:
                    if Action["ActionId"] == ActionId:
                        Action["EndTime"] = EndTime
                        Action["Status"] = Status
                        Action["Result"] = Result
                        break
                
                self.SessionManager.SaveSessionState(State)
            
            self.Logger.info(f"Action {ActionId} completed with status {Status}")
            
            # Log to database
            self.DatabaseManager.LogToDatabase(
                "INFO",
                "ActionTracker",
                f"Action {ActionId} completed with status {Status}",
                SessionId,
                {"Result": Result}
            )
            
            return True
        except Exception as e:
            self.Logger.error(f"Error completing action: {e}")
            return False
    
    def ExecuteAction(self, ActionType, ActionFunction, Params=None):
        """
        Execute an action with tracking.
        
        This wraps a function call with action tracking, making it possible
        to recover from crashes during action execution.
        
        Args:
            ActionType (str): Type of action being performed
            ActionFunction (callable): Function to execute
            Params (dict, optional): Parameters for the function
            
        Returns:
            tuple: (success, result, action_id)
        """
        try:
            # Record the action
            ActionId = self.RecordAction(ActionType, Params)
            if not ActionId:
                return (False, {"Error": "Failed to record action"}, None)
            
            try:
                # Execute the function
                if Params:
                    Result = ActionFunction(**Params)
                else:
                    Result = ActionFunction()
                
                # Record success
                self.CompleteAction(ActionId, Result=Result)
                return (True, Result, ActionId)
            except Exception as e:
                # Record failure
                ErrorDetails = {
                    "Error": str(e),
                    "ErrorType": type(e).__name__
                }
                self.CompleteAction(ActionId, Result=ErrorDetails, Status="FAILED")
                self.Logger.error(f"Action {ActionType} failed: {str(e)}")
                return (False, ErrorDetails, ActionId)
        except Exception as e:
            self.Logger.error(f"Error executing action: {e}")
            return (False, {"Error": str(e)}, None)
    
    def GetActionById(self, ActionId):
        """
        Get an action by its ID.
        
        Args:
            ActionId (str): ID of the action to retrieve
            
        Returns:
            dict: Action information
        """
        try:
            Query = """
                SELECT ActionId, SessionId, ActionType, StartTime, EndTime, Status, Params, Result
                FROM Actions
                WHERE ActionId = ?
            """
            
            Actions = self.DatabaseManager.ExecuteQuery(Query, (ActionId,))
            
            if Actions:
                Action = Actions[0]
                
                # Parse JSON fields
                if Action["Params"]:
                    try:
                        Action["Params"] = json.loads(Action["Params"])
                    except:
                        pass
                
                if Action["Result"]:
                    try:
                        Action["Result"] = json.loads(Action["Result"])
                    except:
                        pass
                
                return Action
            
            return None
        except Exception as e:
            self.Logger.error(f"Error getting action by ID: {e}")
            return None
    
    def GetSessionActions(self, SessionId=None, Limit=20):
        """
        Get actions for a session.
        
        Args:
            SessionId (str, optional): Session ID to get actions for (defaults to current)
            Limit (int, optional): Maximum number of actions to retrieve
            
        Returns:
            list: List of action dictionaries
        """
        try:
            if not SessionId and not self.SessionManager.SessionId:
                self.Logger.warning("No session specified")
                return []
            
            TargetSessionId = SessionId if SessionId else self.SessionManager.SessionId
            
            Query = """
                SELECT ActionId, ActionType, StartTime, EndTime, Status, Params, Result
                FROM Actions
                WHERE SessionId = ?
                ORDER BY StartTime DESC
                LIMIT ?
            """
            
            Actions = self.DatabaseManager.ExecuteQuery(Query, (TargetSessionId, Limit))
            
            # Parse JSON fields
            for Action in Actions:
                if Action["Params"]:
                    try:
                        Action["Params"] = json.loads(Action["Params"])
                    except:
                        pass
                
                if Action["Result"]:
                    try:
                        Action["Result"] = json.loads(Action["Result"])
                    except:
                        pass
            
            return Actions
        except Exception as e:
            self.Logger.error(f"Error getting session actions: {e}")
            return []
    
    def GetActionsByType(self, ActionType, Limit=20):
        """
        Get actions by type.
        
        Args:
            ActionType (str): Type of actions to retrieve
            Limit (int, optional): Maximum number of actions to retrieve
            
        Returns:
            list: List of action dictionaries
        """
        try:
            Query = """
                SELECT ActionId, SessionId, ActionType, StartTime, EndTime, Status, Params, Result
                FROM Actions
                WHERE ActionType = ?
                ORDER BY StartTime DESC
                LIMIT ?
            """
            
            Actions = self.DatabaseManager.ExecuteQuery(Query, (ActionType, Limit))
            
            # Parse JSON fields
            for Action in Actions:
                if Action["Params"]:
                    try:
                        Action["Params"] = json.loads(Action["Params"])
                    except:
                        pass
                
                if Action["Result"]:
                    try:
                        Action["Result"] = json.loads(Action["Result"])
                    except:
                        pass
            
            return Actions
        except Exception as e:
            self.Logger.error(f"Error getting actions by type: {e}")
            return []
    
    def GetPendingActions(self, SessionId=None):
        """
        Get pending (non-completed) actions for a session.
        
        Args:
            SessionId (str, optional): Session ID to get actions for (defaults to current)
            
        Returns:
            list: List of pending action dictionaries
        """
        try:
            if not SessionId and not self.SessionManager.SessionId:
                self.Logger.warning("No session specified")
                return []
            
            TargetSessionId = SessionId if SessionId else self.SessionManager.SessionId
            
            Query = """
                SELECT ActionId, ActionType, StartTime, Status, Params
                FROM Actions
                WHERE SessionId = ? AND Status = 'STARTED'
                ORDER BY StartTime ASC
            """
            
            Actions = self.DatabaseManager.ExecuteQuery(Query, (TargetSessionId,))
            
            # Parse JSON fields
            for Action in Actions:
                if Action["Params"]:
                    try:
                        Action["Params"] = json.loads(Action["Params"])
                    except:
                        pass
            
            return Actions
        except Exception as e:
            self.Logger.error(f"Error getting pending actions: {e}")
            return []
    
    def CancelAction(self, ActionId):
        """
        Cancel a pending action.
        
        Args:
            ActionId (str): ID of the action to cancel
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            SessionId = self.SessionManager.SessionId
            if not SessionId:
                self.Logger.warning("No active session to cancel action for")
                return False
            
            # Check if action exists and is pending
            Query = """
                SELECT Status
                FROM Actions
                WHERE ActionId = ?
            """
            
            Actions = self.DatabaseManager.ExecuteQuery(Query, (ActionId,))
            if not Actions or Actions[0]["Status"] != "STARTED":
                self.Logger.warning(f"Action {ActionId} is not pending or does not exist")
                return False
            
            # Update as canceled
            EndTime = datetime.now().isoformat()
            
            UpdateDict = {
                "EndTime": EndTime,
                "Status": "CANCELED",
                "Result": json.dumps({"Reason": "Canceled by user"})
            }
            
            WhereClause = "ActionId = ?"
            WhereParams = (ActionId,)
            
            with self.ActionLock:
                self.DatabaseManager.Update("Actions", UpdateDict, WhereClause, WhereParams)
            
            # Update session state
            State = self.SessionManager.LoadSessionState()
            if State and "Actions" in State:
                for Action in State["Actions"]:
                    if Action["ActionId"] == ActionId:
                        Action["EndTime"] = EndTime
                        Action["Status"] = "CANCELED"
                        Action["Result"] = {"Reason": "Canceled by user"}
                        break
                
                self.SessionManager.SaveSessionState(State)
            
            self.Logger.info(f"Action {ActionId} canceled")
            
            # Log to database
            self.DatabaseManager.LogToDatabase(
                "INFO",
                "ActionTracker",
                f"Action {ActionId} canceled",
                SessionId
            )
            
            return True
        except Exception as e:
            self.Logger.error(f"Error canceling action: {e}")
            return False
    
    def RetryAction(self, ActionId):
        """
        Retry a failed action.
        
        Args:
            ActionId (str): ID of the action to retry
            
        Returns:
            str: New action ID if successful, None otherwise
        """
        try:
            SessionId = self.SessionManager.SessionId
            if not SessionId:
                self.Logger.warning("No active session to retry action for")
                return None
            
            # Get the original action
            OriginalAction = self.GetActionById(ActionId)
            if not OriginalAction:
                self.Logger.warning(f"Action {ActionId} not found")
                return None
            
            # Create a new action with the same type and parameters
            ActionType = OriginalAction["ActionType"]
            Params = OriginalAction["Params"]
            
            # Record that this is a retry
            if Params:
                Params["RetryOf"] = ActionId
            else:
                Params = {"RetryOf": ActionId}
            
            # Record the new action
            NewActionId = self.RecordAction(ActionType, Params)
            
            self.Logger.info(f"Action {ActionId} retried as {NewActionId}")
            
            # Log to database
            self.DatabaseManager.LogToDatabase(
                "INFO",
                "ActionTracker",
                f"Action {ActionId} retried as {NewActionId}",
                SessionId
            )
            
            return NewActionId
        except Exception as e:
            self.Logger.error(f"Error retrying action: {e}")
            return None
    
    def GetActionStats(self, SessionId=None):
        """
        Get action statistics for a session.
        
        Args:
            SessionId (str, optional): Session ID to get stats for (defaults to current)
            
        Returns:
            dict: Action statistics
        """
        try:
            if not SessionId and not self.SessionManager.SessionId:
                self.Logger.warning("No session specified")
                return {}
            
            TargetSessionId = SessionId if SessionId else self.SessionManager.SessionId
            
            # Get total count
            CountQuery = """
                SELECT COUNT(*) as TotalCount
                FROM Actions
                WHERE SessionId = ?
            """
            
            CountResult = self.DatabaseManager.ExecuteQuery(CountQuery, (TargetSessionId,))
            TotalCount = CountResult[0]["TotalCount"] if CountResult else 0
            
            # Get status counts
            StatusQuery = """
                SELECT Status, COUNT(*) as Count
                FROM Actions
                WHERE SessionId = ?
                GROUP BY Status
            """
            
            StatusResult = self.DatabaseManager.ExecuteQuery(StatusQuery, (TargetSessionId,))
            
            StatusCounts = {}
            for Status in StatusResult:
                StatusCounts[Status["Status"]] = Status["Count"]
            
            # Get type counts
            TypeQuery = """
                SELECT ActionType, COUNT(*) as Count
                FROM Actions
                WHERE SessionId = ?
                GROUP BY ActionType
            """
            
            TypeResult = self.DatabaseManager.ExecuteQuery(TypeQuery, (TargetSessionId,))
            
            TypeCounts = {}
            for Type in TypeResult:
                TypeCounts[Type["ActionType"]] = Type["Count"]
            
            return {
                "TotalCount": TotalCount,
                "StatusCounts": StatusCounts,
                "TypeCounts": TypeCounts
            }
        except Exception as e:
            self.Logger.error(f"Error getting action stats: {e}")
            return {}

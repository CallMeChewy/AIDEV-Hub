# File: ContextManager.py
# Path: AIDEV-Hub/Core/ContextManager.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-18
# Last Modified: 2025-03-18  7:30PM
# Description: Manages context data within sessions

import json
import logging
import threading
from datetime import datetime

class ContextManager:
    """
    Manages context data within sessions.
    
    This class is responsible for:
    - Storing and retrieving context data
    - Maintaining context across session interactions
    - Managing context scopes and namespaces
    - Persisting context to the database
    """
    
    def __init__(self, DatabaseManager, SessionManager):
        """Initialize the context manager."""
        self.DatabaseManager = DatabaseManager
        self.SessionManager = SessionManager
        self.ContextLock = threading.RLock()
        self.ContextCache = {}
        
        # Set up logging
        self.Logger = logging.getLogger("ContextManager")
        self.Logger.setLevel(logging.INFO)
        
        self.Logger.info("ContextManager initialized")
    
    def GetContext(self, Key=None):
        """
        Get context data, either all or for a specific key.
        
        Args:
            Key (str, optional): Context key to retrieve, or None for all
            
        Returns:
            any: Context value or dict of all context values
        """
        try:
            SessionId = self.SessionManager.SessionId
            if not SessionId:
                self.Logger.warning("No active session to get context for")
                return {} if Key is None else None
            
            # Load session state to get context
            with self.ContextLock:
                # Check if we have a cache for this session
                if SessionId not in self.ContextCache:
                    State = self.SessionManager.LoadSessionState()
                    if State and "Context" in State:
                        self.ContextCache[SessionId] = dict(State["Context"])
                    else:
                        self.ContextCache[SessionId] = {}
                
                # Return the requested context
                if Key is None:
                    return dict(self.ContextCache[SessionId])
                else:
                    return self.ContextCache[SessionId].get(Key)
        except Exception as e:
            self.Logger.error(f"Error getting context: {e}")
            return {} if Key is None else None
    
    def SetContext(self, Key, Value):
        """
        Set context data for a specific key.
        
        Args:
            Key (str): Context key
            Value (any): Context value
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            SessionId = self.SessionManager.SessionId
            if not SessionId:
                self.Logger.warning("No active session to set context for")
                return False
            
            # Load session state
            State = self.SessionManager.LoadSessionState()
            if not State:
                self.Logger.warning("Could not load session state")
                return False
            
            # Update context in state
            if "Context" not in State:
                State["Context"] = {}
            
            State["Context"][Key] = Value
            
            # Save updated state
            self.SessionManager.SaveSessionState(State)
            
            # Update cache
            with self.ContextLock:
                if SessionId not in self.ContextCache:
                    self.ContextCache[SessionId] = {}
                
                self.ContextCache[SessionId][Key] = Value
            
            self.Logger.info(f"Context set for key '{Key}'")
            
            # Log to database
            self.DatabaseManager.LogToDatabase(
                "INFO",
                "ContextManager",
                f"Context set for key '{Key}'",
                SessionId
            )
            
            return True
        except Exception as e:
            self.Logger.error(f"Error setting context: {e}")
            return False
    
    def ClearContext(self, Key=None):
        """
        Clear context data, either all or for a specific key.
        
        Args:
            Key (str, optional): Context key to clear, or None for all
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            SessionId = self.SessionManager.SessionId
            if not SessionId:
                self.Logger.warning("No active session to clear context for")
                return False
            
            # Load session state
            State = self.SessionManager.LoadSessionState()
            if not State or "Context" not in State:
                self.Logger.warning("Could not load session state or no context exists")
                return False
            
            # Update context in state
            if Key is None:
                # Clear all context
                State["Context"] = {}
                self.Logger.info("All context cleared")
                LogMessage = "All context cleared"
            else:
                # Clear specific key
                if Key in State["Context"]:
                    del State["Context"][Key]
                    self.Logger.info(f"Context cleared for key '{Key}'")
                    LogMessage = f"Context cleared for key '{Key}'"
                else:
                    self.Logger.warning(f"Context key '{Key}' not found")
                    return False
            
            # Save updated state
            self.SessionManager.SaveSessionState(State)
            
            # Update cache
            with self.ContextLock:
                if SessionId in self.ContextCache:
                    if Key is None:
                        self.ContextCache[SessionId] = {}
                    elif Key in self.ContextCache[SessionId]:
                        del self.ContextCache[SessionId][Key]
            
            # Log to database
            self.DatabaseManager.LogToDatabase(
                "INFO",
                "ContextManager",
                LogMessage,
                SessionId
            )
            
            return True
        except Exception as e:
            self.Logger.error(f"Error clearing context: {e}")
            return False
    
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
        try:
            NamespacedKey = f"{Namespace}.{Key}"
            return self.SetContext(NamespacedKey, Value)
        except Exception as e:
            self.Logger.error(f"Error setting namespaced context: {e}")
            return False
    
    def GetNamespacedContext(self, Namespace, Key=None):
        """
        Get context data within a namespace.
        
        Args:
            Namespace (str): Context namespace
            Key (str, optional): Context key within the namespace, or None for all
            
        Returns:
            any: Context value or dict of all namespace context values
        """
        try:
            if Key is not None:
                NamespacedKey = f"{Namespace}.{Key}"
                return self.GetContext(NamespacedKey)
            else:
                # Get all context
                AllContext = self.GetContext()
                
                # Filter by namespace
                NamespacePrefix = f"{Namespace}."
                NamespacedContext = {}
                
                for FullKey, Value in AllContext.items():
                    if FullKey.startswith(NamespacePrefix):
                        # Extract the key without the namespace
                        ShortKey = FullKey[len(NamespacePrefix):]
                        NamespacedContext[ShortKey] = Value
                
                return NamespacedContext
        except Exception as e:
            self.Logger.error(f"Error getting namespaced context: {e}")
            return {} if Key is None else None
    
    def ClearNamespacedContext(self, Namespace, Key=None):
        """
        Clear context data within a namespace.
        
        Args:
            Namespace (str): Context namespace
            Key (str, optional): Context key within the namespace, or None for all
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if Key is not None:
                NamespacedKey = f"{Namespace}.{Key}"
                return self.ClearContext(NamespacedKey)
            else:
                # Get all context
                AllContext = self.GetContext()
                
                # Filter by namespace
                NamespacePrefix = f"{Namespace}."
                KeysToRemove = []
                
                for FullKey in AllContext.keys():
                    if FullKey.startswith(NamespacePrefix):
                        KeysToRemove.append(FullKey)
                
                # Remove each key
                Success = True
                for Key in KeysToRemove:
                    if not self.ClearContext(Key):
                        Success = False
                
                return Success
        except Exception as e:
            self.Logger.error(f"Error clearing namespaced context: {e}")
            return False
    
    def GetContextNamespaces(self):
        """
        Get a list of all context namespaces.
        
        Returns:
            list: List of namespace names
        """
        try:
            # Get all context
            AllContext = self.GetContext()
            
            # Extract namespaces
            Namespaces = set()
            
            for Key in AllContext.keys():
                if "." in Key:
                    Namespace = Key.split(".", 1)[0]
                    Namespaces.add(Namespace)
            
            return sorted(list(Namespaces))
        except Exception as e:
            self.Logger.error(f"Error getting context namespaces: {e}")
            return []
    
    def MergeContext(self, ContextDict):
        """
        Merge context data from a dictionary.
        
        Args:
            ContextDict (dict): Dictionary of context key-value pairs to merge
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            SessionId = self.SessionManager.SessionId
            if not SessionId:
                self.Logger.warning("No active session to merge context for")
                return False
            
            # Load session state
            State = self.SessionManager.LoadSessionState()
            if not State:
                self.Logger.warning("Could not load session state")
                return False
            
            # Update context in state
            if "Context" not in State:
                State["Context"] = {}
            
            # Merge the dictionaries
            State["Context"].update(ContextDict)
            
            # Save updated state
            self.SessionManager.SaveSessionState(State)
            
            # Update cache
            with self.ContextLock:
                if SessionId not in self.ContextCache:
                    self.ContextCache[SessionId] = {}
                
                self.ContextCache[SessionId].update(ContextDict)
            
            self.Logger.info(f"Merged {len(ContextDict)} context items")
            
            # Log to database
            self.DatabaseManager.LogToDatabase(
                "INFO",
                "ContextManager",
                f"Merged {len(ContextDict)} context items",
                SessionId
            )
            
            return True
        except Exception as e:
            self.Logger.error(f"Error merging context: {e}")
            return False
    
    def UpdateMergedContext(self, ContextDict, Key):
        """
        Update a specific key within a merged context.
        
        Args:
            ContextDict (dict): Dictionary of new merged context
            Key (str): Key to update
            
        Returns:
            dict: Updated context dictionary
        """
        try:
            AllContext = self.GetContext(Key)
            if not AllContext:
                return ContextDict
            
            # If the context is a dict, merge it
            if isinstance(AllContext, dict) and isinstance(ContextDict, dict):
                Result = dict(AllContext)
                Result.update(ContextDict)
                self.SetContext(Key, Result)
                return Result
            else:
                # Otherwise, just set the new value
                self.SetContext(Key, ContextDict)
                return ContextDict
        except Exception as e:
            self.Logger.error(f"Error updating merged context: {e}")
            return ContextDict
    
    def ImportContext(self, ContextDict):
        """
        Import context data from a dictionary.
        
        Args:
            ContextDict (dict): Dictionary of context data to import
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            SessionId = self.SessionManager.SessionId
            if not SessionId:
                self.Logger.warning("No active session to import context for")
                return False
            
            # Load session state
            State = self.SessionManager.LoadSessionState()
            if not State:
                self.Logger.warning("Could not load session state")
                return False
            
            # Replace context in state
            State["Context"] = dict(ContextDict)
            
            # Save updated state
            self.SessionManager.SaveSessionState(State)
            
            # Update cache
            with self.ContextLock:
                self.ContextCache[SessionId] = dict(ContextDict)
            
            self.Logger.info(f"Imported {len(ContextDict)} context items")
            
            # Log to database
            self.DatabaseManager.LogToDatabase(
                "INFO",
                "ContextManager",
                f"Imported {len(ContextDict)} context items",
                SessionId
            )
            
            return True
        except Exception as e:
            self.Logger.error(f"Error importing context: {e}")
            return False
    
    def ExportContext(self):
        """
        Export all context data.
        
        Returns:
            dict: Dictionary of all context data
        """
        try:
            return self.GetContext()
        except Exception as e:
            self.Logger.error(f"Error exporting context: {e}")
            return {}
    
    def HasContext(self, Key):
        """
        Check if a context key exists.
        
        Args:
            Key (str): Context key to check
            
        Returns:
            bool: True if the key exists, False otherwise
        """
        try:
            Value = self.GetContext(Key)
            return Value is not None
        except Exception as e:
            self.Logger.error(f"Error checking context existence: {e}")
            return False
    
    def GetContextSize(self, Key=None):
        """
        Get the size of context data in bytes.
        
        Args:
            Key (str, optional): Context key to check, or None for all
            
        Returns:
            int: Size of context data in bytes
        """
        try:
            if Key is None:
                ContextData = self.GetContext()
            else:
                ContextData = self.GetContext(Key)
                if ContextData is None:
                    return 0
                ContextData = {Key: ContextData}
            
            # Convert to JSON to get size
            JsonData = json.dumps(ContextData)
            return len(JsonData.encode('utf-8'))
        except Exception as e:
            self.Logger.error(f"Error getting context size: {e}")
            return 0
    
    def TransferContext(self, FromSessionId, ToSessionId=None, Keys=None):
        """
        Transfer context from one session to another.
        
        Args:
            FromSessionId (str): Source session ID
            ToSessionId (str, optional): Destination session ID (defaults to current)
            Keys (list, optional): List of keys to transfer, or None for all
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not ToSessionId:
                ToSessionId = self.SessionManager.SessionId
            
            if not ToSessionId:
                self.Logger.warning("No destination session specified")
                return False
            
            # Get original session state
            SourceStateQuery = """
                SELECT StateData
                FROM StateSnapshots
                WHERE SessionId = ?
                ORDER BY Timestamp DESC
                LIMIT 1
            """
            
            StateRows = self.DatabaseManager.ExecuteQuery(SourceStateQuery, (FromSessionId,))
            if not StateRows or not StateRows[0]["StateData"]:
                self.Logger.warning(f"No state found for session {FromSessionId}")
                return False
            
            try:
                SourceState = json.loads(StateRows[0]["StateData"])
            except:
                self.Logger.warning(f"Could not parse state data for session {FromSessionId}")
                return False
            
            if "Context" not in SourceState:
                self.Logger.warning(f"No context found in session {FromSessionId}")
                return False
            
            SourceContext = SourceState["Context"]
            
            # Get destination session state
            CurrentSessionId = self.SessionManager.SessionId
            OriginalSessionId = CurrentSessionId
            
            # Temporarily switch to destination session if needed
            if ToSessionId != CurrentSessionId:
                # This is a bit of a hack, but we need to access the destination session
                self.SessionManager.SessionId = ToSessionId
            
            try:
                # Load destination state
                DestState = self.SessionManager.LoadSessionState()
                if not DestState:
                    self.Logger.warning(f"Could not load state for session {ToSessionId}")
                    return False
                
                # Ensure context exists
                if "Context" not in DestState:
                    DestState["Context"] = {}
                
                # Transfer selected or all keys
                if Keys:
                    for Key in Keys:
                        if Key in SourceContext:
                            DestState["Context"][Key] = SourceContext[Key]
                else:
                    # Transfer all keys
                    DestState["Context"].update(SourceContext)
                
                # Save destination state
                self.SessionManager.SaveSessionState(DestState)
                
                # Update cache if it exists
                with self.ContextLock:
                    if ToSessionId in self.ContextCache:
                        if Keys:
                            for Key in Keys:
                                if Key in SourceContext:
                                    self.ContextCache[ToSessionId][Key] = SourceContext[Key]
                        else:
                            self.ContextCache[ToSessionId].update(SourceContext)
                
                # Log the transfer
                KeyCount = len(Keys) if Keys else len(SourceContext)
                self.Logger.info(f"Transferred {KeyCount} context keys from session {FromSessionId} to {ToSessionId}")
                
                # Log to database
                self.DatabaseManager.LogToDatabase(
                    "INFO",
                    "ContextManager",
                    f"Transferred {KeyCount} context keys from session {FromSessionId}",
                    ToSessionId,
                    {"FromSessionId": FromSessionId, "Keys": Keys}
                )
                
                return True
            finally:
                # Restore original session
                if ToSessionId != OriginalSessionId:
                    self.SessionManager.SessionId = OriginalSessionId
        except Exception as e:
            self.Logger.error(f"Error transferring context: {e}")
            return False
    
    def GetContextHistory(self, Key, Limit=10):
        """
        Get history of a context key's values across state snapshots.
        
        Args:
            Key (str): Context key to check
            Limit (int, optional): Maximum number of history entries to retrieve
            
        Returns:
            list: List of historical values with timestamps
        """
        try:
            SessionId = self.SessionManager.SessionId
            if not SessionId:
                self.Logger.warning("No active session to get context history for")
                return []
            
            # Get state snapshots
            Query = """
                SELECT SnapshotId, Timestamp, StateData
                FROM StateSnapshots
                WHERE SessionId = ?
                ORDER BY Timestamp DESC
                LIMIT ?
            """
            
            Snapshots = self.DatabaseManager.ExecuteQuery(Query, (SessionId, Limit))
            
            History = []
            for Snapshot in Snapshots:
                try:
                    StateData = json.loads(Snapshot["StateData"])
                    if "Context" in StateData and Key in StateData["Context"]:
                        History.append({
                            "Timestamp": Snapshot["Timestamp"],
                            "Value": StateData["Context"][Key]
                        })
                except:
                    pass
            
            return History
        except Exception as e:
            self.Logger.error(f"Error getting context history: {e}")
            return []
    
    def GetContextKeys(self, Prefix=None):
        """
        Get a list of all context keys.
        
        Args:
            Prefix (str, optional): Prefix to filter keys
            
        Returns:
            list: List of context keys
        """
        try:
            AllContext = self.GetContext()
            
            if Prefix:
                # Filter by prefix
                Keys = [Key for Key in AllContext.keys() if Key.startswith(Prefix)]
            else:
                Keys = list(AllContext.keys())
            
            return sorted(Keys)
        except Exception as e:
            self.Logger.error(f"Error getting context keys: {e}")
            return []
    
    def ClearSessionCache(self, SessionId=None):
        """
        Clear the context cache for a session.
        
        Args:
            SessionId (str, optional): Session ID to clear cache for, or None for current
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            TargetSessionId = SessionId if SessionId else self.SessionManager.SessionId
            
            if not TargetSessionId:
                self.Logger.warning("No session specified")
                return False
            
            with self.ContextLock:
                if TargetSessionId in self.ContextCache:
                    del self.ContextCache[TargetSessionId]
            
            self.Logger.info(f"Context cache cleared for session {TargetSessionId}")
            return True
        except Exception as e:
            self.Logger.error(f"Error clearing context cache: {e}")
            return False
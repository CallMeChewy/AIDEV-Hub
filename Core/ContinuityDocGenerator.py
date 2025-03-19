# File: ContinuityDocGenerator.py
# Path: AIDEV-Hub/Core/ContinuityDocGenerator.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-18
# Last Modified: 2025-03-18  7:45PM
# Description: Generates session continuity documents and crash reports

import os
import json
import logging
from datetime import datetime

class ContinuityDocGenerator:
    """
    Generates session continuity documents.
    
    This class is responsible for:
    - Generating session continuity documents
    - Creating crash reports
    - Documenting action history
    - Providing context for resumed sessions
    """
    
    def __init__(self, DatabaseManager, SessionManager, ConfigManager):
        """Initialize the continuity document generator."""
        self.DatabaseManager = DatabaseManager
        self.SessionManager = SessionManager
        self.ConfigManager = ConfigManager
        
        # Set up logging
        self.Logger = logging.getLogger("ContinuityDocGenerator")
        self.Logger.setLevel(logging.INFO)
        
        self.Logger.info("ContinuityDocGenerator initialized")
    
    def GenerateContinuityDocument(self, ResumedFrom=None, Final=False):
        """
        Generate a session continuity document.
        
        Args:
            ResumedFrom (str, optional): ID of session being resumed
            Final (bool, optional): Whether this is a final document for a completed session
            
        Returns:
            str: Path to the generated document
        """
        try:
            SessionId = self.SessionManager.SessionId
            if not SessionId:
                self.Logger.warning("No active session to generate continuity document for")
                return None
            
            # Get directory paths based on session status
            if Final:
                CompletedSessionDir = self.SessionManager.CompletedSessionDir
                DocPath = f"{CompletedSessionDir}/{SessionId}/continuity.md"
                os.makedirs(os.path.dirname(DocPath), exist_ok=True)
            else:
                ActiveSessionDir = self.SessionManager.ActiveSessionDir
                DocPath = f"{ActiveSessionDir}/{SessionId}/continuity.md"
            
            # Get session info
            SessionInfo = self.SessionManager.GetSessionInfo()
            StartTime = SessionInfo["StartTime"] if SessionInfo else "Unknown"
            
            # Get recent messages
            Messages = self.SessionManager.GetSessionMessages(Limit=10)
            
            # Get recent actions
            ActionsQuery = """
                SELECT ActionId, ActionType, StartTime, EndTime, Status
                FROM Actions 
                WHERE SessionId = ? 
                ORDER BY StartTime DESC 
                LIMIT 5
            """
            
            Actions = self.DatabaseManager.ExecuteQuery(ActionsQuery, (SessionId,))
            
            # If resumed, get info about original session
            OriginalSessionInfo = None
            if ResumedFrom:
                OriginalSessionInfo = self.SessionManager.GetSessionInfo(ResumedFrom)
            
            # Get project name from config (or default)
            ProjectName = self.ConfigManager.GetConfig("PROJECT_NAME", "Project Himalaya")
            
            # Create continuity document
            with open(DocPath, 'w') as f:
                f.write(f"# {ProjectName}: Session Continuity Document\n")
                f.write(f"**Created: {datetime.now().strftime('%B %d, %Y %I:%M%p')}**\n\n")
                
                if ResumedFrom:
                    f.write(f"## Resumed Session Information\n")
                    f.write(f"This session is a continuation of a previous session.\n\n")
                    
                    if OriginalSessionInfo:
                        f.write(f"- **Original Session ID**: {ResumedFrom}\n")
                        f.write(f"- **Original Start Time**: {OriginalSessionInfo['StartTime']}\n")
                        f.write(f"- **Original End Time**: {OriginalSessionInfo['EndTime'] or 'N/A'}\n")
                        f.write(f"- **Original Status**: {OriginalSessionInfo['Status']}\n")
                    else:
                        f.write(f"- **Original Session ID**: {ResumedFrom}\n")
                    
                    f.write(f"- **Current Session ID**: {SessionId}\n")
                    f.write(f"- **Current Start Time**: {StartTime}\n\n")
                else:
                    f.write(f"## Current Session Overview\n\n")
                    f.write(f"- **Session ID**: {SessionId}\n")
                    f.write(f"- **Started**: {StartTime}\n")
                    
                    if Final and SessionInfo:
                        f.write(f"- **Ended**: {SessionInfo['EndTime'] or 'N/A'}\n")
                        f.write(f"- **Status**: {SessionInfo['Status']}\n")
                        f.write(f"- **Summary**: {SessionInfo['Summary'] or 'No summary provided.'}\n")
                    
                    f.write("\n")
                
                # Get current development focus from context
                DevelopmentFocus = self.GetDevelopmentFocusFromContext()
                
                f.write(f"## Current Development Focus\n\n")
                if DevelopmentFocus:
                    f.write(DevelopmentFocus + "\n\n")
                else:
                    f.write("Working on AI Collaboration Hub and related components.\n\n")
                
                f.write(f"## Current Conversation Context\n\n")
                if Messages:
                    f.write("Recent messages:\n\n")
                    for Msg in reversed(Messages):
                        Source = Msg["Source"]
                        FormattedTime = datetime.fromisoformat(Msg["Timestamp"]).strftime('%I:%M:%S%p')
                        Content = Msg["Content"]
                        
                        # Truncate long messages
                        if len(Content) > 100:
                            Content = Content[:100] + "..."
                        
                        f.write(f"**{Source} ({FormattedTime})**: {Content}\n\n")
                else:
                    f.write("No recent messages in this session.\n\n")
                
                f.write(f"## Recent Actions\n\n")
                if Actions:
                    f.write("| Action Type | Start Time | Status |\n")
                    f.write("|------------|------------|--------|\n")
                    for Action in Actions:
                        FormattedTime = datetime.fromisoformat(Action["StartTime"]).strftime('%I:%M:%S%p')
                        f.write(f"| {Action['ActionType']} | {FormattedTime} | {Action['Status']} |\n")
                else:
                    f.write("No recent actions in this session.\n\n")
                
                # Get next steps from context or use default
                NextSteps = self.GetNextStepsFromContext()
                
                f.write(f"\n## Next Steps\n\n")
                
                if Final:
                    f.write("This session has been completed. To continue development:\n\n")
                    
                    if NextSteps:
                        f.write(NextSteps + "\n\n")
                    else:
                        f.write("1. Start a new session\n")
                        f.write("2. Review this continuity document for context\n")
                        f.write("3. Continue with remaining development tasks\n\n")
                else:
                    f.write("To continue this development session:\n\n")
                    
                    if NextSteps:
                        f.write(NextSteps + "\n\n")
                    else:
                        f.write("1. Complete implementation of the current component\n")
                        f.write("2. Test the functionality\n")
                        f.write("3. Integrate with other components\n\n")
                
                # Get technical notes from context or use default
                TechnicalNotes = self.GetTechnicalNotesFromContext()
                
                if TechnicalNotes:
                    f.write(f"\n## Technical Notes\n\n")
                    f.write(TechnicalNotes + "\n\n")
                
                # Get footer from config or use default
                Footer = self.ConfigManager.GetConfig("DOCUMENT_FOOTER", 
                    '*"Code is not merely functional—it is a visual medium that developers interact with for extended periods. '
                    'The choices made in these standards prioritize the axis of symmetry, character distinction, readability at scale, '
                    'and visual hierarchy."*\n\n— Herbert J. Bowers')
                
                f.write("---\n\n")
                f.write(Footer + "\n")
            
            self.Logger.info(f"Continuity document generated at {DocPath}")
            
            # Log to database
            self.DatabaseManager.LogToDatabase(
                "INFO",
                "ContinuityDocGenerator",
                f"Continuity document generated",
                SessionId,
                {"DocPath": DocPath, "Final": Final}
            )
            
            return DocPath
        except Exception as e:
            self.Logger.error(f"Error generating continuity document: {e}")
            return None
    
    def GenerateCrashReport(self, SessionId):
        """
        Generate a crash report for a crashed session.
        
        Args:
            SessionId (str): ID of crashed session
            
        Returns:
            str: Path to the generated report
        """
        try:
            # Get crash session directory
            CrashSessionDir = self.SessionManager.CrashSessionDir
            ReportPath = f"{CrashSessionDir}/{SessionId}/crash_report.md"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(ReportPath), exist_ok=True)
            
            # Load the last saved state if available
            StateFile = f"{CrashSessionDir}/{SessionId}/state.json"
            StateData = {}
            
            if os.path.exists(StateFile):
                try:
                    with open(StateFile, 'r') as f:
                        StateData = json.load(f)
                except:
                    self.Logger.error(f"Could not parse state file for session {SessionId}")
            
            # Get session data from database
            SessionQuery = """
                SELECT StartTime 
                FROM Sessions 
                WHERE SessionId = ?
            """
            
            SessionResult = self.DatabaseManager.ExecuteQuery(SessionQuery, (SessionId,))
            StartTime = SessionResult[0]["StartTime"] if SessionResult else "Unknown"
            
            # Get last actions
            ActionsQuery = """
                SELECT ActionType, StartTime, Status 
                FROM Actions 
                WHERE SessionId = ? 
                ORDER BY StartTime DESC 
                LIMIT 5
            """
            
            Actions = self.DatabaseManager.ExecuteQuery(ActionsQuery, (SessionId,))
            
            # Get last messages
            MessagesQuery = """
                SELECT Source, Content, Timestamp 
                FROM Conversations 
                WHERE SessionId = ? 
                ORDER BY Timestamp DESC 
                LIMIT 5
            """
            
            Messages = self.DatabaseManager.ExecuteQuery(MessagesQuery, (SessionId,))
            
            # Get project name from config (or default)
            ProjectName = self.ConfigManager.GetConfig("PROJECT_NAME", "Project Himalaya")
            
            # Create crash report
            with open(ReportPath, 'w') as f:
                f.write(f"# {ProjectName}: Session Crash Report\n")
                f.write(f"**Created: {datetime.now().strftime('%B %d, %Y %I:%M%p')}**\n\n")
                
                f.write(f"## Session Information\n")
                f.write(f"- **Session ID**: {SessionId}\n")
                f.write(f"- **Started**: {StartTime}\n")
                f.write(f"- **Crashed**: {datetime.now().isoformat()}\n\n")
                
                f.write(f"## Last Actions\n")
                if Actions:
                    f.write("| Action Type | Start Time | Status |\n")
                    f.write("|------------|------------|--------|\n")
                    for Action in Actions:
                        FormattedTime = datetime.fromisoformat(Action["StartTime"]).strftime('%I:%M:%S%p')
                        f.write(f"| {Action['ActionType']} | {FormattedTime} | {Action['Status']} |\n")
                else:
                    f.write("No actions recorded for this session.\n\n")
                
                f.write(f"\n## Last Messages\n")
                if Messages:
                    f.write("| Source | Time | Content |\n")
                    f.write("|--------|------|--------|\n")
                    for Msg in Messages:
                        FormattedTime = datetime.fromisoformat(Msg["Timestamp"]).strftime('%I:%M:%S%p')
                        Content = Msg["Content"]
                        
                        # Truncate long messages
                        if len(Content) > 80:
                            Content = Content[:80] + "..."
                        
                        f.write(f"| {Msg['Source']} | {FormattedTime} | {Content} |\n")
                else:
                    f.write("No messages recorded for this session.\n\n")
                
                f.write(f"\n## Context Information\n")
                if StateData and "Context" in StateData:
                    ContextKeys = StateData["Context"].keys()
                    if ContextKeys:
                        f.write("Available context keys:\n\n")
                        for Key in sorted(ContextKeys):
                            f.write(f"- `{Key}`\n")
                    else:
                        f.write("No context data available.\n")
                else:
                    f.write("No context data available.\n")
                
                f.write(f"\n## Recovery Instructions\n")
                f.write(f"To recover work from this session:\n\n")
                f.write(f"1. Review the session state file at `{StateFile}`\n")
                f.write(f"2. Check the last messages and actions above\n")
                f.write(f"3. Start a new session with `SessionManager.ResumeSession(\"{SessionId}\")`\n\n")
                
                # Get footer from config or use default
                Footer = self.ConfigManager.GetConfig("DOCUMENT_FOOTER", 
                    '*"Code is not merely functional—it is a visual medium that developers interact with for extended periods. '
                    'The choices made in these standards prioritize the axis of symmetry, character distinction, readability at scale, '
                    'and visual hierarchy."*\n\n— Herbert J. Bowers')
                
                f.write("---\n\n")
                f.write(Footer + "\n")
            
            self.Logger.info(f"Crash report generated at {ReportPath}")
            
            # Log to database
            self.DatabaseManager.LogToDatabase(
                "INFO",
                "ContinuityDocGenerator",
                f"Crash report generated for session {SessionId}",
                None,
                {"ReportPath": ReportPath}
            )
            
            return ReportPath
        except Exception as e:
            self.Logger.error(f"Error generating crash report: {e}")
            return None
    
    def GetDevelopmentFocusFromContext(self):
        """
        Get development focus from context.
        
        Returns:
            str: Development focus text
        """
        try:
            # Get context manager
            ContextManager = None
            
            # Try to get context through session state
            State = self.SessionManager.LoadSessionState()
            if State and "Context" in State:
                # Check for development focus in context
                Context = State["Context"]
                
                # Check specific context keys
                if "development_focus" in Context:
                    return Context["development_focus"]
                
                if "focus" in Context:
                    return Context["focus"]
                
                if "dev_focus" in Context:
                    return Context["dev_focus"]
                
                # Check documentation namespace
                if "documentation.focus" in Context:
                    return Context["documentation.focus"]
            
            return None
        except Exception as e:
            self.Logger.error(f"Error getting development focus from context: {e}")
            return None
    
    def GetNextStepsFromContext(self):
        """
        Get next steps from context.
        
        Returns:
            str: Next steps text
        """
        try:
            # Get context through session state
            State = self.SessionManager.LoadSessionState()
            if State and "Context" in State:
                # Check for next steps in context
                Context = State["Context"]
                
                # Check specific context keys
                if "next_steps" in Context:
                    return Context["next_steps"]
                
                if "steps" in Context:
                    return Context["steps"]
                
                if "todo" in Context:
                    return Context["todo"]
                
                # Check documentation namespace
                if "documentation.next_steps" in Context:
                    return Context["documentation.next_steps"]
            
            return None
        except Exception as e:
            self.Logger.error(f"Error getting next steps from context: {e}")
            return None
    
    def GetTechnicalNotesFromContext(self):
        """
        Get technical notes from context.
        
        Returns:
            str: Technical notes text
        """
        try:
            # Get context through session state
            State = self.SessionManager.LoadSessionState()
            if State and "Context" in State:
                # Check for technical notes in context
                Context = State["Context"]
                
                # Check specific context keys
                if "technical_notes" in Context:
                    return Context["technical_notes"]
                
                if "notes" in Context:
                    return Context["notes"]
                
                # Check documentation namespace
                if "documentation.technical_notes" in Context:
                    return Context["documentation.technical_notes"]
            
            return None
        except Exception as e:
            self.Logger.error(f"Error getting technical notes from context: {e}")
            return None
    
    def SetDocumentMetadata(self, Key, Value):
        """
        Set metadata for continuity documents.
        
        Args:
            Key (str): Metadata key
            Value (str): Metadata value
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Store in context with special namespace
            ContextKey = f"documentation.{Key}"
            
            # Get session state
            State = self.SessionManager.LoadSessionState()
            if not State:
                self.Logger.warning("Could not load session state")
                return False
            
            # Update context in state
            if "Context" not in State:
                State["Context"] = {}
            
            State["Context"][ContextKey] = Value
            
            # Save updated state
            self.SessionManager.SaveSessionState(State)
            
            self.Logger.info(f"Document metadata set for key '{Key}'")
            
            return True
        except Exception as e:
            self.Logger.error(f"Error setting document metadata: {e}")
            return False
    
    def GenerateSessionSummary(self, SessionId=None):
        """
        Generate a summary of a session's activities.
        
        Args:
            SessionId (str, optional): Session ID to summarize (defaults to current)
            
        Returns:
            str: Summary text
        """
        try:
            TargetSessionId = SessionId if SessionId else self.SessionManager.SessionId
            
            if not TargetSessionId:
                self.Logger.warning("No session specified")
                return None
            
            # Get session info
            SessionInfo = self.SessionManager.GetSessionInfo(TargetSessionId)
            if not SessionInfo:
                self.Logger.warning(f"Session {TargetSessionId} not found")
                return None
            
            # Get action statistics
            ActionsQuery = """
                SELECT ActionType, COUNT(*) as Count
                FROM Actions
                WHERE SessionId = ?
                GROUP BY ActionType
            """
            
            ActionsStats = self.DatabaseManager.ExecuteQuery(ActionsQuery, (TargetSessionId,))
            
            # Get message statistics
            MessagesQuery = """
                SELECT Source, COUNT(*) as Count
                FROM Conversations
                WHERE SessionId = ?
                GROUP BY Source
            """
            
            MessagesStats = self.DatabaseManager.ExecuteQuery(MessagesQuery, (TargetSessionId,))
            
            # Calculate session duration
            StartTime = datetime.fromisoformat(SessionInfo["StartTime"])
            EndTime = None
            
            if SessionInfo["EndTime"]:
                EndTime = datetime.fromisoformat(SessionInfo["EndTime"])
            else:
                EndTime = datetime.now()
            
            Duration = EndTime - StartTime
            DurationStr = str(Duration).split(".")[0]  # Remove microseconds
            
            # Build summary
            Summary = f"Session {TargetSessionId} ({SessionInfo['Status']}) lasted {DurationStr}. "
            
            # Add message stats
            TotalMessages = SessionInfo.get("MessageCount", 0)
            if TotalMessages > 0:
                Summary += f"Recorded {TotalMessages} messages"
                
                SourceCounts = []
                for Stat in MessagesStats:
                    SourceCounts.append(f"{Stat['Count']} from {Stat['Source']}")
                
                if SourceCounts:
                    Summary += f" ({', '.join(SourceCounts)}). "
                else:
                    Summary += ". "
            
            # Add action stats
            if ActionsStats:
                ActionCounts = []
                for Stat in ActionsStats:
                    ActionCounts.append(f"{Stat['Count']} {Stat['ActionType']}")
                
                if ActionCounts:
                    Summary += f"Performed {', '.join(ActionCounts)}. "
            
            return Summary.strip()
        except Exception as e:
            self.Logger.error(f"Error generating session summary: {e}")
            return None
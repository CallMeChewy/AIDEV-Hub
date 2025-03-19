# File: main.py
# Path: AIDEV-Hub/main.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-18
# Last Modified: 2025-03-18  8:15PM
# Description: Main entry point for the AI Collaboration Hub application

import os
import sys
import cmd
import time
import json
from datetime import datetime

from Core.StateManager import StateManager

class AIDevHubCLI(cmd.Cmd):
    """Command-line interface for the AI Collaboration Hub."""
    
    intro = """
    Welcome to AI Collaboration Hub
    ==============================
    Type 'help' for a list of commands.
    Type 'exit' to quit.
    """
    prompt = "AIDEV-Hub> "
    
    def __init__(self):
        """Initialize the CLI."""
        super().__init__()
        self.StateManager = None
        self.StartTime = datetime.now()
    
    def preloop(self):
        """Initialize the state manager before the command loop starts."""
        print("Initializing AI Collaboration Hub...")
        self.StateManager = StateManager()
        print(f"Session started: {self.StateManager.SessionId}")
    
    def do_status(self, arg):
        """Show the current session status."""
        if not self.StateManager or not self.StateManager.SessionId:
            print("No active session.")
            return
        
        SessionInfo = self.StateManager.GetSessionInfo()
        
        print(f"Current Session: {self.StateManager.SessionId}")
        print(f"Started: {SessionInfo.get('StartTime', 'Unknown')}")
        
        # Calculate running time
        StartTime = datetime.fromisoformat(SessionInfo.get('StartTime', datetime.now().isoformat()))
        RunningTime = datetime.now() - StartTime
        print(f"Running time: {RunningTime}")
        
        # Get message count
        MessageCount = SessionInfo.get("MessageCount", 0)
        print(f"Messages: {MessageCount}")
        
        # Get action count
        ActionStats = self.StateManager.ActionTracker.GetActionStats()
        ActionCount = ActionStats.get("TotalCount", 0)
        print(f"Actions: {ActionCount}")
        
        # Show status
        Status = SessionInfo.get("Status", "ACTIVE")
        print(f"Status: {Status}")
    
    def do_message(self, arg):
        """Record a message: message <source> <content>
        Example: message User "This is a test message"
        """
        Args = arg.split(maxsplit=1)
        if len(Args) < 2:
            print("Usage: message <source> <content>")
            return
        
        Source, Content = Args
        MessageId = self.StateManager.RecordMessage(Source, Content)
        print(f"Message recorded with ID: {MessageId}")
    
    def do_action(self, arg):
        """Record and execute a test action: action <action_type> [param=value param2=value2 ...]
        Example: action TestAction name="Test" value=123
        """
        Args = arg.split(maxsplit=1)
        if not Args:
            print("Usage: action <action_type> [param=value param2=value2 ...]")
            return
        
        ActionType = Args[0]
        Params = {}
        
        if len(Args) > 1:
            ParamStr = Args[1]
            ParamPairs = ParamStr.split()
            
            for Pair in ParamPairs:
                if "=" in Pair:
                    Key, Value = Pair.split("=", 1)
                    # Try to convert to appropriate types
                    if Value.isdigit():
                        Value = int(Value)
                    elif Value.lower() in ("true", "false"):
                        Value = Value.lower() == "true"
                    Params[Key] = Value
        
        # Define a test action function
        def TestAction(**kwargs):
            # Simulate work
            print(f"Executing {ActionType} with parameters: {kwargs}")
            time.sleep(1)
            return {"Status": "success", "Parameters": kwargs}
        
        # Execute with tracking
        Success, Result, ActionId = self.StateManager.ExecuteActionWithTracking(
            ActionType, TestAction, Params
        )
        
        if Success:
            print(f"Action completed successfully with ID: {ActionId}")
            print(f"Result: {Result}")
        else:
            print(f"Action failed with ID: {ActionId}")
            print(f"Error: {Result}")
    
    def do_context(self, arg):
        """Get or set context data: context [key [value]]
        - With no arguments: show all context
        - With one argument: show value for that key
        - With two arguments: set value for that key
        """
        Args = arg.split(maxsplit=1)
        
        if not Args:
            Context = self.StateManager.GetContext()
            print("Current context:")
            for Key, Value in Context.items():
                print(f"  {Key}: {Value}")
            return
        
        Key = Args[0]
        
        if len(Args) == 1:
            Value = self.StateManager.GetContext(Key)
            print(f"{Key}: {Value}")
        else:
            Value = Args[1]
            try:
                # Try to parse as JSON for complex values
                Value = json.loads(Value)
            except json.JSONDecodeError:
                # If not valid JSON, use as string
                pass
            
            self.StateManager.SetContext(Key, Value)
            print(f"Context set: {Key} = {Value}")
    
    def do_clear_context(self, arg):
        """Clear context data: clear_context [key]
        - With no arguments: clear all context
        - With one argument: clear that specific key
        """
        if arg:
            self.StateManager.ClearContext(arg)
            print(f"Context cleared for key: {arg}")
        else:
            self.StateManager.ClearContext()
            print("All context cleared")
    
    def do_history(self, arg):
        """Show session history."""
        try:
            Limit = int(arg) if arg else 5
        except ValueError:
            print("Usage: history [limit]")
            return
        
        Sessions = self.StateManager.GetSessionHistory(Limit)
        print(f"Recent Sessions (limit {Limit}):")
        
        for Session in Sessions:
            Status = Session["Status"]
            StatusDisplay = {
                "ACTIVE": "🟢 Active",
                "COMPLETED": "✅ Completed",
                "CRASHED": "❌ Crashed"
            }.get(Status, Status)
            
            print(f"- {Session['SessionId']} ({StatusDisplay})")
            print(f"  Started: {Session['StartTime']}")
            if Session["EndTime"]:
                print(f"  Ended: {Session['EndTime']}")
            if Session["Summary"]:
                print(f"  Summary: {Session['Summary']}")
            print()
    
    def do_continuity(self, arg):
        """Generate a continuity document for the current session."""
        DocPath = self.StateManager.GenerateContinuityDocument()
        print(f"Continuity document generated: {DocPath}")
        
        # Try to open the document with default application
        try:
            if sys.platform == "win32":
                os.startfile(DocPath)
            elif sys.platform == "darwin":
                os.system(f"open {DocPath}")
            else:
                os.system(f"xdg-open {DocPath}")
        except Exception as e:
            print(f"Could not open document automatically: {e}")
    
    def do_simulate_crash(self, arg):
        """Simulate a crash for testing recovery."""
        print("Simulating a crash...")
        print("The application will exit without cleaning up.")
        print("On next start, the crash recovery should detect this.")
        
        # Exit without proper cleanup to simulate crash
        os._exit(1)
    
    def do_backup(self, arg):
        """Create a backup of the current state."""
        BackupPath = self.StateManager.BackupState()
        print(f"State backup created: {BackupPath}")
    
    def do_config(self, arg):
        """Get or set configuration: config [key [value [type [description]]]]
        - With no arguments: show all configuration
        - With one argument: show value for that key
        - With two+ arguments: set value for that key
        """
        Args = arg.split(maxsplit=3)
        
        if not Args:
            # Get all config details
            AllConfig = self.StateManager.ConfigManager.GetAllConfigDetails()
            print("Current configuration:")
            for Config in AllConfig:
                print(f"  {Config['Key']} ({Config['Type']}): {Config['Value']}")
                if Config['Description']:
                    print(f"    Description: {Config['Description']}")
            return
        
        Key = Args[0]
        
        if len(Args) == 1:
            # Get single config value
            ConfigDetails = self.StateManager.ConfigManager.GetConfigDetails(Key)
            if ConfigDetails:
                print(f"{Key} ({ConfigDetails['Type']}): {ConfigDetails['Value']}")
                if ConfigDetails['Description']:
                    print(f"Description: {ConfigDetails['Description']}")
                print(f"Default: {ConfigDetails['DefaultValue']}")
                print(f"Last Modified: {ConfigDetails['LastModified']}")
            else:
                print(f"Configuration key '{Key}' not found")
        else:
            # Set config value
            Value = Args[1]
            Type = Args[2] if len(Args) > 2 else "TEXT"
            Description = Args[3] if len(Args) > 3 else None
            
            try:
                # Convert value based on type
                if Type == "INTEGER":
                    Value = int(Value)
                elif Type == "FLOAT":
                    Value = float(Value)
                elif Type == "BOOLEAN":
                    Value = Value.lower() in ("true", "yes", "1", "t", "y")
                elif Type == "JSON":
                    Value = json.loads(Value)
            except:
                print(f"Error converting value to {Type}")
                return
            
            self.StateManager.SetConfig(Key, Value, Type, Description)
            print(f"Configuration set: {Key} = {Value} ({Type})")
    
    def do_validate(self, arg):
        """Validate input against a rule: validate <rule_type> <input>
        Example: validate EMAIL user@example.com
        """
        Args = arg.split(maxsplit=1)
        if len(Args) < 2:
            print("Usage: validate <rule_type> <input>")
            return
        
        RuleType, Input = Args
        IsValid, ErrorMessage = self.StateManager.ValidateInput(Input, RuleType)
        
        if IsValid:
            print(f"Input '{Input}' is valid for rule type '{RuleType}'")
        else:
            print(f"Input '{Input}' is NOT valid for rule type '{RuleType}'")
            print(f"Error: {ErrorMessage}")
    
    def do_resume(self, arg):
        """Resume a crashed session: resume <session_id>"""
        if not arg:
            print("Usage: resume <session_id>")
            return
        
        SessionId = arg.strip()
        
        # First end current session
        if self.StateManager.SessionId:
            self.StateManager.EndSession("Ended to resume another session")
        
        # Try to resume session
        NewSessionId = self.StateManager.ResumeSession(SessionId)
        
        if NewSessionId:
            print(f"Resumed session {SessionId} as new session {NewSessionId}")
        else:
            print(f"Failed to resume session {SessionId}")
    
    def do_exit(self, arg):
        """Exit the application."""
        if self.StateManager and self.StateManager.SessionId:
            Summary = arg if arg else f"Session ended by user after {datetime.now() - self.StartTime}"
            self.StateManager.EndSession(Summary)
            print(f"Session ended.")
        
        print("Exiting AI Collaboration Hub. Goodbye!")
        return True
    
    def do_quit(self, arg):
        """Exit the application (alias for exit)."""
        return self.do_exit(arg)
    
    def do_EOF(self, arg):
        """Exit on Ctrl-D."""
        print()  # Add newline
        return self.do_exit("Session ended with Ctrl-D")
    
    # Helper methods
    def emptyline(self):
        """Do nothing on empty line."""
        pass

def Main():
    """Main entry point for the application."""
    CLI = AIDevHubCLI()
    try:
        CLI.cmdloop()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt.")
        CLI.do_exit("Session interrupted by user")
    
    return 0

if __name__ == "__main__":
    sys.exit(Main())

# File: DatabaseManager.py
# Path: AIDEV-Hub/Core/DatabaseManager.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-18
# Last Modified: 2025-03-18  6:15PM
# Description: Manages database connections and operations with transaction support

import os
import sqlite3
import json
import threading
from datetime import datetime
import logging

class DatabaseManager:
    """
    Manages database connections and operations.
    
    This class is responsible for:
    - Database initialization and schema management
    - Providing transaction support
    - Executing queries and non-queries
    - Handling connection pooling
    - Database migration
    """
    
    def __init__(self, DbPath="State/AIDevHub.db"):
        """Initialize the database manager."""
        self.DbPath = DbPath
        self.ConnectionLock = threading.Lock()
        self.LocalStorage = threading.local()
        
        # Set up logging
        self.SetupLogging()
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.DbPath), exist_ok=True)
        
        # Initialize database schema
        self.InitializeDatabase()
        
        self.Logger.info(f"DatabaseManager initialized with database at {self.DbPath}")
    
    def SetupLogging(self):
        """Set up logging for the database manager."""
        # Create logs directory if it doesn't exist
        os.makedirs("Logs", exist_ok=True)
        
        # Configure logger
        self.Logger = logging.getLogger("DatabaseManager")
        self.Logger.setLevel(logging.INFO)
        
        # File handler
        LogFile = f"Logs/database_manager_{datetime.now().strftime('%Y%m%d')}.log"
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
    
    def GetConnection(self):
        """
        Get a database connection.
        
        For thread safety, each thread gets its own connection.
        """
        if not hasattr(self.LocalStorage, 'connection'):
            self.LocalStorage.connection = sqlite3.connect(self.DbPath)
            # Enable foreign keys
            self.LocalStorage.connection.execute("PRAGMA foreign_keys = ON")
            # Configure for better performance and safety
            self.LocalStorage.connection.execute("PRAGMA journal_mode = WAL")
            self.LocalStorage.connection.execute("PRAGMA synchronous = NORMAL")
            
            # Row factory to get dictionary-like results
            self.LocalStorage.connection.row_factory = sqlite3.Row
            
        return self.LocalStorage.connection
    
    def InitializeDatabase(self):
        """Initialize the database schema if it doesn't exist."""
        self.Logger.info("Initializing database schema")
        
        # Use a connection just for initialization
        Conn = sqlite3.connect(self.DbPath)
        Cursor = Conn.cursor()
        
        # Create sessions table
        Cursor.execute('''
        CREATE TABLE IF NOT EXISTS Sessions (
            SessionId TEXT PRIMARY KEY,
            StartTime TEXT,
            EndTime TEXT,
            Status TEXT,
            Summary TEXT
        )
        ''')
        
        # Create conversations table
        Cursor.execute('''
        CREATE TABLE IF NOT EXISTS Conversations (
            MessageId TEXT PRIMARY KEY,
            SessionId TEXT,
            Timestamp TEXT,
            Source TEXT,
            Content TEXT,
            FOREIGN KEY (SessionId) REFERENCES Sessions (SessionId)
        )
        ''')
        
        # Create actions table
        Cursor.execute('''
        CREATE TABLE IF NOT EXISTS Actions (
            ActionId TEXT PRIMARY KEY,
            SessionId TEXT,
            ActionType TEXT,
            StartTime TEXT,
            EndTime TEXT,
            Status TEXT,
            Params TEXT,
            Result TEXT,
            FOREIGN KEY (SessionId) REFERENCES Sessions (SessionId)
        )
        ''')
        
        # Create models table
        Cursor.execute('''
        CREATE TABLE IF NOT EXISTS Models (
            ModelId TEXT PRIMARY KEY,
            ModelName TEXT,
            ModelType TEXT,
            Location TEXT,
            Status TEXT,
            LastUsed TEXT,
            Capabilities TEXT
        )
        ''')
        
        # Create routing rules table
        Cursor.execute('''
        CREATE TABLE IF NOT EXISTS RoutingRules (
            RuleId TEXT PRIMARY KEY,
            TaskType TEXT,
            PreferredModel TEXT,
            FallbackModel TEXT,
            Priority INTEGER,
            FOREIGN KEY (PreferredModel) REFERENCES Models (ModelId),
            FOREIGN KEY (FallbackModel) REFERENCES Models (ModelId)
        )
        ''')
        
        # Create state snapshots table
        Cursor.execute('''
        CREATE TABLE IF NOT EXISTS StateSnapshots (
            SnapshotId TEXT PRIMARY KEY,
            SessionId TEXT,
            Timestamp TEXT,
            StateData TEXT,
            FOREIGN KEY (SessionId) REFERENCES Sessions (SessionId)
        )
        ''')
        
        # Create session relationships table
        Cursor.execute('''
        CREATE TABLE IF NOT EXISTS SessionRelationships (
            RelationshipId INTEGER PRIMARY KEY AUTOINCREMENT,
            ParentSessionId TEXT,
            ChildSessionId TEXT,
            RelationType TEXT,
            FOREIGN KEY (ParentSessionId) REFERENCES Sessions (SessionId),
            FOREIGN KEY (ChildSessionId) REFERENCES Sessions (SessionId)
        )
        ''')
        
        # Create configuration table
        Cursor.execute('''
        CREATE TABLE IF NOT EXISTS Configuration (
            ConfigKey TEXT PRIMARY KEY,
            ConfigValue TEXT,
            ConfigType TEXT,
            DefaultValue TEXT,
            Description TEXT,
            LastModified TEXT
        )
        ''')
        
        # Create validation rules table
        Cursor.execute('''
        CREATE TABLE IF NOT EXISTS ValidationRules (
            RuleId TEXT PRIMARY KEY,
            RuleType TEXT,
            Pattern TEXT,
            ErrorMessage TEXT,
            Description TEXT
        )
        ''')
        
        # Create input fields table
        Cursor.execute('''
        CREATE TABLE IF NOT EXISTS InputFields (
            FieldId TEXT PRIMARY KEY,
            FieldName TEXT,
            ValidationRuleId TEXT,
            Required INTEGER,
            Description TEXT,
            FOREIGN KEY (ValidationRuleId) REFERENCES ValidationRules (RuleId)
        )
        ''')
        
        # Create log table
        Cursor.execute('''
        CREATE TABLE IF NOT EXISTS SystemLogs (
            LogId INTEGER PRIMARY KEY AUTOINCREMENT,
            Timestamp TEXT,
            LogLevel TEXT,
            Component TEXT,
            Message TEXT,
            SessionId TEXT,
            AdditionalData TEXT
        )
        ''')
        
        # Create schema version table
        Cursor.execute('''
        CREATE TABLE IF NOT EXISTS SchemaVersion (
            VersionId INTEGER PRIMARY KEY AUTOINCREMENT,
            VersionNumber TEXT,
            AppliedAt TEXT,
            Description TEXT
        )
        ''')
        
        # Insert default configuration if it doesn't exist
        Cursor.execute("SELECT COUNT(*) FROM Configuration")
        ConfigCount = Cursor.fetchone()[0]
        
        if ConfigCount == 0:
            self.Logger.info("Inserting default configuration values")
            DefaultConfigs = [
                ('SESSION_TIMEOUT_MINUTES', '60', 'INTEGER', '60', 'Session timeout in minutes', datetime.now().isoformat()),
                ('MAX_MESSAGES_PER_SESSION', '1000', 'INTEGER', '1000', 'Maximum number of messages per session', datetime.now().isoformat()),
                ('DEFAULT_AI_MODEL', 'LOCAL_LLAMA', 'TEXT', 'LOCAL_LLAMA', 'Default AI model to use', datetime.now().isoformat()),
                ('ENABLE_CRASH_RECOVERY', 'true', 'BOOLEAN', 'true', 'Enable crash recovery', datetime.now().isoformat()),
                ('LOG_LEVEL', 'INFO', 'TEXT', 'INFO', 'Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)', datetime.now().isoformat()),
                ('STATE_BACKUP_COUNT', '5', 'INTEGER', '5', 'Number of state backups to keep', datetime.now().isoformat()),
                ('UI_THEME', 'LIGHT', 'TEXT', 'LIGHT', 'UI theme (LIGHT, DARK)', datetime.now().isoformat())
            ]
            
            Cursor.executemany(
                "INSERT INTO Configuration (ConfigKey, ConfigValue, ConfigType, DefaultValue, Description, LastModified) VALUES (?, ?, ?, ?, ?, ?)",
                DefaultConfigs
            )
        
        # Insert default validation rules if they don't exist
        Cursor.execute("SELECT COUNT(*) FROM ValidationRules")
        RulesCount = Cursor.fetchone()[0]
        
        if RulesCount == 0:
            self.Logger.info("Inserting default validation rules")
            DefaultRules = [
                ('EMAIL_RULE', 'EMAIL', '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', 'Invalid email format', 'Email validation rule'),
                ('USERNAME_RULE', 'USERNAME', '^[a-zA-Z0-9_-]{3,16}$', 'Username must be 3-16 characters and contain only letters, numbers, underscores, and hyphens', 'Username validation rule'),
                ('PATH_RULE', 'PATH', '^(/[^/ ]*)+/?$', 'Invalid path format', 'File path validation rule'),
                ('URL_RULE', 'URL', '^(http|https)://[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}(/.*)?$', 'Invalid URL format', 'URL validation rule'),
                ('IPADDRESS_RULE', 'IPADDRESS', '^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$', 'Invalid IP address format', 'IP address validation rule')
            ]
            
            Cursor.executemany(
                "INSERT INTO ValidationRules (RuleId, RuleType, Pattern, ErrorMessage, Description) VALUES (?, ?, ?, ?, ?)",
                DefaultRules
            )
        
        # Record schema version if not already present
        Cursor.execute("SELECT COUNT(*) FROM SchemaVersion")
        VersionCount = Cursor.fetchone()[0]
        
        if VersionCount == 0:
            Cursor.execute(
                "INSERT INTO SchemaVersion (VersionNumber, AppliedAt, Description) VALUES (?, ?, ?)",
                ("1.0", datetime.now().isoformat(), "Initial schema creation")
            )
        
        Conn.commit()
        Conn.close()
        
        self.Logger.info("Database schema initialized successfully")
    
    def BeginTransaction(self):
        """Begin a database transaction."""
        Conn = self.GetConnection()
        self.Logger.info("Beginning transaction")
        # Store the current state so we know if we need to commit or rollback
        self.LocalStorage.in_transaction = True
        return Conn
    
    def CommitTransaction(self):
        """Commit the current transaction."""
        if hasattr(self.LocalStorage, 'in_transaction') and self.LocalStorage.in_transaction:
            Conn = self.GetConnection()
            Conn.commit()
            self.LocalStorage.in_transaction = False
            self.Logger.info("Transaction committed")
    
    def RollbackTransaction(self):
        """Roll back the current transaction."""
        if hasattr(self.LocalStorage, 'in_transaction') and self.LocalStorage.in_transaction:
            Conn = self.GetConnection()
            Conn.rollback()
            self.LocalStorage.in_transaction = False
            self.Logger.info("Transaction rolled back")
    
    def ExecuteQuery(self, Query, Params=None):
        """
        Execute a query and return results.
        
        Args:
            Query (str): SQL query to execute
            Params (tuple, dict, optional): Parameters for the query
            
        Returns:
            list: List of rows as dictionaries
        """
        try:
            Conn = self.GetConnection()
            Cursor = Conn.cursor()
            
            if Params:
                Cursor.execute(Query, Params)
            else:
                Cursor.execute(Query)
            
            Rows = Cursor.fetchall()
            
            # Convert rows to dictionaries
            Result = []
            for Row in Rows:
                RowDict = {}
                for idx, col in enumerate(Cursor.description):
                    RowDict[col[0]] = Row[idx]
                Result.append(RowDict)
            
            return Result
        except sqlite3.Error as e:
            self.Logger.error(f"Error executing query: {e}")
            if not hasattr(self.LocalStorage, 'in_transaction') or not self.LocalStorage.in_transaction:
                # If not in a transaction, we need to cleanup
                if hasattr(self.LocalStorage, 'connection'):
                    self.LocalStorage.connection.rollback()
            raise
    
    def ExecuteScalar(self, Query, Params=None):
        """
        Execute a query and return a single value.
        
        Args:
            Query (str): SQL query to execute
            Params (tuple, dict, optional): Parameters for the query
            
        Returns:
            Any: First column of the first row of the result
        """
        try:
            Conn = self.GetConnection()
            Cursor = Conn.cursor()
            
            if Params:
                Cursor.execute(Query, Params)
            else:
                Cursor.execute(Query)
            
            Row = Cursor.fetchone()
            if Row:
                return Row[0]
            return None
        except sqlite3.Error as e:
            self.Logger.error(f"Error executing scalar query: {e}")
            if not hasattr(self.LocalStorage, 'in_transaction') or not self.LocalStorage.in_transaction:
                if hasattr(self.LocalStorage, 'connection'):
                    self.LocalStorage.connection.rollback()
            raise
    
    def ExecuteNonQuery(self, Query, Params=None):
        """
        Execute a non-query statement.
        
        Args:
            Query (str): SQL statement to execute
            Params (tuple, dict, optional): Parameters for the statement
            
        Returns:
            int: Number of rows affected
        """
        try:
            Conn = self.GetConnection()
            Cursor = Conn.cursor()
            
            if Params:
                Cursor.execute(Query, Params)
            else:
                Cursor.execute(Query)
            
            RowCount = Cursor.rowcount
            
            # Only commit if we're not in a transaction
            if not hasattr(self.LocalStorage, 'in_transaction') or not self.LocalStorage.in_transaction:
                Conn.commit()
            
            return RowCount
        except sqlite3.Error as e:
            self.Logger.error(f"Error executing non-query: {e}")
            if not hasattr(self.LocalStorage, 'in_transaction') or not self.LocalStorage.in_transaction:
                if hasattr(self.LocalStorage, 'connection'):
                    self.LocalStorage.connection.rollback()
            raise
    
    def ExecuteNonQueryMany(self, Query, ParamsList):
        """
        Execute a non-query statement with multiple parameter sets.
        
        Args:
            Query (str): SQL statement to execute
            ParamsList (list): List of parameter tuples or dictionaries
            
        Returns:
            int: Number of rows affected
        """
        try:
            Conn = self.GetConnection()
            Cursor = Conn.cursor()
            
            Cursor.executemany(Query, ParamsList)
            
            RowCount = Cursor.rowcount
            
            # Only commit if we're not in a transaction
            if not hasattr(self.LocalStorage, 'in_transaction') or not self.LocalStorage.in_transaction:
                Conn.commit()
            
            return RowCount
        except sqlite3.Error as e:
            self.Logger.error(f"Error executing many non-query: {e}")
            if not hasattr(self.LocalStorage, 'in_transaction') or not self.LocalStorage.in_transaction:
                if hasattr(self.LocalStorage, 'connection'):
                    self.LocalStorage.connection.rollback()
            raise
    
    def InsertWithId(self, Table, ColumnDict):
        """
        Insert a row and return the ID of the new row.
        
        Args:
            Table (str): Table name
            ColumnDict (dict): Dictionary of column names and values
            
        Returns:
            Any: ID of the new row (typically the rowid or primary key)
        """
        try:
            Columns = list(ColumnDict.keys())
            Placeholders = ["?" for _ in Columns]
            Values = [ColumnDict[col] for col in Columns]
            
            Query = f"INSERT INTO {Table} ({', '.join(Columns)}) VALUES ({', '.join(Placeholders)})"
            
            Conn = self.GetConnection()
            Cursor = Conn.cursor()
            
            Cursor.execute(Query, Values)
            
            # Get the ID of the new row
            NewId = Cursor.lastrowid
            
            # Only commit if we're not in a transaction
            if not hasattr(self.LocalStorage, 'in_transaction') or not self.LocalStorage.in_transaction:
                Conn.commit()
            
            return NewId
        except sqlite3.Error as e:
            self.Logger.error(f"Error inserting with ID: {e}")
            if not hasattr(self.LocalStorage, 'in_transaction') or not self.LocalStorage.in_transaction:
                if hasattr(self.LocalStorage, 'connection'):
                    self.LocalStorage.connection.rollback()
            raise
    
    def Update(self, Table, ColumnDict, WhereClause, WhereParams=None):
        """
        Update rows in a table.
        
        Args:
            Table (str): Table name
            ColumnDict (dict): Dictionary of column names and values to update
            WhereClause (str): WHERE clause for the update
            WhereParams (tuple, dict, optional): Parameters for the WHERE clause
            
        Returns:
            int: Number of rows affected
        """
        try:
            SetClause = ", ".join([f"{col} = ?" for col in ColumnDict.keys()])
            SetParams = [ColumnDict[col] for col in ColumnDict.keys()]
            
            Query = f"UPDATE {Table} SET {SetClause} WHERE {WhereClause}"
            
            # Combine parameters
            AllParams = SetParams
            if WhereParams:
                if isinstance(WhereParams, dict):
                    for param in WhereParams.values():
                        AllParams.append(param)
                else:
                    AllParams.extend(WhereParams)
            
            Conn = self.GetConnection()
            Cursor = Conn.cursor()
            
            Cursor.execute(Query, AllParams)
            
            RowCount = Cursor.rowcount
            
            # Only commit if we're not in a transaction
            if not hasattr(self.LocalStorage, 'in_transaction') or not self.LocalStorage.in_transaction:
                Conn.commit()
            
            return RowCount
        except sqlite3.Error as e:
            self.Logger.error(f"Error updating: {e}")
            if not hasattr(self.LocalStorage, 'in_transaction') or not self.LocalStorage.in_transaction:
                if hasattr(self.LocalStorage, 'connection'):
                    self.LocalStorage.connection.rollback()
            raise
    
    def Delete(self, Table, WhereClause, WhereParams=None):
        """
        Delete rows from a table.
        
        Args:
            Table (str): Table name
            WhereClause (str): WHERE clause for the delete
            WhereParams (tuple, dict, optional): Parameters for the WHERE clause
            
        Returns:
            int: Number of rows affected
        """
        try:
            Query = f"DELETE FROM {Table} WHERE {WhereClause}"
            
            return self.ExecuteNonQuery(Query, WhereParams)
        except sqlite3.Error as e:
            self.Logger.error(f"Error deleting: {e}")
            raise
    
    def TableExists(self, TableName):
        """
        Check if a table exists.
        
        Args:
            TableName (str): Table name to check
            
        Returns:
            bool: True if the table exists, False otherwise
        """
        Query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        Result = self.ExecuteScalar(Query, (TableName,))
        return Result is not None
    
    def CreateBackup(self, BackupPath=None):
        """
        Create a backup of the database.
        
        Args:
            BackupPath (str, optional): Path for the backup file
            
        Returns:
            str: Path to the backup file
        """
        if not BackupPath:
            Timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            BackupPath = f"State/Backup/db_backup_{Timestamp}.db"
        
        # Ensure backup directory exists
        os.makedirs(os.path.dirname(BackupPath), exist_ok=True)
        
        # Lock to prevent other operations during backup
        with self.ConnectionLock:
            # Get a new connection just for the backup
            SourceConn = sqlite3.connect(self.DbPath)
            DestConn = sqlite3.connect(BackupPath)
            
            SourceConn.backup(DestConn)
            
            DestConn.close()
            SourceConn.close()
        
        self.Logger.info(f"Database backed up to {BackupPath}")
        return BackupPath
    
    def LogToDatabase(self, LogLevel, Component, Message, SessionId=None, AdditionalData=None):
        """
        Log a message to the database.
        
        Args:
            LogLevel (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            Component (str): Component that generated the log
            Message (str): Log message
            SessionId (str, optional): ID of the session related to this log
            AdditionalData (dict, optional): Additional data to include in the log
            
        Returns:
            int: ID of the new log entry
        """
        try:
            Timestamp = datetime.now().isoformat()
            
            ColumnDict = {
                "Timestamp": Timestamp,
                "LogLevel": LogLevel,
                "Component": Component,
                "Message": Message,
                "SessionId": SessionId
            }
            
            if AdditionalData:
                ColumnDict["AdditionalData"] = json.dumps(AdditionalData)
            
            return self.InsertWithId("SystemLogs", ColumnDict)
        except Exception as e:
            # If we can't log to the database, at least log to the file
            self.Logger.error(f"Error logging to database: {e}")
            return None
    
    def CloseConnections(self):
        """Close all database connections."""
        if hasattr(self.LocalStorage, 'connection'):
            try:
                if hasattr(self.LocalStorage, 'in_transaction') and self.LocalStorage.in_transaction:
                    self.Logger.warning("Closing connection with active transaction, rolling back")
                    self.LocalStorage.connection.rollback()
                
                self.LocalStorage.connection.close()
                del self.LocalStorage.connection
                if hasattr(self.LocalStorage, 'in_transaction'):
                    del self.LocalStorage.in_transaction
                
                self.Logger.info("Database connection closed")
            except Exception as e:
                self.Logger.error(f"Error closing database connection: {e}")

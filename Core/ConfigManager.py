# File: ConfigManager.py
# Path: AIDEV-Hub/Core/ConfigManager.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-18
# Last Modified: 2025-03-18  6:30PM
# Description: Manages application configuration stored in the database

import json
import logging
from datetime import datetime
import threading

class ConfigManager:
    """
    Manages application configuration from database.
    
    This class is responsible for:
    - Loading configuration from the database
    - Providing access to configuration values
    - Updating configuration values
    - Type conversion for configuration values
    """
    
    def __init__(self, DatabaseManager):
        """Initialize the configuration manager."""
        self.DatabaseManager = DatabaseManager
        self.ConfigCache = {}
        self.CacheLock = threading.RLock()
        
        # Set up logging
        self.Logger = logging.getLogger("ConfigManager")
        self.Logger.setLevel(logging.INFO)
        
        # Load all configuration into cache
        self.LoadAllConfig()
        
        self.Logger.info("ConfigManager initialized")
    
    def LoadAllConfig(self):
        """Load all configuration from the database into cache."""
        try:
            Query = "SELECT ConfigKey, ConfigValue, ConfigType FROM Configuration"
            Rows = self.DatabaseManager.ExecuteQuery(Query)
            
            with self.CacheLock:
                self.ConfigCache.clear()
                for Row in Rows:
                    Key = Row['ConfigKey']
                    Value = self.ConvertValueFromString(Row['ConfigValue'], Row['ConfigType'])
                    self.ConfigCache[Key] = Value
            
            self.Logger.info(f"Loaded {len(Rows)} configuration items into cache")
        except Exception as e:
            self.Logger.error(f"Error loading configuration: {e}")
            raise
    
    def ConvertValueFromString(self, ValueStr, TypeStr):
        """
        Convert a string value to the appropriate type.
        
        Args:
            ValueStr (str): String value to convert
            TypeStr (str): Type to convert to (INTEGER, BOOLEAN, TEXT, FLOAT, JSON)
            
        Returns:
            Any: Converted value
        """
        if ValueStr is None:
            return None
        
        try:
            if TypeStr == "INTEGER":
                return int(ValueStr)
            elif TypeStr == "BOOLEAN":
                return ValueStr.lower() in ("true", "yes", "1", "t", "y")
            elif TypeStr == "FLOAT":
                return float(ValueStr)
            elif TypeStr == "JSON":
                return json.loads(ValueStr)
            else:  # Default to TEXT
                return ValueStr
        except Exception as e:
            self.Logger.warning(f"Error converting value '{ValueStr}' to type {TypeStr}: {e}")
            return ValueStr
    
    def ConvertValueToString(self, Value, TypeStr):
        """
        Convert a value to a string for storage.
        
        Args:
            Value (Any): Value to convert
            TypeStr (str): Type to convert from (INTEGER, BOOLEAN, TEXT, FLOAT, JSON)
            
        Returns:
            str: String representation of the value
        """
        if Value is None:
            return None
        
        try:
            if TypeStr == "JSON":
                return json.dumps(Value)
            elif TypeStr == "BOOLEAN":
                return "true" if Value else "false"
            else:
                return str(Value)
        except Exception as e:
            self.Logger.warning(f"Error converting value of type {type(Value)} to string: {e}")
            return str(Value)
    
    def GetConfig(self, Key, DefaultValue=None):
        """
        Get a configuration value.
        
        Args:
            Key (str): Configuration key
            DefaultValue (Any, optional): Default value if key doesn't exist
            
        Returns:
            Any: Configuration value
        """
        with self.CacheLock:
            if Key in self.ConfigCache:
                return self.ConfigCache[Key]
        
        # If not in cache, try to load from database
        try:
            Query = """
                SELECT ConfigValue, ConfigType, DefaultValue 
                FROM Configuration 
                WHERE ConfigKey = ?
            """
            Rows = self.DatabaseManager.ExecuteQuery(Query, (Key,))
            
            if Rows:
                Row = Rows[0]
                Value = self.ConvertValueFromString(Row['ConfigValue'], Row['ConfigType'])
                
                # Update cache
                with self.CacheLock:
                    self.ConfigCache[Key] = Value
                
                return Value
            else:
                # If we have a default value supplied, use it
                if DefaultValue is not None:
                    return DefaultValue
                
                # Log warning for missing configuration
                self.Logger.warning(f"Configuration key '{Key}' not found")
                return None
        except Exception as e:
            self.Logger.error(f"Error getting configuration '{Key}': {e}")
            if DefaultValue is not None:
                return DefaultValue
            return None
    
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
        try:
            # Check if key exists
            Query = "SELECT COUNT(*) FROM Configuration WHERE ConfigKey = ?"
            Count = self.DatabaseManager.ExecuteScalar(Query, (Key,))
            
            # Convert value to string for storage
            ValueStr = self.ConvertValueToString(Value, Type)
            Timestamp = datetime.now().isoformat()
            
            if Count > 0:
                # Update existing key
                Query = """
                    UPDATE Configuration 
                    SET ConfigValue = ?, ConfigType = ?, LastModified = ?
                    WHERE ConfigKey = ?
                """
                Params = (ValueStr, Type, Timestamp, Key)
                
                if Description:
                    Query = """
                        UPDATE Configuration 
                        SET ConfigValue = ?, ConfigType = ?, LastModified = ?, Description = ?
                        WHERE ConfigKey = ?
                    """
                    Params = (ValueStr, Type, Timestamp, Description, Key)
                
                self.DatabaseManager.ExecuteNonQuery(Query, Params)
            else:
                # Insert new key
                DefaultValue = ValueStr
                ColumnDict = {
                    "ConfigKey": Key,
                    "ConfigValue": ValueStr,
                    "ConfigType": Type,
                    "DefaultValue": DefaultValue,
                    "LastModified": Timestamp
                }
                
                if Description:
                    ColumnDict["Description"] = Description
                
                self.DatabaseManager.InsertWithId("Configuration", ColumnDict)
            
            # Update cache
            with self.CacheLock:
                self.ConfigCache[Key] = Value
            
            self.Logger.info(f"Configuration '{Key}' set to '{Value}'")
            return True
        except Exception as e:
            self.Logger.error(f"Error setting configuration '{Key}': {e}")
            return False
    
    def DeleteConfig(self, Key):
        """
        Delete a configuration entry.
        
        Args:
            Key (str): Configuration key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            Query = "DELETE FROM Configuration WHERE ConfigKey = ?"
            RowsAffected = self.DatabaseManager.ExecuteNonQuery(Query, (Key,))
            
            # Remove from cache
            with self.CacheLock:
                if Key in self.ConfigCache:
                    del self.ConfigCache[Key]
            
            self.Logger.info(f"Configuration '{Key}' deleted")
            return RowsAffected > 0
        except Exception as e:
            self.Logger.error(f"Error deleting configuration '{Key}': {e}")
            return False
    
    def GetAllConfig(self):
        """
        Get all configuration values.
        
        Returns:
            dict: Dictionary of all configuration key-value pairs
        """
        try:
            # Return a copy of the cache to prevent modification
            with self.CacheLock:
                return dict(self.ConfigCache)
        except Exception as e:
            self.Logger.error(f"Error getting all configuration: {e}")
            return {}
    
    def GetConfigDetails(self, Key):
        """
        Get detailed information about a configuration key.
        
        Args:
            Key (str): Configuration key
            
        Returns:
            dict: Dictionary with details or None if not found
        """
        try:
            Query = """
                SELECT ConfigKey, ConfigValue, ConfigType, DefaultValue, Description, LastModified
                FROM Configuration
                WHERE ConfigKey = ?
            """
            Rows = self.DatabaseManager.ExecuteQuery(Query, (Key,))
            
            if Rows:
                Row = Rows[0]
                Value = self.ConvertValueFromString(Row['ConfigValue'], Row['ConfigType'])
                return {
                    "Key": Row['ConfigKey'],
                    "Value": Value,
                    "Type": Row['ConfigType'],
                    "DefaultValue": self.ConvertValueFromString(Row['DefaultValue'], Row['ConfigType']),
                    "Description": Row['Description'],
                    "LastModified": Row['LastModified']
                }
            return None
        except Exception as e:
            self.Logger.error(f"Error getting configuration details for '{Key}': {e}")
            return None
    
    def GetAllConfigDetails(self):
        """
        Get detailed information about all configuration keys.
        
        Returns:
            list: List of dictionaries with configuration details
        """
        try:
            Query = """
                SELECT ConfigKey, ConfigValue, ConfigType, DefaultValue, Description, LastModified
                FROM Configuration
                ORDER BY ConfigKey
            """
            Rows = self.DatabaseManager.ExecuteQuery(Query)
            
            Result = []
            for Row in Rows:
                Value = self.ConvertValueFromString(Row['ConfigValue'], Row['ConfigType'])
                Result.append({
                    "Key": Row['ConfigKey'],
                    "Value": Value,
                    "Type": Row['ConfigType'],
                    "DefaultValue": self.ConvertValueFromString(Row['DefaultValue'], Row['ConfigType']),
                    "Description": Row['Description'],
                    "LastModified": Row['LastModified']
                })
            
            return Result
        except Exception as e:
            self.Logger.error(f"Error getting all configuration details: {e}")
            return []
    
    def ResetToDefault(self, Key):
        """
        Reset a configuration value to its default.
        
        Args:
            Key (str): Configuration key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            Query = """
                UPDATE Configuration
                SET ConfigValue = DefaultValue, LastModified = ?
                WHERE ConfigKey = ?
            """
            Timestamp = datetime.now().isoformat()
            RowsAffected = self.DatabaseManager.ExecuteNonQuery(Query, (Timestamp, Key))
            
            # Update cache
            if RowsAffected > 0:
                # Get the updated value
                Query = "SELECT DefaultValue, ConfigType FROM Configuration WHERE ConfigKey = ?"
                Rows = self.DatabaseManager.ExecuteQuery(Query, (Key,))
                
                if Rows:
                    Row = Rows[0]
                    Value = self.ConvertValueFromString(Row['DefaultValue'], Row['ConfigType'])
                    
                    with self.CacheLock:
                        self.ConfigCache[Key] = Value
            
                self.Logger.info(f"Configuration '{Key}' reset to default")
                return True
            
            self.Logger.warning(f"Configuration '{Key}' not found for reset")
            return False
        except Exception as e:
            self.Logger.error(f"Error resetting configuration '{Key}': {e}")
            return False
    
    def ResetAllToDefault(self):
        """
        Reset all configuration values to their defaults.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            Query = """
                UPDATE Configuration
                SET ConfigValue = DefaultValue, LastModified = ?
            """
            Timestamp = datetime.now().isoformat()
            self.DatabaseManager.ExecuteNonQuery(Query, (Timestamp,))
            
            # Reload cache
            self.LoadAllConfig()
            
            self.Logger.info("All configuration reset to defaults")
            return True
        except Exception as e:
            self.Logger.error(f"Error resetting all configuration: {e}")
            return False
    
    def GetConfigByGroup(self, GroupPrefix):
        """
        Get configuration values that belong to a group (by prefix).
        
        Args:
            GroupPrefix (str): Prefix that defines the group
            
        Returns:
            dict: Dictionary of configuration values in the group
        """
        try:
            Query = """
                SELECT ConfigKey, ConfigValue, ConfigType
                FROM Configuration
                WHERE ConfigKey LIKE ?
                ORDER BY ConfigKey
            """
            Rows = self.DatabaseManager.ExecuteQuery(Query, (f"{GroupPrefix}%",))
            
            Result = {}
            for Row in Rows:
                Key = Row['ConfigKey']
                Value = self.ConvertValueFromString(Row['ConfigValue'], Row['ConfigType'])
                # Remove the prefix if desired
                ShortKey = Key[len(GroupPrefix):] if Key.startswith(GroupPrefix) else Key
                Result[ShortKey] = Value
            
            return Result
        except Exception as e:
            self.Logger.error(f"Error getting configuration group '{GroupPrefix}': {e}")
            return {}
    
    def ExportConfig(self, FilePath=None):
        """
        Export all configuration to a JSON file.
        
        Args:
            FilePath (str, optional): Path for the export file
            
        Returns:
            str: Path to the export file
        """
        try:
            import os
            from datetime import datetime
            
            if not FilePath:
                Timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                FilePath = f"State/Export/config_export_{Timestamp}.json"
            
            # Ensure export directory exists
            os.makedirs(os.path.dirname(FilePath), exist_ok=True)
            
            ConfigData = self.GetAllConfigDetails()
            
            with open(FilePath, 'w') as f:
                json.dump(ConfigData, f, indent=2)
            
            self.Logger.info(f"Configuration exported to {FilePath}")
            return FilePath
        except Exception as e:
            self.Logger.error(f"Error exporting configuration: {e}")
            return None
    
    def ImportConfig(self, FilePath):
        """
        Import configuration from a JSON file.
        
        Args:
            FilePath (str): Path to the import file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(FilePath, 'r') as f:
                ConfigData = json.load(f)
            
            # Begin transaction for atomic import
            self.DatabaseManager.BeginTransaction()
            
            ImportCount = 0
            for Item in ConfigData:
                if "Key" in Item and "Value" in Item:
                    Type = Item.get("Type", "TEXT")
                    Description = Item.get("Description")
                    
                    self.SetConfig(Item["Key"], Item["Value"], Type, Description)
                    ImportCount += 1
            
            # Commit the transaction
            self.DatabaseManager.CommitTransaction()
            
            # Reload cache to ensure consistency
            self.LoadAllConfig()
            
            self.Logger.info(f"Imported {ImportCount} configuration items from {FilePath}")
            return True
        except Exception as e:
            # Rollback on error
            self.DatabaseManager.RollbackTransaction()
            self.Logger.error(f"Error importing configuration: {e}")
            return False
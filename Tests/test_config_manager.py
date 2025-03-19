# File: test_config_manager.py
# Path: AIDEV-Hub/Tests/test_config_manager.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-19
# Last Modified: 2025-03-19  10:00AM
# Description: Unit tests for the ConfigManager class

import os
import unittest
import tempfile
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Core.DatabaseManager import DatabaseManager
from Core.ConfigManager import ConfigManager

class TestConfigManager(unittest.TestCase):
    """Tests for the ConfigManager class."""
    
    def setUp(self):
        """Set up for each test by creating a temporary database."""
        # Create a temporary directory and database
        self.TempDir = tempfile.TemporaryDirectory()
        self.DbPath = os.path.join(self.TempDir.name, "test_config.db")
        
        # Initialize database and config manager
        self.DatabaseManager = DatabaseManager(self.DbPath)
        self.ConfigManager = ConfigManager(self.DatabaseManager)
    
    def tearDown(self):
        """Clean up after each test."""
        self.DatabaseManager.CloseConnections()
        self.TempDir.cleanup()
    
    def test_get_config_with_cache(self):
        """Test getting a configuration value from cache."""
        # Set up test data
        TestKey = "TEST_CONFIG"
        TestValue = "test_value"
        
        # Insert directly into cache
        with self.ConfigManager.CacheLock:
            self.ConfigManager.ConfigCache[TestKey] = TestValue
        
        # Get the value
        Value = self.ConfigManager.GetConfig(TestKey)
        
        # Verify result
        self.assertEqual(Value, TestValue)
    
    def test_get_config_from_database(self):
        """Test getting a configuration value from the database."""
        # Set up test data
        TestKey = "DB_CONFIG"
        TestValue = "db_value"
        
        # Insert directly into database
        ColumnDict = {
            "ConfigKey": TestKey,
            "ConfigValue": TestValue,
            "ConfigType": "TEXT",
            "DefaultValue": TestValue,
            "LastModified": datetime.now().isoformat()
        }
        self.DatabaseManager.InsertWithId("Configuration", ColumnDict)
        
        # Clear cache to force database lookup
        with self.ConfigManager.CacheLock:
            self.ConfigManager.ConfigCache.clear()
        
        # Get the value
        Value = self.ConfigManager.GetConfig(TestKey)
        
        # Verify result
        self.assertEqual(Value, TestValue)
        
        # Verify value was cached
        with self.ConfigManager.CacheLock:
            self.assertIn(TestKey, self.ConfigManager.ConfigCache)
            self.assertEqual(self.ConfigManager.ConfigCache[TestKey], TestValue)
    
    def test_get_config_with_default(self):
        """Test getting a non-existent configuration with default value."""
        # Set up test data
        TestKey = "NONEXISTENT_CONFIG"
        DefaultValue = "default_value"
        
        # Get the value with default
        Value = self.ConfigManager.GetConfig(TestKey, DefaultValue)
        
        # Verify result
        self.assertEqual(Value, DefaultValue)
    
    def test_set_config_new(self):
        """Test setting a new configuration value."""
        # Set up test data
        TestKey = "NEW_CONFIG"
        TestValue = "new_value"
        TestType = "TEXT"
        TestDesc = "Test description"
        
        # Set the value
        Result = self.ConfigManager.SetConfig(TestKey, TestValue, TestType, TestDesc)
        
        # Verify result
        self.assertTrue(Result)
        
        # Verify value was cached
        with self.ConfigManager.CacheLock:
            self.assertIn(TestKey, self.ConfigManager.ConfigCache)
            self.assertEqual(self.ConfigManager.ConfigCache[TestKey], TestValue)
        
        # Verify value was stored in database
        Query = """
            SELECT ConfigValue, ConfigType, Description
            FROM Configuration
            WHERE ConfigKey = ?
        """
        Results = self.DatabaseManager.ExecuteQuery(Query, (TestKey,))
        
        self.assertEqual(len(Results), 1)
        self.assertEqual(Results[0]["ConfigValue"], TestValue)
        self.assertEqual(Results[0]["ConfigType"], TestType)
        self.assertEqual(Results[0]["Description"], TestDesc)
    
    def test_set_config_update(self):
        """Test updating an existing configuration value."""
        # Set up test data
        TestKey = "UPDATE_CONFIG"
        OldValue = "old_value"
        NewValue = "new_value"
        
        # Insert initial value
        ColumnDict = {
            "ConfigKey": TestKey,
            "ConfigValue": OldValue,
            "ConfigType": "TEXT",
            "DefaultValue": OldValue,
            "LastModified": datetime.now().isoformat()
        }
        self.DatabaseManager.InsertWithId("Configuration", ColumnDict)
        
        # Update the value
        Result = self.ConfigManager.SetConfig(TestKey, NewValue)
        
        # Verify result
        self.assertTrue(Result)
        
        # Verify value was updated in cache
        with self.ConfigManager.CacheLock:
            self.assertIn(TestKey, self.ConfigManager.ConfigCache)
            self.assertEqual(self.ConfigManager.ConfigCache[TestKey], NewValue)
        
        # Verify value was updated in database
        Query = "SELECT ConfigValue FROM Configuration WHERE ConfigKey = ?"
        Results = self.DatabaseManager.ExecuteQuery(Query, (TestKey,))
        
        self.assertEqual(len(Results), 1)
        self.assertEqual(Results[0]["ConfigValue"], NewValue)
    
    def test_convert_value_types(self):
        """Test converting values between different types."""
        # Set up test cases
        TestCases = [
            {"Value": "123", "Type": "INTEGER", "Expected": 123},
            {"Value": "3.14", "Type": "FLOAT", "Expected": 3.14},
            {"Value": "true", "Type": "BOOLEAN", "Expected": True},
            {"Value": "false", "Type": "BOOLEAN", "Expected": False},
            {"Value": '{"key": "value"}', "Type": "JSON", "Expected": {"key": "value"}},
            {"Value": "plain text", "Type": "TEXT", "Expected": "plain text"}
        ]
        
        for Case in TestCases:
            # Test conversion from string
            Result = self.ConfigManager.ConvertValueFromString(Case["Value"], Case["Type"])
            self.assertEqual(Result, Case["Expected"])
            
            # Test conversion to string
            StrResult = self.ConfigManager.ConvertValueToString(Case["Expected"], Case["Type"])
            
            # For JSON, we need to parse the result to compare objects
            if Case["Type"] == "JSON":
                self.assertEqual(json.loads(StrResult), Case["Expected"])
            elif Case["Type"] == "BOOLEAN":
                self.assertIn(StrResult.lower(), ["true", "false"])
            else:
                self.assertEqual(str(Case["Expected"]), StrResult)
    
    def test_delete_config(self):
        """Test deleting a configuration value."""
        # Set up test data
        TestKey = "DELETE_CONFIG"
        TestValue = "delete_me"
        
        # Insert the value
        ColumnDict = {
            "ConfigKey": TestKey,
            "ConfigValue": TestValue,
            "ConfigType": "TEXT",
            "DefaultValue": TestValue,
            "LastModified": datetime.now().isoformat()
        }
        self.DatabaseManager.InsertWithId("Configuration", ColumnDict)
        
        # Add to cache
        with self.ConfigManager.CacheLock:
            self.ConfigManager.ConfigCache[TestKey] = TestValue
        
        # Delete the value
        Result = self.ConfigManager.DeleteConfig(TestKey)
        
        # Verify result
        self.assertTrue(Result)
        
        # Verify removed from cache
        with self.ConfigManager.CacheLock:
            self.assertNotIn(TestKey, self.ConfigManager.ConfigCache)
        
        # Verify removed from database
        Query = "SELECT COUNT(*) FROM Configuration WHERE ConfigKey = ?"
        Count = self.DatabaseManager.ExecuteScalar(Query, (TestKey,))
        
        self.assertEqual(Count, 0)
    
    def test_get_all_config(self):
        """Test getting all configuration values."""
        # Set up test data
        TestConfigs = {
            "CONFIG1": "value1",
            "CONFIG2": "value2",
            "CONFIG3": "value3"
        }
        
        # Replace the entire cache instead of trying to match exactly
        with self.ConfigManager.CacheLock:
            self.ConfigManager.ConfigCache = dict(TestConfigs)
        
        # Get all values
        AllConfigs = self.ConfigManager.GetAllConfig()
        
        # Verify all test keys are present with correct values
        for Key, Value in TestConfigs.items():
            self.assertIn(Key, AllConfigs)
            self.assertEqual(AllConfigs[Key], Value)
    
    def test_reset_to_default(self):
        """Test resetting a configuration value to its default."""
        # Set up test data
        TestKey = "RESET_CONFIG"
        OriginalValue = "original"
        ModifiedValue = "modified"
        
        # Insert with default
        ColumnDict = {
            "ConfigKey": TestKey,
            "ConfigValue": ModifiedValue,
            "ConfigType": "TEXT",
            "DefaultValue": OriginalValue,
            "LastModified": datetime.now().isoformat()
        }
        self.DatabaseManager.InsertWithId("Configuration", ColumnDict)
        
        # Add to cache
        with self.ConfigManager.CacheLock:
            self.ConfigManager.ConfigCache[TestKey] = ModifiedValue
        
        # Mock the database query for getting updated value
        with patch.object(self.DatabaseManager, 'ExecuteQuery', return_value=[{
            "DefaultValue": OriginalValue,
            "ConfigType": "TEXT"
        }]):
            # Reset to default
            Result = self.ConfigManager.ResetToDefault(TestKey)
            
            # Verify result
            self.assertTrue(Result)
            
            # Verify cache was updated
            with self.ConfigManager.CacheLock:
                self.assertEqual(self.ConfigManager.ConfigCache[TestKey], OriginalValue)
    
    def test_get_config_by_group(self):
        """Test getting configuration values by group prefix."""
        # Set up test data with a common prefix
        Prefix = "GROUP_"
        TestConfigs = {
            f"{Prefix}ONE": "value1",
            f"{Prefix}TWO": "value2",
            f"{Prefix}THREE": "value3",
            "OTHER_CONFIG": "other_value"  # Should not be included in group
        }
        
        # Mock the database query
        with patch.object(self.DatabaseManager, 'ExecuteQuery', return_value=[
            {"ConfigKey": f"{Prefix}ONE", "ConfigValue": "value1", "ConfigType": "TEXT"},
            {"ConfigKey": f"{Prefix}TWO", "ConfigValue": "value2", "ConfigType": "TEXT"},
            {"ConfigKey": f"{Prefix}THREE", "ConfigValue": "value3", "ConfigType": "TEXT"}
        ]):
            # Get group configs
            GroupConfigs = self.ConfigManager.GetConfigByGroup(Prefix)
            
            # Verify results
            self.assertEqual(len(GroupConfigs), 3)  # Only the 3 with the prefix
            self.assertEqual(GroupConfigs["ONE"], "value1")  # Keys should have prefix removed
            self.assertEqual(GroupConfigs["TWO"], "value2")
            self.assertEqual(GroupConfigs["THREE"], "value3")
            self.assertNotIn("OTHER_CONFIG", GroupConfigs)

if __name__ == '__main__':
    unittest.main()
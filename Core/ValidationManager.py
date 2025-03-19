# File: ValidationManager.py
# Path: AIDEV-Hub/Core/ValidationManager.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-18
# Last Modified: 2025-03-18  6:45PM
# Description: Manages validation rules and validates input against them

import re
import logging
import uuid
import json
import threading
from datetime import datetime

class ValidationManager:
    """
    Manages validation rules and validates input.
    
    This class is responsible for:
    - Loading validation rules from the database
    - Validating input against rules
    - Managing rules for specific fields
    - Providing validation errors
    """
    
    def __init__(self, DatabaseManager):
        """Initialize the validation manager."""
        self.DatabaseManager = DatabaseManager
        self.RulesCache = {}
        self.FieldRulesCache = {}
        self.CacheLock = threading.RLock()
        
        # Set up logging
        self.Logger = logging.getLogger("ValidationManager")
        self.Logger.setLevel(logging.INFO)
        
        # Load validation rules
        self.LoadValidationRules()
        
        self.Logger.info("ValidationManager initialized")
    
    def LoadValidationRules(self):
        """Load validation rules from the database."""
        try:
            # Load rules
            Query = "SELECT RuleId, RuleType, Pattern, ErrorMessage FROM ValidationRules"
            Rules = self.DatabaseManager.ExecuteQuery(Query)
            
            # Load field rules
            FieldQuery = """
                SELECT FieldId, FieldName, ValidationRuleId, Required, Description 
                FROM InputFields
            """
            Fields = self.DatabaseManager.ExecuteQuery(FieldQuery)
            
            with self.CacheLock:
                # Clear existing cache
                self.RulesCache.clear()
                self.FieldRulesCache.clear()
                
                # Populate rules cache
                for Rule in Rules:
                    RuleDict = {
                        "RuleId": Rule["RuleId"],
                        "RuleType": Rule["RuleType"],
                        "Pattern": Rule["Pattern"],
                        "ErrorMessage": Rule["ErrorMessage"]
                    }
                    
                    # Cache by both ID and type for efficient lookup
                    self.RulesCache[Rule["RuleId"]] = RuleDict
                    
                    # Also store by rule type, assuming rule types are unique
                    # If multiple rules share the same type, this will keep the last one
                    self.RulesCache[Rule["RuleType"]] = RuleDict
                
                # Populate field rules cache
                for Field in Fields:
                    self.FieldRulesCache[Field["FieldName"]] = {
                        "FieldId": Field["FieldId"],
                        "ValidationRuleId": Field["ValidationRuleId"],
                        "Required": bool(Field["Required"]),
                        "Description": Field["Description"]
                    }
            
            self.Logger.info(f"Loaded {len(Rules)} validation rules and {len(Fields)} field rules")
        except Exception as e:
            self.Logger.error(f"Error loading validation rules: {e}")
            raise
    
    def RegisterRule(self, RuleType, Pattern, ErrorMessage, Description=None):
        """
        Register a validation rule.
        
        Args:
            RuleType (str): Type of rule (e.g., EMAIL, USERNAME)
            Pattern (str): Regular expression pattern for validation
            ErrorMessage (str): Error message to display on validation failure
            Description (str, optional): Description of the rule
            
        Returns:
            str: Rule ID if successful, None otherwise
        """
        try:
            # Check if rule type already exists
            Query = "SELECT COUNT(*) FROM ValidationRules WHERE RuleType = ?"
            Count = self.DatabaseManager.ExecuteScalar(Query, (RuleType,))
            
            if Count > 0:
                # Update existing rule
                UpdateQuery = """
                    UPDATE ValidationRules 
                    SET Pattern = ?, ErrorMessage = ?
                    WHERE RuleType = ?
                """
                Params = (Pattern, ErrorMessage, RuleType)
                
                if Description:
                    UpdateQuery = """
                        UPDATE ValidationRules 
                        SET Pattern = ?, ErrorMessage = ?, Description = ?
                        WHERE RuleType = ?
                    """
                    Params = (Pattern, ErrorMessage, Description, RuleType)
                
                self.DatabaseManager.ExecuteNonQuery(UpdateQuery, Params)
                
                # Get the ID
                IdQuery = "SELECT RuleId FROM ValidationRules WHERE RuleType = ?"
                RuleId = self.DatabaseManager.ExecuteScalar(IdQuery, (RuleType,))
            else:
                # Generate new rule ID
                RuleId = str(uuid.uuid4())
                
                # Insert new rule
                ColumnDict = {
                    "RuleId": RuleId,
                    "RuleType": RuleType,
                    "Pattern": Pattern,
                    "ErrorMessage": ErrorMessage
                }
                
                if Description:
                    ColumnDict["Description"] = Description
                
                self.DatabaseManager.InsertWithId("ValidationRules", ColumnDict)
            
            # Update cache
            with self.CacheLock:
                RuleDict = {
                    "RuleId": RuleId,
                    "RuleType": RuleType,
                    "Pattern": Pattern,
                    "ErrorMessage": ErrorMessage
                }
                
                self.RulesCache[RuleId] = RuleDict
                self.RulesCache[RuleType] = RuleDict
            
            self.Logger.info(f"Registered validation rule '{RuleType}' with ID {RuleId}")
            return RuleId
        except Exception as e:
            self.Logger.error(f"Error registering validation rule: {e}")
            return None
    
    def RegisterFieldRule(self, FieldName, RuleType, Required=False, Description=None):
        """
        Register a validation rule for a field.
        
        Args:
            FieldName (str): Name of the field
            RuleType (str): Type of validation rule to apply
            Required (bool, optional): Whether the field is required
            Description (str, optional): Description of the field
            
        Returns:
            str: Field ID if successful, None otherwise
        """
        try:
            # Get rule ID from type
            Rule = self.GetRuleByType(RuleType)
            if not Rule:
                self.Logger.error(f"Cannot register field rule: Rule type '{RuleType}' not found")
                return None
            
            # Check if field already exists
            Query = "SELECT COUNT(*) FROM InputFields WHERE FieldName = ?"
            Count = self.DatabaseManager.ExecuteScalar(Query, (FieldName,))
            
            if Count > 0:
                # Update existing field
                UpdateQuery = """
                    UPDATE InputFields 
                    SET ValidationRuleId = ?, Required = ?
                    WHERE FieldName = ?
                """
                Params = (Rule["RuleId"], 1 if Required else 0, FieldName)
                
                if Description:
                    UpdateQuery = """
                        UPDATE InputFields 
                        SET ValidationRuleId = ?, Required = ?, Description = ?
                        WHERE FieldName = ?
                    """
                    Params = (Rule["RuleId"], 1 if Required else 0, Description, FieldName)
                
                self.DatabaseManager.ExecuteNonQuery(UpdateQuery, Params)
                
                # Get the ID
                IdQuery = "SELECT FieldId FROM InputFields WHERE FieldName = ?"
                FieldId = self.DatabaseManager.ExecuteScalar(IdQuery, (FieldName,))
            else:
                # Generate new field ID
                FieldId = str(uuid.uuid4())
                
                # Insert new field
                ColumnDict = {
                    "FieldId": FieldId,
                    "FieldName": FieldName,
                    "ValidationRuleId": Rule["RuleId"],
                    "Required": 1 if Required else 0
                }
                
                if Description:
                    ColumnDict["Description"] = Description
                
                self.DatabaseManager.InsertWithId("InputFields", ColumnDict)
            
            # Update cache
            with self.CacheLock:
                self.FieldRulesCache[FieldName] = {
                    "FieldId": FieldId,
                    "ValidationRuleId": Rule["RuleId"],
                    "Required": Required,
                    "Description": Description
                }
            
            self.Logger.info(f"Registered field rule for '{FieldName}' with rule type '{RuleType}'")
            return FieldId
        except Exception as e:
            self.Logger.error(f"Error registering field rule: {e}")
            return None
    
    def GetRuleByType(self, RuleType):
        """
        Get a validation rule by its type.
        
        Args:
            RuleType (str): Type of rule to retrieve
            
        Returns:
            dict: Rule dictionary or None if not found
        """
        with self.CacheLock:
            Rule = self.RulesCache.get(RuleType)
            if Rule:
                return Rule
        
        # Not in cache, try database
        try:
            Query = "SELECT RuleId, RuleType, Pattern, ErrorMessage FROM ValidationRules WHERE RuleType = ?"
            Rules = self.DatabaseManager.ExecuteQuery(Query, (RuleType,))
            
            if Rules:
                Rule = {
                    "RuleId": Rules[0]["RuleId"],
                    "RuleType": Rules[0]["RuleType"],
                    "Pattern": Rules[0]["Pattern"],
                    "ErrorMessage": Rules[0]["ErrorMessage"]
                }
                
                # Update cache
                with self.CacheLock:
                    self.RulesCache[RuleType] = Rule
                    self.RulesCache[Rule["RuleId"]] = Rule
                
                return Rule
            
            return None
        except Exception as e:
            self.Logger.error(f"Error getting rule by type '{RuleType}': {e}")
            return None
    
    def GetRuleById(self, RuleId):
        """
        Get a validation rule by its ID.
        
        Args:
            RuleId (str): ID of rule to retrieve
            
        Returns:
            dict: Rule dictionary or None if not found
        """
        with self.CacheLock:
            Rule = self.RulesCache.get(RuleId)
            if Rule:
                return Rule
        
        # Not in cache, try database
        try:
            Query = "SELECT RuleId, RuleType, Pattern, ErrorMessage FROM ValidationRules WHERE RuleId = ?"
            Rules = self.DatabaseManager.ExecuteQuery(Query, (RuleId,))
            
            if Rules:
                Rule = {
                    "RuleId": Rules[0]["RuleId"],
                    "RuleType": Rules[0]["RuleType"],
                    "Pattern": Rules[0]["Pattern"],
                    "ErrorMessage": Rules[0]["ErrorMessage"]
                }
                
                # Update cache
                with self.CacheLock:
                    self.RulesCache[RuleId] = Rule
                    self.RulesCache[Rule["RuleType"]] = Rule
                
                return Rule
            
            return None
        except Exception as e:
            self.Logger.error(f"Error getting rule by ID '{RuleId}': {e}")
            return None
    
    def ValidateInput(self, Input, RuleType):
        """
        Validate input against a rule type.
        
        Args:
            Input (str): Input to validate
            RuleType (str): Type of rule to validate against
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Get rule by type
            Rule = self.GetRuleByType(RuleType)
            if not Rule:
                self.Logger.warning(f"Cannot validate: Rule type '{RuleType}' not found")
                return (False, f"Unknown validation rule: {RuleType}")
            
            # Check if input is None or empty
            if Input is None or Input == "":
                return (False, "Input cannot be empty")
            
            # Validate using regular expression
            Pattern = Rule["Pattern"]
            if re.match(Pattern, Input):
                return (True, None)
            else:
                return (False, Rule["ErrorMessage"])
        except Exception as e:
            self.Logger.error(f"Error validating input against rule '{RuleType}': {e}")
            return (False, f"Validation error: {str(e)}")
    
    def ValidateField(self, FieldName, Value):
        """
        Validate a specific field's value.
        
        Args:
            FieldName (str): Name of the field to validate
            Value (str): Value to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Get field rule
            FieldRule = None
            with self.CacheLock:
                FieldRule = self.FieldRulesCache.get(FieldName)
            
            if not FieldRule:
                # Try to load from database
                Query = """
                    SELECT FieldId, ValidationRuleId, Required, Description 
                    FROM InputFields 
                    WHERE FieldName = ?
                """
                Fields = self.DatabaseManager.ExecuteQuery(Query, (FieldName,))
                
                if Fields:
                    FieldRule = {
                        "FieldId": Fields[0]["FieldId"],
                        "ValidationRuleId": Fields[0]["ValidationRuleId"],
                        "Required": bool(Fields[0]["Required"]),
                        "Description": Fields[0]["Description"]
                    }
                    
                    # Update cache
                    with self.CacheLock:
                        self.FieldRulesCache[FieldName] = FieldRule
            
            if not FieldRule:
                self.Logger.warning(f"Cannot validate: Field '{FieldName}' not registered")
                return (False, f"Unknown field: {FieldName}")
            
            # Check if field is required
            if FieldRule["Required"] and (Value is None or Value == ""):
                return (False, f"Field '{FieldName}' is required")
            
            # If not required and empty, it's valid
            if not FieldRule["Required"] and (Value is None or Value == ""):
                return (True, None)
            
            # Get the rule and validate
            Rule = self.GetRuleById(FieldRule["ValidationRuleId"])
            if not Rule:
                self.Logger.warning(f"Cannot validate: Rule ID '{FieldRule['ValidationRuleId']}' not found")
                return (False, f"Unknown validation rule for field: {FieldName}")
            
            # Validate using regular expression
            Pattern = Rule["Pattern"]
            if re.match(Pattern, Value):
                return (True, None)
            else:
                return (False, Rule["ErrorMessage"])
        except Exception as e:
            self.Logger.error(f"Error validating field '{FieldName}': {e}")
            return (False, f"Validation error: {str(e)}")
    
    def ValidateObject(self, Object):
        """
        Validate an object against field rules.
        
        Args:
            Object (dict): Object with field-value pairs to validate
            
        Returns:
            tuple: (is_valid, errors_dict)
        """
        try:
            Errors = {}
            
            for FieldName, Value in Object.items():
                IsValid, ErrorMessage = self.ValidateField(FieldName, Value)
                if not IsValid:
                    Errors[FieldName] = ErrorMessage
            
            # Check for missing required fields
            with self.CacheLock:
                for FieldName, FieldRule in self.FieldRulesCache.items():
                    if FieldRule["Required"] and FieldName not in Object:
                        Errors[FieldName] = f"Field '{FieldName}' is required"
            
            return (len(Errors) == 0, Errors)
        except Exception as e:
            self.Logger.error(f"Error validating object: {e}")
            return (False, {"general": f"Validation error: {str(e)}"})
    
    def DeleteRule(self, RuleType):
        """
        Delete a validation rule.
        
        Args:
            RuleType (str): Type of rule to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Begin transaction
            self.DatabaseManager.BeginTransaction()
            
            # Get rule ID
            Rule = self.GetRuleByType(RuleType)
            if not Rule:
                self.Logger.warning(f"Cannot delete: Rule type '{RuleType}' not found")
                self.DatabaseManager.RollbackTransaction()
                return False
            
            RuleId = Rule["RuleId"]
            
            # First update any fields using this rule to set them to NULL
            UpdateQuery = """
                UPDATE InputFields
                SET ValidationRuleId = NULL
                WHERE ValidationRuleId = ?
            """
            self.DatabaseManager.ExecuteNonQuery(UpdateQuery, (RuleId,))
            
            # Then delete the rule
            DeleteQuery = "DELETE FROM ValidationRules WHERE RuleId = ?"
            RowsAffected = self.DatabaseManager.ExecuteNonQuery(DeleteQuery, (RuleId,))
            
            # Commit transaction
            self.DatabaseManager.CommitTransaction()
            
            # Update cache
            with self.CacheLock:
                if RuleId in self.RulesCache:
                    del self.RulesCache[RuleId]
                if RuleType in self.RulesCache:
                    del self.RulesCache[RuleType]
            
            self.Logger.info(f"Deleted validation rule '{RuleType}' with ID {RuleId}")
            return RowsAffected > 0
        except Exception as e:
            self.DatabaseManager.RollbackTransaction()
            self.Logger.error(f"Error deleting rule '{RuleType}': {e}")
            return False
    
    def DeleteFieldRule(self, FieldName):
        """
        Delete a field rule.
        
        Args:
            FieldName (str): Name of field to delete rule for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get field ID
            FieldRule = None
            with self.CacheLock:
                FieldRule = self.FieldRulesCache.get(FieldName)
            
            if not FieldRule:
                self.Logger.warning(f"Cannot delete: Field rule '{FieldName}' not found")
                return False
            
            FieldId = FieldRule["FieldId"]
            
            # Delete the field rule
            DeleteQuery = "DELETE FROM InputFields WHERE FieldId = ?"
            RowsAffected = self.DatabaseManager.ExecuteNonQuery(DeleteQuery, (FieldId,))
            
            # Update cache
            with self.CacheLock:
                if FieldName in self.FieldRulesCache:
                    del self.FieldRulesCache[FieldName]
            
            self.Logger.info(f"Deleted field rule for '{FieldName}'")
            return RowsAffected > 0
        except Exception as e:
            self.Logger.error(f"Error deleting field rule '{FieldName}': {e}")
            return False
    
    def GetAllRules(self):
        """
        Get all validation rules.
        
        Returns:
            list: List of rule dictionaries
        """
        try:
            Query = """
                SELECT RuleId, RuleType, Pattern, ErrorMessage, Description
                FROM ValidationRules
                ORDER BY RuleType
            """
            Rules = self.DatabaseManager.ExecuteQuery(Query)
            
            return Rules
        except Exception as e:
            self.Logger.error(f"Error getting all rules: {e}")
            return []
    
    def GetAllFieldRules(self):
        """
        Get all field rules.
        
        Returns:
            list: List of field rule dictionaries
        """
        try:
            Query = """
                SELECT f.FieldId, f.FieldName, f.ValidationRuleId, f.Required, f.Description,
                       r.RuleType, r.Pattern, r.ErrorMessage
                FROM InputFields f
                LEFT JOIN ValidationRules r ON f.ValidationRuleId = r.RuleId
                ORDER BY f.FieldName
            """
            Fields = self.DatabaseManager.ExecuteQuery(Query)
            
            return Fields
        except Exception as e:
            self.Logger.error(f"Error getting all field rules: {e}")
            return []
    
    def ValidateEmailFormat(self, Email):
        """
        Validate an email format.
        
        Args:
            Email (str): Email to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        return self.ValidateInput(Email, "EMAIL")
    
    def ValidateUsernameFormat(self, Username):
        """
        Validate a username format.
        
        Args:
            Username (str): Username to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        return self.ValidateInput(Username, "USERNAME")
    
    def ValidatePathFormat(self, Path):
        """
        Validate a file path format.
        
        Args:
            Path (str): File path to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        return self.ValidateInput(Path, "PATH")
    
    def ValidateUrlFormat(self, Url):
        """
        Validate a URL format.
        
        Args:
            Url (str): URL to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        return self.ValidateInput(Url, "URL")
    
    def ValidateIpAddressFormat(self, IpAddress):
        """
        Validate an IP address format.
        
        Args:
            IpAddress (str): IP address to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        return self.ValidateInput(IpAddress, "IPADDRESS")
    
    def AddCustomRule(self, RuleType, Pattern, ErrorMessage, Description=None):
        """
        Add a custom validation rule.
        
        Args:
            RuleType (str): Unique type for the rule
            Pattern (str): Regular expression pattern
            ErrorMessage (str): Error message on validation failure
            Description (str, optional): Description of the rule
            
        Returns:
            str: Rule ID if successful, None otherwise
        """
        # Validate the pattern by trying to compile it
        try:
            re.compile(Pattern)
        except re.error as e:
            self.Logger.error(f"Invalid regular expression pattern: {e}")
            return None
        
        return self.RegisterRule(RuleType, Pattern, ErrorMessage, Description)
    
    def ExportRules(self, FilePath=None):
        """
        Export all validation rules to a JSON file.
        
        Args:
            FilePath (str, optional): Path for the export file
            
        Returns:
            str: Path to the export file
        """
        try:
            import os
            
            if not FilePath:
                Timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                FilePath = f"State/Export/validation_rules_{Timestamp}.json"
            
            # Ensure export directory exists
            os.makedirs(os.path.dirname(FilePath), exist_ok=True)
            
            # Get all rules and field rules
            Rules = self.GetAllRules()
            FieldRules = self.GetAllFieldRules()
            
            ExportData = {
                "Rules": Rules,
                "FieldRules": FieldRules
            }
            
            with open(FilePath, 'w') as f:
                json.dump(ExportData, f, indent=2)
            
            self.Logger.info(f"Validation rules exported to {FilePath}")
            return FilePath
        except Exception as e:
            self.Logger.error(f"Error exporting validation rules: {e}")
            return None
    
    def ImportRules(self, FilePath):
        """
        Import validation rules from a JSON file.
        
        Args:
            FilePath (str): Path to the import file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(FilePath, 'r') as f:
                ImportData = json.load(f)
            
            # Begin transaction for atomic import
            self.DatabaseManager.BeginTransaction()
            
            # Import rules
            RuleCount = 0
            if "Rules" in ImportData:
                for Rule in ImportData["Rules"]:
                    if "RuleType" in Rule and "Pattern" in Rule and "ErrorMessage" in Rule:
                        Description = Rule.get("Description")
                        self.RegisterRule(Rule["RuleType"], Rule["Pattern"], Rule["ErrorMessage"], Description)
                        RuleCount += 1
            
            # Import field rules
            FieldCount = 0
            if "FieldRules" in ImportData:
                for Field in ImportData["FieldRules"]:
                    if "FieldName" in Field and "RuleType" in Field:
                        Required = Field.get("Required", False)
                        Description = Field.get("Description")
                        self.RegisterFieldRule(Field["FieldName"], Field["RuleType"], Required, Description)
                        FieldCount += 1
            
            # Commit transaction
            self.DatabaseManager.CommitTransaction()
            
            # Reload rules to ensure cache consistency
            self.LoadValidationRules()
            
            self.Logger.info(f"Imported {RuleCount} rules and {FieldCount} field rules from {FilePath}")
            return True
        except Exception as e:
            # Rollback on error
            self.DatabaseManager.RollbackTransaction()
            self.Logger.error(f"Error importing validation rules: {e}")
            return False
# File: SessionRelationships.py
# Path: AIDEV-Hub/Core/SessionRelationships.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-18
# Last Modified: 2025-03-18  5:00PM
# Description: Creates the session relationships table in the database

import sqlite3

def CreateSessionRelationshipsTable(db_path):
    """Create the SessionRelationships table if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create session relationships table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS SessionRelationships (
        RelationshipId INTEGER PRIMARY KEY AUTOINCREMENT,
        ParentSessionId TEXT,
        ChildSessionId TEXT,
        RelationType TEXT,
        FOREIGN KEY (ParentSessionId) REFERENCES Sessions (SessionId),
        FOREIGN KEY (ChildSessionId) REFERENCES Sessions (SessionId)
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"SessionRelationships table created in {db_path}")

if __name__ == "__main__":
    CreateSessionRelationshipsTable("../State/AIDevHub.db")

# Here are the SQLite commands for your needs:

## Print the Full Database Schema

sqlite3 ~/Desktop/AIDEV-Hub/State/AIDevHub.db .schema

**This will display all the CREATE TABLE statements and other schema-related definitions.**

## Rebuild the Database

To rebuild the database from a schema file, follow these steps:

### First, export the schema using:

sqlite3 ~/Desktop/AIDEV-Hub/State/AIDevHub.db .schema > schema.sql

### Then, create a new database and apply the schema:

sqlite3 new_database.db < schema.sql

## Dump the Database Contents

### To export both the schema and data (a full backup):

sqlite3 ~/Desktop/AIDEV-Hub/State/AIDevHub.db .dump > database_dump.sql

### To Import the Dump into a New Database

sqlite3 new_database.db < database_dump.sql

This will recreate the tables and populate them with the existing data.

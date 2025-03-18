#!/bin/bash
# File: setup-aidev-hub.sh
# Path: AIDEV-Hub/setup-aidev-hub.sh
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-18
# Last Modified: 2025-03-18  11:00AM
# Description: Setup script for AI Collaboration Hub (AIDEV-Hub)

# Exit on error
set -e

# Define color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up AI Collaboration Hub (AIDEV-Hub)...${NC}"

# Create project root directory on desktop
PROJECT_ROOT="$HOME/Desktop/AIDEV-Hub"
mkdir -p "$PROJECT_ROOT"
echo -e "${GREEN}Created project root directory: $PROJECT_ROOT${NC}"

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
python3 -m venv "$PROJECT_ROOT/.venv"

# Check if sqlite3 is installed
if ! command -v sqlite3 &> /dev/null
then
  echo -e "${RED}sqlite3 is not installed. Please install it using: sudo apt-get install sqlite3${NC}"
  exit 1
fi

source "$PROJECT_ROOT/.venv/bin/activate"
echo -e "${GREEN}Virtual environment created and activated.${NC}"

# Create requirements.txt if it doesn't exist
if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
  echo -e "${BLUE}Creating requirements.txt...${NC}"
  touch "$PROJECT_ROOT/requirements.txt"
  echo -e "${GREEN}Created requirements.txt${NC}"
fi

# Install requirements if requirements.txt exists
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
  echo -e "${BLUE}Installing requirements...${NC}"
  pip install -r "$PROJECT_ROOT/requirements.txt"
else
  echo -e "${RED}No requirements.txt found. Skipping dependency installation.${NC}"
fi

# Verify SQLite3 availability using Python
echo -e "${BLUE}Verifying SQLite3 availability...${NC}"
python3 -c "import sqlite3; print('SQLite3 is available')" || {
  echo -e "${RED}SQLite3 is not available. Please install SQLite3 and try again.${NC}"
  exit 1
}

# Create required directories
mkdir -p "$PROJECT_ROOT/Core"
mkdir -p "$PROJECT_ROOT/UI"
mkdir -p "$PROJECT_ROOT/AI/Local"
mkdir -p "$PROJECT_ROOT/AI/Web"
mkdir -p "$PROJECT_ROOT/State"
mkdir -p "$PROJECT_ROOT/Session"
mkdir -p "$PROJECT_ROOT/Docs/Notes"
mkdir -p "$PROJECT_ROOT/Scripts"
mkdir -p "$PROJECT_ROOT/Tests"
echo -e "${GREEN}Created project directory structure${NC}"

# Create __init__.py files
touch "$PROJECT_ROOT/Core/__init__.py"
touch "$PROJECT_ROOT/AI/__init__.py"
touch "$PROJECT_ROOT/AI/Local/__init__.py"
touch "$PROJECT_ROOT/AI/Web/__init__.py"
touch "$PROJECT_ROOT/UI/__init__.py"

# Create SQLite database
echo -e "${BLUE}Creating SQLite database...${NC}"
sqlite3 "$PROJECT_ROOT/State/AIDevHub.db" << 'EOF'
-- Create tables
CREATE TABLE IF NOT EXISTS Sessions (
    SessionId TEXT PRIMARY KEY,
    StartTime TEXT NOT NULL,
    EndTime TEXT NOT NULL,
    Status TEXT NOT NULL,
    Summary TEXT,
    CrashRecoveryTime TEXT
);

CREATE TABLE IF NOT EXISTS AIModels (
    ModelId INTEGER PRIMARY KEY AUTOINCREMENT,
    ModelName TEXT NOT NULL UNIQUE,
    ModelType TEXT NOT NULL, -- 'Local' or 'Web'
    ApiEndpoint TEXT,
    Status TEXT NOT NULL,
    LastUpdated TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ModelCapabilities (
    CapabilityId INTEGER PRIMARY KEY AUTOINCREMENT,
    ModelId INTEGER NOT NULL,
    TaskType TEXT NOT NULL,
    Confidence REAL NOT NULL,
    FOREIGN KEY (ModelId) REFERENCES AIModels(ModelId)
);

CREATE TABLE IF NOT EXISTS Conversations (
    ConversationId TEXT PRIMARY KEY,
    SessionId TEXT NOT NULL,
    Title TEXT NOT NULL,
    StartTime TEXT NOT NULL,
    EndTime TEXT NOT NULL,
    Status TEXT NOT NULL,
    FOREIGN KEY (SessionId) REFERENCES Sessions(SessionId)
);

CREATE TABLE IF NOT EXISTS Messages (
    MessageId INTEGER PRIMARY KEY AUTOINCREMENT,
    ConversationId TEXT NOT NULL,
    ModelId INTEGER,
    Role TEXT NOT NULL, -- 'user', 'assistant', or 'system'
    Content TEXT NOT NULL,
    Timestamp TEXT NOT NULL,
    FOREIGN KEY (ConversationId) REFERENCES Conversations(ConversationId),
    FOREIGN KEY (ModelId) REFERENCES AIModels(ModelId)
);

CREATE TABLE IF NOT EXISTS TaskRouting (
    RuleId INTEGER PRIMARY KEY AUTOINCREMENT,
    TaskType TEXT NOT NULL,
    PreferredModelId INTEGER,
    Priority INTEGER NOT NULL,
    UserDefined BOOLEAN NOT NULL,
    FOREIGN KEY (PreferredModelId) REFERENCES AIModels(ModelId)
);
EOF
echo -e "${GREEN}Created SQLite database: $PROJECT_ROOT/State/AIDevHub.db${NC}"

echo -e "${GREEN}AI Collaboration Hub setup completed successfully.${NC}"

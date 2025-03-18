# AI Collaboration Hub Setup Instructions
**Created: March 18, 2025**

This document provides step-by-step instructions for setting up the AI Collaboration Hub (AIDEV-Hub) project on your system.

## Prerequisites

- Ubuntu Desktop 24.04 (or compatible Linux distribution)
- Git installed (`sudo apt install git`)
- Python 3.10+ installed (`python3 --version` to check)
- SQLite3 installed (`sudo apt install sqlite3`)
- GitHub account (username: CallMeChewy)

## Setup Steps

### 1. Download the Setup Script

First, download the setup script to your computer:

1. Create a temporary directory:
   ```bash
   mkdir -p ~/Desktop/temp
   cd ~/Desktop/temp
   ```

2. Save the `setup-aidev-hub.sh` script (from the provided artifact) to this directory.

3. Make the script executable:
   ```bash
   chmod +x setup-aidev-hub.sh
   ```

### 2. Run the Setup Script

Run the setup script to create the project structure:

```bash
./setup-aidev-hub.sh
```

This will:
- Create the AIDEV-Hub directory on your desktop
- Set up the required directory structure
- Initialize the SQLite database
- Create initial skeleton files

### 3. Initialize the GitHub Repository

1. Navigate to the AIDEV-Hub Scripts directory:
   ```bash
   cd ~/Desktop/AIDEV-Hub/Scripts
   ```

2. Run the GitHub setup script:
   ```bash
   ./github-setup.sh
   ```

3. Follow the instructions provided by the script to complete GitHub setup.

4. If you encounter an authentication error when pushing to GitHub:
   - Create a personal access token at: https://github.com/settings/tokens
   - Use this token instead of your password when prompted
   - Ensure the token has the "repo" scope

### 4. Install Required Packages

1. Navigate to the AIDEV-Hub directory:
   ```bash
   cd ~/Desktop/AIDEV-Hub
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

   If you prefer to use a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### 5. Test the Setup

Run the application to ensure everything is set up correctly:

```bash
python main.py
```

At this point, you should see a message indicating that the application started successfully, although it will just be a placeholder since the core components are not yet fully implemented.

## Project Structure

After setup, your project structure should look like this:

```
~/Desktop/AIDEV-Hub/
├── Core/               # Core functionality modules
│   ├── AIRouter.py
│   ├── StateManager.py
│   └── __init__.py
├── UI/                 # User interface components
│   ├── MainWindow.py
│   └── __init__.py
├── AI/                 # AI integration modules
│   ├── Local/          # Local AI model connectors
│   │   └── __init__.py
│   ├── Web/            # Web-based AI service connectors
│   │   └── __init__.py
│   └── __init__.py
├── State/              # State management and persistence
│   └── AIDevHub.db     # SQLite database for state persistence
├── Session/            # Session management and continuity
├── Docs/               # Documentation
│   └── Notes/          # Development notes and ideas
├── Scripts/            # Utility scripts
│   └── github-setup.sh
├── Tests/              # Test modules
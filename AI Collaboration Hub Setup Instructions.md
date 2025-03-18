# AI Collaboration Hub Setup Instructions
**Created: March 18, 2025 2:30 PM**

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
│   └── Temp/           # Temporary session files
├── Docs/               # Documentation
│   └── Notes/          # Development notes and ideas
├── Scripts/            # Utility scripts
│   └── github-setup.sh
├── Tests/              # Test modules
│   └── __init__.py
├── .gitignore          # Git ignore file
├── LICENSE             # MIT license file
├── README.md           # Project readme
├── main.py             # Main application entry point
└── requirements.txt    # Python dependencies
```

## Next Steps

After successfully setting up the project, you can begin development:

1. **Implement Core Components**:
   - Start with the StateManager to handle session persistence
   - Develop the AIRouter to manage task routing logic

2. **Set Up Local AI Integration**:
   - Implement connectors for local models (e.g., Ollama)
   - Create model loading and management functionality

3. **Develop Web AI Integration**:
   - Create API clients for web-based AI services
   - Implement authentication and request management

4. **Build User Interface**:
   - Develop the main application window
   - Create conversation and code display panels

5. **Integrate with AIDEV-State**:
   - Follow the AIDEV-State Integration Guide for ProjectHimalaya
   - Implement session continuity mechanisms

## Troubleshooting

### Common Setup Issues

1. **GitHub Authentication Errors**:
   - Use a personal access token instead of password
   - Ensure SSH keys are properly configured

2. **Python Package Installation Failures**:
   - Try upgrading pip: `pip install --upgrade pip`
   - Install development libraries: `sudo apt install python3-dev`

3. **Database Creation Errors**:
   - Ensure SQLite3 is installed: `sudo apt install sqlite3`
   - Check file permissions in the State directory

4. **Script Execution Failures**:
   - Ensure scripts have execute permissions: `chmod +x script.sh`
   - Check for line ending issues: `dos2unix script.sh`

### Getting Help

If you encounter issues not covered here:

1. Check the project GitHub repository for known issues
2. Create a new issue with detailed information about your problem
3. Include error messages and steps to reproduce the issue

## Maintenance

### Keeping the Project Updated

1. Pull the latest changes:
   ```bash
   cd ~/Desktop/AIDEV-Hub
   git pull
   ```

2. Update dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Database Management

The SQLite database is located at `~/Desktop/AIDEV-Hub/State/AIDevHub.db`. You can:

1. Backup the database:
   ```bash
   cp ~/Desktop/AIDEV-Hub/State/AIDevHub.db ~/Desktop/AIDEV-Hub/State/AIDevHub.db.backup
   ```

2. Reset the database:
   ```bash
   rm ~/Desktop/AIDEV-Hub/State/AIDevHub.db
   cd ~/Desktop/AIDEV-Hub
   python -c "from Scripts.db_init import initialize_database; initialize_database()"
   ```

---

*"Code is not merely functional—it is a visual medium that developers interact with for extended periods. The choices made in these standards prioritize the axis of symmetry, character distinction, readability at scale, and visual hierarchy."*

— Herbert J. Bowers

# AI Collaboration Hub - Setup Instructions

## Prerequisites
- **Python 3.8+** installed
- **SQLite3** available (bundled with Python or installable separately)
- **Bash** (for running the script)

## Installation Steps

1. **Run the Setup Script**
    ```bash
    chmod +x setup-aidev-hub.sh
    ./setup-aidev-hub.sh
    ```
    
2. **What the Script Does**
    - Creates the project directory at `~/Desktop/AIDEV-Hub`
    - Sets up a Python virtual environment in `.venv`
    - Activates the virtual environment
    - Installs dependencies using `requirements.txt` if available
    - Verifies SQLite3 availability using Python
    - Initializes the database using the provided schema

3. **Troubleshooting**
    - If `sqlite3: command not found` appears, ensure SQLite3 is installed:
      ```bash
      sudo apt update
      sudo apt install sqlite3
      ```
    - If Python is missing, install it using:
      ```bash
      sudo apt install python3 python3-venv python3-pip
      ```

4. **Starting the Project**
    After the script completes, activate the virtual environment:
    ```bash
    source ~/Desktop/AIDEV-Hub/.venv/bin/activate
    ```

5. **Next Steps**
    - Open the project directory: `cd ~/Desktop/AIDEV-Hub`
    - Start developing using your preferred IDE.
    - Deactivate the environment when finished using:
      ```bash
      deactivate
      ```


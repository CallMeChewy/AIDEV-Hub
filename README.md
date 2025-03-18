# AIDEV-State

AIDEV-State is a state management, session continuity, and crash recovery tool designed for ProjectHimalaya components. It provides a robust mechanism for maintaining state during development sessions, tracking changes to components, and recovering from crashes.

## Features

- **Session Management**: Track development sessions and generate continuity documents
- **Component Tracking**: Monitor file changes and dependencies between components
- **Action Tracking**: Safely execute actions with crash recovery capabilities
- **SQLite Integration**: Robust database-backed state persistence
- **Command-line Interface**: Simple commands for managing state
- **Shell Integration**: Easy-to-use command-line shortcuts

## Directory Structure

```
AIDEV-State/
├── Core/                  # Core modules
│   ├── ActionTracker.py   # Tracks actions and their artifacts
│   ├── ComponentTracker.py # Tracks component state
│   ├── SessionManager.py  # Manages session state
│   └── __init__.py
├── Actions/               # Action record files
├── ActionSummaries/       # Markdown summaries of actions
├── Examples/              # Example usage scripts
├── Generated/             # Generated artifacts
├── Session/               # Session state and continuity documents
│   └── state.db           # SQLite database file
├── Tests/                 # Test scripts
├── AIDEV-State.py         # Main entry point
└── README.md              # This file
```

## Usage

### Starting a Session

```bash
python AIDEV-State.py start
```

### Registering a Component

```bash
python AIDEV-State.py component register ComponentName /path/to/component
```

### Checking Status

```bash
python AIDEV-State.py status
```

### Ending a Session

```bash
python AIDEV-State.py end --summary "Description of what was done"
```

### Command-line Shortcuts

For more convenient usage, you can source the `state_monitor.sh` script:

```bash
source /path/to/state_monitor.sh
```

This provides the following commands:

- `startmon` - Start monitoring the current project
- `endmon` - End monitoring and generate a continuity document
- `monstat` - Check monitoring status

## Integration with Other Components

See the `Examples/` directory for examples of integrating AIDEV-State with other ProjectHimalaya components.

## Database Structure

AIDEV-State uses SQLite for state persistence. The database schema is defined in the `InitializeDatabase` method of the `AIDevState` class.

## Development

To run tests:

```bash
cd Tests
python -m unittest discover
```

## License

Copyright © 2025 Herbert J. Bowers. All rights reserved.

---

*"Code is not merely functional—it is a visual medium that developers interact with for extended periods. The choices made in these standards prioritize the axis of symmetry, character distinction, readability at scale, and visual hierarchy."*

— Herbert J. Bowers

## Setting Up AIDEV-State

To set up AIDEV-State for the first time:

1. Clone the repository or extract the archive
2. Run the setup script:
   ```bash
   ./setup.sh
   ```
3. Add the command-line shortcuts to your .bashrc (optional):
   ```bash
   echo "source $(pwd)/Scripts/state_monitor.sh" >> ~/.bashrc
   source ~/.bashrc
   ```
4. Set up GitHub integration (optional):
   ```bash
   cd AIDEV-State
   ./Scripts/GitHubSetup.sh init
   ```

For more detailed instructions, see the INSTALL.md file.

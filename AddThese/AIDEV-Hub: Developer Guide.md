# AIDEV-Hub: Developer Guide
**Created: March 19, 2025 7:15 PM**

## Introduction

AIDEV-Hub is a collaboration framework designed to maintain session continuity and context across AI development sessions. It helps solve common challenges in AI-human collaborative development, such as:

- Loss of context when sessions terminate unexpectedly
- Difficulty maintaining state across multiple sessions
- Tracking actions and their results over time
- Managing configuration consistently
- Validating inputs according to defined rules

This guide provides developers with information on how to use AIDEV-Hub effectively in their AI-assisted development projects.

## Key Features

- **Session Continuity**: Automatically recover from crashes and resume sessions
- **Context Management**: Store and retrieve contextual information between sessions
- **Action Tracking**: Record and monitor actions with detailed history
- **Configuration Management**: Centralized configuration with type validation
- **Validation Framework**: Define and enforce validation rules
- **Documentation Generation**: Automatically create continuity documents for reference

## Getting Started

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/username/AIDEV-Hub.git
   cd AIDEV-Hub
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the environment:
   ```bash
   python -m UI.Main
   ```

### Command Line Interface

AIDEV-Hub provides a command-line interface (CLI) for interacting with the system. The CLI is the primary interface for managing sessions, recording messages, executing actions, and managing context.

To start the CLI:

```bash
python -m UI.Main
```

## Core Functionality

### Session Management

Sessions are the foundation of AIDEV-Hub. Each session represents a development period with its own context, messages, and actions.

#### Starting a Session

When you start AIDEV-Hub, a new session is automatically created. You can see the current session ID in the startup message.

#### Viewing Session Status

To check the status of the current session:

```
AIDEV-Hub> status
```

This displays:
- Current session ID
- Start time
- Running duration
- Message count
- Action count
- Session status

#### Ending a Session

To properly end a session:

```
AIDEV-Hub> exit [optional summary]
```

This:
1. Updates the session status to "COMPLETED"
2. Moves session data to the completed sessions directory
3. Records the provided summary
4. Generates a final continuity document

#### Resuming a Crashed Session

If a session crashes (abnormal termination), you can resume it with:

```
AIDEV-Hub> resume <session_id>
```

This creates a new session that includes all context, messages, and actions from the crashed session.

### Context Management

Context allows you to store and retrieve data across sessions. This is especially useful for maintaining state during AI-human collaboration.

#### Viewing Context

To view all context data:

```
AIDEV-Hub> context
```

To view a specific context value:

```
AIDEV-Hub> context <key>
```

#### Setting Context

To set a context value:

```
AIDEV-Hub> context <key> <value>
```

Values can be simple strings or more complex JSON structures:

```
AIDEV-Hub> context user_info {"name": "John", "role": "Developer"}
```

#### Clearing Context

To clear all context:

```
AIDEV-Hub> clear_context
```

To clear a specific context key:

```
AIDEV-Hub> clear_context <key>
```

### Message Recording

Messages represent communications between participants (human, AI, system, etc.) in a session.

To record a message:

```
AIDEV-Hub> message <source> <content>
```

Example:

```
AIDEV-Hub> message User "Can you help me implement this feature?"
AIDEV-Hub> message Assistant "I'd be happy to help. Let's break down the requirements."
```

Messages are stored in the database and included in session continuity documents.

### Action Tracking

Actions represent tasks performed during a session. They have a defined lifecycle and store both parameters and results.

To execute and track an action:

```
AIDEV-Hub> action <action_type> [param1=value1 param2=value2 ...]
```

Example:

```
AIDEV-Hub> action CodeGeneration language=Python function_name=ProcessData
```

This records the action, executes it, and stores the result.

### Configuration Management

AIDEV-Hub provides centralized configuration management with type validation.

#### Viewing Configuration

To view all configuration:

```
AIDEV-Hub> config
```

To view a specific configuration value:

```
AIDEV-Hub> config <key>
```

#### Setting Configuration

To set a configuration value:

```
AIDEV-Hub> config <key> <value> [type] [description]
```

Example:

```
AIDEV-Hub> config MAX_MESSAGES_PER_SESSION 2000 INTEGER "Maximum messages allowed in a session"
```

### Input Validation

AIDEV-Hub includes a validation framework for ensuring input meets defined rules.

To validate input against a rule:

```
AIDEV-Hub> validate <rule_type> <input>
```

Example:

```
AIDEV-Hub> validate EMAIL user@example.com
```

### Continuity Documents

AIDEV-Hub automatically generates continuity documents that summarize the current session state.

To generate a continuity document:

```
AIDEV-Hub> continuity
```

This creates a Markdown document with:
- Session information
- Recent messages
- Recent actions
- Current context
- Next steps

These documents are crucial for maintaining continuity across development sessions.

## Advanced Usage

### Namespaced Context

Context can be organized using namespaces:

```python
# In Python code:
StateManager.SetNamespacedContext("project", "name", "AIDEV-Hub")
StateManager.SetNamespacedContext("project", "version", "1.0")

# Get all context in a namespace
ProjectContext = StateManager.GetNamespacedContext("project")
```

### Complex Actions

For complex actions that require tracking:

```python
def ComplexOperation(param1, param2):
    # Implementation here
    return {"result": "success", "data": processed_data}

Success, Result, ActionId = StateManager.ExecuteActionWithTracking(
    "COMPLEX_OPERATION", 
    ComplexOperation, 
    {"param1": value1, "param2": value2}
)
```

### Database Transactions

For operations that need transactional integrity:

```python
# Begin a transaction
StateManager.DatabaseManager.BeginTransaction()

try:
    # Perform multiple operations
    StateManager.SetContext("key1", "value1")
    StateManager.RecordMessage("User", "Message content")
    
    # Commit if all operations succeed
    StateManager.DatabaseManager.CommitTransaction()
except Exception as e:
    # Rollback on error
    StateManager.DatabaseManager.RollbackTransaction()
    raise
```

## Integration with AI-Human Collaborative Development

AIDEV-Hub is designed to enhance AI-human collaboration. Here are some best practices for integration:

### 1. Session Structure

- Start each development session with a clear focus
- Record key messages to provide context
- Set relevant context variables for the session
- End each session with a summary

### 2. Context Management

- Use namespaces to organize context data
- Set development focus in context for documentation generation
- Store next steps in context for session continuity
- Use context for passing data between sessions

### 3. Action Tracking

- Define clear action types for different operations
- Include sufficient parameters for action traceability
- Review action history to understand development progression
- Use action statistics to measure productivity

### 4. Documentation

- Generate continuity documents at the end of each session
- Use the documents to resume work in subsequent sessions
- Add metadata to improve document quality
- Follow the established template structure

## Troubleshooting

### Common Issues

#### Session Lock File Remains After Crash

**Symptom**: Unable to start a new session due to existing lock file.
**Solution**: Manually remove the lock file at `State/session.lock`.

#### Database Errors

**Symptom**: Errors related to database operations.
**Solution**: 
1. Check database connection
2. Verify database file exists and is not corrupted
3. Try creating a backup with `StateManager.DatabaseManager.CreateBackup()`

#### Context Not Persisting

**Symptom**: Context values are not available in subsequent sessions.
**Solution**:
1. Ensure session is ended properly
2. Check that context keys and values are valid
3. Verify state snapshots are being created

### Recovery Procedures

#### Recovering from Crash

1. Note the session ID from error messages
2. Start AIDEV-Hub and use `resume <session_id>`
3. Review the continuity document to understand the session state
4. Continue work from where you left off

#### Backing Up State

To create a backup of the current state:

```
AIDEV-Hub> backup
```

This creates a backup of the database and generates a continuity document.

## Best Practices

1. **End Sessions Properly**: Always use the `exit` command to end sessions properly.

2. **Meaningful Context Keys**: Use descriptive names for context keys, preferably with namespaces.

3. **Regular Continuity Documents**: Generate continuity documents regularly, not just at the end of sessions.

4. **Track Important Actions**: Define and track significant actions rather than trivial operations.

5. **Use Validation**: Implement validation rules for critical inputs to maintain data integrity.

6. **Meaningful Session Summaries**: Provide detailed summaries when ending sessions.

7. **Simulate Crashes During Testing**: Use `simulate_crash` command to test recovery procedures.

8. **Document Next Steps**: Always record next steps in context for future reference.

## System Architecture

For developers who need to extend or modify AIDEV-Hub, understanding the architecture is essential:

### Core Components

1. **StateManager**: Central coordinator for all components
2. **DatabaseManager**: Handles all database operations with transaction support
3. **ConfigManager**: Manages application configuration
4. **SessionManager**: Manages session lifecycle and state
5. **ActionTracker**: Tracks and manages actions
6. **ContextManager**: Manages context data
7. **ContinuityDocGenerator**: Generates session documentation
8. **ValidationManager**: Validates input against rules

### Component Interaction

- **StateManager** initializes and coordinates all other components
- **SessionManager** depends on **DatabaseManager** for persistence
- **ActionTracker** uses **SessionManager** to associate actions with sessions
- **ContextManager** uses **SessionManager** to store context in session state
- **ContinuityDocGenerator** uses information from all components

### Data Flow

1. User commands are processed by the CLI
2. CLI invokes appropriate methods on **StateManager**
3. **StateManager** delegates to specialized components
4. Results are returned to CLI and displayed to user
5. State changes are persisted to database
6. State snapshots are created at key points

## Conclusion

AIDEV-Hub provides a robust framework for maintaining continuity in AI-human collaborative development. By following this guide, developers can leverage its features to enhance their productivity and ensure reliable state management across sessions.

For further assistance, please refer to the documentation in the `Docs` directory or contact the project maintainers.

---

*"Code is not merely functional—it is a visual medium that developers interact with for extended periods. The choices made in these standards prioritize the axis of symmetry, character distinction, readability at scale, and visual hierarchy."*

— Herbert J. Bowers

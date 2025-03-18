# AIDEV-Hub Database Schema
**Created: March 18, 2025**

This document describes the SQLite database schema for AI Collaboration Hub. The database (`AIDevHub.db`) is structured to support session continuity, AI model management, conversation history, and task routing preferences.

## Schema Overview

```
Sessions
  ↓
  ↓ 1:N
  ↓
Conversations → → → → → → → → → →
  ↓                         ↑
  ↓ 1:N                     ↑ N:1
  ↓                         ↑
Messages → → → AIModels ← ModelCapabilities
                ↑
                ↑ N:1
                ↑
          TaskRouting
                ↑
                ↑ N:1
                ↑
       CodeContext
```

## Tables

### Sessions

Tracks application sessions, including start and end times, and crash recovery information.

| Column | Type | Description |
|--------|------|-------------|
| SessionId | TEXT | Primary key, unique identifier for the session |
| StartTime | TEXT | ISO format timestamp when session started |
| EndTime | TEXT | ISO format timestamp when session ended (null if active) |
| Status | TEXT | 'Active', 'Completed', or 'Crashed' |
| Summary | TEXT | Optional summary of the session |
| CrashRecoveryTime | TEXT | Timestamp of crash recovery (if applicable) |

### AIModels

Stores information about available AI models, both local and web-based.

| Column | Type | Description |
|--------|------|-------------|
| ModelId | INTEGER | Primary key, auto-incremented |
| ModelName | TEXT | Name of the AI model (unique) |
| ModelType | TEXT | 'Local' or 'Web' |
| ApiEndpoint | TEXT | API endpoint for web models (null for local) |
| Status | TEXT | 'Active', 'Inactive', or 'Error' |
| LastUpdated | TEXT | ISO format timestamp of last update |

### ModelCapabilities

Tracks what types of tasks each AI model is capable of handling and with what confidence level.

| Column | Type | Description |
|--------|------|-------------|
| CapabilityId | INTEGER | Primary key, auto-incremented |
| ModelId | INTEGER | Foreign key to AIModels.ModelId |
| TaskType | TEXT | Type of task (e.g., 'CodeCompletion', 'Documentation') |
| Confidence | REAL | Confidence score (0.0 to 1.0) |

### Conversations

Represents conversations with AI models, linked to sessions.

| Column | Type | Description |
|--------|------|-------------|
| ConversationId | TEXT | Primary key, unique identifier |
| SessionId | TEXT | Foreign key to Sessions.SessionId |
| Title | TEXT | Title of the conversation |
| StartTime | TEXT | ISO format timestamp when conversation started |
| EndTime | TEXT | ISO format timestamp when conversation ended (null if active) |
| Status | TEXT | 'Active', 'Completed', or 'Interrupted' |

### Messages

Stores individual messages within conversations.

| Column | Type | Description |
|--------|------|-------------|
| MessageId | INTEGER | Primary key, auto-incremented |
| ConversationId | TEXT | Foreign key to Conversations.ConversationId |
| ModelId | INTEGER | Foreign key to AIModels.ModelId (null for user messages) |
| Role | TEXT | 'user', 'assistant', or 'system' |
| Content | TEXT | Content of the message |
| Timestamp | TEXT | ISO format timestamp when message was sent |

### TaskRouting

Defines rules for routing tasks to specific AI models based on task type.

| Column | Type | Description |
|--------|------|-------------|
| RuleId | INTEGER | Primary key, auto-incremented |
| TaskType | TEXT | Type of task to route |
| PreferredModelId | INTEGER | Foreign key to AIModels.ModelId (null for auto-select) |
| Priority | INTEGER | Priority of the rule (higher numbers take precedence) |
| UserDefined | BOOLEAN | Whether the rule was defined by the user |

### CodeContext

Stores code snippets and files that provide context for conversations.

| Column | Type | Description |
|--------|------|-------------|
| ContextId | INTEGER | Primary key, auto-incremented |
| ConversationId | TEXT | Foreign key to Conversations.ConversationId |
| FilePath | TEXT | Path to the file providing context |
| FileContent | TEXT | Content of the file |
| AddedTimestamp | TEXT | ISO format timestamp when context was added |

## Default Data

The database is initialized with default task routing rules:

| TaskType | PreferredModelId | Priority | UserDefined |
|----------|------------------|----------|-------------|
| CodeCompletion | NULL | 10 | 0 |
| Documentation | NULL | 10 | 0 |
| Brainstorming | NULL | 10 | 0 |
| Debugging | NULL | 10 | 0 |
| Refactoring | NULL | 10 | 0 |

When `PreferredModelId` is `NULL`, the system will automatically select the most appropriate model based on capabilities and availability.

## Relationships

- A **Session** can have multiple **Conversations**
- A **Conversation** can have multiple **Messages**
- A **Message** can be associated with one **AIModel** (or none for user messages)
- An **AIModel** can have multiple **ModelCapabilities**
- A **TaskType** can have multiple routing **Rules**
- A **Conversation** can have multiple **CodeContext** items

## Schema Evolution

As the application evolves, the schema may need to be updated. When making changes:

1. Create a migration script in the `Scripts` directory
2. Use SQLite's `ALTER TABLE` statements where possible
3. For complex changes, create a new table and migrate data
4. Update the version number in the database metadata

## Usage Notes

1. All timestamps are stored in ISO format (YYYY-MM-DDTHH:MM:SS.sssZ)
2. Session and Conversation IDs use UUID format for uniqueness
3. The database file should be included in version control
4. Regular backups of the database are recommended

---

*"Code is not merely functional—it is a visual medium that developers interact with for extended periods. The choices made in these standards prioritize the axis of symmetry, character distinction, readability at scale, and visual hierarchy."*

— Herbert J. Bowers

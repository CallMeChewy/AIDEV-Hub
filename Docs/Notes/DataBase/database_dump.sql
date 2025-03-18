PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE Sessions (
    SessionId TEXT PRIMARY KEY,
    StartTime TEXT NOT NULL,
    EndTime TEXT NOT NULL,
    Status TEXT NOT NULL,
    Summary TEXT,
    CrashRecoveryTime TEXT
);
CREATE TABLE AIModels (
    ModelId INTEGER PRIMARY KEY AUTOINCREMENT,
    ModelName TEXT NOT NULL UNIQUE,
    ModelType TEXT NOT NULL, -- 'Local' or 'Web'
    ApiEndpoint TEXT,
    Status TEXT NOT NULL,
    LastUpdated TEXT NOT NULL
);
CREATE TABLE ModelCapabilities (
    CapabilityId INTEGER PRIMARY KEY AUTOINCREMENT,
    ModelId INTEGER NOT NULL,
    TaskType TEXT NOT NULL,
    Confidence REAL NOT NULL,
    FOREIGN KEY (ModelId) REFERENCES AIModels(ModelId)
);
CREATE TABLE Conversations (
    ConversationId TEXT PRIMARY KEY,
    SessionId TEXT NOT NULL,
    Title TEXT NOT NULL,
    StartTime TEXT NOT NULL,
    EndTime TEXT NOT NULL,
    Status TEXT NOT NULL,
    FOREIGN KEY (SessionId) REFERENCES Sessions(SessionId)
);
CREATE TABLE Messages (
    MessageId INTEGER PRIMARY KEY AUTOINCREMENT,
    ConversationId TEXT NOT NULL,
    ModelId INTEGER,
    Role TEXT NOT NULL, -- 'user', 'assistant', or 'system'
    Content TEXT NOT NULL,
    Timestamp TEXT NOT NULL,
    FOREIGN KEY (ConversationId) REFERENCES Conversations(ConversationId),
    FOREIGN KEY (ModelId) REFERENCES AIModels(ModelId)
);
CREATE TABLE TaskRouting (
    RuleId INTEGER PRIMARY KEY AUTOINCREMENT,
    TaskType TEXT NOT NULL,
    PreferredModelId INTEGER,
    Priority INTEGER NOT NULL,
    UserDefined BOOLEAN NOT NULL,
    FOREIGN KEY (PreferredModelId) REFERENCES AIModels(ModelId)
);
DELETE FROM sqlite_sequence;
COMMIT;

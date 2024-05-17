import sqlite3

# Connect to SQLite database (or create it)
conn = sqlite3.connect('../data/godlike.sqlite')

# Create a cursor object to interact with the database
cur = conn.cursor()

# Define the SQL commands to create the necessary tables
schema = '''
-- Table for Rolls
CREATE TABLE IF NOT EXISTS Rolls (
    RollID INTEGER PRIMARY KEY AUTOINCREMENT,
    UserID INTEGER,
    RollValue TEXT,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

-- Table for Basic Information
CREATE TABLE IF NOT EXISTS CharacterInfo (
    CharacterID INTEGER PRIMARY KEY AUTOINCREMENT,
    Nickname TEXT NOT NULL,
    FullName TEXT,
    Sex TEXT,
    NationEthnicity TEXT,
    Height TEXT,
    Weight TEXT,
    Age INTEGER,
    DateOfManifestation TEXT,
    Education TEXT,
    Profession TEXT,
    Description TEXT
);

-- Table for Stats
CREATE TABLE IF NOT EXISTS Stats (
    CharacterID INTEGER,
    Brains INTEGER,
    Body INTEGER,
    Command INTEGER,
    Coordination INTEGER,
    Cool INTEGER,
    Sense INTEGER,
    BaseWill INTEGER,
    FOREIGN KEY (CharacterID) REFERENCES CharacterInfo(CharacterID)
);

-- Table for Wounds
CREATE TABLE IF NOT EXISTS Health (
    CharacterID INTEGER,
    WoundSlot TEXT,
    HealthStatus TEXT,
    CurrentWill INTEGER,
    FOREIGN KEY (CharacterID) REFERENCES CharacterInfo(CharacterID)
);

-- Table for Skills
CREATE TABLE IF NOT EXISTS Skills (
    CharacterID INTEGER,
    SkillName TEXT,
    Attribute TEXT,
    Rating INTEGER,
    FOREIGN KEY (CharacterID) REFERENCES CharacterInfo(CharacterID)
);

-- Table for Talents
CREATE TABLE IF NOT EXISTS Talents (
    CharacterID INTEGER,
    TalentName TEXT,
    TalentDescription TEXT,
    RegularDice INTEGER,
    HardDice INTEGER,
    WiggleDice INTEGER,
    FOREIGN KEY (CharacterID) REFERENCES CharacterInfo(CharacterID)
);
'''

# Execute the schema to create the tables
cur.executescript(schema)

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database setup completed successfully.")
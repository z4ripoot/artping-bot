-- Everything since the initial schema, which the live database was created with.
-- SQLite can't add a constraint to an existing table, so the name tables are rebuilt; their IDs are kept, so the
-- pings, aliases and wallets referencing them stay valid.

-- Character and currency names, and aliases, are unique regardless of case; an alias names exactly one character.
-- Character names and aliases are stored with each part capitalized, e.g. black_knight -> Black_Knight:
-- NORMALIZE_NAME is util.name_util.normalize_name, registered by database.connect. Currency names are not normalized.
-- Fails on existing duplicates, e.g. Lucina and lucina, or élise and Élise.
CREATE TABLE NEW_CHARACTERS (
    CHARACTER_ID INTEGER PRIMARY KEY,
    NAME TEXT NOT NULL UNIQUE COLLATE NOCASE
);
INSERT INTO NEW_CHARACTERS (CHARACTER_ID, NAME) SELECT CHARACTER_ID, NORMALIZE_NAME(NAME) FROM CHARACTERS;
DROP TABLE CHARACTERS;
ALTER TABLE NEW_CHARACTERS RENAME TO CHARACTERS;

CREATE TABLE NEW_GACHA_CURRENCY (
    GACHA_CURRENCY_ID INTEGER PRIMARY KEY,
    NAME TEXT NOT NULL UNIQUE COLLATE NOCASE
);
INSERT INTO NEW_GACHA_CURRENCY (GACHA_CURRENCY_ID, NAME) SELECT GACHA_CURRENCY_ID, NAME FROM GACHA_CURRENCY;
DROP TABLE GACHA_CURRENCY;
ALTER TABLE NEW_GACHA_CURRENCY RENAME TO GACHA_CURRENCY;

CREATE TABLE NEW_ALIAS (
    CHARACTER_ID INTEGER NOT NULL,
    ALIAS TEXT NOT NULL UNIQUE COLLATE NOCASE,
    FOREIGN KEY (CHARACTER_ID)
        REFERENCES CHARACTERS (CHARACTER_ID)
            ON DELETE CASCADE
            ON UPDATE CASCADE
);
INSERT INTO NEW_ALIAS (CHARACTER_ID, ALIAS) SELECT CHARACTER_ID, NORMALIZE_NAME(ALIAS) FROM ALIAS;
DROP TABLE ALIAS;
ALTER TABLE NEW_ALIAS RENAME TO ALIAS;

-- Votes of non-admins to add a character, by their message, and the users who clicked their Vote button.
-- Several votes for one name may be open at once, and the character doesn't exist yet, so there is no foreign key.
CREATE TABLE CHARACTER_VOTE (
    MESSAGE_ID TEXT NOT NULL PRIMARY KEY,
    CHANNEL_ID TEXT NOT NULL,
    CHARACTER_NAME TEXT NOT NULL COLLATE NOCASE,
    PROPOSER TEXT NOT NULL
);
CREATE INDEX CHARACTER_VOTE_NAME ON CHARACTER_VOTE (CHARACTER_NAME);
CREATE TABLE CHARACTER_VOTE_VOTER (
    MESSAGE_ID TEXT NOT NULL REFERENCES CHARACTER_VOTE (MESSAGE_ID) ON DELETE CASCADE,
    USER TEXT NOT NULL,
    PRIMARY KEY (MESSAGE_ID, USER)
);

-- Resources: content that anyone can post with ~<name>, set by admins from a Discord message or a website link.
-- SOURCE is the link the content came from; for a website link, CONTENT is the link itself.
CREATE TABLE RESOURCE (
    NAME TEXT NOT NULL PRIMARY KEY COLLATE NOCASE,
    CONTENT TEXT NOT NULL,
    SOURCE TEXT NOT NULL
);

-- The Voting Gauntlet that is running (at most one row; its ID is the tournament number on the official site) and
-- the users tracking a character in it, who are pinged while that character is Weaker. Removing the gauntlet when it
-- ends removes its trackers.
CREATE TABLE VOTING_GAUNTLET (
    TOURNAMENT_ID INTEGER PRIMARY KEY
);
CREATE TABLE VOTING_GAUNTLET_TRACKER (
    TOURNAMENT_ID INTEGER NOT NULL REFERENCES VOTING_GAUNTLET (TOURNAMENT_ID) ON DELETE CASCADE,
    USER TEXT NOT NULL,
    CHARACTER_NAME TEXT NOT NULL,
    PRIMARY KEY (TOURNAMENT_ID, USER, CHARACTER_NAME)
);

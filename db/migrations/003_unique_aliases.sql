-- An alias names exactly one character, regardless of case.
-- SQLite can't add a constraint to an existing table, so the table is rebuilt. Fails on existing duplicates.

CREATE TABLE NEW_ALIAS (
    CHARACTER_ID INTEGER NOT NULL,
    ALIAS TEXT NOT NULL UNIQUE COLLATE NOCASE,
    FOREIGN KEY (CHARACTER_ID)
        REFERENCES CHARACTERS (CHARACTER_ID)
            ON DELETE CASCADE
            ON UPDATE CASCADE
);
INSERT INTO NEW_ALIAS (CHARACTER_ID, ALIAS) SELECT CHARACTER_ID, ALIAS FROM ALIAS;
DROP TABLE ALIAS;
ALTER TABLE NEW_ALIAS RENAME TO ALIAS;

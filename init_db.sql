DROP TABLE IF EXISTS CHARACTERS;
CREATE TABLE IF NOT EXISTS CHARACTERS (
    CHARACTER_ID INTEGER PRIMARY KEY,
    NAME TEXT NOT NULL
);

DROP TABLE IF EXISTS ALIAS;
CREATE TABLE IF NOT EXISTS ALIAS(
	CHARACTER_ID INTEGER NOT NULL,
    ALIAS TEXT NOT NULL,
    PRIMARY KEY (CHARACTER_ID),
    FOREIGN KEY (CHARACTER_ID)
        REFERENCES CHARACTERS (CHARACTER_ID)
            ON DELETE CASCADE
            ON UPDATE CASCADE
);

DROP TABLE IF EXISTS PINGS;
CREATE TABLE IF NOT EXISTS PINGS (
    CHARACTER_ID INTEGER NOT NULL,
    USER TEXT NOT NULL,
    PRIMARY KEY (CHARACTER_ID, USER)
    FOREIGN KEY (CHARACTER_ID)
        REFERENCES CHARACTERS (CHARACTER_ID)
            ON DELETE CASCADE
            ON DELETE CASCADE
);
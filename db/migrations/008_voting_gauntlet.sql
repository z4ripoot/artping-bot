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

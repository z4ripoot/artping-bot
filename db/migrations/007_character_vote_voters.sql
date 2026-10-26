-- Votes are now cast with a button, which keeps no list of who clicked, so the voters are stored.
-- USES_BUTTON marks the votes: 0 for votes converted from reactions, 1 for votes that count the stored voters.

CREATE TABLE CHARACTER_VOTE_VOTER (
    MESSAGE_ID TEXT NOT NULL REFERENCES CHARACTER_VOTE (MESSAGE_ID) ON DELETE CASCADE,
    USER TEXT NOT NULL,
    PRIMARY KEY (MESSAGE_ID, USER)
);
ALTER TABLE CHARACTER_VOTE ADD COLUMN USES_BUTTON INTEGER NOT NULL DEFAULT 0;

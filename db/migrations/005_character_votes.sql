-- Votes of non-admins to add a character; reactions aren't stored, they are counted on the vote message.
-- Several votes for one name may be open at once, and the character doesn't exist yet, so there is no foreign key.

CREATE TABLE CHARACTER_VOTE (
    MESSAGE_ID TEXT NOT NULL PRIMARY KEY,
    CHANNEL_ID TEXT NOT NULL,
    CHARACTER_NAME TEXT NOT NULL COLLATE NOCASE,
    PROPOSER TEXT NOT NULL
);
CREATE INDEX CHARACTER_VOTE_NAME ON CHARACTER_VOTE (CHARACTER_NAME);

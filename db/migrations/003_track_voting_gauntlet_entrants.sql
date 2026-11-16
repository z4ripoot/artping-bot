-- Trackers follow an entrant's slot in the bracket rather than its name, since two entrants can share a name (the
-- male and female Shez of gauntlet 114).

-- The running gauntlet's entrants, by slot (1-8, the same in every round), with their name on the page.
CREATE TABLE VOTING_GAUNTLET_ENTRANT (
    TOURNAMENT_ID INTEGER NOT NULL REFERENCES VOTING_GAUNTLET (TOURNAMENT_ID) ON DELETE CASCADE,
    SLOT INTEGER NOT NULL,
    NAME TEXT NOT NULL,
    PRIMARY KEY (TOURNAMENT_ID, SLOT)
);

-- The trackers stored by name before this script. The next hourly post, which stores the entrants, moves each one
-- whose name belongs to a single entrant to that entrant's slot and drops the rest (a "Shez"), leaving this
-- table empty for good; a later script can drop it.
ALTER TABLE VOTING_GAUNTLET_TRACKER RENAME TO VOTING_GAUNTLET_NAMED_TRACKER;

CREATE TABLE VOTING_GAUNTLET_TRACKER (
    TOURNAMENT_ID INTEGER NOT NULL,
    USER TEXT NOT NULL,
    SLOT INTEGER NOT NULL,
    PRIMARY KEY (TOURNAMENT_ID, USER, SLOT),
    FOREIGN KEY (TOURNAMENT_ID, SLOT) REFERENCES VOTING_GAUNTLET_ENTRANT (TOURNAMENT_ID, SLOT) ON DELETE CASCADE
);

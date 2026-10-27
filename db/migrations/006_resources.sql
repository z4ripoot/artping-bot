-- Resources: content that anyone can post with ~<name>, set by admins from a Discord message or a website link.
-- SOURCE is the link the content came from; for a website link, CONTENT is the link itself.

CREATE TABLE RESOURCE (
    NAME TEXT NOT NULL PRIMARY KEY COLLATE NOCASE,
    CONTENT TEXT NOT NULL,
    SOURCE TEXT NOT NULL
);

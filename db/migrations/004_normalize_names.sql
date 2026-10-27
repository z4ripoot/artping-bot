-- Character names and aliases are stored with each part capitalized, e.g. black_knight -> Black_Knight.
-- NORMALIZE_NAME is util.name_util.normalize_name, registered by database.connect. Only the case changes, so names
-- stay unique; fails on names that differ only in non-ASCII case, e.g. élise and Élise.

UPDATE CHARACTERS SET NAME = NORMALIZE_NAME(NAME);
UPDATE ALIAS SET ALIAS = NORMALIZE_NAME(ALIAS);

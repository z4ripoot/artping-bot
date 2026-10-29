-- Every vote uses the button now: the votes counted by their reactions, which 007 marked to be converted, were never
-- released, so the conversion and its mark are gone.

ALTER TABLE CHARACTER_VOTE DROP COLUMN USES_BUTTON;

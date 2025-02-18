import logging
import sqlite3

from util.repository_util import getDatabaseConnection

CONN = getDatabaseConnection()
CURSOR = CONN.cursor()

class CharacterRepository():
    def getCharacterRow(characterName):
        try:
            logging.info("Getting character %s", characterName)
            
            CURSOR.execute(f"""
            SELECT C.CHARACTER_ID, C.NAME
            FROM CHARACTERS C
            WHERE LOWER(C.NAME) = ?
            """, (str(characterName).lower(),))
            result = CURSOR.fetchone()
            
            if result is None:
                raise Exception
            
            logging.info("Got character %s", characterName)
            
            return result
        except sqlite3.OperationalError as e:
            logging.error("Failed to get character %s. %s", characterName, e)
            return None
        except:
            logging.info("Failed to get character %s", characterName)
            return None
        
    def getCharacterRows(characterNames):
        try:
            logging.info("Getting characters %s", characterNames)
            
            sql = """
            SELECT *
            FROM CHARACTERS C
            WHERE LOWER(C.NAME) IN ({})
            """.format(','.join("?" * len(characterNames)))
            
            parameters = (list(map(str.lower, characterNames)))
            CURSOR.execute(sql, (parameters))
            result = CURSOR.fetchall()
            
            if result is None:
                raise Exception
            
            logging.info("Got characters %s", characterNames)
            
            return result
        except sqlite3.OperationalError as e:
            logging.error("Failed to get characters %s. %s", characterNames, e)
            return None
        except:
            logging.info("Failed to get characters %s", characterNames)
            return None
        
    def getMissingCharacterRows(characterNames):
        try:
            logging.info("Getting missing characters %s", characterNames)
            
            sql = """
            WITH INPUT(NAME) AS (
                VALUES {}
            )
            SELECT I.NAME
            FROM INPUT I
            WHERE I.NAME NOT IN (
                SELECT LOWER(C.NAME)
                FROM CHARACTERS C
            )
            """.format(','.join(("(?)",) * len(characterNames)))
            
            parameters = (list(map(str.lower, characterNames)))
            CURSOR.execute(sql, (parameters))
            result = CURSOR.fetchall()
            
            if result is None:
                raise Exception
            
            logging.info("Got missing characters %s", characterNames)
            
            return result
        except sqlite3.OperationalError as e:
            logging.error("Failed to get missing characters %s. %s", characterNames, e)
            return None
        except:
            logging.info("Failed to get missing characters %s", characterNames)
            return None
        
    def getCharacterName(characterName):
        try:
            logging.info("Getting character %s", characterName)
            
            CURSOR.execute(f"""
            SELECT C.NAME 
            FROM CHARACTERS C
            WHERE LOWER(C.NAME) IS ?
            """, (str(characterName).lower(),))
            result = CURSOR.fetchone()[0]
            
            if result is None:
                raise Exception
            
            logging.info("Got character %s", characterName)
            
            return result
        except sqlite3.OperationalError as e:
            logging.error("Failed to get character %s. %s", characterName, e)
            return None
        except:
            logging.info("Failed to get character %s", characterName)
            return None
        
    def addCharacter(characterName):
        try:
            logging.info("Adding character %s", characterName)
            
            CURSOR.execute("""
            INSERT INTO CHARACTERS (NAME)
            VALUES (?)
            """, (characterName,))
            CONN.commit()
            
            logging.info("Added character %s", characterName)
            
            return True
        except sqlite3.OperationalError as e:
            logging.error("Failed to add character %s. %s", characterName, e)
            return False
        except:
            logging.error("Failed to add character %s", characterName)
            return False
    
    def removeCharacter(characterName):
        try:
            logging.info("Removing character %s", characterName)
            
            CURSOR.execute("""
            DELETE FROM CHARACTERS AS C
            WHERE LOWER(C.NAME) = ?
            """, (str(characterName).lower(),))
            CONN.commit()
            
            logging.info("Removed character %s", characterName)
            
            return True
        except sqlite3.OperationalError as e:
            logging.error("Failed to remove character %s. %s", characterName, e)
            return False
        except:
            logging.error("Failed to remove character %s", characterName)
            return False
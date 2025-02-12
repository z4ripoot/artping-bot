import logging
import sqlite3

from util.repository_util import getDatabaseConnection

CONN = getDatabaseConnection()
CURSOR = CONN.cursor()

class CharacterRepository():
    def getCharacterRow(character):
        try:
            logging.info("Getting character %s", character)
            
            CURSOR.execute(f"""
            SELECT C.CHARACTER_ID, C.NAME
            FROM CHARACTERS C
            WHERE LOWER(C.NAME) = ?
            """, (str(character).lower(),))
            result = CURSOR.fetchone()
            
            if result is None:
                raise Exception
            
            logging.info("Got character %s", character)
            
            return result
        except sqlite3.OperationalError as e:
            logging.error("Failed to get character %s. %s", character, e)
            return None
        except:
            logging.info("Failed to get character %s", character)
            return None
        
    def getCharacterRows(characters):
        try:
            logging.info("Getting characters %s", characters)
            
            sql = """
            SELECT *
            FROM CHARACTERS C
            WHERE LOWER(C.NAME) IN ({})
            """.format(','.join("?" * len(characters)))
            
            parameters = (list(map(str.lower, characters)))
            CURSOR.execute(sql, (parameters))
            result = CURSOR.fetchall()
            
            if result is None:
                raise Exception
            
            logging.info("Got characters %s", characters)
            
            return result
        except sqlite3.OperationalError as e:
            logging.error("Failed to get characters %s. %s", characters, e)
            return None
        except:
            logging.info("Failed to get characters %s", characters)
            return None
        
    def getMissingCharacterRows(characters):
        try:
            logging.info("Getting missing characters %s", characters)
            
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
            """.format(','.join(("(?)",) * len(characters)))
            
            parameters = (list(map(str.lower, characters)))
            CURSOR.execute(sql, (parameters))
            result = CURSOR.fetchall()
            
            if result is None:
                raise Exception
            
            logging.info("Got missing characters %s", characters)
            
            return result
        except sqlite3.OperationalError as e:
            logging.error("Failed to get missing characters %s. %s", characters, e)
            return None
        except:
            logging.info("Failed to get missing characters %s", characters)
            return None
        
    def getCharacter(character):
        try:
            logging.info("Getting character %s", character)
            
            CURSOR.execute(f"""
            SELECT C.NAME 
            FROM CHARACTERS C
            WHERE LOWER(C.NAME) IS ?
            """, (str(character).lower(),))
            result = CURSOR.fetchone()[0]
            
            if result is None:
                raise Exception
            
            logging.info("Got character %s", character)
            
            return result
        except sqlite3.OperationalError as e:
            logging.error("Failed to get character %s. %s", character, e)
            return None
        except:
            logging.info("Failed to get character %s", character)
            return None
        
    def addCharacter(character):
        try:
            logging.info("Adding character %s", character)
            
            CURSOR.execute("""
            INSERT INTO CHARACTERS (NAME)
            VALUES (?)
            """, (character,))
            CONN.commit()
            
            logging.info("Added character %s", character)
            
            return True
        except sqlite3.OperationalError as e:
            logging.error("Failed to add character %s. %s", character, e)
            return False
        except:
            logging.error("Failed to add character %s", character)
            return False
    
    def removeCharacter(character):
        try:
            logging.info("Removing character %s", character)
            
            CURSOR.execute("""
            DELETE FROM CHARACTERS AS C
            WHERE LOWER(C.NAME) = ?
            """, (str(character).lower(),))
            CONN.commit()
            
            logging.info("Removed character %s", character)
            
            return True
        except sqlite3.OperationalError as e:
            logging.error("Failed to remove character %s. %s", character, e)
            return False
        except:
            logging.error("Failed to remove character %s", character)
            return False
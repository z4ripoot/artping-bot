import logging
import sqlite3

from util.repository_util import getDatabaseConnection, getIds

CONN = getDatabaseConnection()
CURSOR = CONN.cursor()

class ArtPingRepository():
    def getArtPing(characterId, userId):
        try:
            logging.info("Getting art ping")
            
            CURSOR.execute("""
            SELECT P.CHARACTER_ID, P.USER
            FROM PINGS P
            WHERE P.CHARACTER_ID = ? AND P.USER = ?
            """, (characterId, userId,))
            userIds = CURSOR.fetchone()[0]
            
            logging.info("Got art ping")
            
            return userIds
        except sqlite3.OperationalError as e:
            logging.error("Failed to get art ping. %s", e)
            return None
        except:
            logging.error("Failed to get art ping")
            return None
        
    def getArtPings(characterIds):
        try:
            logging.info("Getting pings")
            
            sql = """
            SELECT DISTINCT P.USER
            FROM PINGS P
            WHERE P.CHARACTER_ID IN ({})
            """.format(','.join("?" * len(characterIds)))
            CURSOR.execute(sql, characterIds)
            userIds = getIds(CURSOR.fetchall())
            
            logging.info("Got pings")
            
            return userIds
        except sqlite3.OperationalError as e:
            logging.error("Failed to ping characters. %s", e)
            return None
        except:
            logging.error("Failed to ping characters")
            return None
        
    def addPing(characterId, userId):
        try:
            logging.info("Adding ping")
            
            CURSOR.execute("""
            INSERT INTO PINGS (CHARACTER_ID, USER)
            VALUES (?, ?)
            """, (characterId, userId,))
            CONN.commit()
            
            logging.info("Added ping")
            
            return True
        except sqlite3.OperationalError as e:
            logging.error("Failed to add ping. %s", e)
            return False
        except:
            logging.error("Failed to add ping")
            return False

    def removePing(characterId, userId):
        try:
            logging.info("Removing ping")
            
            CURSOR.execute("""
            DELETE FROM PINGS AS P
            WHERE P.CHARACTER_ID = ?
            AND P.USER = ?
            """, (characterId, userId,))
            CONN.commit()
            
            logging.info("Removed ping")
            
            return True
        except sqlite3.OperationalError as e:
            logging.error("Failed to remove ping. %s", e)
            return False
        except:
            logging.error("Failed to remove ping")
            return False
        
    def getUserPings(userId):
        try:
            logging.info(f"Getting user pings for {userId}")
            
            CURSOR.execute("""
            SELECT C.NAME
            FROM PINGS P
            LEFT JOIN CHARACTERS C ON
            P.CHARACTER_ID = C.CHARACTER_ID
            WHERE P.USER = ?
            ORDER BY
            C.NAME ASC
            """, (userId,))
            pings = getIds(CURSOR.fetchall())
            
            logging.info(f"Got art pings for user {userId}")
            
            return pings
        except sqlite3.OperationalError as e:
            logging.error("Failed to get users ping. %s", e)
            return None
        except:
            logging.error("Failed to get users ping")
            return None
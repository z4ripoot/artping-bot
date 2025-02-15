import logging
import sqlite3

from util.repository_util import getDatabaseConnection

CONN = getDatabaseConnection()
CURSOR = CONN.cursor()

class CurrencyRepository():
    def getCurrency(currency):
        try:
            logging.info("Getting currency %s", currency)
            
            CURSOR.execute(f"""
            SELECT C.GACHA_CURRENCY_ID, C.NAME
            FROM GACHA_CURRENCY C
            WHERE LOWER(C.NAME) = ?
            """, (str(currency).lower(),))
            
            result = CURSOR.fetchone()
            if result is None:
                raise Exception
            
            logging.info("Got currency %s", currency)
            
            return result
        except sqlite3.OperationalError as e:
            logging.error("Failed to get currency %s. %s", currency, e)
            return None
        except:
            logging.error("Failed to get currency %s", currency)
            return None
        
    def addCurrency(currency):
        try:
            logging.info("Adding currency %s", currency)
            
            CURSOR.execute("""
            INSERT INTO GACHA_CURRENCY (NAME)
            VALUES (?)
            """, (currency,))
            CONN.commit()
            
            logging.info("Added currency %s", currency)
            
            return True
        except sqlite3.OperationalError as e:
            logging.error("Failed to add currency %s. %s", currency, e)
            return False
        except:
            logging.error("Failed to add currency %s", currency)
            return False
        
    def removeCurrency(currencyId):
        try:
            logging.info("Removing currency %s", currencyId)
            
            CURSOR.execute("""
            DELETE FROM GACHA_CURRENCY AS C
            WHERE C.GACHA_CURRENCY_ID = ?
            """, (currencyId,))
            CONN.commit()
            
            logging.info("Removed currency %s", currencyId)
            
            return True
        except sqlite3.OperationalError as e:
            logging.error("Failed to remove currency %s. %s", currencyId, e)
            return False
        except:
            logging.error("Failed to remove currency %s", currencyId)
            return False
        
    def setCurrency(userId, currencyId, amount):
        try:
            logging.info("Setting user %s's currency %s to %s", userId, currencyId, amount)
            
            CURSOR.execute("""
            UPDATE GACHA_CURRENCY_WALLET AS W
            SET AMOUNT = ?
            WHERE W.GACHA_CURRENCY_ID = ? AND W.USER = ?
            """, (amount, currencyId, userId,))
            CONN.commit()
            
            logging.info("Set user %s's currency %s to %s", userId, currencyId, amount)
            
            return True
        except sqlite3.OperationalError as e:
            logging.error("Failed to set user %s's currency %s to %s. %s", userId, currencyId, amount, e)
            return False
        except:
            logging.error("Failed to set user %s's currency %s to %s", userId, currencyId, amount)
            return False
        
    def clearCurrency(userId, currencyId):
        try:
            logging.info("Clearing user %s's currency %s", userId, currencyId)
            
            CURSOR.execute("""
            DELETE FROM GACHA_CURRENCY_WALLET AS W
            WHERE W.GACHA_CURRENCY_ID = ? AND W.USER = ?
            """, (currencyId, str(userId),))
            CONN.commit()
            
            logging.info("Cleared user %s's currency %s", userId, currencyId)
            
            return True
        except sqlite3.OperationalError as e:
            logging.error("Failed to clear user %s's currency %s. %s", userId, currencyId, e)
            return False
        except:
            logging.error("Failed to clear user %s's currency %s", userId, currencyId)
            return False
        
    def getWalletRow(userId, currencyId):
        try:
            logging.info("Getting user %s's wallet for currency %s", userId, currencyId)
            
            CURSOR.execute("""
            SELECT *
            FROM GACHA_CURRENCY_WALLET W
            WHERE W.GACHA_CURRENCY_ID = ? AND W.USER = ?
            """, (currencyId, userId,))
            result = CURSOR.fetchone()
            
            if result is None:
                raise Exception
            
            logging.info("Got user %s's wallet for currency %s", userId, currencyId)
            
            return result
        except sqlite3.OperationalError as e:
            logging.error("Failed to get user %s's wallet for currency %s. %s", userId, currencyId, e)
            return None
        except:
            logging.error("Failed to get user %s's wallet for currency %s", userId, currencyId)
            return None
        
    def getWalletRows(userId):
        try:
            logging.info("Getting user %s's wallet", userId)
            
            CURSOR.execute("""
            SELECT C.NAME, W.AMOUNT
            FROM GACHA_CURRENCY_WALLET W
            LEFT JOIN GACHA_CURRENCY C ON
            W.GACHA_CURRENCY_ID = C.GACHA_CURRENCY_ID
            WHERE W.USER = ?
            """, (userId,))
            result = CURSOR.fetchall()
            
            if result is None:
                raise Exception
            
            logging.info("Got user %s's wallet", userId)
            
            return result
        except sqlite3.OperationalError as e:
            logging.error("Failed to get user %s's wallet. %s", userId, e)
            return None
        except:
            logging.error("Failed to get user %s's wallet", userId)
            return None
        
    def createWallet(userId, currencyId, amount):
        try:
            logging.info("Creating user %s's wallet for currency %s with %s amount", userId, currencyId, amount)
            
            CURSOR.execute("""
            INSERT INTO GACHA_CURRENCY_WALLET (GACHA_CURRENCY_ID, USER, AMOUNT)
            VALUES (?, ?, ?)
            """, (currencyId, str(userId), amount))
            CONN.commit()
            
            logging.info("Created user %s's wallet for currency %s with %s amount", userId, currencyId, amount)
            
            return True
        except sqlite3.OperationalError as e:
            logging.error("Failed to create user %s's wallet for currency %s with %s amount. %s", userId, currencyId, amount, e)
            return False
        except:
            logging.error("Failed to create user %s's wallet for currency %s with %s amount", userId, currencyId, amount)
            return False
        
    def getScoreboard(currencyId):
        try:
            logging.info("Getting scoreboard for %s", currencyId)
            
            CURSOR.execute("""
            SELECT W.USER, W.AMOUNT
            FROM GACHA_CURRENCY_WALLET W
            WHERE W.GACHA_CURRENCY_ID = ?
            ORDER BY W.AMOUNT DESC
            """, (currencyId,))
            result = CURSOR.fetchall()
            
            if result is None:
                raise Exception
            
            logging.info("Got scoreboard for %s", currencyId)
            
            return result
        except sqlite3.OperationalError as e:
            logging.error("Failed to get scoreboard for %s. %s", currencyId, e)
            return None
        except:
            logging.error("Failed to get scoreboard for %s", currencyId)
            return None
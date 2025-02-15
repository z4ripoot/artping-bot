import logging
import discord

from repository.currency_repository import CurrencyRepository
from util.message_util import getEntries, getFirst

class CurrencyService():
    def addCurrency(message : discord.Message):
        entry = getFirst(message.content)
        
        if entry is None:
            out = "Failed to add currency"
            logging.warning(out)
            return out
        
        if CurrencyRepository.getCurrency(entry):
            out = f"Failed to add currency {entry}. Currency {entry} already exists"
            logging.warning(out)
            return out
        
        logging.info("Adding currency %s", entry)
        
        isAdded =  CurrencyRepository.addCurrency(entry)
        
        if isAdded:
            out = f"Currency {entry} has been added"
            logging.info(out)
            return out
        else:
            out = f"Failed to add currency {entry}"
            logging.warning(out)
            return out
        
    def removeCurrency(message : discord.Message):
        entry = getFirst(message.content)
        
        if entry is None:
            out = "Failed to remove currency"
            logging.warning(out)
            return out
        
        row = CurrencyRepository.getCurrency(entry)
        
        if row is None:
            out = f"Failed to remove currency {entry}. Currency {entry} doesn't exist"
            logging.warning(out)
            return out
        
        id = row[0]
        name = row[1]
        
        logging.info("Removing currency %s", name)
        
        isRemoved = CurrencyRepository.removeCurrency(id)
        
        if isRemoved:
            out = f"Currency {name} has been removed"
            logging.info(out)
            return out
        else:
            out = f"Failed to remove currency {name}"
            logging.warning(out)
            return out
    
    def setCurrency(message : discord.Message):
        entries = getEntries(message.content)
        
        if entries is None or len(entries) != 2:
            out = "Failed to set currency"
            logging.warning(out)
            return out
        
        entry = entries[0]
        amount = entries[1]
        currencyRow = CurrencyRepository.getCurrency(entry)
        
        if currencyRow is None:
            out = f"Failed to set currency {entry} for user. Currency {entry} doesn't exist"
            logging.warning(out)
            return out
        
        currencyId = currencyRow[0]
        currencyName = currencyRow[1]
        userId = str(message.author.id)
        walletRow = CurrencyRepository.getWalletRow(userId, currencyId)
        
        isSet = None
        if walletRow:
            logging.info("Set user %s's currency %s to %s", message.author.global_name, currencyName, amount)
            isSet = CurrencyRepository.setCurrency(userId, currencyId, amount)
        else:
            logging.info("No user currency row found. Creating user currency row for user %s's currency %s with %s", message.author.global_name, currencyName, amount)
            isSet = CurrencyRepository.createWallet(userId, currencyId, amount)
            
        if isSet:
            out = f"Your {currencyName} has been set to {amount}"
            logging.info(out)
            return out
        else:
            out = f"Failed to set your {currencyName}"
            logging.warning(out)
            return out
        
    def clearCurrency(message : discord.Message):
        entry = getFirst(message.content)
        
        if entry is None:
            out = "Failed to clear currency"
            logging.warning(out)
            return out
        
        currencyRow = CurrencyRepository.getCurrency(entry)
        
        if currencyRow is None:
            out = f"Failed to clear currency {entry} for user. Currency {entry} doesn't exist"
            logging.warning(out)
            return out
        
        currencyId = currencyRow[0]
        currencyName = currencyRow[1]
        userId = str(message.author.id)
        walletRow = CurrencyRepository.getWalletRow(userId, currencyId)
        
        if walletRow is None:
            out = f"Failed to clear currency {currencyName} for user. Currency {currencyName} for user doesn't exist"
            logging.warning(out)
            return out
        
        logging.info("Clearing user %s's currency %s", message.author.name, currencyName)
        
        isCleared = CurrencyRepository.clearCurrency(userId, currencyId)
        
        if isCleared:
            out = f"Your {currencyName} has been cleared"
            logging.info(out)
            return out
        else:
            out = f"Failed to clear {currencyName} for user"
            logging.warning(out)
            return out
    
    def checkWallet(message : discord.Message):
        userId = str(message.author.id)
        rows = CurrencyRepository.getWalletRows(userId)
        out = f"User {message.author.name}'s wallet:\n"
        
        if rows is None:
            return out
        
        for row in rows:
            out += f"{row[0]}: {row[1]}\n"
        
        return out
    
    async def getScoreboard(self : discord.Client, message : discord.Message):
        entry = getFirst(message.content)
        
        if entry is None:
            out = f"Failed to check scoreboard"
            logging.warning(out)
            return out
        
        currencyRow = CurrencyRepository.getCurrency(entry)
        
        if currencyRow is None:
            out = f"Failed to check scoreboard for {entry}. Currency {entry} doesn't exist"
            logging.warning(out)
            return out
        
        id = currencyRow[0]
        name = currencyRow[1]
        
        logging.info("Check scoreboard for currency %s", name)
        
        scoreboardRows = CurrencyRepository.getScoreboard(id)
        out = f"Scoreboard for {name}:\n" 
        
        if scoreboardRows is None:
            return out
        
        for i, scoreboardRow in enumerate(scoreboardRows, start=1):
            user : discord.User = await self.fetch_user(scoreboardRow[0]) 
            username = user.global_name
            out += f"{i}. {username} ({scoreboardRow[1]})"
        
        logging.info("Checked scoreboard for currency %s", name)
        return out
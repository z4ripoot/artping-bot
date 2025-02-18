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
        
        if CurrencyRepository.getCurrencyRow(entry):
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
        
        currency = CurrencyRepository.getCurrencyRow(entry)
        
        if currency is None:
            out = f"Failed to remove currency {entry}. Currency {entry} doesn't exist"
            logging.warning(out)
            return out
        
        id = currency[0]
        name = currency[1]
        
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
        
        try:
            amount = int(entries[1])
        except:
            out = f"Failed to set currency. Please enter a valid amount for your {entry}."
            logging.warning(out)
            return out
        
        currency = CurrencyRepository.getCurrencyRow(entry)
        
        if currency is None:
            out = f"Failed to set currency {entry} for user. Currency {entry} doesn't exist"
            logging.warning(out)
            return out
        
        currencyId = currency[0]
        currencyName = currency[1]
        userId = str(message.author.id)
        wallet = CurrencyRepository.getWalletRow(userId, currencyId)
        
        isSet = None
        if wallet:
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
        
        currency = CurrencyRepository.getCurrencyRow(entry)
        
        if currency is None:
            out = f"Failed to clear currency {entry} for user. Currency {entry} doesn't exist"
            logging.warning(out)
            return out
        
        currencyId = currency[0]
        currencyName = currency[1]
        userId = str(message.author.id)
        wallet = CurrencyRepository.getWalletRow(userId, currencyId)
        
        if wallet is None:
            out = f"Failed to clear currency {currencyName} for user. Currency {currencyName} for user doesn't exist"
            logging.warning(out)
            return out
        
        logging.info("Clearing user %s's currency %s", message.author.global_name, currencyName)
        
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
        wallets = CurrencyRepository.getWalletRows(userId)
        out = f"User {message.author.global_name}'s wallet:\n"
        
        if wallets is None:
            return out
        
        for wallet in wallets:
            out += f"{wallet[0]}: {wallet[1]}\n"
        
        return out
    
    async def getScoreboard(self : discord.Client, message : discord.Message):
        entry = getFirst(message.content)
        
        if entry is None:
            out = f"Failed to check scoreboard"
            logging.warning(out)
            return out
        
        currency = CurrencyRepository.getCurrencyRow(entry)
        
        if currency is None:
            out = f"Failed to check scoreboard for {entry}. Currency {entry} doesn't exist"
            logging.warning(out)
            return out
        
        id = currency[0]
        name = currency[1]
        
        logging.info("Check scoreboard for currency %s", name)
        
        scoreboardRows = CurrencyRepository.getScoreboardRows(id)
        out = f"Scoreboard for {name}:\n" 
        
        if scoreboardRows is None:
            return out
        
        for i, row in enumerate(scoreboardRows, start=1):
            user : discord.User = await self.fetch_user(row[0]) 
            username = user.global_name
            out += f"{i}. {username} ({row[1]})\n"
        
        logging.info("Checked scoreboard for currency %s", name)
        return out
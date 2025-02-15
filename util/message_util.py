import logging


def getEntries(content):
    splitEntries = content.split(" ")
    
    if len(splitEntries) < 2:
        logging.warning("No entries found")
        return None
    
    entryList = []
    
    logging.info("Getting entries")
    
    # Get all entries
    for entry in splitEntries[1:]:
        entryList.append(entry)
    
    logging.info("Found %d entries", len(entryList))
    
    return entryList

def getFirst(content):
    splitEntries = content.split(" ")
    
    if len(splitEntries) < 2 :
        logging.warning("No entries found")
        return None
    
    logging.info("Getting first entry")
    
    return splitEntries[1]
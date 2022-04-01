import logging
import config
import socket
import struct
import os

try:
    #Získanie IP adresy zvoleného sieťového rozhrania
    import netifaces as ni
    def getIPAddress(interface):
        return ni.ifaddresses(interface)[ni.AF_INET][0]['addr']
except:
    pass

#Skúška, čí zložka existuje
def dirExist(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)

#Premenovanie existujúceho súroru
def csvRename(path, oldName, newName):
    if not os.path.isfile(os.path.join(path,newName)) and os.path.isfile(os.path.join(path,oldName)):
        os.rename(os.path.join(path,oldName),os.path.join(path,newName))

#Vytvorenie formy vytvárania logov
class Logs():
    def __init__(self):
        self.setLogger()

    def setLogger(self):
        #Získanie IP adresy zvoleného rozhrania
        try:
            ipAddress = getIPAddress(config.IP_ADDRESS_INTERFACE)
        except:
            #Pre prípad nemožnosti získania IP adresy
            ipAddress = "NoneIPAddress"

        logDir = os.path.join(config.ROOT_DIRECTORY,config.LOG_DIRECTORY)
        dirExist(logDir)
        
        #Nastavenie formátu logu
        self.logger = logging.getLogger(config.HOST_ID)
        self.logger.setLevel(logging.INFO)
        formater = logging.Formatter(config.LOG_FORMAT.format(ipAddress))
        logHandler = logging.FileHandler(os.path.join(logDir,config.LOG_FILE_NAME))
        logHandler.setFormatter(formater)
        self.logger.addHandler(logHandler)
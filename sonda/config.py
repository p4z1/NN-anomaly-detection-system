#Parametre, ktoré slúžia na nastavenie chovania sa sondy.

#----- RB settings -----
REMOTE = True
VERBOSE = True
#LOGGING = True
LOG_TIME = True

#----- Directories -----
ROOT_DIRECTORY = "."
IMAGE_DIRECTORY = "images"
CSV_DIRECTORY = "csvFiles"
CHECK_DIRECTORY = "checked"
LOG_DIRECTORY = "logs"

#----- OPENVINO -----
MODEL_ROOT_DIR = "model"
NCS_MODEL = "anomalie.xml"
NCS_WEIGHTS = "anomalie.bin"
NCS_DEVICE = "MYRIAD"
BATCH_SIZE = 3

#----- Image Options -----
IMAGE_HEIGHT = 224
IMAGE_WIDTH = 224
SCALE = 4
NUMBER_OF_ARGUMENTS = 4

#----- IP Addresses -----
REDIS_IP = "127.0.0.1"
API_IP = "127.0.0.1"
REMOTE_API_IP = "185.146.4.71"

#----- Ports -----
REDIS_PORT = 6379
API_PORT = 5001
REMOTE_API_PORT = 5000

#----- Logging -----

LOG_FORMAT = '%(asctime)s %(name)s %(levelname)s {} %(message)s'
HOST_ID = "OPENVINO_RB_1"
IP_ADDRESS_INTERFACE = "eth0"
LOG_FILE_NAME = "RBLogs.log"

#----- Category mapping -----
CATEGORIES_MAP = {
    "Benign":0,
    "Bot":1,
    "Brute Force -XSS":2,
    "Brute Force -Web":3,
    "SSH-Bruteforce":4,
    "FTP-BruteForce":5,        
    "SQL Injection":6,            
    "DDoS attacks-LOIC-HTTP":7,
    "DDOS attack-HOIC":8,
    "DDOS attack-LOIC-UDP":9,
    "DoS attacks-GoldenEye":10,
    "DoS attacks-Slowloris":11,
    "DoS attacks-Hulk":12,
    "Dos Heartbleed":13,
    "DoS attacks-SlowHTTPTest":14,
    "Infilteration":15,          
    "PortScan":16
}

REVERSE_CATEGORIES_MAP = {      #Pouzivane pri predikcii
    0:"Benign",
    1:"Bot",
    2:"BruteForce XSS",
    3:"BruteForce Web",
    4:"BruteForce SSH",
    5:"BruteForce FTP",        
    6:"SQL-Injection",            
    7:"DDoS-attack LOIC-HTTP",
    8:"DDOS-attack HOIC",
    9:"DDOS-attack LOIC-UDP",
    10:"DoS-attack GoldenEye",
    11:"DoS-attack Slowloris",
    12:"DoS-attack Hulk",
    13:"Dos-attack Heartbleed",
    14:"DoS-attacks SlowHTTPTest",
    15:"Infilteration",          
    16:"PortScan"
}
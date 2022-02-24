#----- RB settings -----

REMOTE = False
VERBOSE = True
LOGGING = True

#----- Directories -----
ROOT_DIRECTORY = "."
IMAGE_DIRECTORY = "images"
CSV_DIRECTORY = "csvFiles"
CHECK_DIRECTORY = "checked"
LOG_DIRECTORY = "logs"

#----- IP Addresses -----
REDIS_IP = "127.0.0.1"
API_IP = "127.0.0.1"

#----- Ports -----
REDIS_PORT = 6379
API_PORT = 5000

#----- OPENVINO -----
MODEL_ROOT_DIR = "model"
NCS_MODEL = "anomalie.xml"
NCS_WEIGHTS = "anomalie.bin"
NCS_DEVICE = "MYRIAD"
BATCH_SIZE = 10

#----- Image Options -----
IMAGE_HEIGHT = 224
IMAGE_WIDTH = 224
SCALE = 4
NUMBER_OF_ARGUMENTS = 4

#----- Logging -----

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
INFO_FILE_NAME = "default.log"
WARNING_FILE_NAME = "foundAnomaly.log"
ERROR_FILE_NAME = "errors.log"
BACKUP_COUNT_INFO = 30
BACKUP_COUNT_WARNING = 10

#----- Remote Data Transfer -----

REMOTE_IP = "x.x.x.x"
REMOTE_PORT = 5001
BUFFER_SIZE = 4096

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
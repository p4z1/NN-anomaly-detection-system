#----- General settings -----
LOG_TIME = True
CATEGORIES_FULL_NAME = False

#----- Files settings
ALLOWED_EXTENSIONS = {'csv'}
ALLOWED_IMAGE_EXTENSIONS = {'jpeg','png'}

#----- Directories -----
ROOT_DIRECTORY = "."
UPLOAD_FOLDER = "uploads"
IMAGE_DIRECTORY = "images"
CSV_DIRECTORY = "csvFiles"
LOG_DIRECTORY = "logs"

#----- Pytorch -----
MODEL_ROOT_DIR = "model"
TORCH_MODEL = "mobilenet_v3_large"
#TORCH_MODEL = "efficientnet_b7" #????
TORCH_DEVICE = "cuda:0"

#----- Image Options -----
IMAGE_HEIGHT = 224
IMAGE_WIDTH = 224
SCALE = 4
NUMBER_OF_ARGUMENTS = 8

#----- IP Addresses -----
API_HOST = "0.0.0.0"
API_LOCAL_IP = "127.0.0.1"

#----- Ports -----
API_PORT = 5000

#----- Logging -----
LOG_FORMAT = '%(asctime)s %(name)s %(levelname)s {} %(message)s'
HOST_ID = "GPU_SERVER"
IP_ADDRESS_INTERFACE = "eth0"

LOG_FILE_NAME = "centralLogs.log"

#----- Category mapping -----
CATEGORIES_MAP = {      #Pouzivane pre vytvaranie datovej sady
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
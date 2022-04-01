from utilities import dirExist, toRedis
from skimage import io
from PIL import Image

import imageTransformation
import requests
import config
import redis
import time
import os

#Spracovanie CSV súborov na predikciu
def csvPreprocessing(csvID,logs):
    r = redis.Redis(host=config.REDIS_IP, port=config.REDIS_PORT) 
    imgTransf = imageTransformation.Transformation()

    #Overenie existencie zložiek
    csvDir = os.path.join(config.ROOT_DIRECTORY, config.CSV_DIRECTORY)
    outputDir = os.path.join(config.ROOT_DIRECTORY, config.CHECK_DIRECTORY)
    dirExist(csvDir)
    dirExist(outputDir)   
    
    csvIDs = csvID.split(',')
    assert(len(csvIDs) == config.BATCH_SIZE)
    startTime = time.time()
    try:
        #Vytvorenie obrázkov z CSV súboru a vloženie do redisu
        for id in csvIDs:
            file = str(id) + ".csv"
            image = imgTransf.imageCreation(file).numpy()
            os.replace(os.path.join(csvDir,file),os.path.join(outputDir,file))
            toRedis(r,image,str(id))
        #Žiadosť API o vytvorenie predikcie na vytvorených obrázkov
        apiRequest = requests.get(f"http://{config.API_IP}:{config.API_PORT}/predictions?csv={csvID}")
        if apiRequest.status_code != 200:
            logs.logger.error(f"Request issue: status code {apiRequest.status_code}")
    except:
        logs.logger.error(f"CSV transformation to image didn't complete")
        return False
    if config.LOG_TIME: logs.logger.info(f"CSV transformation to image took {time.time()-startTime:.4f}s")
    return True

#Spracovanie obrázkov na predikciu  
def imgsPreprocessing(id,logs):   
    r = redis.Redis(host=config.REDIS_IP, port=config.REDIS_PORT) 
    imgTransf = imageTransformation.Transformation()
    #Overenie existencie zložiek
    imgsDir =  os.path.join(config.ROOT_DIRECTORY, config.IMAGE_DIRECTORY)
    outputDir = os.path.join(config.ROOT_DIRECTORY, config.CHECK_DIRECTORY)
    dirExist(imgsDir)
    dirExist(outputDir)
    
    files = os.listdir(imgsDir)
    #Výber obrázkov zo zložky ak je ich požadovaný počet
    while (len(files) // config.BATCH_SIZE) >= 1:
        imageList = []
        #Spracovanie a normalizácia obrázkov a vloženie do redisu
        for _ in range(config.BATCH_SIZE):
            file = files.pop(0)
            os.replace(os.path.join(imgsDir,file),os.path.join(outputDir,file))
            image = io.imread(os.path.join(outputDir,file))
            image = imgTransf.normalize(Image.fromarray(image)).numpy()
            imageID = f"{str(id)};{file}"
            imageList.append(imageID)
            toRedis(r,image,imageID)
            id += 1
        images = ','.join(imageList)
        #Žiadosť API o vytvorenie predikcie na spracovaných obrázkoch
        apiRequest = requests.get(f"http://{config.API_IP}:{config.API_PORT}/predictions?imgs={images}")
        if apiRequest.status_code != 200:
            logs.logger.error(f"Request issue: status code {apiRequest.status_code}")
    return id
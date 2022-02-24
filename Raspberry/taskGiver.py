import imageTransformation
from skimage import io
import pandas as pd
import requests
import logging
import config
import redis
import time
import os

def toRedis(r,a,n):
   encoded = a.tobytes()
   r.set(n,encoded)

def dirExist(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)

def csvPreprocessing(csvID,logs):
    r = redis.Redis(host=config.REDIS_IP, port=config.REDIS_PORT) 
    imgTransf = imageTransformation.Transformation()

    csvDir = os.path.join(config.ROOT_DIRECTORY, config.CSV_DIRECTORY)
    outputDir = os.path.join(config.ROOT_DIRECTORY, config.CHECK_DIRECTORY)
    dirExist(csvDir)
    dirExist(outputDir)   

    csvIDs = csvID.split(',')
    assert(len(csvIDs) == config.BATCH_SIZE)
    startTime = time.time()
    try:
        for id in csvIDs:
            file = str(id) + ".csv"
            image = imgTransf.imageCreation(file)
            os.replace(os.path.join(csvDir,file),os.path.join(outputDir,file))
            toRedis(r,image,str(id))
        apiRequest = requests.get(f"http://{config.API_IP}:{config.API_PORT}/addTask?imgs={csvID}")
        if apiRequest.status_code != 200:
            logs.logger.error(f"Request error: status code {apiRequest.status_code}")
    except:
        logs.logger.error(f"Error while image creation.")
    logs.logger.info(f"CSV transformation to image took: {time.time()-startTime:.4f}s")
    return True
    
def imgsPreprocessing(id,logs):   
    r = redis.Redis(host=config.REDIS_IP, port=config.REDIS_PORT) 
    imgTransf = imageTransformation.Transformation()

    imgsDir =  os.path.join(config.ROOT_DIRECTORY, config.IMAGE_DIRECTORY)
    outputDir = os.path.join(config.ROOT_DIRECTORY, config.CHECK_DIRECTORY)
    dirExist(imgsDir)
    dirExist(outputDir)
    
    files = os.listdir(imgsDir)
    while (len(files) // config.BATCH_SIZE) >= 1:
        imageList = []
        for _ in range(config.BATCH_SIZE):
            file = files.pop(0)
            os.replace(os.path.join(imgsDir,file),os.path.join(outputDir,file))
            image = io.imread(os.path.join(outputDir,file))
            image = imgTransf.normalize(image)
            imageList.append(str(id))
            toRedis(r,image,str(id))
            id += 1
        images = ','.join(imageList)
        apiRequest = requests.get(f"http://{config.API_IP}:{config.API_PORT}/addTask?imgs={images}")
        if apiRequest.status_code != 200:
            logs.logger.error(f"Request error: status code {apiRequest.status_code}")
    return id
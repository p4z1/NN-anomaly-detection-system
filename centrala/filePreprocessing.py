from utilities import dirExist
import config
import time
import os

#Spracovanie CSV súborov na predikciu
def csvPreprocessing(files,logs, imgTransf):

    #Overenie existencie zložiek
    csvDir = os.path.join(config.ROOT_DIRECTORY, config.CSV_DIRECTORY)
    uploadDir = os.path.join(config.ROOT_DIRECTORY, config.UPLOAD_FOLDER)
    dirExist(csvDir)
    dirExist(uploadDir)   

    csvFiles = files.split(',')
    startTime = time.time()
    imgTuples = []
    try:
        #Vytvorenie obrázkov z CSV súboru
        for file in csvFiles:
            os.replace(os.path.join(uploadDir,file),os.path.join(csvDir,file))
            images = imgTransf.groupImageCreation(file)
            for image in images:
                imgTuples.append((image,file))
    except:
        logs.logger.error(f"CSV transformation to image didn't complete")
        return imgTuples
    if config.LOG_TIME: logs.logger.info(f"CSV transformation to image took {time.time()-startTime:.4f}s")
    return imgTuples
from openvino.inference_engine import IECore
import numpy as np
import redis
import multiprocessing
import config
import fileTransfer
import time
import os
import logging
import logging.handlers as handlers

class OnlyOneLevelFilter(object):
    def __init__(self, level):
        self.level = level

    def filter(self, logRecord):
        return logRecord.levelno == self.level

class Logs():
    def __init__(self):
        self.setLogger()

    def setLogger(self):
        
        logDir = os.path.join(config.ROOT_DIRECTORY,config.LOG_DIRECTORY)
        if not os.path.exists(logDir):
            os.mkdir(logDir)
        self.logger = logging.getLogger("OPENVINO")
        self.logger.setLevel(logging.INFO)
        formater = logging.Formatter(config.LOG_FORMAT)

        logHandler = handlers.TimedRotatingFileHandler(os.path.join(logDir,config.INFO_FILE_NAME), when='D', interval=1, backupCount=config.BACKUP_COUNT_INFO)
        logHandler.setLevel(logging.INFO)
        logHandler.addFilter(OnlyOneLevelFilter(logging.INFO))
        logHandler.setFormatter(formater)

        warnLogHandler = handlers.TimedRotatingFileHandler(os.path.join(logDir,config.WARNING_FILE_NAME), when='D', interval=3, backupCount=config.BACKUP_COUNT_WARNING)
        warnLogHandler.setLevel(logging.WARNING)
        warnLogHandler.addFilter(OnlyOneLevelFilter(logging.WARNING))
        warnLogHandler.setFormatter(formater)

        errorLogHandler = handlers.RotatingFileHandler(os.path.join(logDir,config.ERROR_FILE_NAME), maxBytes=500000, backupCount=3)
        errorLogHandler.setLevel(logging.ERROR)
        errorLogHandler.addFilter(OnlyOneLevelFilter(logging.ERROR))
        errorLogHandler.setFormatter(formater)

        self.logger.addHandler(logHandler)
        self.logger.addHandler(warnLogHandler)
        self.logger.addHandler(errorLogHandler)

class Classify():
    def __init__(self, r, logs):
        self.model = os.path.join(config.ROOT_DIRECTORY,config.MODEL_ROOT_DIR,config.NCS_MODEL)
        self.weights = os.path.join(config.ROOT_DIRECTORY,config.MODEL_ROOT_DIR,config.NCS_WEIGHTS)
        self.device = config.NCS_DEVICE
        self.batchSize = config.BATCH_SIZE
        self.r = r
        self.logs = logs
        self.loadModel()

    def loadModel(self):
        try:
            startTime = time.time()
            ie = IECore()
            self.net = ie.read_network(model=self.model,weights=self.weights) 
            self.input_blob = next(iter(self.net.inputs))
            self.out_blob = next(iter(self.net.outputs))
            self.net.batch_size = self.batchSize
            self.exec_net = ie.load_network(network=self.net, device_name=self.device)
            self.logs.logger.info(f"Model for OPENVINO is loaded. Time took: {time.time()-startTime:.4f}s")
        except:
            self.logs.logger.error("Something when wrong during OPENVINO model reading.")
    def _fromRedis(self, r,id):
        encoded = r.get(id)
        a = np.frombuffer(encoded,dtype=np.float32).reshape(3,224,224)
        return a

    def _delFromRedis(self,r,ids,batchSize):
        for i in range(batchSize):
            r.delete(ids[i])

    def _checkPrediction(self,res, imageNumbers):
        found = []
        benign = []
        for i, probs in enumerate(res):
            probs = np.squeeze(probs)
            id = np.argsort(probs)[-1:][::-1]
            if config.VERBOSE:
                print(f"File : {imageNumbers[i]}.csv -> {id[0]}")
            if str(id[0]) == '1':
                found.append(imageNumbers[i])                   
            elif str(id[0]) == '0':
                benign.append(imageNumbers[i])
        if config.LOGGING:
            if found:
                anomaly = ','.join([" "+str(i)+".csv" for i in found])
                self.logs.logger.warning(f"Possible anomaly detected in files:{anomaly}")
            if benign:
                benign = ','.join([" "+str(i)+".csv" for i in benign])
                self.logs.logger.info(f"Anomaly wasn't detected in file:{benign}")
        if config.REMOTE:
            p = multiprocessing.Process(target=fileTransfer.uploadFile, args=(found,))
            p.start()

    def startDetection(self,files):
        startTime = time.time() 
        n, c, h, w = self.net.input_info[self.input_blob].input_data.shape
        images = np.ndarray(shape=(n, c, h, w))
        imageNumbers = files.split(',')
        for i in range(n):      
            images[i] = self._fromRedis(self.r,imageNumbers[i])
        try:
            res = self.exec_net.infer(inputs={self.input_blob: images})
            res = res[self.out_blob]
            self.logs.logger.info(f"Prediction took {time.time()-startTime:.4f}s for {n} images.")
            self._checkPrediction(res,imageNumbers)      
            self._delFromRedis(self.r,imageNumbers, self.batchSize)
        except:
            self.logs.logger.error("Something when wrong during predictions.")
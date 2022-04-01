from openvino.inference_engine import IECore
from utilities import uploadFile, fromRedis, delFromRedis

import multiprocessing
import numpy as np
import config
import time
import os
import sys

# Softmax funkcia pre upravu hodnôt v 1D numpy poli
def softmax(x):
    exp=np.exp(x)
    probability=exp/np.sum(exp)
    return probability

class Classify():
    def __init__(self, r, logs):
        #Nastavenie počiatočných parametrov pre predikciu neurónovou siete
        self.model = os.path.join(config.ROOT_DIRECTORY,config.MODEL_ROOT_DIR,config.NCS_MODEL)
        self.weights = os.path.join(config.ROOT_DIRECTORY,config.MODEL_ROOT_DIR,config.NCS_WEIGHTS)
        self.device = config.NCS_DEVICE
        self.batchSize = config.BATCH_SIZE
        self.r = r
        self.logs = logs
        self._loadModel()

    #Otvorenie zvoleného modelu pomocou OPENVINO toolkit a jeho príprava na predikciu
    def _loadModel(self):
        try:
            startTime = time.time()
            ie = IECore()
            self.net = ie.read_network(model=self.model,weights=self.weights) 
            self.input_blob = next(iter(self.net.inputs))
            self.out_blob = next(iter(self.net.outputs))
            self.net.batch_size = self.batchSize
            self.exec_net = ie.load_network(network=self.net, device_name=self.device)
            self.logs.logger.info(f"Initialisation: Model for OPENVINO is loaded")
            if config.LOG_TIME: self.logs.logger.info(f"Model initiasation took {time.time()-startTime:.4f}s")
        except:
            self.logs.logger.error("Something when wrong during OPENVINO initialisation")
            sys.exit(1)

    #Skontrolovanie výstupu z neurónovej siete po predikcií
    def _checkPrediction(self,res, imageNumbers,tag):
        found = []
        for i, probs in enumerate(res):
            #Výber najlepšieho výsledku
            probs = np.squeeze(probs)
            id = np.argsort(probs)[-1:][::-1]
            #Úprava výstupu do percentuálnej formy a výber najväčšej hodnoty
            topProb = np.sort(softmax(probs))[-1]
            if tag == "csv":
                file = f"{imageNumbers[i]}.csv"
            else:
                file = str(imageNumbers[i].split(';')[1])

            #Zaznamenanie výsledku do logov
            if str(id[0]) == '1':               
                self.logs.logger.warning(f"{float(topProb*100):.4f}% {file} Anomaly")
                found.append(file)
            else:                
                self.logs.logger.info(f"{float(topProb*100):.4f}% {file} Benign")
                found.append(file)
            
            #Výpis výsledkov do konzoly
            if config.VERBOSE:
                print(f"File : {file} -> {id[0]}")
        # Zaslanie zistených anomálií na prekontrolvanie centrále                 
        if config.REMOTE:
            p = multiprocessing.Process(target=uploadFile, args=(found,))
            p.start()

    #Vytvorenie predikcie na obrázkoch
    def startDetection(self,files,tag):
        startTime = time.time() 
        n, c, h, w = self.net.input_info[self.input_blob].input_data.shape
        images = np.ndarray(shape=(n, c, h, w))
        imageNumbers = files.split(',')
        #Výber obrázkov z redisu
        for i in range(n):      
            images[i] = fromRedis(self.r,imageNumbers[i])
        try:
            #Začiatok predikcie 
            res = self.exec_net.infer(inputs={self.input_blob: images})
            res = res[self.out_blob]
            if config.LOG_TIME: self.logs.logger.info(f"Prediction took {time.time()-startTime:.4f}s for {n} images")
            #Spracovanie výstupu
            self._checkPrediction(res,imageNumbers,tag)     
            #Odstranenie obrázkov z redisu
            delFromRedis(self.r,imageNumbers, self.batchSize)
        except:
            self.logs.logger.error("Something when wrong during predictions")
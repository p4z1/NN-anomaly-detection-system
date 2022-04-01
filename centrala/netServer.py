from torchvision import models
import torch.nn.functional as nnf
import torch.nn as nn
import utilities
import config
import torch
import time
import sys
import os

class Classify():
    def __init__(self, logs):
        self.logs = logs
        self.modelPath = os.path.join(config.ROOT_DIRECTORY,config.MODEL_ROOT_DIR)

        #Nastavenie počiatočných parametrov pre predikciu neurónovou siete
        self.device = torch.device(config.TORCH_DEVICE if torch.cuda.is_available() else "cpu")       
        if self.device.type == 'cuda':
            self.logs.logger.info(f"Initiasaion: Using {self.device.type} on {torch.cuda.get_device_name(torch.cuda.current_device())} as torch device")
        else:
            self.logs.logger.info(f"Initiasaion: Using {self.device.type} as torch device.")
        self._loadModel()

    #Otvorenie zvoleného modelu pomocou Pytorch a jeho príprava na predikciu
    def _loadModel(self):
        try:
            startTime = time.time()
            if config.TORCH_MODEL == "mobilenet_v3_large":
                self.model = models.mobilenet_v3_large(pretrained=False)
            elif config.TORCH_MODEL == "efficientnet_b7":
                self.model = models.efficientnet_b7(pretrained=False)
                self.model.classifier[1] = nn.Linear(in_features=2560, out_features=20)
            self.model.load_state_dict(torch.load(os.path.join(self.modelPath, f"{config.TORCH_MODEL}.pth")))
            self.model.eval()
            self.model.to(self.device)
            self.logs.logger.info(f"Initiasaion: Model {config.TORCH_MODEL.split('.')[0]} is loaded.")
            if config.LOG_TIME: self.logs.logger.info(f"Model initiasation took {time.time()-startTime:.4f}s")
        except:
            self.logs.logger.critical("Something when wrong during torch model initialisation")
            sys.exit(1)

    #Skontrolovanie výstupu z neurónovej siete po predikcií
    def _checkPrediction(self,output, fileName):
        #Úprava výstupu do percentuálnej formy a výber najväčšej hodnoty
        probs = nnf.softmax(output, dim=1)
        topProb, topClass = probs.topk(1, dim = 1)
        mappedClass = topClass.item()
        #Mapovanie výstupu na kategóriu
        if mappedClass < 16:
            mappedClass = config.REVERSE_CATEGORIES_MAP[mappedClass]

        #Odstránenie špecifického názvu útoku
        if not config.CATEGORIES_FULL_NAME: mappedClass = str(mappedClass).split(' ')[0]

        #Zaznamenanie výsledku do logov
        if int(topClass.item()) > 0:
            if fileName.split('.')[-1] == "csv":
                self.logs.logger.warning(f"{float(topProb.item()*100):.4f}% {fileName} CSV {mappedClass}")
            else:
                self.logs.logger.info(f"{float(topProb.item()*100):.4f}% {fileName} Image {mappedClass}")
        else:
            if fileName.split('.')[-1] == "csv":
                path = os.path.join(config.ROOT_DIRECTORY, config.CSV_DIRECTORY)
                utilities.csvRename(path, fileName, "FP"+fileName)      #Tagovanie súboru v prípade FP
                self.logs.logger.info(f"{float(topProb.item()*100):.4f}% {fileName} CSV {mappedClass} FalsePositive")
            else:
                self.logs.logger.info(f"{float(topProb.item()*100):.4f}% {fileName} Image {mappedClass} Negative")
        return (float(topProb.item()),mappedClass)
    
    #Vytvorenie predikcie na obrázkoch
    def getPrediction(self,image):
        startTime = time.time() 
        try:
            with torch.no_grad():
                input = image[0].unsqueeze(0)
                input = input.to(self.device)
                outputs = self.model.forward(input)
                if config.LOG_TIME: self.logs.logger.info(f"Prediction took {time.time()-startTime:.4f}s")
                return self._checkPrediction(outputs, image[1])
        except:
            self.logs.logger.error("Something when wrong during predictions")
         
from torchvision import transforms
from PIL import Image

import pandas as pd
import numpy as np
import random
import config
import tqdm
import os

class Transformation():
    def __init__(self):
        self.width = config.IMAGE_WIDTH // config.SCALE
        self.height = config.IMAGE_HEIGHT // config.SCALE
        self._scaleMul = config.SCALE      
        self._imagesDir = os.path.join(config.ROOT_DIRECTORY,config.IMAGE_DIRECTORY)
        self._csvDir = os.path.join(config.ROOT_DIRECTORY,config.CSV_DIRECTORY)
        if config.NUMBER_OF_ARGUMENTS == 4 or config.NUMBER_OF_ARGUMENTS == 8:
            self._pixelsPerFlow = config.NUMBER_OF_ARGUMENTS
        else:
            self._pixelsPerFlow = 4     

    #Vytvorenie zložky ak nieje vytvorená
    def _existOrCreateDir(self, path):
        if not os.path.exists(path):
            os.mkdir(path)

    #Vytvorenie csv súboru s označením obrázkov vytvorenej dátovej sady.
    #Značky sú 0 (benign) a 1 (anomaly)   
    def _createLabelBin(self,labels, fileName):
        df = pd.DataFrame(labels)
        print("Creating labels")
        df.to_csv(os.path.join(self._imagesDir,fileName+'.csv'),index=False)

    #Vytvorenie csv súboru s označením obrázkov vytvorenej dátovej sady.
    #Značky sú pridenené každému označenému útoku
    def _createLabelCat(self, labels, fileName):
        df = pd.DataFrame(labels)
        print("Creating Cat labels")
        df.to_csv(os.path.join(self._imagesDir,fileName+'.csv'),index=False)

    #Usporiadanie dátovej sady podľa času
    def _preprocessing(self, df):
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], infer_datetime_format = True)
        df.sort_values(by = 'Timestamp', ascending = True, inplace = True)
        df.reset_index(drop=True, inplace=True)
        return df

    # Rozdelenie hodnoty v decimalnej sústave na dve 8bitové hodonty
    def _decToBinSplit16b(self, value):
        if value < 0:
            value = 0
        elif value > 65535:
            value = 65535

        binnary = bin(value)[2:]
        while len(binnary) < 16:
            binnary = "0" + binnary

        return [int("0b"+binnary[:8],2),int("0b"+binnary[8:16],2)]

    #Rozdelenie hodnoty v decimalnej sústave na tri 8bitové hodonty
    def _decToBinSplit24b(self, value):
        if value < 0:
            value = 0
        elif value > 16777215:
            value = 16777215

        binnary = bin(value)[2:]
        while len(binnary) < 24:
            binnary = "0" + binnary

        return [int("0b"+binnary[:8],2),int("0b"+binnary[8:16],2),int("0b"+binnary[16:24],2)]

    #Zvacsenie obrázku na požadované rozmery
    def _imageScale(self, picture):
        pixelRow = []
        pixels = []
        numberOfPixels = 0
        for pixel in picture:
            for i in range(self._scaleMul):
                pixelRow.append(pixel)
                numberOfPixels +=1
            if numberOfPixels == self.width:
                numberOfPixels = 0
                for i in range(4):
                    pixels.append(pixelRow)
                pixelRow = []
        array = np.array(pixels, dtype=np.uint8)
        array = np.reshape(array,(config.IMAGE_HEIGHT,config.IMAGE_WIDTH,3))
        return array

    #Postup vytvorenia štyroch pixelov z jednéj relácie.
    def _create4Pixels(self,CSVfile,row):
        pixels = []

        # 2x 8bit hodnoty s cieľového portu
        port = self._decToBinSplit16b(int(CSVfile["Dst Port"].values[row]))

        # 1x 8bit hodnota s počtu vyskytnutých sa flagov
        fin = int(CSVfile["FIN Flag Cnt"].values[row])
        syn = int(CSVfile["SYN Flag Cnt"].values[row])
        rst = int(CSVfile["RST Flag Cnt"].values[row])
        psh = int(CSVfile["PSH Flag Cnt"].values[row])
        ack = int(CSVfile["ACK Flag Cnt"].values[row])
        urg = int(CSVfile["URG Flag Cnt"].values[row])
        cwe = int(CSVfile["CWE Flag Count"].values[row])
        ece = int(CSVfile["ECE Flag Cnt"].values[row])
            
        flagValue = fin*(2**0)+syn*(2**1)+rst*(2**2)+psh*(2**3)+ack*(2**4)+urg*(2**5)+cwe*(2**6)+ece*(2**7)
        
        #1x 8bit hodnota s priemernov veľkosťov paketu
        #Hodnota je zaradená do blokov o veľkosti 256
        packetSizeAver = int(CSVfile["Pkt Size Avg"].values[row])
        packetSizeAverValue = packetSizeAver//256
        if packetSizeAverValue > 255:
            packetSizeAverValue = 255

        #2x 8bit hodnota s dľžkov trvania relácie
        flowDuration = int(CSVfile["Flow Duration"].values[row])
        flowDuration = flowDuration//4
        flowDuration = self._decToBinSplit16b(flowDuration)

        #3x 8bit hodnota s priemerným časom medzi paketmi 
        flowIATMean = int(CSVfile["Flow IAT Mean"].values[row])
        flowIATMean = flowIATMean//3
        flowIATMean = self._decToBinSplit24b(flowIATMean)
        
        #3x 8bit hodnota s počtom paketov za sekundu počas relácie
        flowPackets = float(CSVfile["Flow Pkts/s"].values[row])  
        if flowPackets > 16777.215:
            flowPackets = 16777.215
        flowPackets = int(flowPackets*1000)
        flowPackets = self._decToBinSplit24b(flowPackets)

        #Poskladanie vytvorených častí do formy pixelov
        pixels.append((flowDuration[0],flowDuration[1],flagValue))
        pixels.append((port[0],port[1],packetSizeAverValue))
        pixels.append((flowIATMean[0],flowIATMean[1],flowIATMean[2]))
        pixels.append((flowPackets[0],flowPackets[1],flowPackets[2]))

        return pixels
    #Postup vytvorenia štyroch pixelov z jednéj relácie.
    def _create8Pixels(self,CSVfile,row):
        #Vytvorenie štyroch pixelov
        pixels = self._create4Pixels(CSVfile,row)

        #1x 8bit hodnota s celkovým počtom kupredným paketov
        totalFwdPacket = int(CSVfile["Tot Fwd Pkts"].values[row])
        if totalFwdPacket > 255:
            totalFwdPacket = 255

        #2x 8bit hodnota s dopredným priemerným časom medzi paketmi 
        fwdHeaderLength = int(CSVfile["Fwd Header Len"].values[row])
        fwdHeaderLength = self._decToBinSplit16b(fwdHeaderLength)

        #3x 8bit hodnota s dopredným priemerným časom medzi paketmi 
        fwdIATMean = int(CSVfile["Fwd IAT Mean"].values[row])
        fwdIATMean = self._decToBinSplit24b(fwdIATMean)

        #3x 8bit hodnota s dopredným štandartným časom medzi paketmi 
        fwdIATStd = int(CSVfile["Fwd IAT Std"].values[row])
        fwdIATStd = self._decToBinSplit24b(fwdIATStd)

        #3x 8bit hodnota s dozadným priemerným časom medzi paketmi 
        bwdIATMean = int(CSVfile["Bwd IAT Mean"].values[row])
        bwdIATMean = self._decToBinSplit24b(bwdIATMean)
        
        #Poskladanie vytvorených častí do formy pixelov
        pixels.append((totalFwdPacket,fwdHeaderLength[1],fwdHeaderLength[0]))
        pixels.append((fwdIATMean[2],fwdIATMean[0],fwdIATMean[1]))
        pixels.append((fwdIATStd[1],fwdIATStd[2],fwdIATStd[0]))
        pixels.append((bwdIATMean[2],bwdIATMean[1],bwdIATMean[0]))
        return pixels

    #Vytvorenie obrázku o požadovanej veľkosti z poskytnutého CSV súboru
    def _createPicture(self, CSVfile, startRow = 0):
        pixels = []  
        label = 0
        labelCat = "Benign"

        #Prechádzanie postupne relácií v CSV súboru
        for i in range(self.width*self.height//self._pixelsPerFlow):
            flowRow = startRow + i
            #Ak nie je koniec súboru
            if flowRow < len(CSVfile.index):
                if self._pixelsPerFlow == 4:    # 4 pixely z jednej relácie
                    flow = self._create4Pixels(CSVfile,flowRow)
                else:                           # 8 pixely z jednej relácie
                    flow = self._create8Pixels(CSVfile,flowRow)
                #Vytvorenie označenia vytvoreného obrázka
                if self._labelCreation:
                    # Overenie doposiaľ vybrané označenie pre prípad neprepisovania
                    if CSVfile["Label"].values[flowRow] != "Benign" and label == 0:
                        label = config.CATEGORIES_MAP[CSVfile["Label"].values[flowRow]]
                        labelCat = CSVfile["Label"].values[flowRow]
            #Ak je CSV súbor na konci, pixely majú čiernu farbu
            else:   
                flow = [(0,0,0)]*self._pixelsPerFlow
            for pixel in flow:
                pixels.append(pixel)
        if self._labelCreation:
            return pixels, label, labelCat
        else:
            return pixels

    #Normalizácia obrázka pre požiadavky neuronovej siete
    def normalize(self,image):
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                    std=[0.229, 0.224, 0.225])
        transform = transforms.Compose([
            transforms.ToTensor(),
            normalize,
        ])
        return transform(image)

    #Vytvorenie iba jedného obrázku z CSV súboru
    def imageCreation(self, file):
        self._labelCreation = False
        CSVfile = pd.read_csv(os.path.join(self._csvDir,file))
        image = self._createPicture(CSVfile=CSVfile)
        image = self._imageScale(image)
        
        #Výstup je zväčšený a noramlizovaný obrázok vo forme tenzoru
        return self.normalize(Image.fromarray(image))
    
    #Vytvorenie maximálneho počtu obrázkov z CSV súboru
    #Ak posledný obrázok nie je plne zaplnený reláciami, tak nie je vytváraný
    def groupImageCreation(self, file):
        images = []
        self._labelCreation = False
        CSVfile = pd.read_csv(os.path.join(self._csvDir,file))
        rowsPerImage = (self.width*self.height//self._pixelsPerFlow)#Počet relácií na jeden obrázok
        numOfImages = len(CSVfile.index)//rowsPerImage              #Počet vytváraných obrázkov
        
        for i in range(numOfImages):
            image = self._createPicture(CSVfile=CSVfile,startRow=rowsPerImage*i)
            image = self._imageScale(image)
            image = self.normalize(Image.fromarray(image))
            images.append(image)
        # Výstup je pole zväčšených a normalizovaných obrázkov
        return images   

    # Vytvorenie dátovej sady pozostávajúcej z obrázkov a označením 
    def dataSetCreation(self):
        self._labelCreation = True
        imageNumber = 0
        labels = []
        labelsCat = []
        
        self._existOrCreateDir(os.path.join(self._imagesDir))
        #Získanie názvou CSV súborov v zložke 
        csvFiles = os.listdir(os.path.join(self._csvDir)) 

        for file in csvFiles:
            # Čítanie a uprava CSV dát
            CSVfileRand = pd.read_csv(os.path.join(self._csvDir,file))
            CSVfile = self._preprocessing(CSVfileRand)
            
            numberOfFlows = len(CSVfile.index)
            partialImagesCount = self._pixelsPerFlow*((numberOfFlows*2)//(self.width*self.height))-1
            
            progress = tqdm.tqdm(range(partialImagesCount), f"Processing {file}.", unit="Images", unit_scale=True, unit_divisor=256)
            for offset in range(partialImagesCount):
                flowRow = offset*self.width*self.height//(self._pixelsPerFlow*2)
                # Vytvorenie označení a obrázka
                image, label, labelCat = self._createPicture(CSVfile, startRow = flowRow)
                
                #Úprava obrázka a jeho uloženie
                image = self._imageScale(image)
                saveDir = os.path.join(self._imagesDir,labelCat)
                self._existOrCreateDir(saveDir)
                imageName = str(imageNumber)+".png"
                imagePath = os.path.join(saveDir,imageName)
                image = Image.fromarray(image).save(imagePath)
                labels.append([os.path.join(labelCat,imageName), 1 if label > 0 else 0])
                labelsCat.append([os.path.join(labelCat,imageName),label])

                imageNumber += 1
                progress.update(1)
            progress.close()

        #Vytvorenie súboru so všetkými označeniami obrázkov a cesty k ním
        self._createLabelBin(labels, "Labels")
        self._createLabelCat(labelsCat, "LabelsCat")
import config
import random
import config
from PIL import Image
import pandas as pd
import numpy as np
from torchvision import transforms
import os
import tqdm

"""
    -- init 
        - width of image
        - height of image
        - image scale factor. (default is 4 -> 56x56 -> 224x224)
        - directory with csv files

    -- detection
        input : csv name

        return normalized image 

    -- dataSetCreation
        input : label mode
"""

class Transformation():
    def __init__(self):
        self.width = config.IMAGE_WIDTH // config.SCALE
        self.height = config.IMAGE_HEIGHT // config.SCALE
        self._scaleMul = config.SCALE
        self._rootDir = config.ROOT_DIRECTORY      
        self._imagesDir = config.IMAGE_DIRECTORY
        self._csvDir = config.CSV_DIRECTORY
        if config.NUMBER_OF_ARGUMENTS == 4 or config.NUMBER_OF_ARGUMENTS == 8:
            self._pixelsPerFlow = config.NUMBER_OF_ARGUMENTS
        else:
            self._pixelsPerFlow = 4     

    def _existOrCreateDir(self, path):
        if not os.path.exists(path):
            os.mkdir(path)

    def _createLabelBin(self,labels, text):
        df = pd.DataFrame(labels)
        print("Creating labels")
        df.to_csv('Images/'+text+'.csv',index=False)

    def _createLabelCat(self, labels, text):
        df = pd.DataFrame(labels)
        print("Creating Cat labels")
        df.to_csv('Images/'+text+'.csv',index=False)

    def _preprocessing(self, df):
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], infer_datetime_format = True)
        df.sort_values(by = 'Timestamp', ascending = True, inplace = True)
        df.reset_index(drop=True, inplace=True)
        ## pridat zistovnie a opravovanie nazvou !!!
        return df

    def _decToBinSplit16b(self, value):
        if value < 0:
            value = 0
        elif value > 65535:
            value = 65535

        binnary = bin(value)[2:]
        while len(binnary) < 16:
            binnary = "0" + binnary
        if len(binnary) > 16:
            print(len(binnary))

        return [int("0b"+binnary[:8],2),int("0b"+binnary[8:16],2)]

    def _decToBinSplit24b(self, value):
        if value < 0:
            value = 0
        elif value > 16777215:
            value = 16777215

        binnary = bin(value)[2:]
        while len(binnary) < 24:
            binnary = "0" + binnary

        return [int("0b"+binnary[:8],2),int("0b"+binnary[8:16],2),int("0b"+binnary[16:24],2)]
    
    def _dataArgumentation(self, picture):
        argPicture = []
        shuffleArray = []
        for i in range(28*28):
            shuffleArray.append(i)
        random.shuffle(shuffleArray)
        for i in shuffleArray:
            for j in range(4):
                argPicture.append(picture[(i*4)+j])
        return argPicture 

    def _imageScale(self, picture):
        pixelRow = []
        pixels = []
        numberOfPixels = 0
        for pixel in picture:
            for i in range(self._scaleMul):
                pixelRow.append(pixel)
                numberOfPixels +=1
            if numberOfPixels == 224:
                numberOfPixels = 0
                for i in range(4):
                    pixels.append(pixelRow)
                pixelRow = []
        array = np.array(pixels, dtype=np.uint8)
        array = np.reshape(array,(224,224,3))
        return array

    def _create4Pixels(self,CSVfile,row):
        pixels = []

        port = self._decToBinSplit16b(int(CSVfile["Dst Port"].values[row]))

        fin = int(CSVfile["FIN Flag Cnt"].values[row])
        syn = int(CSVfile["SYN Flag Cnt"].values[row])
        rst = int(CSVfile["RST Flag Cnt"].values[row])
        psh = int(CSVfile["PSH Flag Cnt"].values[row])
        ack = int(CSVfile["ACK Flag Cnt"].values[row])
        urg = int(CSVfile["URG Flag Cnt"].values[row])
        cwe = int(CSVfile["CWE Flag Count"].values[row])
        ece = int(CSVfile["ECE Flag Cnt"].values[row])

        flagValue = fin*(2**0)+syn*(2**1)+rst*(2**2)+psh*(2**3)+ack*(2**4)+urg*(2**5)+cwe*(2**6)+ece*(2**7)
        
        packetSizeAver = int(CSVfile["Pkt Size Avg"].values[row])
        packetSizeAverValue = packetSizeAver//256
        if packetSizeAverValue > 255:
            packetSizeAverValue = 255

        flowDuration = int(CSVfile["Flow Duration"].values[row])
        flowDuration = flowDuration//4
        flowDuration = self._decToBinSplit16b(flowDuration)

        flowIATMean = int(CSVfile["Flow IAT Mean"].values[row])
        flowIATMean = flowIATMean//3
        flowIATMean = self._decToBinSplit24b(flowIATMean)

        flowPackets = float(CSVfile["Flow Pkts/s"].values[row])  
        if flowPackets > 16777.215:
            flowPackets = 16777.215
        flowPackets = int(flowPackets*1000)
        flowPackets = self._decToBinSplit24b(flowPackets)

        pixels.append((flowDuration[0],flowDuration[1],flagValue))
        pixels.append((port[0],port[1],packetSizeAverValue))
        pixels.append((flowIATMean[0],flowIATMean[1],flowIATMean[2]))
        pixels.append((flowPackets[0],flowPackets[1],flowPackets[2]))

        return pixels
        
    def _create8Pixels(self,CSVfile,row):
        pixels = self._create4Pixels(CSVfile,row)

        totalFwdPacket = int(CSVfile["Tot Fwd Pkts"].values[row])
        if totalFwdPacket > 255:
            totalFwdPacket = 255

        fwdHeaderLength = int(CSVfile["Fwd Header Len"].values[row])
        fwdHeaderLength = self._decToBinSplit16b(fwdHeaderLength)

        fwdIATMean = int(CSVfile["Fwd IAT Mean"].values[row])
        fwdIATMean = self._decToBinSplit24b(fwdIATMean)

        fwdIATStd = int(CSVfile["Fwd IAT Std"].values[row])
        fwdIATStd = self._decToBinSplit24b(fwdIATStd)

        bwdIATMean = int(CSVfile["Bwd IAT Mean"].values[row])
        bwdIATMean = self._decToBinSplit24b(bwdIATMean)
        
        pixels.append((totalFwdPacket,fwdHeaderLength[1],fwdHeaderLength[0]))
        pixels.append((fwdIATMean[2],fwdIATMean[0],fwdIATMean[1]))
        pixels.append((fwdIATStd[1],fwdIATStd[2],fwdIATStd[0]))
        pixels.append((bwdIATMean[2],bwdIATMean[1],bwdIATMean[0]))
        return pixels

    def _createPicture(self, CSVfile, startRow = 0):
        pixels = []  
        label = 0
        labelCat = "Benign"

        for i in range(self.width*self.height//self._pixelsPerFlow):
            flowRow = startRow + i
            if flowRow < len(CSVfile.index):
                if self._pixelsPerFlow == 4:
                    flow = self._create4Pixels(CSVfile,flowRow)
                else:
                    flow = self._create8Pixels(CSVfile,flowRow)
                if self._labelCreation:
                    if CSVfile["Label"].values[flowRow] != "Benign" and label == 0:
                        label = config.CATEGORIES_MAP[CSVfile["Label"].values[flowRow]]
                        labelCat = CSVfile["Label"].values[flowRow]
            else:
                flow = [(0,0,0)]*self._pixelsPerFlow
            for pixel in flow:
                pixels.append(pixel)
        if self._labelCreation:
            return pixels, label, labelCat
        else:
            return pixels

    def normalize(image):
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                    std=[0.229, 0.224, 0.225])
        transform = transforms.Compose([
            transforms.ToTensor(),
            normalize,
        ])
        return transform(Image.fromarray(image)).numpy()

    def imageCreation(self, file):
        self._labelCreation = False
        CSVfile = pd.read_csv(os.path.join(self._rootDir,self._csvDir,file))
        image = self._createPicture(CSVfile=CSVfile)
        image = self._imageScale(image)

        return self.normalize(image)
        
    def dataSetCreation(self):
        self._labelCreation = True
        imageNumber = 0
        labels = []
        labelsCat = []
        
        self._existOrCreateDir(os.path.join(self._rootDir,self._imagesDir))
        csvFiles = os.listdir(os.path.join(self._rootDir,self._csvDir)) 

        for file in csvFiles:
            CSVfileRand = pd.read_csv(os.path.join(self._rootDir,self._csvDir,file))
            CSVfile = self._preprocessing(CSVfileRand)
            numberOfFlows = len(CSVfile.index)
            partialImages = self._pixelsPerFlow*((numberOfFlows*2)//(self.width*self.height))-1
            progress = tqdm.tqdm(range(partialImages), f"Processing {file}.", unit="Images", unit_scale=True, unit_divisor=256)
            for offset in range(partialImages):
                flowRow = offset*self.width*self.height//(self._pixelsPerFlow*2)
                image, label, labelCat = self._createPicture(CSVfile, startRow = flowRow)

                ## image argumentation

                image = self._imageScale(image)
                saveDir = os.path.join(self._rootDir,self._imagesDir,labelCat)
                self._existOrCreateDir(saveDir)
                imageName = str(imageNumber)+".png"
                imagePath = os.path.join(saveDir,imageName)
                image = Image.fromarray(image).save(imagePath)

                labels.append([os.path.join(labelCat,imageName), 1 if label > 0 else 0])
                labelsCat.append([os.path.join(labelCat,imageName),label])
                imageNumber += 1
                progress.update(1)
            progress.close()

        self._createLabelBin(labels, "Labels")
        self._createLabelCat(labelsCat, "LabelsCat")
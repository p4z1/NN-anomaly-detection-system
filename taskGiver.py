from PIL import Image
from skimage import io
from torchvision import transforms
import numpy as np
import pandas as pd
import redis
import struct
import requests
import time
import os
import argparse

def parserCheck():
    parser = argparse.ArgumentParser(description="Creating images for CNN")
    parser.add_argument("-m","--mode", dest = "mode",metavar='',type=int, help="1 is live mode with csv files, 0 is debug mode with images")
    parser.add_argument("-c","--csv", dest = "csv",metavar='',type=str, help="Path to dir with csv files. Default ./csvFiles")
    parser.add_argument("-i","--images", dest = "images",metavar='',type=str, help="Path to dir with images. Default ./Images")
    parser.add_argument("-o", "--output", dest = "output",metavar='',type=str, help="Path to output dir. Default ./Checked")
    parser.add_argument("-b", "--batch", dest = "batch",metavar='',type=int, help="Setting batch size. Default is 10")
    parser.add_argument("-a", "--api", dest = "api",metavar='',type=int, help="Setting IP:PORT to api. Default 127.0.0.1:5000")
    

    return parser.parse_args()

def toRedis(r,a,n):
   encoded = a.tobytes()
   r.set(n,encoded)

def decToBinSplit16b(value):
    binnary = bin(value)
    dec1 = "0b"
    dec2 = "0b"
    for i in range(16):
        if i <= 17-len(binnary):
            if len(dec1) < 10:
                dec1 += "0"
            else:
                dec2 += "0"
        else:
            if len(dec1) < 10:
                dec1 += binnary[len(binnary)-16+i]
            else:
                dec2 += binnary[len(binnary)-16+i]
    return [int(dec1,2),int(dec2,2)]

def decToBinSplit24b(value):
    binnary = bin(value)
    dec1 = "0b"
    dec2 = "0b"
    dec3 = "0b"
    for i in range(32):
        if i <= 33-len(binnary):
            if len(dec1) < 10:
                dec1 += "0"
            elif len(dec2) < 10:
                dec2 += "0"
            else:
                dec3 += "0"
        else:
            if len(dec1) < 10:
                dec1 += binnary[len(binnary)-32+i]
            elif len(dec2) < 10:
                dec2 += binnary[len(binnary)-32+i]
            else:
                dec3 += binnary[len(binnary)-32+i]
    return [int(dec1,2),int(dec2,2),int(dec3,2)]

def createPixel(CSVfile,row):
    port = decToBinSplit16b(int(CSVfile["Dst Port"].values[row]))

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
    packetSizeAverValue = packetSizeAver*255/1500
    if packetSizeAverValue > 255:
        packetSizeAverValue = 255
    elif packetSizeAverValue < 0:
        packetSizeAverValue = 0

    flowDuration = int(CSVfile["Flow Duration"].values[row])
    flowDuration = flowDuration//4
    if flowDuration > 65535:
        flowDuration = 65535
    elif flowDuration < 0:
        flowDuration = 0
    flowDuration = decToBinSplit16b(flowDuration)

    flowIATMean = int(CSVfile["Flow IAT Mean"].values[row])
    flowIATMean = flowIATMean//3
    if flowIATMean > 16777215:
        flowIATMean = 16777215
    elif flowIATMean < 0:
        flowIATMean = 0
    flowIATMean = decToBinSplit24b(flowIATMean)

    flowPackets = float(CSVfile["Flow Pkts/s"].values[row])
    
    if flowPackets > 16777.215:
        flowPackets = 16777.215
    elif flowPackets < 0:
        flowPackets = 0
    flowPackets = int(flowPackets*1000)
    flowPackets = decToBinSplit24b(flowPackets)

    return (flowDuration[0],flowDuration[1],flagValue),(port[0],port[1],packetSizeAverValue
    ),(flowIATMean[0],flowIATMean[1],flowIATMean[2]),(flowPackets[0],flowPackets[1],flowPackets[2])  

def CSVToImage(csvfile):
    numberOfPixels = 0
    width = 28
    height = 56
    pixels = []
    pixelRow = []
    for i in range(width*int(height//2)):
        flowRow = i
        if flowRow < len(csvfile.index):
            pixel1, pixel2,pixel3,pixel4 = createPixel(csvfile,flowRow)
        else:
            pixel1, pixel2,pixel3,pixel4 = (0,0,0),(0,0,0),(0,0,0),(0,0,0)
        for i in range(4):
            pixelRow.append(pixel1)
            numberOfPixels +=1
        for i in range(4):
            pixelRow.append(pixel2)
            numberOfPixels +=1
        for i in range(4):
            pixelRow.append(pixel3)
            numberOfPixels +=1
        for i in range(4):
            pixelRow.append(pixel4)
            numberOfPixels +=1
        if numberOfPixels == 224:
            numberOfPixels = 0
            for i in range(4):
                pixels.append(pixelRow)
            pixelRow = []
    array = np.array(pixels, dtype=np.uint8)
    array = np.reshape(array,(224,224,3))

    return array

def normalize(image):
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
    transform = transforms.Compose([
        transforms.ToTensor(),
        normalize,
    ])
    return transform(Image.fromarray(image)).numpy()

def dirExist(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)

def main():
    
    r = redis.Redis(host='localhost', port=6379)

    csvDir = "./csvFiles/"
    outputDir = "./Checked/"
    imagesDir = "./Images/"
    batchSize = 10
    apiIP = "127.0.0.1:5000"

    args = parserCheck()
    if args.batch is not None:
        batchSize = args.batch
    
    if args.api is not None:
        apiIP = args.api
    
    if args.mode == 0:
        if args.images is not None:
            imagesDir = args.images    
        if args.output is not None:
            outputDir = args.output
        
        dirExist(imagesDir)
        dirExist(outputDir)

        id = 0
        while True:
            files = os.listdir(imagesDir)
            while (len(files) // batchSize) >= 1:
                imageList = []
                for _ in range(batchSize):
                    file = files.pop(0)
                    os.replace(imagesDir+file,outputDir+file)
                    image = io.imread("./Checked/"+file)
                    image = normalize(image)
                    imageList.append(str(id))
                    toRedis(r,image,str(id))
                    id += 1
                imageList.append(str(batchSize))
                images = ','.join(imageList)
                apiRequest = requests.get('http://'+apiIP+'/task?n='+images)
            time.sleep(1)

    if args.mode == 1:
        if args.csv is not None:
            csvDir = args.csv    
        if args.output is not None:
            outputDir = args.output
        
        dirExist(csvDir)
        dirExist(outputDir)

        while True:
            csvList = os.listdir(csvDir)
            while ((len(csvList)-1) // batchSize) >= 1:
                imageList = []
                csvList.sort()
                for _ in range(batchSize):
                    file = csvList.pop(0)
                    os.replace(csvDir+file,outputDir+file)
                    csv = pd.read_csv(outputDir+file)
                    id = file[:-4]
                    image = CSVToImage(csv)
                    image = normalize(image)
                    imageList.append(str(id))
                    toRedis(r,image,str(id))
                imageList.append(str(batchSize))
                images = ','.join(imageList)
                apiRequest = requests.get('http://'+apiIP+'/task?n='+images)
                print(apiRequest.text)
            time.sleep(1)

if __name__ == "__main__":
    main()

    

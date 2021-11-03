from PIL import Image

import argparse
import pandas as pd
import numpy as np
import os
from scipy.sparse.lil import _prepare_index_for_memoryview

"""
Creating basic function structure for data conversion.
    Following task have to take place:

    1. Take data from CSV file.
    2. Select relevant collumn from data structure
    3. Find right pixel representation for selected data
    4. Repeat for every relevant collumn until image is created

    One relation to pixel:
        [(flow duration[1. part],
        flow duration[2. part],  set trashhold to ???
        Flags binary [FIN,SYN,RST,PSH,ACK,URG])        
        (port,
        port,  in binary
        Packet Size Average)] 
"""
#-----------------------------------------------------
#----------------------Parsing------------------------
#-----------------------------------------------------
"""
 Name:              Argument:           Description:

 -t  --testing      None                Creating pictures without labels
 -l  --learning     None                Creating pictures with labels
 -m  --mode         1 , 2 , 3           Type of data representation
 -h  --height       Int                 Height of image in pixels
 -w  --width        Int                 Width of image in pixels
 -b  --binnaty      None                Label output is in 0 or 1 format
 -c  --categories   None                Label output have categorical format
 -o  --output       Path                Path to output dir
 -i  --input        Path                Path to cvs file


"""
def parserCheck():
    parser = argparse.ArgumentParser(description="Creating images for CNN")
    purpose = parser.add_mutually_exclusive_group()
    purpose.add_argument("-t", "--testing", action='store_true', help="Creating pictures without labels")
    purpose.add_argument("-l", "--learning", action='store_true', help="Creating pictures with labels")
    outputFormat = parser.add_mutually_exclusive_group()
    outputFormat.add_argument("-b","--binnary",action='store_true', help="Label output is in 0 or 1 format")
    outputFormat.add_argument("-c","--categories",action='store_true', help="Label output have categorical format")
    parser.add_argument("-m","--mode", metavar='',type=int, help="Type of data representation")
    parser.add_argument("-iH","--height", metavar='',type=int, help="Height of image in pixels")
    parser.add_argument("-iW","--width", metavar='',type=int, help="Width of image in pixels")
    parser.add_argument("-o", "--output", metavar='',type=int, help="Path to output dir")
    parser.add_argument("-i", "--input", metavar='',type=int, help="Path to cvs file")

    return parser.parse_args()

#-----------------------------------------------------
#----------------------Labeling-----------------------
#-----------------------------------------------------
"""
    Needs to be in format: imageName, category
"""
def createLabelBin(labels):
    #cwd = os.getcwd()
    #print(cwd)
    #np.savetxt("Labels.csv",labels,delimiter=',')
    df = pd.DataFrame(labels)
    print("Creating labels")
    df.to_csv('Images/Labels.csv',index=False)

def createLabelCat(labels):
    return

#-----------------------------------------------------
#-----------------------Mapping-----------------------
#-----------------------------------------------------

def decToBinSplit(value):
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

#-----------------------------------------------------
#--------------------Image Creation-------------------
#-----------------------------------------------------

def createPixel(CSVfile,row):
    port = decToBinSplit(int(CSVfile["Dst Port"].values[row]))

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
    flowDuration = decToBinSplit(flowDuration)
    return (flowDuration[0],flowDuration[1],flagValue),(port[0],port[1],packetSizeAverValue)

def createPictures(CSVfile, width, height, flowNumber, imageNumber):
    pixels = []
    pixelRow = []
    numberOfPixels = 0
    label = 0
    anomaly = False
    for i in range(width*int(height//2)):
        flowRow = (flowNumber*width*height//4)+i
        if flowRow < len(CSVfile.index):
            pixel1, pixel2 = createPixel(CSVfile,flowRow)
            if anomaly:
                label = 1
            elif CSVfile["Label"].values[flowRow] != "Benign":
                anomaly = True
        else:
            pixel1, pixel2 = (0,0,0),(0,0,0)
        for i in range(4):
                pixelRow.append(pixel1)
                numberOfPixels +=1
        for i in range(4):
            pixelRow.append(pixel2)
            numberOfPixels +=1
        if numberOfPixels == 224:
            numberOfPixels = 0
            for i in range(4):
                pixels.append(pixelRow)
            pixelRow = []
        
    array = np.array(pixels, dtype=np.uint8)
    array = np.reshape(array,(height*4,width*4,3))
    
    new_image = Image.fromarray(array)
    file = "./Images/Anomaly"+str(imageNumber)+".png"
    new_image = new_image.save(file)

    labels = ["Anomaly"+str(imageNumber)+".png",label]
    print(file + " ==> "+str(label))    
    
    return labels

#-----------------------------------------------------
#--------------------Preprocessing--------------------
#-----------------------------------------------------    
                                 
def csvSorting(df):
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], infer_datetime_format = True)
    df.sort_values(by = 'Timestamp', ascending = True, inplace = True)
    df.reset_index(drop=True, inplace=True) 
    return df

#-----------------------------------------------------
#-------------------------Main------------------------
#-----------------------------------------------------

def getFileList(path):
    return os.listdir(path)
    

def main():
    #args = parserCheck()
    rootPath = './Datasets/'
    imageNumber = 0
    labels = []
    pictureWidth = 56
    pictureHeight = 56
    csvFiles = getFileList(rootPath)
    for file in csvFiles:
        df = pd.read_csv(rootPath+file)
        print("[+] ==> "+ rootPath+file)
        dfSorted = csvSorting(df)
        numberOfFlows = len(dfSorted.index)  
        for i in range((4*(numberOfFlows)//(pictureWidth*pictureHeight))+1):
            labels.append(createPictures(dfSorted,pictureWidth,pictureHeight,i,imageNumber))
            imageNumber += 1
    createLabelBin(labels)

if __name__ == "__main__":
    main()
from PIL import Image
import torch
import pandas as pd
import os, sys
from skimage import io
import matplotlib.pyplot as plt
import numpy as np
from torch.utils.data import Dataset
from torchvision import datasets, transforms

class AnomalyDataset(Dataset):
    def __init__(self,csvFile,rootDir,transform=None):
        self.annotations = pd.read_csv(csvFile)
        self.rootDir = rootDir
        self.transform = transform
    
    def __len__(self):
        return len(self.annotations)
        

    def __getitem__(self, index):
        imgPath = os.path.join(self.rootDir,self.annotations.iloc[index,0])
        print(self.annotations.iloc[index,0])
        print(self.annotations.iloc[index,1])
        image = io.imread(imgPath)
        yLabel = torch.tensor(int(self.annotations.iloc[index,1]))
        print(type(image))
        if self.transform:
            image = self.transform(Image.fromarray(image))
            print(type(image))
        
        return (image,yLabel)    

inputSize = 224
batchSize = 50
learninigRate = 0.001
epochs = 150

normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])

transform = transforms.Compose([
        transforms.RandomResizedCrop(inputSize, scale=(0.2, 1.0)), 
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        normalize,
    ])

dataset = AnomalyDataset(csvFile="./Images/Labels.csv", rootDir="Images",transform=transform)

trainDatasetLength = int(len(dataset)*0.7)

trainSet, testSet = torch.utils.data.random_split(dataset,[trainDatasetLength,len(dataset)-trainDatasetLength]) #splitovanie datasetu na testovacie a trenovacie data

trainLoader = torch.utils.data.DataLoader(trainSet,batch_size=batchSize,shuffle=True)
testLoader = torch.utils.data.DataLoader(testSet,batch_size=batchSize,shuffle=True)

model = torch.hub.load('pytorch/vision:v0.10.0','mobilenet_v2', pretrained=False)
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

criterion = torch.nn.CrossEntropyLoss()
model = model.cuda()
optimizer = torch.optim.Adam(model.parameters(),lr=learninigRate)

trainLoss = []
testLoss = []
trainAcc = []
testAcc = []

for epoch in range(1,epochs+1):
    runningLoss = .0
    correct = 0
    total = 0
    for i, (inputs,labels) in enumerate(trainLoader):
        inputs = inputs.cuda()
        labels = labels.cuda()

        optimizer.zero_grad()
        inputs.size()
        outputs = model(inputs)
        loss = criterion(outputs, labels) 

        loss.backward()

        optimizer.step()

        runningLoss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    runningLoss /= len(trainLoader)
    trainLoss.append(runningLoss)
    runningAcc = correct / total
    trainAcc.append(runningAcc)

    if epoch % 2 == 0:
        file_object = open('learninigOutput.txt', 'a')
        file_object.write("\nEpoch: {}".format(epoch))
        file_object.write('Train Acc. => {:.3f}%'.format(100*runningAcc))
        file_object.write('Train Loss => {:.5f}'.format(runningLoss))
        file_object.close()

    with torch.no_grad():
        correct = 0
        total = 0
        testRunningLoss = 0
        for data in testLoader:
            inputs, labels = data
            inputs = inputs.cuda()
            labels = labels.cuda()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            testRunningLoss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
        
        testRunningLoss /= len(testLoader)
        testLoss.append(testRunningLoss)
        testRunningAcc = correct /total
        testAcc.append(testRunningAcc)

        if epoch % 2 == 0:
            file_object = open('learninigOutput.txt', 'a')
            file_object.write("\nEpoch: {}".format(epoch))
            file_object.write('Test Acc. => {:.3f}%'.format(100 * testRunningAcc))
            file_object.write('Test Loss => {:.5f}'.format(testRunningLoss))
            file_object.close()

print('Finished Training')

def modelSave(model):
    torch.save(model,"anomalie.pth")

modelSave(model)
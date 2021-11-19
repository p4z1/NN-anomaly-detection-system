import requests
import time
import os

csvDir = "./Images/"
checkedCsv = "./Checked/"
batchSize = 10
if not os.path.exists(csvDir):
    os.mkdir(csvDir)
if not os.path.exists(checkedCsv):
    os.mkdir(checkedCsv)


while True:
    csvList = os.listdir(csvDir) 
    while (len(csvList) // batchSize) >= 1:
        files = ""
        print(len(csvList))
        for _ in range(batchSize-1):
            file = csvList.pop(0)
            os.replace(csvDir+file,checkedCsv+file)
            files += file
            files += ","
        file = csvList.pop(0)
        os.replace(csvDir+file,checkedCsv+file)
        files += file
        print(files + "\n")
        r = requests.get('http://10.0.0.2:5000/task?n='+files)
        print(r.text)
    time.sleep(1)
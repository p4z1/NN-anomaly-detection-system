import requests

filenames = ['test1.csv',"test2.csv","test3.csv","test4.csv"]
#filenames = ['107.png',"4564.png","13464.png"]
files = []
for name in filenames:
    file = open("./"+name,"rb")
    files.append(('files',file))
url = "http://185.146.4.71:5000/csvPredict"
#url = "http://10.0.0.5:5000/csvPredict"
test_response = requests.post(url, files = files) #, verify = "./certs/server.pem"
#url = "http://10.0.0.5:5000/imgPredicts"
#test_response = requests.post(url, files = files)
if test_response.ok:
    print("Upload completed successfully!")
    print(test_response.text)
else:
    print("Something went wrong!")
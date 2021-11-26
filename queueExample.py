from flask import Flask, request
from rq import Queue
from openvino.inference_engine import IECore

from torchvision import transforms
from PIL import Image
import numpy as np
import logging
import struct
import redis
import time
import sys
import os

app = Flask(__name__)

r = redis.Redis(host='localhost', port=6379)
q = Queue(connection=r)

BATCH_SIZE = 5



def fromRedis(r,n):
   """Retrieve Numpy array from Redis key 'n'"""
   encoded = r.get(n)
   #c, h, w = struct.unpack('>III',encoded[:12])
   # Add slicing here, or else the array would differ from the original
   #a = np.frombuffer(encoded[12:],dtype=np.float32).reshape(c, h, w)
   a = np.frombuffer(encoded,dtype=np.float32).reshape(3,224,224)
   return a

def delFromRedis(r,n):
    for i in range(BATCH_SIZE):
        r.delete(n[i])


def anomalyDetection(files):
    start_time = time.time()
    ie = IECore()
    net = ie.read_network(model="./anomalie.xml",weights="./anomalie.bin")
    device = "MYRIAD"
    print ("Model took " + str(time.time() - start_time) +"to load")
    start_time = time.time()
    imageNumbers = files.split(',')
    input_blob = next(iter(net.input_info))
    out_blob = next(iter(net.outputs))
    net.batch_size = BATCH_SIZE
    n, c, h, w = net.input_info[input_blob].input_data.shape
    images = np.ndarray(shape=(n, c, h, w))
    for i in range(n):      
        #image = io.imread("./Images/Anomaly"+imageNumbers[i]+".png")
        #image = fromRedis(r,imageNumbers[i])
        #image = transform(Image.fromarray(image))
        #images[i] = image.numpy()
        images[i] = fromRedis(r,imageNumbers[i])

    exec_net = ie.load_network(network=net, device_name=device)
    res = exec_net.infer(inputs={input_blob: images})
    res = res[out_blob]
    for i, probs in enumerate(res):
        probs = np.squeeze(probs)
        id = np.argsort(probs)[-1:][::-1]
        print("Image {}\n".format("./Checked/"+imageNumbers[i]+".csv"))
        print(f"Classid: {id}")
        if str(id) == '1':
            app.logger.warning("Possible anomaly detected in file: "+imageNumbers[i]+".csv")
        if str(id) == '0':
            app.logger.info("Anomaly wasn't detected in file: "+imageNumbers[i]+".csv")
    print ("Image evaluation took " + str(time.time() - start_time))
    delFromRedis(r,imageNumbers)


@app.route("/task")
def add_task():

    if request.args.get("n"):

        job = q.enqueue(anomalyDetection, request.args.get("n"))
        #job = q.enqueue(bacground_task, request.args.get("n"))

        q_len = len(q)

        return f"Task {job.id} added to queue at {job.enqueued_at}. {q_len} tasks in the queue"

    return "No value for n"

@app.route("/task")
def dashboard():
    qLen = len(q)
    return "In the queue are " + qLen + " tasks."

if __name__ == "__name__":
    logging.basicConfig(filename='anomaly.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #app.logger.info("Flask API started")
    app.run()
from flask import Flask, request
import redis
from rq import Queue

import time

from openvino.inference_engine import IECore
from skimage import io
from torchvision import transforms
from PIL import Image
import numpy as np
import sys
import os

app = Flask(__name__)

r = redis.Redis()
q = Queue(connection=r)




def anomalyDetection(files):
    start_time = time.time()
    ie = IECore()
    net = ie.read_network(model="./anomalie.xml",weights="anomalie.bin")
    device = "MYRIAD"
    print ("Model took " + str(time.time() - start_time) +"to load")
    start_time = time.time()
    imageNumbers = files.split(',')
    input_blob = next(iter(net.input_info))
    out_blob = next(iter(net.outputs))
    net.batch_size = 10
    n, c, h, w = net.input_info[input_blob].input_data.shape
    images = np.ndarray(shape=(n, c, h, w))

    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
    transform = transforms.Compose([
        transforms.ToTensor(),
        normalize,
    ])

    for i in range(n):      
        #image = io.imread("./Images/Anomaly"+imageNumbers[i]+".png")
        image = io.imread("./Checked/"+imageNumbers[i])
        image = transform(Image.fromarray(image))
        images[i] = image.numpy()

    exec_net = ie.load_network(network=net, device_name=device)
    res = exec_net.infer(inputs={input_blob: images})
    res = res[out_blob]
    values = []
    for i, probs in enumerate(res):
        probs = np.squeeze(probs)
        id = np.argsort(probs)[-1:][::-1]
        values.append(f"Classid: {id}")
        print("Image {}\n".format("./Checked/"+imageNumbers[i]))
        print(f"Classid: {id}")
    print ("Image evaluation took " + str(time.time() - start_time))
    return values


@app.route("/task")
def add_task():

    if request.args.get("n"):

        job = q.enqueue(anomalyDetection, request.args.get("n"))
        #job = q.enqueue(bacground_task, request.args.get("n"))

        q_len = len(q)

        return f"Task {job.id} added to queue at {job.enqueued_at}. {q_len} tasks in the queue"

    return "No value for n"

if __name__ == "__name__":
    app.run()
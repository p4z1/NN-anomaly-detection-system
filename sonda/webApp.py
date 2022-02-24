from flask import Flask, render_template, request
import multiprocessing
import redis
import netRB
import taskGiver
import config
import sys

app = Flask(__name__)
logs = netRB.Logs()

try:
    r = redis.Redis(host=config.REDIS_IP, port=config.REDIS_PORT)
except:
    logs.logger.error("Connecting to redis failed.")
    sys.exit(1)
model = netRB.Classify(r,logs)
global id
id = 0

@app.route("/capture")
def newCapture():
    if request.args.get("csv"):
        p = multiprocessing.Process(target=taskGiver.csvPreprocessing, args=(request.args.get("csv"),logs,))
        p.start()
        return "CSV added to the queue."
    else:
        return "No CSV files specify"

@app.route("/debug")
def debug():
    global id
    lastID = id
    try:
        id = taskGiver.imgsPreprocessing(id,logs)
    except:
        logs.logger.error("Error in debug mode.")
        return "Error in debug mode."
    return f"{id-lastID} images was preprocessed."

@app.route("/addTask")
def addTask():

    if request.args.get("imgs"):
        imgs = request.args.get("imgs")
        try:
            model.startDetection(imgs)
        except:
            logs.logger.error(f"Prediction error. Images IDs: {imgs}")
            return "Prediction error."

        return "Prediction completed."

    return "No images for prediction was given."

@app.route("/")
def server():
    return render_template("index.html")

if __name__ == "__name__":
    app.run(port=config.API_PORT, debug = False)
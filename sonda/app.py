from flask import Flask, render_template, request

import multiprocessing
import utilities
import filePreprocessing
import config
import redis
import netRB
import sys

#Počiatočná inicializácia objektov
logs = utilities.Logs()

try:
    r = redis.Redis(host=config.REDIS_IP, port=config.REDIS_PORT)
except:
    logs.logger.error("Connecting to redis failed.")
    sys.exit(1)

app = Flask(__name__)
model = netRB.Classify(r,logs)
global id
id = 0

#Prijímanie žiadosti na spracovanie CSV súborov
#Spracovávané CSV súbory majú byť uložené v zložke ./csvFiles
@app.route("/capture")
def newCapture():
    #Príjem ID CSV súborov
    if request.args.get("csv"):
        p = multiprocessing.Process(target=filePreprocessing.csvPreprocessing, args=(request.args.get("csv"), logs,))
        p.start()
        return "CSV added to the queue."
    else:
        return "No CSV files specify"

#Prijímanie žiadosti na debugovanie systému spracovaním predvytvorenými obrázkami
#Overované obrázky majú byť uložené v zložke ./images
@app.route("/debug")
def debug():
    global id
    lastID = id
    try:
        id = filePreprocessing.imgsPreprocessing(id,logs)
    except:
        logs.logger.error("Error in debug mode.")
        return "Error in debug mode."
    return f"{id-lastID} images was preprocessed."

#Prijímanie žiadosti na vytvorenie predikcie
#Obrázky musia byť uložené v redise 
@app.route("/predictions")
def predictions():
    #Predikcia na obrázkov z csv súborov
    if request.args.get("csv"):
        imgs = request.args.get("csv")
        try:
            model.startDetection(imgs,"csv")
        except:
            logs.logger.error(f"Prediction error. CSV IDs: {imgs}")
            return "Prediction error."
        return "Prediction completed."
    #Predikcia na obrázkoch pre debugovanie
    if request.args.get("imgs"):
        imgs = request.args.get("imgs")
        try:
            model.startDetection(imgs,"image")
        except:
            logs.logger.error(f"Prediction error. Images IDs: {imgs}")
            return "Prediction error."
        return "Prediction completed."
    return "No images for prediction was given."


if __name__ == "__name__":
    app.run(port=config.API_PORT, debug = False)
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from PIL import Image

import imageTransformation
import utilities
import netServer
import filePreprocessing
import requests
import config
import io
import os

imgTransf = imageTransformation.Transformation()
logs = utilities.Logs()
model = netServer.Classify(logs)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(config.ROOT_DIRECTORY,config.UPLOAD_FOLDER)

#Kontrola nahraného súboru na nepovolenú príponu
def allowedFile(filename, allowedExtension):
    extension = filename.rsplit('.', 1)[1].lower()
    if '.' in filename and extension in allowedExtension:
        return True
    else:
        logs.logger.warning(f"Forbidden extension {extension} was provided from {request.remote_addr}!")
        return False

#Žiadosť o predikciu na uložených csv súboroch
#Súbory sa musia nachádzať v súbore ./uploads
@app.route('/predictions')
def predict():
    if request.args.get("csv"):
        images = filePreprocessing.csvPreprocessing(request.args.get("csv"), logs, imgTransf)
        for image in images:
            model.getPrediction(image)
        return "Predictions completed."
    logs.logger.warning(f"CSV prediction was called from {request.remote_addr} without CSV files!")
    return "None csv for prediction!"

#Žiadosť o predikciu na nahraných obrázkoch
#Obrázky nie sú ukladané.
@app.route('/imgPredicts', methods = ['GET', 'POST'])
def debugs():
    if request.method == "POST" and request.files.getlist("images"):
        uploadedImages = request.files.getlist("images")
        predictions = []
        for uploadedImage in uploadedImages:
            filename = secure_filename(uploadedImage.filename)
            if allowedFile(filename,config.ALLOWED_IMAGE_EXTENSIONS):   #Kontrola prípony súboru
                #Načítanie a úprava obrázka
                byteImage = uploadedImage.read()           
                image = Image.open(io.BytesIO(byteImage))
                image = imgTransf.normalize(image)
                #Predikcia na spracovanom obrázku
                predictions.append((uploadedImage.filename,model.getPrediction((image,uploadedImage.filename))))
        if len(predictions) != 0:
            response = ""
            for pred in predictions:
                response += f"File: {pred[0]}\tPrecition: {pred[1][0]}\tClassification: {pred[1][1]}\n"
            return response
    logs.logger.warning(f"Image prediction was called from {request.remote_addr} without files!")
    return "No images was given for prediction!"

#Žiadosť o predikciu na nahraných csv súboroch
#CSV súbory sú ukladané v súbore ./uploads
@app.route('/csvPredict', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST' and request.files.getlist('files'):
        uploadedFiles = request.files.getlist('files')
        filenames = []
        for uploadedFile in uploadedFiles:
            #Kontrola a uloženie prijatého súboru
            filename = secure_filename(uploadedFile.filename)
            if allowedFile(filename,config.ALLOWED_EXTENSIONS):             
                filenames.append(filename)
                uploadedFile.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
        if len(filenames) != 0:
            #Zaslanie žiadosti o začatie predikcie.
            csvFiles = ','.join(filenames)
            apiRequest = requests.get(f"http://{config.API_LOCAL_IP}:{config.API_PORT}/predictions?csv={csvFiles}")
            return apiRequest.text
    logs.logger.warning(f"CSV prediction was called from {request.remote_addr} without CSV files!")
    return "No csv was provided!"

if __name__ == '__main__':
    app.run(config.API_HOST, port=config.API_PORT, debug = True) #, ssl_context=('./certs/cert.pem', './certs/key.pem')
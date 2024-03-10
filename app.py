from datetime import date
import os.path
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pydantic import BaseModel
import geopy.distance
import csv
from fuzzywuzzy import process, fuzz
import pandas as pd



current_dir = os.getcwd()
DATA_FOLDER = os.path.join(current_dir, 'static/data')
DATA_FILE = os.path.join(DATA_FOLDER, 'data.json')
CSV_FILE = os.path.join(DATA_FOLDER, 'Mental_Health_independent_list.csv')
CITIES_DATA = os.path.join(DATA_FOLDER, 'israel_cities.csv')
CITIES_COOR = os.path.join(DATA_FOLDER, 'city_coordinates.json')

CITIES = pd.read_json(CITIES_COOR, encoding="utf-8").columns


print(CITIES)

app = Flask(__name__,template_folder='templates', static_folder="static")
CORS(app)

@app.route("/",  methods=['GET','POST']) 
def root():
    return render_template('index.html', cities = list(CITIES))

@app.route("/DATA_FILE",  methods=['GET']) 
def data_file():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


@app.route("/CITIES_COOR",  methods=['GET']) 
def city_coor_file():
    with open(CITIES_COOR, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

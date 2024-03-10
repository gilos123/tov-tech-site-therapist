from datetime import date
import os.path
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pydantic import BaseModel
import geopy.distance
import csv
from fuzzywuzzy import process, fuzz



# DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
current_dir = os.getcwd()
DATA_FOLDER = os.path.join(current_dir, 'data')
DATA_FILE = os.path.join(DATA_FOLDER, 'data.json')
CSV_FILE = os.path.join(DATA_FOLDER, 'Mental_Health_independent_list.csv')
CITIES_DATA = os.path.join(DATA_FOLDER, 'israel_cities.csv')
CITIES_COOR = os.path.join(DATA_FOLDER, 'city_coordinates.json')

def load_data():
    if not os.path.exists(DATA_FILE):
        print('doesnt exist')
        save_data([])

    with open(DATA_FILE, "r", encoding='utf-8') as file:
        return json.load(file)

def save_data(therapists):
    with open(DATA_FILE, "w", encoding='utf-8') as file:
        json.dump(therapists, file, ensure_ascii=False, indent=4)

class Therapist(BaseModel):
    id: int = None
    region: str
    name: str
    city: str
    profession: str
    notes: str
    languages: str
    phone: str
    address: str
    gender: str



@app.route("/therapists", methods=["GET"])
def read_data():
    return jsonify(load_data())

@app.route("/therapists", methods=["POST"])
def create_data():
    therapist_data = request.json
    therapist = Therapist(**therapist_data)
    therapists = load_data()
    therapist_id = max((therapist["id"] for therapist in therapists), default=0) + 1
    therapist.id = therapist_id
    therapists.append(therapist.model_dump())
    save_data(therapists)
    return jsonify(therapist)

@app.route("/therapists/<int:therapist_id>", methods=["GET"])
def read_single_data(therapist_id):
    therapists = load_data()
    therapist = next((therapist for therapist in therapists if therapist["id"] == therapist_id), None)
    if therapist is None:
        return jsonify({"error": "Therapist not found"}), 404
    return jsonify(therapist)

@app.route("/therapists/<int:therapist_id>", methods=["PUT"])
def update_therapist(therapist_id):
    therapists = load_data()
    updated_therapist_data = request.json
    updated_therapist_data["id"] = therapist_id
    therapist_index = next((index for index, r in enumerate(therapists) if r["id"] == therapist_id), None)

    if therapist_index is None:
        return jsonify({"error": "Therapist not found"}), 404

    therapists[therapist_index] = updated_therapist_data
    save_data(therapists)
    return jsonify(updated_therapist_data)

@app.route("/therapists/<int:therapist_id>", methods=["DELETE"])
def delete_data(therapist_id):
    therapists = load_data()
    therapist_index = next((index for index, r in enumerate(therapists) if r["id"] == therapist_id), None)

    if therapist_index is None:
        return jsonify({"error": "Therapist not found"}), 404

    del therapists[therapist_index]
    save_data(therapists)
    return jsonify({"status": "success", "message": "Therapist deleted successfully"})

@app.route("/therapists/search_therapists/<string:city_name>/<int:max_distance>", methods=["GET"])
def search_data(city_name, max_distance):
    therapists = load_data()
    matching_therapists = []

    if city_name == "_":
        return jsonify(therapists)

    matching_therapists, city_name = get_close_cities(city_name, DATA_FILE, CITIES_COOR, max_distance)

    if not matching_therapists:
        return jsonify({"error": "No matching therapists found"}), 404
    else:
        response = jsonify(matching_therapists, city_name)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'  # Set response header for UTF-8 encoding
        return response, 200

def get_city_coordinates(cities_data, city_name):
    with open(cities_data, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    city_names = list(data.keys())
    
    match = process.extractOne(city_name, city_names)
    if match and match[1] >= 70:
        matched_city_name = match[0]
        x_coordinate, y_coordinate = data[matched_city_name]
  
        return x_coordinate, y_coordinate, matched_city_name
    else:
        raise NameError(status_code=404, detail="No matching city found")

def get_close_cities(searched_city, json_data_file, cities_coor_file, max_distance):
    x_coordinate, y_coordinate, city_name = get_city_coordinates(cities_coor_file, searched_city) 
    data = open_file(cities_coor_file)

    close_city_dict = {}

    for city, city_coor in data.items():
        dist = geopy.distance.geodesic((city_coor[0],city_coor[1]),(x_coordinate, y_coordinate))
        distance_in_meters = dist.meters
        distance_in_km = dist.meters / 1000
 
        if distance_in_km <= max_distance:

            if not city in close_city_dict:
                close_city_dict[city] = distance_in_km

    therepist_list = open_file(json_data_file)   
    filtered_therapists = get_filtered_cities(close_city_dict, therepist_list)
    return filtered_therapists, city_name

def open_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def get_filtered_cities(cities_dict, therapists_list):
    filtered_therapist_list = []
    for detail in therapists_list:
        # Fuzzy matching for the city name
        best_match = max(cities_dict.keys(), key=lambda city: fuzz.token_sort_ratio(city, detail.get('city')))
        similarity_score = fuzz.token_sort_ratio(best_match, detail.get('city'))

        if similarity_score > 80:  # Adjust the threshold as needed
            detail['city'] = best_match
            detail['distance'] = round(cities_dict[best_match], 2) 
            filtered_therapist_list.append(detail)

    sorted_filtered_therapist_list = sorted(filtered_therapist_list, key=lambda x: x["distance"])
    return sorted_filtered_therapist_list


def csv_to_json(csv_file, json_file):
    data = []
    titles_array = ['gender','address','phone', 'languages', 'notes', 'profession', 'city', 'name', 'region'][::-1]
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=',')

        for _ in range(5):
            next(reader)

        for row in reader:
            therapist = {}
            for i, item in enumerate(row):
                therapist[titles_array[i]] = item
            data.append(therapist)
  
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def convert_data_to_dict(data_file, filename):
        
    city_distance_dict = {}

    with open(data_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=',')
        next(reader)
        for row in reader:
            city = row[5]
            x_coordinate = float(row[0]) / 100000
            y_coordinate = float(row[1]) / 100000

            city_distance_dict[city] = (x_coordinate, y_coordinate)
    
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(city_distance_dict, file, ensure_ascii=False, indent=4)

    return city_distance_dict
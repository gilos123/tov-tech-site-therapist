"""
API for Therapist Keeper Application.

This module provides endpoints for CRUD operations on therapists.
It uses a JSON file for storage, and FastAPI for the web server.
"""
from datetime import date
import os.path
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import geopy.distance
import csv
from fuzzywuzzy import process, fuzz
import math

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


current_dir = os.getcwd()
DATA_FOLDER = os.path.join(current_dir, 'data')
DATA_FILE = os.path.join(DATA_FOLDER, 'data.json')
CSV_FILE = os.path.join(DATA_FOLDER, 'Mental_Health_independent_list.csv')
CITIES_DATA = os.path.join(DATA_FOLDER, 'israel_cities.csv')
CITIES_COOR = os.path.join(DATA_FOLDER, 'city_coordinates.json')

def load_data():
    """
    Load therapists from JSON file into memory.

    If the JSON file does not exist, it initializes an empty list.

    Returns:
        list: A list of therapists.
    """
    if not os.path.exists(DATA_FILE):
        print('doesnt exist')
        save_data([])

    with open(DATA_FILE, "r", encoding='utf-8') as file:
        return json.load(file)


def save_data(therapists):
    """
    Save the current state of therapists into JSON file.

    Args:
        therapists (list): List of therapists to save.
    """
    with open(DATA_FILE, "w", encoding='utf-8') as file:
        json.dump(therapists, file, ensure_ascii=False, indent=4)


class Therapist(BaseModel):
    """Therapist Model.

    Attributes:
        id (int): Therapist identifier.
        name (str): Name of the therapist.
        ingredients (list[str]): List of ingredients for the therapist.
        url (str): Url of therapist image.
        date (date): Date of scheduling the date of making the therapist.

    """
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


@app.get("/therapists")
def read_data():
    """Retrieve all therapists."""
    return load_data()


@app.post("/therapists")
def create_data(therapist: Therapist):
    """Create a new therapist.

    Args:
        therapist (Therapist): The therapist details to create.

    Returns:
        dict: The created therapist.
    """
    therapists = load_data()
    therapist_id = max((therapist["id"] for therapist in therapists), default=0) + 1
    therapist.id = therapist_id
    therapists.append(therapist.model_dump())
    save_data(therapists)
    return therapist


@app.get("/therapists/{therapist_id}")
def read_data(therapist_id: int):
    """Retrieve a single therapist by its ID.

    Args:
        therapist_id (int): ID of the therapist to retrieve.

    Raises:
        HTTPException: If the therapist with the specified ID is not found.

    Returns:
        dict: The requested therapist.
    """
    therapists = load_data()
    therapist = next((therapist for therapist in therapists if therapist["id"] == therapist_id), None)
    if therapist is None:
        raise HTTPException(status_code=404, detail="Therapist not found")
    return therapist


@app.put("/therapists/{therapist_id}")
def update_therapist(therapist_id: int, updated_therapist: Therapist):
    """Update a therapist by its ID.

    Args:
        therapist_id (int): ID of the therapist to update.
        updated_therapist (Therapist): New details for the therapist.

    Raises:
        HTTPException: If the therapist with the specified ID is not found.

    Returns:
        dict: The updated therapist.
    """
    therapists = load_data()
    therapist_index = next((index for index, r in enumerate(therapists) if r["id"] == therapist_id), None)

    if therapist_index is None:
        raise HTTPException(status_code=404, detail="Therapist not found")

    updated_therapist.id = therapist_id
    therapists[therapist_index] = updated_therapist.model_dump()
    save_data(therapists)
    return updated_therapist


@app.delete("/therapists/{therapist_id}")
def delete_data(therapist_id: int):
    """Delete a therapist by its ID.

    Args:
        therapist_id (int): ID of the therapist to delete.

    Raises:
        HTTPException: If the therapist with the specified ID is not found.

    Returns:
        dict: A status message indicating successful deletion.
    """
    therapists = load_data()
    therapist_index = next((index for index, r in enumerate(therapists) if r["id"] == therapist_id), None)

    if therapist_index is None:
        raise HTTPException(status_code=404, detail="Therapist not found")

    del therapists[therapist_index]
    save_data(therapists)
    return {"status": "success", "message": "Therapist deleted successfully"}


@app.get("/therapists/search_therapists/{city_name}/{max_distance}")
def search_data(city_name: str, max_distance: int):
    """Retrieve multiple cities by their name.

    Args:
        city_name (str): name of the city to retrieve.
        max_distance (int): distance of other cities to retrieve.

    Raises:
        HTTPException: If the city with the specified name is not found.

    Returns:
         array: The requested cities. str: name of the city to retrieve
    """
    print("Searching", city_name, max_distance)
    therapists = load_data()
    matching_therapists = []

    if city_name == "_":
        return therapists

    matching_therapists, city_name = get_close_cities(city_name, DATA_FILE, CITIES_COOR, max_distance)

    if not matching_therapists:
        print("Could not find")
        raise HTTPException(status_code=404, detail="No matching therapists found")

    return matching_therapists, city_name


def get_city_coordinates(cities_data, city_name):
    with open(cities_data, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    city_names = list(data.keys())
    
    # Use fuzzy matching to find the closest match to the input city name
    match = process.extractOne(city_name, city_names)
    
    # If a match is found and its similarity score is above a threshold (e.g., 70),
    #  retrieve its coordinates
    if match and match[1] >= 70:
        matched_city_name = match[0]
        x_coordinate, y_coordinate = data[matched_city_name]
        return x_coordinate, y_coordinate, matched_city_name
    else:
        raise HTTPException(status_code=404, detail="No matching city found")

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
        print(best_match, similarity_score)
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
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

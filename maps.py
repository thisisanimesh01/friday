import requests
import os
from dotenv import load_dotenv
from math import radians, cos, sin, sqrt, atan2

import re as regex

load_dotenv()

API_KEY = os.getenv("MAP")
BASE_URL = "https://api.opencagedata.com/geocode/v1/json"

def clean_place(place):
    place = regex.sub(r'[^\w\s]', '', place)
    return place.strip()

def get_coordinates(place):
    place = clean_place(place)

    params = {
        "q": place + ", India",
        "key": API_KEY,
        "limit": 1
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if data.get("results"):
        result = data["results"][0]

        lat = result["geometry"]["lat"]
        lng = result["geometry"]["lng"]
        formatted = result["formatted"]

        return lat, lng, formatted

    print("DEBUG FAILED:", data)
    return None, None, None


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return round(R * c, 2)


def get_distance(query):
    try:
        query = query.lower().strip()
        query = query.replace("distance", "").replace("from", "").replace("between", "").strip()

        if " to " not in query:
            return "Tell me like: distance delhi to chandigarh"

        parts = query.split(" to ")

        if len(parts) != 2:
            return "Tell me like: distance delhi to chandigarh"

        place1 = clean_place(parts[0]).replace("between", "").strip()
        place2 = clean_place(parts[1]).strip()

        if not place1 or not place2:
            return "Please provide both locations."

        place1 = place1.title()
        place2 = place2.title()

        lat1, lon1, name1 = get_coordinates(place1)
        lat2, lon2, name2 = get_coordinates(place2)

        if None in (lat1, lon1):
            lat1, lon1, name1 = get_coordinates(place1 + ", India")

        if None in (lat2, lon2):
            lat2, lon2, name2 = get_coordinates(place2 + ", India")

        if None in (lat1, lon1, lat2, lon2):
            return f"Couldn't find location: {place1} or {place2}"

        distance = calculate_distance(lat1, lon1, lat2, lon2)

        return f"Distance between {name1} and {name2} is {distance} km."

    except Exception as e:
        print("ERROR:", e)
        return "Something went wrong while calculating distance."


def get_location():
    try:
        res = requests.get("https://ipinfo.io/json")
        data = res.json()

        city = data.get("city")
        region = data.get("region")
        country = data.get("country")

        return f"You are in {city}, {region}, {country}"

    except:
        return "Couldn't detect your location."
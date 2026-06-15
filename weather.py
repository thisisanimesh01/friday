import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

def extract_city(query):
    query = query.lower()

    stopwords = [
        "weather", "in", "of", "tell", "me", "what", "is",
        "the", "current", "temperature", "today" , "like", "how", "about"
    ]

    words = query.split()
    city_words = [w for w in words if w not in stopwords]

    city = " ".join(city_words).strip()

    if not city:
        return "Delhi"

    return city.title()


def get_weather(query="weather"):
    try:
        city = extract_city(query)

        params = {
            "q": f"{city},IN",
            "appid": API_KEY,
            "units": "metric"
        }

        response = requests.get(BASE_URL, params=params, timeout=5)
        data = response.json()

        # Debug if needed
        if data.get("cod") != 200:
            print("DEBUG:", data)
            return f"Couldn't find weather for {city}."

        name = data["name"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        weather_desc = data["weather"][0]["description"].title()
        wind_speed = data["wind"]["speed"]

        return (
            f"Weather in {name}:\n"
            f"Temperature: {temp}°C\n"
            f"Feels like: {feels_like}°C\n"
            f"Condition: {weather_desc}\n"
            f"Humidity: {humidity}%\n"
            f"Wind Speed: {wind_speed} m/s"
        )

    except Exception as e:
        print("ERROR:", str(e))
        return "Something went wrong while fetching weather."
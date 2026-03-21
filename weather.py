import requests
from datetime import datetime
from config import WEATHER_API_KEY, WEATHER_CITY


def get_weather():
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": WEATHER_CITY,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "ru"
    }

    r = requests.get(url, params=params).json()

    sunrise = datetime.fromtimestamp(r["sys"]["sunrise"]).strftime("%H:%M")
    sunset = datetime.fromtimestamp(r["sys"]["sunset"]).strftime("%H:%M")

    return {
        "temp": round(r["main"]["temp"]),
        "text": r["weather"][0]["description"],
        "icon": r["weather"][0]["icon"],
        "sunrise": sunrise,
        "sunset": sunset
    }


def get_rates():
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    r = requests.get(url).json()

    return {
        "usd": round(r["Valute"]["USD"]["Value"], 2),
        "eur": round(r["Valute"]["EUR"]["Value"], 2)
    }

import requests
import json
import os
import time
from datetime import datetime
from config import WEATHER_API_KEY, LAT, LON
from weather_icons import get_weather_icon

CACHE_FILE = "weather_cache.json"
CACHE_TTL = 3600  # 1 час


def beaufort_scale(speed):
    scale = [
        (0.2, 0), (1.5, 1), (3.3, 2), (5.4, 3), (7.9, 4),
        (10.7, 5), (13.8, 6), (17.1, 7), (20.7, 8),
        (24.4, 9), (28.4, 10), (32.6, 11), (999, 12)
    ]
    for limit, b in scale:
        if speed <= limit:
            return b


def is_cache_valid():
    if not os.path.exists(CACHE_FILE):
        return False
    mtime = os.path.getmtime(CACHE_FILE)
    return (time.time() - mtime) < CACHE_TTL


def load_cache():
    with open(CACHE_FILE, "r") as f:
        return json.load(f)


def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)


def fetch_weather():
    # --- текущая погода ---
    url_current = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": LAT,
        "lon": LON,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    current = requests.get(url_current, params=params).json()
    weather = current["weather"][0]
    wind_speed = current.get("wind", {}).get("speed", 0)

    sunrise = datetime.fromtimestamp(
        current["sys"]["sunrise"]).strftime("%H:%M")
    sunset = datetime.fromtimestamp(current["sys"]["sunset"]).strftime("%H:%M")
    now_is_day = weather["icon"].endswith("d")
    icon_code = get_weather_icon(weather["id"], now_is_day)

    # --- прогноз на 5 дней через 3 часа ---
    url_forecast = "https://api.openweathermap.org/data/2.5/forecast"
    forecast = requests.get(url_forecast, params=params).json()
    hourly = forecast["list"]  # каждые 3 часа

    # --- ближайший противоположный период ---
    target = None
    for h in hourly[:18]:  # первые ~54 часа
        target_icon_code = h["weather"][0]["icon"]
        target_is_day = target_icon_code.endswith("d")

        # ищем противоположное время суток
        if now_is_day and not target_is_day:
            target = h
            break
        elif not now_is_day and target_is_day:
            target = h
            break

    if target is None:
        target = hourly[3]

    target_dt = datetime.fromtimestamp(target["dt"])
    target_weather = target["weather"][0]
    target_icon_code = target_weather["icon"]
    target_is_day = target_icon_code.endswith("d")
    target_icon = get_weather_icon(target_weather["id"], target_is_day)

    # --- приближённая фаза луны (0-1) ---
    moon_phase = (datetime.now().day % 30) / 29.0  # грубое приближение

    data = {
        "temp": round(current["main"]["temp"]),
        "feels_like": round(current["main"]["feels_like"]),
        "text": weather["description"],

        "weather_id": weather["id"],
        "icon": icon_code,
        "is_day": now_is_day,

        "pressure": current["main"]["pressure"],
        "humidity": current["main"]["humidity"],

        "sunrise": sunrise,
        "sunset": sunset,

        "wind_speed": wind_speed,
        "wind_deg": current.get("wind", {}).get("deg", 0),
        "wind_beaufort": beaufort_scale(wind_speed),

        "next": {
            "time": target_dt.strftime("%H:%M"),
            "temp": round(target["main"]["temp"]),
            "weather_id": target_weather["id"],
            "icon": target_icon,
            "is_day": target_is_day,
            "text": target_weather["description"]
        },

        "moon_phase": moon_phase,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return data


def get_weather():
    if is_cache_valid():
        return load_cache()
    data = fetch_weather()
    save_cache(data)
    return data


def get_rates():
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    r = requests.get(url).json()
    return {
        "usd": round(r["Valute"]["USD"]["Value"], 2),
        "eur": round(r["Valute"]["EUR"]["Value"], 2)
    }

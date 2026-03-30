def get_weather_icon(weather_id: int, is_day: bool) -> str:
    d = is_day

    # --- ГРОЗА ---
    if 200 <= weather_id <= 232:
        if weather_id in (200, 230):
            return "wi-day-storm-showers.svg" if d else "wi-night-alt-storm-showers.svg"
        elif weather_id in (201, 231):
            return "wi-day-thunderstorm.svg" if d else "wi-night-alt-thunderstorm.svg"
        elif weather_id in (202, 232):
            return "wi-day-snow-thunderstorm.svg" if d else "wi-night-alt-snow-thunderstorm.svg"
        else:
            return "wi-thunderstorm.svg"

    # --- МОРОСЬ ---
    if 300 <= weather_id <= 321:
        if weather_id in (300, 301):
            return "wi-day-sprinkle.svg" if d else "wi-night-alt-sprinkle.svg"
        elif weather_id in (302, 312, 314):
            return "wi-showers.svg"
        elif weather_id in (310, 311, 313):
            return "wi-rain-mix.svg"
        elif weather_id == 321:
            return "wi-day-showers.svg" if d else "wi-night-alt-showers.svg"

    # --- ДОЖДЬ ---
    if 500 <= weather_id <= 531:
        if weather_id == 500:
            return "wi-day-rain.svg" if d else "wi-night-alt-rain.svg"
        elif weather_id == 501:
            return "wi-rain.svg"
        elif weather_id in (502, 503, 504):
            return "wi-rain-wind.svg"
        elif weather_id == 511:
            return "wi-sleet.svg"
        elif weather_id in (520, 521):
            return "wi-showers.svg"
        elif weather_id in (522, 531):
            return "wi-storm-showers.svg"

    # --- СНЕГ / ЛЁД ---
    if 600 <= weather_id <= 622:
        if weather_id in (600, 601):
            return "wi-day-snow.svg" if d else "wi-night-alt-snow.svg"
        elif weather_id == 602:
            return "wi-snow-wind.svg"
        elif weather_id in (611, 612, 613):
            return "wi-sleet.svg"
        elif weather_id in (615, 616):
            return "wi-rain-mix.svg"
        elif weather_id in (620, 621):
            return "wi-day-snow.svg" if d else "wi-night-alt-snow.svg"
        elif weather_id == 622:
            return "wi-snow-wind.svg"

    # --- АТМОСФЕРА ---
    if 700 <= weather_id <= 781:
        if weather_id == 701:
            return "wi-fog.svg"
        elif weather_id == 711:
            return "wi-smoke.svg"
        elif weather_id == 721:
            return "wi-day-haze.svg" if d else "wi-night-fog.svg"
        elif weather_id in (731, 751, 761):
            return "wi-dust.svg"
        elif weather_id == 741:
            return "wi-fog.svg"
        elif weather_id == 762:
            return "wi-volcano.svg"
        elif weather_id == 771:
            return "wi-strong-wind.svg"
        elif weather_id == 781:
            return "wi-tornado.svg"

    # --- ЯСНО ---
    if weather_id == 800:
        return "wi-day-sunny.svg" if d else "wi-night-clear.svg"

    # --- ОБЛАКА ---
    if weather_id == 801:
        return "wi-day-sunny-overcast.svg" if d else "wi-night-alt-partly-cloudy.svg"
    if weather_id == 802:
        return "wi-day-cloudy.svg" if d else "wi-night-alt-cloudy.svg"
    if weather_id == 803:
        return "wi-cloudy.svg"
    if weather_id == 804:
        return "wi-cloudy.svg"

    # --- FALLBACK ---
    return "wi-na.svg"


def get_moon_icon(moon_phase: float) -> str:
    # нормализуем
    p = moon_phase % 1.0

    # --- ключевые точки ---
    if p < 0.03 or p > 0.97:
        return "wi-moon-alt-new.svg"
    if 0.22 <= p <= 0.28:
        return "wi-moon-alt-first-quarter.svg"
    if 0.47 <= p <= 0.53:
        return "wi-moon-alt-full.svg"
    if 0.72 <= p <= 0.78:
        return "wi-moon-alt-third-quarter.svg"

    # --- фазы ---
    if p < 0.25:
        # waxing crescent (6 стадий)
        idx = int((p / 0.25) * 6) + 1
        return f"wi-moon-alt-waxing-crescent-{idx}.svg"
    elif p < 0.5:
        # waxing gibbous
        idx = int(((p - 0.25) / 0.25) * 6) + 1
        return f"wi-moon-alt-waxing-gibbous-{idx}.svg"
    elif p < 0.75:
        # waning gibbous
        idx = int(((p - 0.5) / 0.25) * 6) + 1
        return f"wi-moon-alt-waning-gibbous-{idx}.svg"
    else:
        # waning crescent
        idx = int(((p - 0.75) / 0.25) * 6) + 1
        return f"wi-moon-alt-waning-crescent-{idx}.svg"


def get_wind_beaufort_icon(b: int) -> str:
    b = max(0, min(12, int(b)))
    return f"wi-wind-beaufort-{b}.svg"


def get_wind_direction_style(deg: float) -> str:
    return f"transform: rotate({deg}deg);"

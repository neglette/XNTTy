import time
import os
import sys
from datetime import datetime, timedelta

from feeds import get_new_news
from printer import print_image, close_printer
from beeper import init_beep, print_beep, alert_beep
from renderer import *
from weather import get_weather, get_rates
from config import CHECK_INTERVAL, INTERVAL_DIGEST_MINUTES, INTERVAL_WEATHER_MINUTES, PAUSE_PRE_PRINT, PAUSE_POST_PRINT

# Проверка флага --test
TEST_MODE = "--test" in sys.argv
if TEST_MODE:
    TEST_FOLDER = "test"
    os.makedirs(TEST_FOLDER, exist_ok=True)


def beep(func):
    """Вызывает бипер только если не тестовый режим"""
    if not TEST_MODE:
        func()


def output_image(img, name=None):
    """Печать на принтер или сохранение в тестовом режиме"""
    if TEST_MODE and name:
        path = os.path.join(TEST_FOLDER, name)
        img.save(path)
        print(f"[TEST MODE] Saved image to {path}")
    else:
        print_image(img)


def print_start_message():
    print("TeleType started")
    img = render_status_block("started")
    time.sleep(PAUSE_PRE_PRINT)
    beep(init_beep)
    output_image(img, "status_started.png" if TEST_MODE else None)
    time.sleep(PAUSE_POST_PRINT)


def print_shutdown_message():
    img = render_status_block("stopped", False)
    time.sleep(PAUSE_PRE_PRINT)
    beep(init_beep)
    output_image(img, "status_stopped.png" if TEST_MODE else None)
    time.sleep(PAUSE_POST_PRINT)


def get_slot(dt, interval_minutes):
    """Получаем таймслот для заданного интервала"""
    total_minutes = dt.hour * 60 + dt.minute
    slot_minutes = (total_minutes // interval_minutes) * interval_minutes
    hour, minute = divmod(slot_minutes, 60)
    return dt.replace(hour=hour, minute=minute, second=0, microsecond=0)


def next_time(now, interval_minutes):
    """Следующее время события через заданный интервал"""
    total_minutes = now.hour * 60 + now.minute
    next_slot_minutes = (
        (total_minutes // interval_minutes) + 1) * interval_minutes
    days_to_add = next_slot_minutes // (24 * 60)
    next_slot_minutes = next_slot_minutes % (24 * 60)
    hour, minute = divmod(next_slot_minutes, 60)
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_to_add)


def main():
    print_start_message()

    digest_slots = {}
    last_digest_slot = None
    last_weather_time = None

    now = datetime.now()
    next_digest = next_time(now, INTERVAL_DIGEST_MINUTES)
    next_weather = next_time(now, INTERVAL_WEATHER_MINUTES)

    # --- ПЕЧАТЬ ПОГОДЫ ПРИ СТАРТЕ ---
    weather = get_weather()
    rates = get_rates()
    img_weather = render_weather_block(weather, rates)
    time.sleep(PAUSE_PRE_PRINT)
    beep(print_beep)
    output_image(img_weather, "weather.png" if TEST_MODE else None)
    time.sleep(PAUSE_POST_PRINT)
    last_weather_time = get_slot(datetime.now(), INTERVAL_WEATHER_MINUTES)

    # --- СТАРТОВЫЙ ДАЙДЖЕСТ (новости за последний интервал) ---
    startup_news = get_new_news(first_run=True)
    if startup_news:
        startup_news.sort(key=lambda x: x["timestamp"])
        img_digest = render_digest(startup_news)
        time.sleep(PAUSE_PRE_PRINT)
        beep(print_beep)
        output_image(img_digest, "digest.png" if TEST_MODE else None)
        time.sleep(PAUSE_POST_PRINT)
        last_digest_slot = get_slot(datetime.now(), INTERVAL_DIGEST_MINUTES)

    try:
        while True:
            now = datetime.now()
            current_digest_slot = get_slot(now, INTERVAL_DIGEST_MINUTES)

            # --- СБОР НОВОСТЕЙ ---
            news = get_new_news(first_run=False)
            for item in news:
                if item.get("important", False):
                    img_item = render_important_news(item)
                    time.sleep(PAUSE_PRE_PRINT)
                    beep(alert_beep)
                    output_image(img_item)
                    time.sleep(PAUSE_POST_PRINT)
                else:
                    ts = item.get("timestamp", datetime.now())
                    slot = get_slot(ts, INTERVAL_DIGEST_MINUTES)
                    digest_slots.setdefault(slot, []).append(item)

            # --- ПЕЧАТЬ ПОГОДЫ ---
            if now >= next_weather:
                weather = get_weather()
                rates = get_rates()
                img_weather = render_weather_block(weather, rates)
                time.sleep(PAUSE_PRE_PRINT)
                beep(print_beep)
                output_image(img_weather)
                time.sleep(PAUSE_POST_PRINT)
                last_weather_time = get_slot(now, INTERVAL_WEATHER_MINUTES)
                next_weather = next_time(now, INTERVAL_WEATHER_MINUTES)

            # --- ПЕЧАТЬ ДАЙДЖЕСТА ---
            if current_digest_slot != last_digest_slot:
                slot_to_print = current_digest_slot - \
                    timedelta(minutes=INTERVAL_DIGEST_MINUTES)
                items = digest_slots.get(slot_to_print, [])
                if items:
                    items.sort(key=lambda x: x["timestamp"])
                    img_digest = render_digest(items)
                    time.sleep(PAUSE_PRE_PRINT)
                    beep(print_beep)
                    output_image(img_digest)
                    time.sleep(PAUSE_POST_PRINT)
                    del digest_slots[slot_to_print]
                last_digest_slot = current_digest_slot

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("Stopped.")
        print_shutdown_message()
    finally:
        close_printer()


if __name__ == "__main__":
    main()

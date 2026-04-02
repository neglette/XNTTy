import time
import os
import sys
from datetime import datetime, timedelta

from feeds import get_new_news
from printer import print_image, close_printer
from beeper import init_beep, print_beep, alert_beep
from renderer import *
from weather import get_weather, get_rates
from config import CHECK_INTERVAL

PAUSE_PRE_PRINT = 0.9
PAUSE_POST_PRINT = 0.9

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


def get_digest_slot(dt):
    """Получаем таймслот для дайджеста (каждые 30 минут)"""
    return dt.replace(
        minute=(dt.minute // 30) * 30,
        second=0,
        microsecond=0
    )


def next_digest_time(now):
    """Следующий таймслот через 30 минут"""
    minute = (now.minute // 30 + 1) * 30
    if minute >= 60:
        return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        return now.replace(minute=minute, second=0, microsecond=0)


def next_weather_time(now):
    """Следующее обновление погоды каждые 4 часа"""
    hour = (now.hour // 4 + 1) * 4
    if hour >= 24:
        return now.replace(hour=0, minute=5, second=0, microsecond=0) + timedelta(days=1)
    else:
        return now.replace(hour=hour, minute=5, second=0, microsecond=0)


def main():
    print_start_message()

    digest_slots = {}
    last_digest_slot = None
    last_weather_slot = None

    now = datetime.now()

    next_digest = next_digest_time(now)
    next_weather = next_weather_time(now)

    # --- ПЕЧАТЬ ПОГОДЫ ПРИ СТАРТЕ ---
    weather = get_weather()
    rates = get_rates()
    img_weather = render_weather_block(weather, rates)
    time.sleep(PAUSE_PRE_PRINT)
    beep(print_beep)
    output_image(img_weather, "weather.png" if TEST_MODE else None)
    time.sleep(PAUSE_POST_PRINT)

    # --- СТАРТОВЫЙ ДАЙДЖЕСТ (новости за 4 часа) ---
    startup_news = get_new_news(first_run=True)
    if startup_news:
        startup_news.sort(key=lambda x: x["timestamp"])
        img_digest = render_digest(startup_news)
        time.sleep(PAUSE_PRE_PRINT)
        beep(print_beep)
        output_image(img_digest, "digest.png" if TEST_MODE else None)
        time.sleep(PAUSE_POST_PRINT)
        last_digest_slot = get_digest_slot(datetime.now())

    try:
        while True:
            now = datetime.now()
            current_slot = get_digest_slot(now)

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
                    slot = get_digest_slot(ts)
                    if slot not in digest_slots:
                        digest_slots[slot] = []
                    digest_slots[slot].append(item)

            # --- ПЕЧАТЬ ПОГОДЫ ---
            if now >= next_weather:
                weather = get_weather()
                rates = get_rates()
                img_weather = render_weather_block(weather, rates)
                time.sleep(PAUSE_PRE_PRINT)
                beep(print_beep)
                output_image(img_weather)
                time.sleep(PAUSE_POST_PRINT)
                next_weather = next_weather_time(now)

            # --- ПЕЧАТЬ ДАЙДЖЕСТА ---
            if current_slot != last_digest_slot:
                slot_to_print = current_slot - timedelta(minutes=30)
                items = digest_slots.get(slot_to_print, [])
                if items:
                    items.sort(key=lambda x: x["timestamp"])
                    img_digest = render_digest(items)
                    time.sleep(PAUSE_PRE_PRINT)
                    beep(print_beep)
                    output_image(img_digest)
                    time.sleep(PAUSE_POST_PRINT)
                    del digest_slots[slot_to_print]
                last_digest_slot = current_slot

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("Stopped.")
        print_shutdown_message()
    finally:
        close_printer()


if __name__ == "__main__":
    main()

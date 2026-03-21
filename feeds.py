import csv
from urllib.parse import urlparse, urlunparse
from datetime import datetime, timedelta, timezone

import feedparser
from database import load_db, save_db
from scoring import classify_news  # классификатор


def clean_url(url):
    parsed = urlparse(url)
    clean = parsed._replace(query="")
    return urlunparse(clean)


def load_feeds():
    feeds = []
    with open("feeds.csv") as f:
        reader = csv.reader(f)
        for row in reader:
            feeds.append({"url": row[0], "name": row[1]})
    return feeds


def parse_entry_time(entry):
    """Безопасный парсинг времени RSS"""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)  # fallback


def clean_text(text):
    """Очищаем текст от пробелов и HTML, приводим к строке"""
    if text is None:
        return ""
    text = str(text).replace("\xa0", " ").replace("&nbsp;", " ").strip()
    return text


def parse_item(entry, source_name):
    ts = parse_entry_time(entry)
    now = datetime.now(timezone.utc)
    if ts > now:
        ts = now

    title = clean_text(entry.get("title", ""))
    summary = clean_text(entry.get("summary", ""))

    item = {
        "title": title,
        "summary": summary,
        "link": clean_url(entry.get("link", "")),
        "source": source_name,
        "timestamp": ts.astimezone().replace(tzinfo=None),
        "important": False
    }

    # классификация новости
    classification = classify_news(item)
    if classification == "ignore":
        return None  # блокируем новости
    elif classification == "important":
        item["important"] = True

    return item


def get_new_news(first_run=False):
    feeds = load_feeds()
    printed = load_db()
    fresh = []

    # main.py
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    cutoff_4h = now - timedelta(hours=4)
    cutoff_fresh = now - timedelta(minutes=20)

    # сделать их offset-naive перед передачей
    cutoff_4h = cutoff_4h.replace(tzinfo=None)
    cutoff_fresh = cutoff_fresh.replace(tzinfo=None)

    for feed in feeds:
        parsed = feedparser.parse(feed["url"])
        for entry in parsed.entries:
            url = clean_url(entry.get("link", ""))

            if not first_run and url in printed:
                continue

            item = parse_item(entry, feed["name"])
            if item is None:
                continue  # заблокированные новости

            # фильтр по времени
            if first_run and item["timestamp"] < cutoff_4h:
                continue
            elif not first_run and item["timestamp"] < cutoff_fresh:
                continue

            fresh.append(item)

            if not first_run:
                printed.add(url)

    save_db(printed)
    return fresh

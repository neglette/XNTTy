import json
from config import DB_FILE


def load_db():
    try:
        with open(DB_FILE) as f:
            return set(json.load(f))
    except:
        return set()


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(list(data), f)
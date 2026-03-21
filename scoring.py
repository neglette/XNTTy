import pymorphy2
import re

# --------------------
# Морфология
# --------------------
morph = pymorphy2.MorphAnalyzer()

# --------------------
# Ключевые слова
# --------------------
IMPORTANT_KEYWORDS = [
    "убийство", "смерть", "скончаться", "умереть", "погибнуть",
    "не_стало", "закон", "поправка", "запрет", "теракт", "хлопок", "взрыв"
]

BLOCK_KEYWORDS = [
    "спорт", "олимпиада", "кубок", "взять_золото", "взять_серебро", "взять_бронзу",
    "футбол", "баскетбол", "теннис", "хоккей", "волейбол", "чемпионат",
    "матч", "игрок", "тулуп", "покер", "аутсайдер"
]

# --------------------
# Функции
# --------------------


def text_to_lemmas(text):
    """Возвращает список лемм текста, очищая от пунктуации"""
    text = text.lower()
    text = re.sub(r"[^а-яa-z0-9_]+", " ", text)
    words = text.split()
    lemmas = [morph.parse(w)[0].normal_form for w in words]
    return lemmas


def is_blocked(text):
    """Проверка на запрещённые слова/темы"""
    lemmas = text_to_lemmas(text)
    for kw in BLOCK_KEYWORDS:
        if kw in lemmas:
            return True
    return False


def is_important(text):
    """Проверка на важные слова"""
    lemmas = text_to_lemmas(text)
    for kw in IMPORTANT_KEYWORDS:
        if kw in lemmas:
            return True
    return False


def classify_news(item):
    """
    Классификация новости.
    Возвращает:
        'ignore'  — блокируем (спорт и запрещённые темы)
        'important' — важная
        'normal' — обычная
    """
    text = item.get("title", "") + " " + item.get("summary", "")
    if is_blocked(text):
        return "ignore"
    elif is_important(text):
        return "important"
    else:
        return "normal"

# XNTTy – Xprinter News Teletype v 1.93

## О проекте

XNTTy — программа для твоего термопринтера Xprinter, превращающая его в мини-телетайп.  

Функции:  
- Обработка RSS-фидов и автоматическое разделение новостей по морфологии:  
  - **Срочные** — печатаются немедленно с QR-кодом и саммари;  
  - **Обычные** — печатаются каждые 30 минут;  
  - **Мусорные** — игнорируются.  
- Печать стартовых дайджестов, обычных дайджестов и срочных новостей;
- Обработка погоды через OpenWeatherMap и печать: при старте и каждые 4 часа;
- Иконки погоды, атмосферных и астрономических событий, адаптированные под монохромный принтер;
- Процессинг и печать курса валют;
- Разнообразные сигналы встроенного бипера принтера, создающие атмосферу старого телетайпа;
- Программа совместима с большинством моделей термопринтеров Xprinter, но протестирована только на XP-365B.  

---

## Установка

1. Создай виртуальное окружение и активируй его:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

2. Установи зависимости:

```bash
pip install -r requirements.txt
```
3. Скопируй .env.example в .env и отредактируй его:
4. Найди данные принтера через lsusb:

```bash
lsusb
```
Определи VENDOR_ID и PRODUCT_ID для своего принтера и внеси их в .env.

## Использование

После настройки запусти программу:

```bash
python3.10 main.py
```
Xprinter начнёт печатать новости, погоду и курсы валют с эффектом старого телетайпа.

## Лицензия и ключи

OpenWeather API ключ в репозитории найден в аддонах lain, он не мой. Используй аккуратно и не превышай лимиты.

Иконки погоды - [Weather Icons by Eric Flowers](https://erikflowers.github.io/weather-icons/).

## About

XNTTy turns your Xprinter thermal printer into a mini teleprinter.

Features:

- Processes RSS feeds and splits news automatically by urgency:
    - **Urgent** — printed immediately with QR code and summary;
    - **Normal** — printed every 30 minutes;
    - **Trash** — ignored.
- Prints startup digests, normal digests, and urgent news.
- Processes weather via OpenWeatherMap and prints at startup and every 4 hours.
- Weather icons adapted for a monochrome printer.
- Processes and prints currency rates.
- Various built-in printer beeps create a retro teletype effect;
- The program is compatible with most Xprinter thermal printer models, but has been tested only on the XP-365B.

## Installation

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```
3. Copy .env.example to .env and edit it:
4. Find your printer data via lsusb:

```bash
lsusb
```
Determine VENDOR_ID and PRODUCT_ID for your printer and put them in .env.

## Usage

Run the program after configuration:

```bash
python3.10 main.py
```
Your Xprinter will start printing news, weather, and currency rates with a retro teletype feel.

## License and Keys

The OpenWeather API key in the repo was found in lain addons, **it is not mine**. Use carefully to avoid exceeding limits.
Weather icons - [Weather Icons by Eric Flowers](https://erikflowers.github.io/weather-icons/).

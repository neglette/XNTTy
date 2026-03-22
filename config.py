import os
from dotenv import load_dotenv

load_dotenv()

# --- FROM .env ---
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_CITY = os.getenv("WEATHER_CITY")
VENDOR_ID = int(os.getenv("VENDOR_ID"), 16)  # hex в int
PRODUCT_ID = int(os.getenv("PRODUCT_ID"), 16)  # hex в int

# ---  PRINT ---
PAPER_WIDTH_MM = 80

META_SPACING = 10
DASH_STEP = 14

PADDING_X = 8
PADDING_Y = 8

LINE_SPACING = 2
BLOCK_SPACING = 6
SECTION_SPACING = 4

QR_MARGIN = 10

DOUBLE_LINE_WIDTH = 2

# ---  CHECK INTERVAL ---
CHECK_INTERVAL = 60


# ---  PATHS ---
DB_FILE = "printed_news.json"
ICON_PATH = "weather_icons"

# ---  FONTS ---
FONT_PATH_MONO = "fonts/DejaVuSansMono.ttf"
FONT_PATH_UI = "fonts/DejaVuSans.ttf"

FONT_SIZE_MONO = 20
FONT_SIZE_UI_TITLE = 24
FONT_SIZE_UI_TEXT = 22

BOLD_OFFSET = 1

# ---- BEEPER | параметры бипера
INIT_BEEP_TIMES = 1
INIT_BEEP_DURATION = 2

PRINT_BEEP_TIMES = 5
PRINT_BEEP_DURATION = 1

ALERT_BEEP_TIMES = 3
ALERT_BEEP_DURATION = 4

# ---- COMPUTABLE | вычисляемые параметры
if PAPER_WIDTH_MM == 80:
    PRINT_WIDTH = 576
    QR_SIZE = 140
elif PAPER_WIDTH_MM == 56:
    PRINT_WIDTH = 384
    QR_SIZE = 100
else:
    raise ValueError("Unsupported paper width")

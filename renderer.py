from weasyprint import HTML
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import qrcode
from weather_icons import *
from playwright.sync_api import sync_playwright
import tempfile
import os
from pdf2image import convert_from_bytes
from pathlib import Path
import base64
from cairosvg import svg2png
from io import BytesIO

from config import (
    # шрифты
    FONT_PATH_MONO,
    FONT_PATH_UI,
    FONT_SIZE_MONO,
    FONT_SIZE_UI_TITLE,
    FONT_SIZE_UI_TEXT,

    # геометрия / отступы
    PRINT_WIDTH,
    PADDING_X,
    PADDING_Y,
    LINE_SPACING,
    BLOCK_SPACING,
    SECTION_SPACING,

    # прочее
    QR_SIZE,
    QR_MARGIN,
    DASH_STEP,
    DOUBLE_LINE_WIDTH,
    BOLD_OFFSET,
    ICON_PATH
)

# --------------------
# FONTS
# --------------------
FONT_MONO = ImageFont.truetype(FONT_PATH_MONO, FONT_SIZE_MONO)
FONT_UI_TITLE = ImageFont.truetype(FONT_PATH_UI, FONT_SIZE_UI_TITLE)
FONT_UI_TEXT = ImageFont.truetype(FONT_PATH_UI, FONT_SIZE_UI_TEXT)

ICON_PATH = Path(ICON_PATH)


def svg_to_data_uri(path, height_px):
    png_bytes = svg2png(url=str(path), output_height=height_px)
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


def clean_text(text: str) -> str:
    return (
        text.replace("&nbsp;", " ")
            .replace("\xa0", " ")
            .replace("&laquo;", "«")
            .replace("&raquo;", "»")
            .strip()
    )

# --------------------
# QR
# --------------------


def make_qr(link):
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=1
    )
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((QR_SIZE, QR_SIZE), Image.NEAREST)
    return img.convert("L")

# --------------------
# THERMAL FILTER
# --------------------


def thermal_threshold(img):
    return img.point(lambda x: 0 if x < 180 else 255, "1")

# --------------------
# PIXEL WRAP
# --------------------


def wrap_text_by_pixel_width(text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        bbox = font.getbbox(test_line)
        w = bbox[2] - bbox[0]

        if w <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines

# --------------------
# STATUS BLOCK
# --------------------


def render_status_block(status_text):
    from version import VERSION, APP_NAME

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"{APP_NAME} v{VERSION}",
        status_text,
        now
    ]

    # --- измерение ---
    dummy_img = Image.new("1", (PRINT_WIDTH, 1000), 255)
    draw = ImageDraw.Draw(dummy_img)

    y = PADDING_Y
    max_w = 0

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=FONT_MONO)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        max_w = max(max_w, w)
        y += h + LINE_SPACING

    total_h = y + PADDING_Y

    # --- финальное изображение ---
    img = Image.new("1", (PRINT_WIDTH, total_h), 255)
    draw = ImageDraw.Draw(img)

    # рамка
    draw.rectangle(
        [(0, 0), (PRINT_WIDTH - 1, total_h - 1)],
        outline=0,
        width=2
    )

    # --- текст ---
    y = PADDING_Y

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=FONT_MONO)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        x = (PRINT_WIDTH - w) // 2
        draw.text((x, y), line, font=FONT_MONO, fill=0)

        y += h + LINE_SPACING

    return img

# --------------------
# IMPORTANT NEWS
# --------------------


def render_important_news(item):
    img = Image.new("L", (PRINT_WIDTH, 2000), 255)
    draw = ImageDraw.Draw(img)

    y = PADDING_Y

    # --- META ---
    source = item["source"]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    draw.text((PADDING_X, y), source, font=FONT_MONO, fill=0)
    time_w = draw.textlength(timestamp, font=FONT_MONO)
    draw.text((PRINT_WIDTH - time_w - PADDING_X, y),
              timestamp, font=FONT_MONO, fill=0)

    y += FONT_SIZE_MONO + LINE_SPACING

    draw.line((0, y, PRINT_WIDTH, y), fill=0, width=1)
    y += SECTION_SPACING

    # --- TITLE ---
    title = clean_text(item["title"])

    title_lines = wrap_text_by_pixel_width(
        title,
        FONT_UI_TITLE,
        PRINT_WIDTH - 2 * QR_MARGIN
    )

    for line in title_lines:
        draw.text((PADDING_X, y), line, font=FONT_UI_TITLE, fill=0)
        draw.text((PADDING_X + BOLD_OFFSET, y),
                  line, font=FONT_UI_TITLE, fill=0)
        y += FONT_SIZE_UI_TITLE + LINE_SPACING

    y += BLOCK_SPACING

    # --- DASH LINE ---
    dash_y = y
    x = 0
    while x < PRINT_WIDTH:
        draw.line((x, dash_y, x + 6, dash_y), fill=0, width=1)
        x += DASH_STEP

    y += SECTION_SPACING

    # --- QR ---
    qr = make_qr(item["link"])
    qr_x = PRINT_WIDTH - QR_SIZE - PADDING_X
    img.paste(qr, (qr_x, y))

    # --- SUMMARY ---
    text_width = qr_x - QR_MARGIN - PADDING_X
    max_lines = int(QR_SIZE / (FONT_SIZE_UI_TEXT + LINE_SPACING))

    summary = clean_text(item.get("summary", ""))

    summary_lines = wrap_text_by_pixel_width(
        summary,
        FONT_UI_TEXT,
        text_width
    )[:max_lines]

    ty = y
    for line in summary_lines:
        draw.text((PADDING_X, ty), line, font=FONT_UI_TEXT, fill=0)
        ty += FONT_SIZE_UI_TEXT + LINE_SPACING

    # --- DOUBLE LINE ---
    line_y = y + QR_SIZE + LINE_SPACING

    draw.line((0, line_y, PRINT_WIDTH, line_y),
              fill=0, width=DOUBLE_LINE_WIDTH)
    draw.line((0, line_y + 3, PRINT_WIDTH, line_y + 3),
              fill=0, width=DOUBLE_LINE_WIDTH)

    y += QR_SIZE + BLOCK_SPACING

    img = img.crop((0, 0, PRINT_WIDTH, y))
    img = thermal_threshold(img)

    return img

# --------------------
# NORMAL NEWS
# --------------------


def render_normal_news(item):
    img = Image.new("L", (PRINT_WIDTH, 1000), 255)
    draw = ImageDraw.Draw(img)

    y = PADDING_Y

    # --- META (source + time) ---
    source = clean_text(item["source"])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    draw.text((PADDING_X, y), source, font=FONT_MONO, fill=0)

    time_w = draw.textlength(timestamp, font=FONT_MONO)
    draw.text((PRINT_WIDTH - time_w - PADDING_X, y),
              timestamp, font=FONT_MONO, fill=0)

    y += FONT_SIZE_MONO + LINE_SPACING

    draw.line((0, y, PRINT_WIDTH, y), fill=0, width=1)
    y += SECTION_SPACING

    # --- TITLE ---
    title = clean_text(item["title"])

    title_lines = wrap_text_by_pixel_width(
        title,
        FONT_UI_TITLE,
        PRINT_WIDTH - 2 * PADDING_X
    )

    for line in title_lines:
        draw.text((PADDING_X, y), line, font=FONT_UI_TITLE, fill=0)
        y += FONT_SIZE_UI_TITLE + LINE_SPACING

    y += BLOCK_SPACING

    img = img.crop((0, 0, PRINT_WIDTH, y))
    img = thermal_threshold(img)

    return img


def render_digest(items):
    img = Image.new("L", (PRINT_WIDTH, 3000), 255)
    draw = ImageDraw.Draw(img)

    y = PADDING_Y

    for item in items:
        title = item.get("title", "")
        ts = item.get("timestamp")

        if ts:
            time_str = ts.strftime("%H:%M")
        else:
            time_str = "--:--"

        # ---------- BULLET + TIME ----------
        header = f"{time_str} || "

        # измеряем ширину таймштампа
        bbox = draw.textbbox((0, 0), header, font=FONT_MONO)
        header_width = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        # рисуем таймштамп
        draw.text((0, y), header, font=FONT_MONO, fill=0)

        # ---------- TITLE ----------
        # Доступная ширина для первой строки с учётом таймштампа
        first_line_max_width = PRINT_WIDTH - header_width - PADDING_X
        rest_max_width = PRINT_WIDTH - 2 * PADDING_X

        words = title.split()
        lines = []
        current_line = ""
        first_line = True

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            w = FONT_UI_TITLE.getbbox(
                test_line)[2] - FONT_UI_TITLE.getbbox(test_line)[0]

            max_width = first_line_max_width if first_line else rest_max_width

            if w <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
                first_line = False

        if current_line:
            lines.append(current_line)

        # рисуем строки
        first_line = True
        for line in lines:
            x = header_width if first_line else 0
            draw.text((x, y), line, font=FONT_UI_TITLE, fill=0)
            y += FONT_SIZE_UI_TITLE + LINE_SPACING
            first_line = False

        # небольшой отступ между новостями
        y += LINE_SPACING * 2

    img = img.crop((0, 0, PRINT_WIDTH, y))
    img = thermal_threshold(img)

    return img


# --- предполагается, что weather и rates уже получены ---

def render_weather_block(weather, rates):
    from pathlib import Path
    from datetime import datetime
    from weasyprint import HTML
    from pdf2image import convert_from_bytes
    from PIL import Image

    ICON_DIR = Path(__file__).parent / "weather_icons"

    def uri(name):
        return (ICON_DIR / name).resolve().as_uri()

    main_icon = svg_to_data_uri(
        ICON_DIR / get_weather_icon(weather['weather_id'], weather['is_day']),
        300
    )

    now = datetime.now().strftime("%H:%M")
    if now < weather["sunset"]:
        sun_icon = "wi-sunset.svg"
        sun_time = weather["sunset"]
    else:
        sun_icon = "wi-sunrise.svg"
        sun_time = weather["sunrise"]

    html = f"""
    <html>
    <head>
    <meta charset="utf-8">

    <style>

    @page {{
    margin:0;
    }}

    body {{
    margin:0;
    padding:0;
    font-family:sans-serif;
    }}

    body::before {{
    content: "";
    display: block;
    border-top: 1px solid black;
    width: 100%;
    }}

    table {{
    border-collapse:collapse;
    width:100%;
    }}

    .main {{
    border:3px solid black;
    }}

    td {{
    padding:6px;
    vertical-align:middle;
    }}

    .center {{ text-align:center; }}
    .left {{ text-align:left; }}

    .vline {{ border-left:2px solid black; }}

    .hline > td {{
    border-top:2px solid black;
    }}

    .cross-top > td {{
    border-top:2px solid black;
    }}

    .cross-left {{
    border-left:2px solid black;
    }}

    .big {{
    font-size:120px;
    font-weight:bold;
    }}

    .mid {{ font-size:48px; }}
    .small {{ font-size:36px; }}

    .currency {{
    font-size:60px;
    font-weight:bold;
    }}

    .icon-main {{ height:260px; }}
    .icon {{ height:90px; }}
    .icon-small {{ height:70px; }}

    </style>
    </head>

    <body>

    <table class="main">

    <tr>

    <!-- ЛЕВЫЙ ВЕРХ -->
    <td width="66%">

    <table width="100%">
    <tr>

    <td class="center" width="45%">
    <img src="{main_icon}" class="icon-main">
    </td>

    <td class="center" width="55%">
    <div class="big">{weather['temp']}°</div>
    <div class="small">{weather['feels_like']}°</div>
    </td>

    </tr>
    </table>

    </td>


    <!-- ПРАВЫЙ ВЕРХ -->
    <td width="34%" class="vline">

    <table width="100%">

    <tr>

    <td class="center">
    <img src="{uri('wi-wind-deg.svg')}" class="icon"
    style="transform:rotate({weather['wind_deg']}deg);">
    </td>

    <td class="center cross-left">
    <img src="{uri('wi-barometer.svg')}" class="icon-small">
    <span class="mid">{weather['pressure']}</span>
    </td>

    </tr>

    <tr class="cross-top">

    <td class="center">
    <img src="{uri(f'wi-wind-beaufort-{weather["wind_beaufort"]}.svg')}" class="icon">
    </td>

    <td class="center cross-left">
    <img src="{uri('wi-humidity.svg')}" class="icon-small">
    <span class="mid">{weather['humidity']}%</span>
    </td>

    </tr>

    </table>

    </td>

    </tr>


    <tr class="hline">

    <!-- ЛЕВЫЙ НИЗ -->
    <td>

    <table width="100%">

    <tr>

    <td width="40%" class="center">
    <img src="{uri(get_moon_icon(weather['moon_phase']))}" class="icon">
    </td>

    <td width="60%" rowspan="2" class="center vline">
    <img src="{uri(get_weather_icon(weather['next']['weather_id'], weather['is_day']))}" class="icon">
    <div class="mid">{weather['next']['temp']}°</div>
    </td>

    </tr>

    <tr>

    <td>

    <table width="100%">
    <tr>

    <td width="40%" class="center">
    <img src="{uri(sun_icon)}" class="icon-small">
    </td>

    <td width="60%" class="left mid">
    {sun_time}
    </td>

    </tr>
    </table>

    </td>

    </tr>

    </table>

    </td>


    <!-- ПРАВЫЙ НИЗ -->
    <td class="vline">

    <table width="100%">

    <tr>
    <td class="center currency">
    $ {rates['usd']:.2f}
    </td>
    </tr>

    <tr>
    <td class="center currency">
    € {rates['eur']:.2f}
    </td>
    </tr>

    </table>

    </td>

    </tr>

    </table>

    </body>
    </html>
    """

    pdf = HTML(string=html).write_pdf()
    img = convert_from_bytes(pdf)[0]

    from PIL import ImageOps

    gray = img.convert("L")
    bbox = ImageOps.invert(gray).getbbox()
    if bbox:
        img = img.crop(bbox)

    printer_width = PRINT_WIDTH
    ratio = printer_width / img.width
    img = img.resize((printer_width, int(img.height * ratio)), Image.LANCZOS)

    return img

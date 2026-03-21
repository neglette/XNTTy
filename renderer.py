from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import qrcode
import os

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


def render_weather_block(weather, rates):
    import os

    # увеличим шрифт температуры
    temp_font_size = FONT_SIZE_UI_TITLE * 2
    FONT_TEMP = ImageFont.truetype(FONT_PATH_UI, temp_font_size)

    # увеличим шрифт для курсов
    FONT_RATE = ImageFont.truetype(FONT_PATH_UI, FONT_SIZE_UI_TITLE)

    img_height = 240
    img = Image.new("L", (PRINT_WIDTH, img_height), 255)
    draw = ImageDraw.Draw(img)

    y = PADDING_Y

    # деление блока на три части
    third_w = PRINT_WIDTH // 3
    left_x = 0
    mid_x = third_w
    right_x = third_w * 2

    # --------------------
    # ЛЕВАЯ ЧАСТЬ: иконка
    # --------------------
    icon_size = third_w - 2 * PADDING_X
    icon = None
    icon_path = os.path.join(ICON_PATH, f"{weather['icon']}.png")
    if os.path.exists(icon_path):
        try:
            icon = Image.open(icon_path).convert("L")
            icon = icon.resize((icon_size, icon_size), Image.LANCZOS)
        except Exception as e:
            print("Ошибка при открытии иконки:", e)
            icon = None
    # иконка вставляется как есть, без конверсии в 1-bit
    icon_h = icon_size if icon else 0

    # --------------------
    # СРЕДНЯЯ ЧАСТЬ: температура и время
    # --------------------
    temp_text = f"{weather['temp']}°C"

    # выбираем ближайшее событие
    now_hm = datetime.now().strftime("%H:%M")
    if now_hm < weather["sunset"]:
        arrow = "↘"
        time_text = f"{arrow} {weather['sunset']}"
    else:
        arrow = "↗"
        time_text = f"{arrow} {weather['sunrise']}"

    temp_bbox = draw.textbbox((0, 0), temp_text, font=FONT_TEMP)
    temp_w = temp_bbox[2] - temp_bbox[0]
    temp_h = temp_bbox[3] - temp_bbox[1]

    time_bbox = draw.textbbox((0, 0), time_text, font=FONT_UI_TEXT)
    time_w = time_bbox[2] - time_bbox[0]
    time_h = time_bbox[3] - time_bbox[1]

    mid_h = temp_h + LINE_SPACING + time_h + 4  # небольшой отступ перед временем

    # --------------------
    # ПРАВАЯ ЧАСТЬ: курсы
    # --------------------
    usd_text = f"${rates['usd']:.2f}"
    eur_text = f"€{rates['eur']:.2f}"

    usd_bbox = draw.textbbox((0, 0), usd_text, font=FONT_RATE)
    usd_w = usd_bbox[2] - usd_bbox[0]
    usd_h = usd_bbox[3] - usd_bbox[1]

    eur_bbox = draw.textbbox((0, 0), eur_text, font=FONT_RATE)
    eur_w = eur_bbox[2] - eur_bbox[0]
    eur_h = eur_bbox[3] - eur_bbox[1]

    right_h = usd_h + LINE_SPACING + eur_h

    # --------------------
    # ОБЩАЯ ВЫСОТА
    # --------------------
    content_h = max(icon_h, mid_h, right_h)
    total_h = y + content_h + PADDING_Y

    # --------------------
    # РАМКА ВСЕГО БЛОКА
    # --------------------
    draw.rectangle(
        [(0, 0), (PRINT_WIDTH - 1, total_h - 1)],
        outline=0,
        width=2
    )

    # --------------------
    # ВЕРТИКАЛЬНОЕ ЦЕНТРИРОВАНИЕ
    # --------------------
    content_top = y

    # --- иконка ---
    if icon:
        icon_y = content_top + (content_h - icon_h) // 2
        img.paste(icon, (left_x + PADDING_X, icon_y))

    # --- температура ---
    temp_x = mid_x + (third_w - temp_w) // 2
    temp_y = content_top + 0  # прижимаем к верху средней части
    draw.text((temp_x, temp_y), temp_text, font=FONT_TEMP, fill=0)

    # --- время восхода/заката ---
    time_x = mid_x + (third_w - time_w) // 2
    time_y = content_top + content_h - time_h - 2  # небольшой отступ от низа
    draw.text((time_x, time_y), time_text, font=FONT_UI_TEXT, fill=0)

    # --- USD ---
    usd_x = right_x + (third_w - usd_w) // 2
    usd_y = content_top + 0  # прижать к верху правой части
    draw.text((usd_x, usd_y), usd_text, font=FONT_RATE, fill=0)
    draw.text((usd_x + BOLD_OFFSET, usd_y), usd_text, font=FONT_RATE, fill=0)

    # --- EUR ---
    eur_x = right_x + (third_w - eur_w) // 2
    eur_y = content_top + content_h - eur_h - 2  # прижать к низу с отступом
    draw.text((eur_x, eur_y), eur_text, font=FONT_RATE, fill=0)
    draw.text((eur_x + BOLD_OFFSET, eur_y), eur_text, font=FONT_RATE, fill=0)

    # --------------------
    # ВЕРТИКАЛЬНЫЕ РАЗДЕЛИТЕЛИ
    # --------------------
    draw.line((third_w, y, third_w, total_h), fill=0, width=1)
    draw.line((third_w * 2, y, third_w * 2, total_h), fill=0, width=1)

    img = img.crop((0, 0, PRINT_WIDTH, total_h))
    return img

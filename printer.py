import sys
import contextlib
from escpos.printer import Usb
from config import PAPER_WIDTH_MM, VENDOR_ID, PRODUCT_ID

printer = None


@contextlib.contextmanager
def suppress_stderr():
    """Контекстный менеджер для временного подавления stderr"""
    old_stderr = sys.stderr
    sys.stderr = open("/dev/null", "w")
    try:
        yield
    finally:
        sys.stderr.close()
        sys.stderr = old_stderr


def get_printer():
    global printer
    if printer is None:
        with suppress_stderr():
            printer = Usb(VENDOR_ID, PRODUCT_ID)
            printer.set(density=2, smooth=True)
            try:
                printer.profile.media_width_pixel = PAPER_WIDTH_MM * 203 // 25.4
            except AttributeError:
                pass
    return printer


def close_printer():
    global printer
    if printer:
        try:
            printer.close()
        except:
            pass
        printer = None


def print_image(img):
    p = get_printer()
    with suppress_stderr():
        p.image(img, impl="bitImageRaster", center=False)
    p.text("\n")
    p.cut()

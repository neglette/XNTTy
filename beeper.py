from config import *
from printer import get_printer


def _beep(times, duration):

    p = get_printer()

    cmd = b'\x1b\x42' + bytes([times]) + bytes([duration])

    p._raw(cmd)


def init_beep():
    _beep(INIT_BEEP_TIMES, INIT_BEEP_DURATION)


def print_beep():
    _beep(PRINT_BEEP_TIMES, PRINT_BEEP_DURATION)


def alert_beep():
    _beep(ALERT_BEEP_TIMES, ALERT_BEEP_DURATION)
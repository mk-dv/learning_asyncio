import time


def hrtime():
    """
    Походу 10e6 - разрешение таймера

    Returns time in microseconds
    """
    return int(time.time() * 10e6)
from loguru import logger
import sys


def get_logger(color='light-blue', format='{process.name}: {message}'):
    logger.remove()
    colored_fmt = '<{color}>{format}</{color}>'.format(color=color, format=format)
    logger.add(sys.stdout, format=colored_fmt)
    return logger

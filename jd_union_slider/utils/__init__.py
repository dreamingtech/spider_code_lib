# -*- coding: utf-8 -*-
import logging


def get_logger(log_name):

    logger = logging.getLogger(log_name)
    logger.setLevel(logging.INFO)
    s_handler = logging.StreamHandler()
    s_handler.setLevel(logging.INFO)
    s_handler_formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)-7s [%(name)s:%(lineno)3d]: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    s_handler.setFormatter(s_handler_formatter)
    logger.addHandler(s_handler)
    return logger

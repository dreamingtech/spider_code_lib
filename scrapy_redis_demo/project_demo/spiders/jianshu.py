# -*- coding: utf-8 -*-
import logging

import scrapy

logger = logging.getLogger(__name__)


class Jianshu(scrapy.Spider):
    name = 'jianshu'

    def parse(self, response, **kwargs):
        logger.info(
            f'response text length: {len(response.body.decode("utf-8"))}, '
            f'response url: {response.url}'
        )

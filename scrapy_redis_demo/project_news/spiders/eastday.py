# -*- coding: utf-8 -*-
import datetime
import hashlib
import logging

import scrapy

logger = logging.getLogger(__name__)


class Eastday(scrapy.Spider):
    name = 'eastday'

    def parse(self, response, **kwargs):
        logger.info(
            f'response text length: {len(response.body.decode("utf-8"))}, '
            f'response url: {response.url}'
        )

        yield dict(
            # 保存到 news 表中
            table='news',
            url=response.url,
            url_id=hashlib.md5(response.url.encode('utf-8')).hexdigest(),
            content=len(response.body.decode("utf-8")),
            crawl=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

# -*- coding: utf-8 -*-
import logging

import scrapy

logger = logging.getLogger(__name__)


class Sogou(scrapy.Spider):
    name = 'sogou'

    url = 'https://news.sogou.com/'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        # 'Connection': 'keep-alive',
        'Host': 'news.sogou.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36 SE 2.X MetaSr 1.0',
    }

    def start_requests(self):
        yield scrapy.Request(
            url=self.url,
            headers=self.headers,
            callback=self.parse,
            dont_filter=True,
            meta={
                "handle_httpstatus_all": True,
            }
        )

    def parse(self, response, **kwargs):
        logger.info(
            f'response text length: {len(response.body.decode("utf-8"))}, '
            f'response url: {response.url}'
        )

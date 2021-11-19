# -*- coding: utf-8 -*-
import logging

import scrapy

logger = logging.getLogger(__name__)


class Hao123(scrapy.Spider):
    name = 'hao123'

    url = 'http://www.hao123.com/'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        # 'Connection': 'keep-alive',
        # 'Cookie': 'BAIDUID=E87D0F50E6784831976B07E179BFBF01:FG=1; nonUnion=1; BID=A138CDD1860431E3354EE25B8A2E61DF:FG=1; Hm_lvt_48c57cebc84275afcff127cd20c37e4b=1637312095; Hm_lpvt_48c57cebc84275afcff127cd20c37e4b=1637312104; __bsi=10100366070461156419_00_37_N_R_4_0303_c02f_Y; hz=0',
        'Host': 'www.hao123.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36 SE 2.X MetaSr 1.0',
    }

    def start_requests(self):
        yield scrapy.Request(
            url=self.url,
            headers=self.headers,
            callback=self.parse,
            dont_filter=True,
            meta={
                # "handle_httpstatus_all": True,
            }
        )

    def parse(self, response, **kwargs):
        logger.info(
            f'response text length: {len(response.body.decode("utf-8"))}, '
            f'response url: {response.url}'
        )

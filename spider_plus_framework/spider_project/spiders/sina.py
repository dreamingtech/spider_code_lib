import time

from spider_plus.core.spider import Spider
from spider_plus.http.request import Request
from spider_plus.item import Item

class SinaSpider(Spider):

    name = "sina"

    def start_requests(self):
        while True:
            url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=50&page=1&r=0.4002104982344896&_=1556415569224"
            yield Request(url, parse='parse', filter=False)
            time.sleep(10)     # 每10秒发起一次请求

    def parse(self, response):
        for news in response.json.get("result").get("data"):
            item = {
                "title": news.get("title", ""),
                "intro": news.get("intro", ""),
                "keywords": news.get("keywords", "")
            }
        yield Item(item)


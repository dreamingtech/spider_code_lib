# coding=utf-8
from spider_plus.core.spider import Spider
from spider_plus.http.request import Request
from spider_plus.item import Item
import urllib.parse


# 继承框架的爬虫基类
class BaiduSpider(Spider):
    name = "baidu"
    start_urls = ['http://www.douban.com', 'http://www.douban.com', 'http://www.baidu.com']  # 设置初始请求url

    def parse(self, response):
        yield Item(response.body[:30])
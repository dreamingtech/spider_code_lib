# coding=utf-8
from spider_plus.core.spider import Spider
from spider_plus.http.request import Request
from spider_plus.item import Item
import urllib.parse


class QiubaiSpider(Spider):
    name = "qiubai"
    start_urls = []

    # 因为 start_requests 方法的作用是 发送 start_urls 中url地址的请求, 所以如果不想把地址写入到 start_urls 中, 也可以重写 start_requests方法
    def start_requests(self):
        url_temp = "https://www.qiushibaike.com/8hr/page/{}/"
        # 糗事百科一共有13页的内容
        for i in range(1, 14):
            yield Request(url_temp.format(i))

    def parse(self, response):  # 提取页面的数据
        # 先分组, 再提取
        div_list = response.xpath('//div[@class="recmd-right"]')
        for div in div_list:
            item = {}
            item["name"] = div.xpath('.//span[@class="recmd-name"]/text()')[0]
            print(item["name"])
            item["title"] = "".join(div.xpath('./a[@class="recmd-content"]//text()'))
            item["url"] = urllib.parse.urljoin(response.url, div.xpath('./a/@href')[0])
            # yield Item(item)
            # 构造详情页的请求对象, 并指定解析函数和meta信息
            yield Request(item["url"], parse="parse_detail", meta={"item": item})
            # 测试代码
            break

    def parse_detail(self, response):
        item = response.meta["item"]
        item["pub_time"] = response.xpath('//span[@class="stats-time"]/text()')[0].strip() if len(response.xpath('//span[@class="stats-time"]/text()'))>0 else ""
        item["vote_num"] = response.xpath('//span[@class="stats-vote"]/i/text()')[0].strip()
        yield Item(item)

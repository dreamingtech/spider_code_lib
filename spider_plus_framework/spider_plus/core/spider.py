# coding=utf-8
# 爬虫

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.item import Item  # 导入Item对象


class Spider(object):
    '''完成对spider的封装'''
    start_urls = []  # 爬虫最开始请求的url地址, 默认初始请求地址

    def start_requests(self):
        '''
        构建start_url地址的初始请求对象并返回
        :return: request对象
        '''
        # 因为初始请求有多个, 所以要进行遍历
        for start_url in self.start_urls:
            # 因为有多个请求, 所以无法使用 return, 需要修改为生成器yield
            yield Request(start_url)

    def parse(self, response):
        '''
        默认处理start_url地址对应的响应
        :param response: response响应对象
        :return: item数据或者是request对象
        '''
        # 因为解析出来的数据可能有多个, 所以不能使用 return, 需要修改为生成器 yield
        yield Item(response.body)  # 返回item对象

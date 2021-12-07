# coding=utf-8
# 响应对象
from lxml import etree
import json
import re


class Response(object):
    """完成响应对象的封装"""

    def __init__(self, url, body, headers, status_code, meta={}):
        '''
        初始化response对象
        :param url: 响应的url地址
        :param body: 响应体
        :param headers: 响应头
        :param status_code: 状态码
        :param meta: 接收request对象中的meta值
        '''
        self.url = url
        self.body = body
        self.headers = headers
        self.status_code = status_code
        self.meta = meta

    def xpath(self, rule):
        '''
        给response对象添加xpath方法, 能够使用xpath提取数据
        :param rule: xpath匹配规则的字符串
        :return: 列表, 包含element对象或者是字符串的列表
        '''
        html = etree.HTML(self.body)
        return html.xpath(rule)

    @property
    def json(self):
        '''
        给response对象添加json属性, 能够直接把响应的json字符串转换为python数据类型
        :return: python数据类型
        '''
        return json.loads(self.body.decode())

    def re_findall(self, rule, data=None):
        '''
        给response对象添加re_findall方法, 能够使用正则从响应中提取数据
        :param rule: 正则表达式的字符串
        :param data:
        :return: 列表
        '''
        # 如果用户没有传递过来data, 就默认从响应体中进行内容的匹配
        if data is None:
            data = self.body
        return re.findall(rule, data)

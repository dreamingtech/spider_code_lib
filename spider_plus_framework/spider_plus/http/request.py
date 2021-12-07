# coding=utf-8
# 请求对象

class Request(object):
    """完成请求对象的封装"""

    def __init__(self, url, method="GET", headers=None, params=None, data=None, parse="parse", meta={}, filter=True):
        '''
        初始化request对象
        :param url: url地址
        :param method: 请求方法
        :param headers:请求头
        :param params: 请求的参数, 查询字符串
        :param data: 请求体, 表单数据
        :param parse: 请求对象对应的响应的解析函数
        :param meta: 字典, 在不同的解析函数之间传递数据
        :param filter: 是否对该请求进行去重, 默认会对请求进行去生
        '''
        self.url = url
        self.method = method
        self.headers = headers
        self.params = params
        self.data = data
        self.parse = parse
        self.meta = meta
        self.filter = filter
        self.retry_time = 0  # 重试次数

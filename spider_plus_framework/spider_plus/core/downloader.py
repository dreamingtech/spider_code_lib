# coding=utf-8
# 下载器

import requests
from spider_plus.http.response import Response
from spider_plus.utils.log import logger


class Downloader(object):
    '''完成对下载器对象的封装'''

    def get_response(self, request):
        '''
        实现接收请求对象, 发送请求, 获取响应
        :param request: 请求对象
        :return: response响应对象
        '''
        try:
            if request.method.upper() == 'GET':
                resp = requests.get(request.url, headers=request.headers, params=request.params, timeout=10)
            elif request.method.upper() == 'POST':
                resp = requests.post(request.url, headers=request.headers, params=request.params, data=request.data, timeout=10)
            else:
                # 如果方法不是get或者post，抛出一个异常
                raise Exception("不支持的请求方法: <{}>".format(request.method))
            # 请求发送成功时保存log信息
            logger.info("<{} {}>".format(resp.status_code, resp.request.url))
            # 2. 构建响应对象,并返回
            return Response(url=resp.url, body=resp.content, headers=resp.headers, status_code=resp.status_code)
        except Exception as e:
            logger.exception("请求出错: <{} {} {}>".format(request.url, request.method, e))

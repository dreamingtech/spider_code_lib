# -*- coding: utf-8 -*-
# 替换 scrapy-redis 的 jsoncompat 对请求进行序列化和反序列化
# 这样, 保存到 redis 中的请求就可以看到内容了
import collections
import json

from scrapy import Item


def convert_str(data):
    """
    https://github.com/mcchae/Flask-Login/blob/81330a13d1a7de475dd071fe459998a2e199173f/appauth_test.py
    Perform the following operations while traversing dict or list members, etc.
    - If it is unicode, it is converted to utf8 and returned.
    - If string, return string
    - If it is a dict, it is disassembled and reassembled by calling individual key:value pairs recursively.
    - If it is a list or tuple, it is disassembled and individual value elements are called recursively and reassembled.
    d = { u'spam': u'eggs', u'foo': True, u'bar': { u'baz': 97 } }
    print(d)
    {u'foo': True, u'bar': {u'baz': 97}, u'spam': u'eggs'}
    d2 = convert_str(d)
    print(d2)
    {'foo': True, 'bar': {'baz': 97}, 'spam': 'eggs'}
    :param data: Object for transformation
    """
    if isinstance(data, str):
        return data
    elif isinstance(data, bytes):
        return data.decode()
    elif isinstance(data, collections.Mapping):
        return dict(map(convert_str, data.items()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert_str, data))
    return data


def dumps(obj):
    """
    序列化 request 请求对象, 类似于 json.dumps
    :param obj:
    :return:
    """
    meta = obj['meta']
    for k in meta.keys():
        if issubclass(type(meta[k]), Item):
            meta[k] = dict(meta[k])
    if 'body' in obj.keys():
        obj['body'] = obj['body'].decode()
    if 'headers' in obj.keys():
        obj['headers'] = convert_str(obj['headers'])
    return json.dumps(obj)


def loads(s):
    """
    反序列化 request 请求对象, 类似于 json.loads
    :param s:
    :return:
    """
    if type(s) is bytes:
        s = s.decode()
    t = json.loads(s)
    if 'body' in t.keys():
        t['body'] = bytes(t['body'], encoding='utf-8')
    return t

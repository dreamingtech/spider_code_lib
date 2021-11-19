# -*- coding: utf-8 -*-
# redis 队列, 添加数据, 删除数据
# 参考 pyspider redis_queue.py
# https://github.com/binux/pyspider/blob/master/pyspider/message_queue/redis_queue.py
import json
import logging
import time
from collections import OrderedDict

import redis
import scrapy.settings

from scrapy_redis import connection


def singleton(cls, *args, **kwargs):
    """
    装饰器实现 python 单例模式
    https://www.cnblogs.com/PigeonNoir/articles/9392047.html
    https://www.cnblogs.com/jiangxinyang/p/8454418.html
    https://blog.csdn.net/qq_35462323/article/details/82912027
    """
    # 创建一个instances字典用来保存单例
    instances = {}

    # 创建一个内层函数来获得单例, 添加不定长参数, 以与 redis_conn 中 __init__ 中传递的参数相符合
    def _get_instance(*args, **kwargs):
        # 判断instances字典中是否含有单例, 如果没有就创建单例并保存到instances字典中, 然后返回该单例
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    # 返回内层函数 get_instance
    return _get_instance


def get_logger(log_name):
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.INFO)
    s_handler = logging.StreamHandler()
    s_handler.setLevel(logging.INFO)
    s_handler_formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)-7s [%(name)s:%(lineno)3d]: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    s_handler.setFormatter(s_handler_formatter)
    logger.addHandler(s_handler)
    return logger


logger = get_logger(__name__)


@singleton
class FifoRedisQueue(object):
    # 失效的 账号信息保存的 key
    redis_key_all = "cookie:all"
    # 正在进行登录的账号信息保存的 key
    redis_key_on = "cookie:on"

    def __init__(self, settings: scrapy.settings.Settings, timeout=5, expire=15):
        """
        因为 queue 是在爬虫中使用的, 所以这里无法获取到 settings_name
        传递进来的是 已经经过实例化的 self.settings
        :param settings: scrapy.settings.Settings
        :param timeout: 当 list 为空时, 阻塞的时间
        :param expire: zset 中值的过期时间
        """
        self.redis_cli = connection.from_settings(settings)
        self.redis_cli: redis.StrictRedis

        # 队列为空时等待的时间
        self.timeout = timeout
        # redis_key_on 中的 value 的过期时间, 单位 mins
        self.expire = expire
        # 启动时删除 REDIS_KEY_ON 中 self.expire 之前的值
        self.remove_expires()

    def all_to_on(self, item):
        """
        从 list key 中取出来 值时, 如果 key 名称为 settings.REDIS_KEY_MAPPING, 就把它保存到 redis_key_on 中
        因为只有 一个 zset key, 所以这里操作 redis_key_on 时, 统一不再传入 key
        """
        # 因为取出来的是 js 字符串, 而保存时必须是 dict 格式, 所以要先转换为 dict
        item = self.js_to_dict(item)
        self.put_to_zset(item=item)

    @staticmethod
    def sort_keys(item: dict):
        """
        把字典根据 key 进行排序, 并转换为 有序字典
        这样才能够判断某个 item 是否已经保存在 两个 key 中了
        只有 item 不在两个 key 中, 才添加
        todo 多层 dict 的处理
        """
        value_sorted = OrderedDict()
        for k, v in item.items():
            # 如果 v 是字典, 先对字典进行排序, 再保存到 value_sorted 字典中
            if isinstance(v, dict):
                v = OrderedDict(sorted(v.items(), key=lambda t: t[0]))
            value_sorted[k] = v
        return OrderedDict(sorted(value_sorted.items(), key=lambda t: t[0]))

    def dict_to_js(self, item: dict):
        """
        dict 格式的 item 转换为 json str 中
        """
        if not isinstance(item, dict):
            raise Exception("item must be dict. type of item: {}".format(type(item)))
        return json.dumps(self.sort_keys(item))

    def js_to_dict(self, js_str: str):
        """
        把从 redis 中取出来的 json str 转换为 dict
        """
        try:
            item = json.loads(js_str)
            return item
        except Exception as e:
            logger.error("error load js to dict. error: {}".format(e))

    def get_list_size(self, key):
        """
        获取 list key 的长度
        """
        return self.redis_cli.llen(key)

    def get_zset_size(self):
        """
        获取 set key 的长度
        """
        return self.redis_cli.zcard(self.redis_key_on)

    def exists_in_list(self, key, item: dict):
        """
        判断 item 是否存在于 某个 list 中
        """
        self.redis_cli.ping()

        # 返回列表, 列表中每个元素都是 bytes 类型的 json.dumps(item)
        values_all = self.redis_cli.lrange(key, start=0, end=-1)
        # if json.dumps(self._sort_keys(item)) in [v.decode() for v in values_all]:
        if self.dict_to_js(item) in [v.decode() for v in values_all]:
            logger.info("item exists in {}".format(key))
            return True
        return False

    def exists_in_zset(self, item: dict):
        """
        判断 item 是否存在 某个 set 中
        """
        self.redis_cli.ping()

        is_exists = self.redis_cli.zscore(self.redis_key_on, self.dict_to_js(item))
        if is_exists:
            logger.info("item exists in {}".format(self.redis_key_on))
        return is_exists

    def put_to_list(self, item: dict):
        """
        把 item 保存到 list redis_key_all 中
        """
        self.redis_cli.ping()

        self.remove_expires()

        if self.exists_in_list(self.redis_key_all, item):
            logger.warning(
                "item already exists in key: {}. project: {}, spider: {}, account: {}".format(
                    self.redis_key_all,
                    item["project"],
                    item["spider"],
                    item["account_info"]["account"],
                )
            )
            return

        if self.exists_in_zset(item):
            logger.warning(
                "item already exists in key_on: {}. project: {}, spider: {}, account: {}".format(
                    self.redis_key_on,
                    item["project"],
                    item["spider"],
                    item["account_info"]["account"],
                )
            )
            return

        # qsize = self.redis_cli.rpush(key, json.dumps(self._sort_keys(item)))
        qsize = self.redis_cli.rpush(self.redis_key_all, self.dict_to_js(item))
        logger.info("total {} item in key {}".format(qsize, self.redis_key_all))

    def put_to_zset(self, item: dict):
        """
        把 item 保存到 有序集合中, 记录其加入时间
        并定时清理 15 分钟前设置的 value
        """
        self.redis_cli.ping()

        mapping = {
            self.dict_to_js(item): int(time.time())
        }
        # 只有当 值 不存在时 才添加
        result = self.redis_cli.zadd(self.redis_key_on, mapping, nx=True)
        if result:
            logger.info(
                "successfully put item to zset: {}. total item: {}".format(
                    self.redis_key_on,
                    self.get_zset_size()
                )
            )
        else:
            logger.info("item already in key: {}".format(self.redis_key_on))

    def get_from_list(self, key):
        """
        从 list 中取出来一个数据
        """
        self.redis_cli.ping()

        # 执行之前删除 self.expires 之前的值
        self.remove_expires()

        # 如果队列不为空, 直接取出一个返回
        if self.get_list_size(key):
            item = self.redis_cli.lpop(key)
        else:
            logger.info("redis key {} is empty, wait for {}s".format(key, self.timeout))
            # 队列为空时, 阻塞一段时间
            item = self.redis_cli.blpop(key, self.timeout)
        # 如果获取到了非空的 item, 才把它保存到 cookie:on 中并返回
        if item:
            self.all_to_on(item=item)
            # 转换为 dict 再返回
            return self.js_to_dict(item)

    def remove_expires(self):
        """
        从 zset 中删除掉 self.expire 之前的值
        执行每条命令之前都先执行一下 remove_expires 的命令
        :return:
        """
        self.redis_cli.ping()

        # 删除 score 在 15 分钟之前的值
        result = self.redis_cli.zremrangebyscore(
            name=self.redis_key_on,
            min=0,
            max=int(time.time()) - 60 * self.expire
        )
        if result:
            logger.info(
                "successfully remove {} expired item from key: {}".format(
                    result,
                    self.redis_key_on
                )
            )
        # else:
        #     logger.info("no expire item in key: {}".format(self.redis_key_on))

    def remove_from_zset(self, item: dict):
        """
        从 set 中删除 item
        用于当获取 cookie 成功并更新到 mysql 之后, 从 set key 中删除
        """
        self.redis_cli.ping()

        result = self.redis_cli.zrem(self.redis_key_on, self.dict_to_js(item))
        if result:
            logger.info("successfully remove item from key: {}".format(self.redis_key_on))
        else:
            logger.info("item doesnt exists in key: {}".format(self.redis_key_on))


if __name__ == '__main__':
    from get_scrapy_settings.project import get_project_settings
    settings = get_project_settings(settings_name='news_pro')
    q = FifoRedisQueue(settings)
    q.put_to_list(item=dict(account='account', password='password'))
    q.put_to_zset(item=dict(account='account', password='password'))

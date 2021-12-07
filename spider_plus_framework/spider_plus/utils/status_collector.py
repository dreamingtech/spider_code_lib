# 进行数量状态的统计
import redis
from spider_plus.conf.settings import REDIS_QUEUE_NAME, REDIS_QUEUE_HOST, REDIS_QUEUE_PORT, REDIS_QUEUE_DB


# redis 队列默认配置
# REDIS_QUEUE_NAME = 'request_queue'
# REDIS_QUEUE_HOST = 'localhost'
# REDIS_QUEUE_PORT = 6379
# REDIS_QUEUE_DB = 10


class StatusCollector(object):

    def __init__(self, spider_names=[], host=REDIS_QUEUE_HOST, port=REDIS_QUEUE_PORT, db=REDIS_QUEUE_DB, password=None):

        self.redis = redis.StrictRedis(host=host, port=port, db=db, password=password)
        # 存储请求数量的键. 通过爬虫名来区分不同的爬虫的键
        self.request_num_key = "_".join(spider_names) + "_request_num"
        # 存储响应数量的键
        self.response_num_key = "_".join(spider_names) + "_response_num"
        # 存储重复请求的键
        self.duplicate_request_num_key = "_".join(spider_names) + "_duplicate_request_num"
        # 存储 start_requests 数量的键, 用来统计总的完成的 start_requests 函数的数量, 每次执行完 一个 start_requests 函数之后, 该键的值都加 1
        self.finished_start_requests_num_key = "_".join(spider_names) + "_start_requests_num"

    def incr(self, key):
        '''
        给键 key 对应的值增加 1, 不存在会自动创建, 并且值为1
        :param key:
        :return:
        '''
        self.redis.incr(key)

    def get(self, key):
        '''
        获取键 key 对应的值, 不存在时为 0, 存在时则获取并转化为 int 类型
        :param key:
        :return:
        '''
        ret = self.redis.get(key)
        if not ret:
            ret = 0
        else:
            ret = int(ret)
        return ret

    def clear(self):
        '''
        程序结束后清空所有的值
        :return:
        '''
        self.redis.delete(self.request_num_key, self.response_num_key, self.duplicate_request_num_key, self.finished_start_requests_num_key)

    @property
    def request_num(self):
        '''获取请求数量'''
        return self.get(self.request_num_key)

    @property
    def response_num(self):
        '''获取响应数量'''
        return self.get(self.response_num_key)

    @property
    def duplicate_request_num(self):
        '''获取重复请求数量'''
        return self.get(self.duplicate_request_num_key)

    @property
    def finished_start_requests_num(self):
        '''获取 start_requests 数量'''
        return self.get(self.finished_start_requests_num_key)

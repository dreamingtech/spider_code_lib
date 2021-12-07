import time
import pickle

import redis
from six.moves import queue as BaseQueue
from spider_plus.conf.settings import REDIS_QUEUE_NAME, REDIS_QUEUE_HOST, REDIS_QUEUE_PORT, REDIS_QUEUE_DB


# 利用redis实现一个Queue，使其接口同python的内置队列接口一致，可以实现无缝转换
class Queue(object):
    """
    A Queue like message built over redis
    """

    Empty = BaseQueue.Empty  # BaseQueue 即为 python 中内置的队列. BaseQueue.Empty 即为 queue 的 Empty 属性, 即队列满了的属性
    Full = BaseQueue.Full
    max_timeout = 0.3

    def __init__(self, maxsize=0, name=REDIS_QUEUE_NAME, host=REDIS_QUEUE_HOST, port=REDIS_QUEUE_PORT, db=REDIS_QUEUE_DB, lazy_limit=True, password=None):
        """
        Constructor for RedisQueue
        maxsize:    an integer that sets the upperbound limit on the number of
                    items that can be placed in the queue.
        lazy_limit: redis queue is shared via instance, a lazy size limit is used
                    for better performance.
        """
        self.name = name
        self.redis = redis.StrictRedis(host=host, port=port, db=db, password=password)
        self.maxsize = maxsize
        self.lazy_limit = lazy_limit
        self.last_qsize = 0

    def qsize(self):
        self.last_qsize = self.redis.llen(self.name)
        return self.last_qsize

    def empty(self):
        if self.qsize() == 0:
            return True
        else:
            return False

    def full(self):
        if self.maxsize and self.qsize() >= self.maxsize:
            return True
        else:
            return False

    def put_nowait(self, obj):
        if self.lazy_limit and self.last_qsize < self.maxsize:
            pass
        elif self.full():
            raise self.Full
        # pickle.dumps 把一个对象转换为二进制字节, 然后添加到redis的列表中
        self.last_qsize = self.redis.rpush(self.name, pickle.dumps(obj))
        return True

    def put(self, obj, block=True, timeout=None):  # block=Ture, 如果队列已满, 就会处理堵塞和等待状态
        if not block:
            return self.put_nowait(obj)

        start_time = time.time()
        while True:
            try:
                return self.put_nowait(obj)
            except self.Full:
                if timeout:
                    lasted = time.time() - start_time
                    if timeout > lasted:
                        time.sleep(min(self.max_timeout, timeout - lasted))
                    else:
                        raise
                else:
                    time.sleep(self.max_timeout)

    def get_nowait(self):
        ret = self.redis.lpop(self.name)
        if ret is None:
            raise self.Empty  # 如果队列为空, 就抛出队列为空的异常
        # 把二进制的数据反序列化为 python 对象
        return pickle.loads(ret)

    def get(self, block=True, timeout=None):
        if not block:
            return self.get_nowait()

        start_time = time.time()
        while True:
            try:
                return self.get_nowait()
            except self.Empty:
                if timeout:
                    lasted = time.time() - start_time
                    if timeout > lasted:
                        time.sleep(min(self.max_timeout, timeout - lasted))
                    else:
                        raise
                else:
                    time.sleep(self.max_timeout)

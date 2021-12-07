'''实现一个对redis哈希类型的操作封装'''
import redis
import pickle

from spider_plus.http.request import Request
from spider_plus.conf import settings


class RedisBackupRequest(object):
    '''利用hash类型，存储每一个请求对象，key是指纹，值就是请求对象'''

    REDIS_BACKUP_NAME = settings.REDIS_BACKUP_NAME
    REDIS_BACKUP_HOST = settings.REDIS_BACKUP_HOST
    REDIS_BACKUP_PORT = settings.REDIS_BACKUP_PORT
    REDIS_BACKUP_DB = settings.REDIS_BACKUP_DB


    def __init__(self):
        self._redis = redis.StrictRedis(host=self.REDIS_BACKUP_HOST, port=self.REDIS_BACKUP_PORT ,db=self.REDIS_BACKUP_DB)
        self._name = self.REDIS_BACKUP_NAME

    # 增删改查
    def save_request(self, fp, request):
        '''将请求对象备份到redis的hash中'''
        bytes_data = pickle.dumps(request)
        # 指纹作为键, 真正的request对象作为值保存下来, 删除时使用 fp 为键进行删除即可
        self._redis.hset(self._name, fp, bytes_data)

    def delete_request(self, fp):
        '''根据请求的指纹，将其删除'''
        self._redis.hdel(self._name, fp)

    def update_request(self, fp, request):
        '''更新已有的fp'''
        self.save_request(fp, request)

    def get_requests(self):
        '''返回全部的请求对象'''
        for fp, bytes_request in self._redis.hscan_iter(self._name):
            request = pickle.loads(bytes_request)
            yield request

    def get_backup_request_length(self):
        return self._redis.hlen(self.REDIS_BACKUP_NAME)
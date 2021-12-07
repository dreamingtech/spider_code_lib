# coding=utf-8
# 调度器

# 利用six模块实现py2和py3兼容
import six
from six.moves.queue import Queue
import w3lib.url
from hashlib import sha1

from spider_plus.utils.log import logger
from spider_plus.utils.queue import Queue as ReidsQueue
from spider_plus.conf.settings import SCHEDULER_PERSIST
from spider_plus.utils.set import NoramlFilterContainer, RedisFilterContainer
from spider_plus.utils.redis_hash import RedisBackupRequest
from spider_plus.conf.settings import MAX_RETRY_TIMES

class Scheduler(object):
    '''完成调试器模块的封装'''

    def __init__(self, collector):
        # 如果不需要持久化, 就使用python内置的 Queue, 如果需要持久化, 就使用基于 Reids 的 RedisQueue
        if not SCHEDULER_PERSIST:
            self.queue = Queue()  # 存储的是待抓取的请求
            # 不使用分布式的时候, 使用 python 的集合存储指纹
            self._filter_container = NoramlFilterContainer()
        else:
            self.queue = ReidsQueue()
            # 使用分布式的时候, 使用 redis 的集合存储指纹
            self._filter_container = RedisFilterContainer()

        # 去重容器, 利用set类型存储每个请求的指纹
        # self._filter_container = set()

        # self.repeat_request_num = 0  # 记录重复的请求数量. 为什么要统计重复请求的数量. 之前在引擎中使用 "总的响应数量 == 总的请求数量" 来确定程序的退出, 如果有重复的请求, 就不会发送请求, 这个条件就永远不会满足. 需要把程序退出的条件修改为 "总的响应数量 + 总的重复数量 == 总的请求数量", 所以这里要记录重复的请求的数量
        self.collector = collector
        self._backup_request = RedisBackupRequest()

    def add_request(self, request):
        '''
        实现添加request到队列中
        :param request: 请求对象
        :return: None
        '''
        # 判断请求是否需要进行去重, 如果不需要, 直接添加到队列
        if not request.filter:  # 不需要进行去重
            request.fp = self._gen_fp(request)  # 手动给 request 对象添加指纹属性
            self.queue.put(request)
            self._backup_request.save_request(request.fp, request)  # 对请求进行备份
            logger.info("添加不去重的请求: <{} {}>".format(request.method, request.url))
            return   # 必须return. 如果不需要进行去重, 那么就直接返回, 后面生成指纹并把指纹保存到去重容器中的操作就不会去执行了. 但是这样做的话 request 对象就没有 fp 的属性, 在以后可能会用到 fp 属性的地方就会出错. 需要在向队列中添加该请求之间给该请求添加一个fp的属性.

        # 调用_filter_request来实现对请求对象的去重
        # 如果指纹不存在, 才把请求对象添加到队列中
        if self._filter_request(request):
            self.queue.put(request)
            self._backup_request.save_request(request.fp, request)  # 对请求进行备份

    def get_request(self):
        '''
        实现获取队列中的request对象
        :return: 请求对象
        '''
        # queue.get(), 默认 block=Ture, 即是堵塞的, 如果队列中没有对象, 就堵塞在这里. 需要修改为非堵塞的.
        # 非堵塞状态可以会报错, 所以使用try...except...
        try:
            request = self.queue.get(block=False)
        except:
            return None
        else:  # 如果try中的语句没有报错
            # 先判断 是否需要进行去重, 如果对请求启用了过滤, 并且启用了请求持久化的功能
            if request.filter is True and SCHEDULER_PERSIST:
                # 判断重试次数是否超过了规定
                request.fp = self._gen_fp(request)
                if request.retry_time >= MAX_RETRY_TIMES:
                    self._backup_request.delete_request(request.fp)    # 如果超过，那么直接删除
                    logger.warnning("出现异常请求，且超过最大尝试的次数：<{} {}>".format(request.method, request.url))
                request.retry_time += 1   # 重试次数+1
                self._backup_request.update_request(request.fp, request)  # 把更新的重试次数更新到备份中
            return request

    def delete_request(self, request):
        '''根据请求从备份删除对应的请求对象'''
        if SCHEDULER_PERSIST:
            request.fp = self._gen_fp(request)
            self._backup_request.delete_request(request.fp)

    def add_lost_requests(self):
        '''将丢失的请求对象再添加到队列中'''
        # 从备份容器取出来，放到队列中
        if SCHEDULER_PERSIST:
            for request in self._backup_request.get_requests():
                self.queue.put(request)

    def _filter_request(self, request):
        '''
        实现对请求对象的去重
        :param request: 请求对象
        :return: bool
        '''
        # 给 request对象添加一个fp属性, 保存指纹
        # 去重容器: 存储已经发过的请求的特征 url, 选用集合类型: set()
        # 利用请求的 url method data 求出一个指纹, 利用sha1
        request.fp = self._gen_fp(request)
        # 如果判断指纹不在指纹集合中, 就把它添加进去
        if not self._filter_container.exists(request.fp):
            logger.info("添加新的请求: <%s>" % request.url)
            # 如果是新的请求, 那么就添加到去重容器中, 表示请求已经添加到了队列中
            self._filter_container.add_fp(request.fp)
            return True
        else:
            logger.info("发现重复的请求：<{} {}>".format(request.method, request.url))
            self.collector.incr(self.collector.duplicate_request_num_key)
            return False

    @staticmethod
    def _to_bytes(string):
        if six.PY2:  # 如果是python2环境
            if isinstance(string, str):  # str类型在py2中是字节类型
                return string
            else:  # 如果是python2的 unicode 类型, 转化为python2字节类型
                return string.encode("utf-8")
        elif six.PY3:  # 如果是python3环境
            if isinstance(string, str):
                return string.encode("utf-8")  # 转换为bytes类型
            else:
                return string  # 说明string是bytes类型，直接返回

    def _gen_fp(self, request):
        '''
        对 url 地址, 请求体, 请求参数, 请求方法进行加密, 生成 request 对象的指纹
        :param request: request对象
        :return: 指纹字符串
        '''
        # 1. url 地址排序：借助w3lib.url模块中的 canonicalize_url 方法
        url = w3lib.url.canonicalize_url(request.url)
        # 2. 请求方法 method, 不需要排序，只要保持大小写一致就可以
        method = request.method.upper()  # 全大写
        # 3. 请求参数params. 排序. 如果有提供则是一个字典，如果没有则是 None
        params = request.params if request.params is not None else {}  # 如果是None，那么设为{}
        params = sorted(params.items(), key=lambda x: x[0])  # 按照key对字典进行排序，结果将是一个列表
        # 4. 请求体data排序：如果有提供则是一个字典，如果没有则是None
        data = request.data if request.data is not None else {}  # 如果是None，那么设为{}
        data = sorted(data.items(), key=lambda x: x[0])  # 按照key对字典进行排序，结果将是一个列表

        # 5. 利用sha1算法，计算指纹
        s1 = sha1()
        # 由于s1接收的只能是bytes类型(python3)、str类型(python2)，他们都是某种编码类型的(如utf-8、gbk)
        # 为了兼容py2和py3, 利用 _to_bytes 方法, 把所有的字符串转化为字节类型
        s1.update(self._to_bytes(url))  # 添加url地址
        s1.update(self._to_bytes(method))  # 添加请求方法
        s1.update(self._to_bytes(str(params)))  # 添加请求参数
        s1.update(self._to_bytes(str(data)))  # 添加请求体

        fp = s1.hexdigest()  # 提取16进制的sha1指纹字符串并返回
        return fp

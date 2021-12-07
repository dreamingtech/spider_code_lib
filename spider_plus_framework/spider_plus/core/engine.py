# coding=utf-8
# 引擎
import time
import importlib

from datetime import datetime

# 为什么要把导入 gevent.Pool 的操作放在最前面, 由于打patch补丁是为了替换掉socket为非阻塞的, 而下载器 Downloader 中正好使用了requests模块，如果在这之后导入协程池，会导致requests中使用的socket没有被替换成功, 从而有可能导致使用出现问题
from spider_plus.conf.settings import ASYNC_TYPE
# 判断使用什么异步模式，改用对应的异步池
if ASYNC_TYPE == 'thread':
    from multiprocessing.dummy import Pool    # 导入线程池对象
elif ASYNC_TYPE == 'coroutine':
    from spider_plus.async.coroutine import Pool
    # from gevent.monkey import patch_all
    # patch_all()
else:
    raise Exception("不支持的异步类型：{},".format(ASYNC_TYPE))

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from spider_plus.conf.settings import SPIDERS, PIPELINES, DOWNLOADER_MIDDLEWARES, SPIDER_MIDDLEWARES, CONCOURRENT_REQUEST
from spider_plus.utils.status_collector import StatusCollector

class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        # 实例化 collector 时要传递爬虫的名字, 所以要把 spiders 的实例化放在前面
        self.spiders = self._auto_import_instances(SPIDERS, is_spider=True)  # 接收外部传入的爬虫对象, 字典
        # 把统计数量的容器放在调度器之前实例化, 因为重复请求的数量是在调度器中进行统计的, 并且在引擎最后面使用到调度器中的重复请求的数量. self.scheduler.repeat_request_num, 所以要把 collector 也传递到调度器中, 经过调度器统计重复请求的数量后才能使用
        self.collector = StatusCollector(list(self.spiders.keys()))
        self.scheduler = Scheduler(self.collector)  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipelines = self._auto_import_instances(PIPELINES)  # 初始化管道对象, 列表
        self.spider_mids = self._auto_import_instances(SPIDER_MIDDLEWARES)  # 初始化爬虫中间件对象, 列表
        self.downloader_mids = self._auto_import_instances(DOWNLOADER_MIDDLEWARES)  # 初始化下载器中间件对象, 列表
        # 为了使处理请求响应数据的方法能够正常退出, 定义两个变量, 当总的响应数量大于等于总的请求数量时, 所有请求都已经处理完毕, 就可以退出了
        # self.total_request_num = 0  # 总的请求数
        # self.total_response_num = 0  # 总的响应数
        self.pool = Pool(5)  # 实例化线程池对象. 线程池的大小默认为cpu的个数, 电脑是单核时线程池的大小就为 1, 可以手动指定线程池的大小
        self.is_running = True  # 程序是否处理运行状态, 依据此状态来决定程序是否退出. 当程序开始运行时, 设置此参数为 Ture, 当所有的请求执行结束后, 设置此参数为 False, 此时程序就退出.

    def _auto_import_instances(self, path=[], is_spider=False):
        '''
        根据配置文件, 实现模块的动态导入, 传入模块路径列表, 返回类的实例
        :param path: settings 中配置的要导入类的路径. 包含模块位置字符串的列表
        :param is_spider: 是否是爬虫. 爬虫是字典的形式, 所以需要进行单独的判断和处理
        :return: 返回爬虫, 管道, 中间件的实例
        '''
        if is_spider is True:
            instances = {}
        else:
            instances = []  # 存储对应类的实例对象

        for p in path:
            module_name = p[:p.rfind(".")]  # 取出模块名称
            module_name = p.rsplit(".", 1)[0]
            cls_name = p[p.rfind(".") + 1:]  # 取出类名称
            cls_name = p.rsplit(".", 1)[-1]
            module = importlib.import_module(module_name)  # 导入模块
            cls = getattr(module, cls_name)  # 根据类名称获取module下的类对象
            if is_spider is True:
                instances[cls.name] = cls()
            else:
                instances.append(cls())  # 实例化类对象
        return instances  # 返回类对象

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        logger.info("当前启动的爬虫: {}".format(SPIDERS))
        logger.info("当前开启的管道: {}".format(PIPELINES))
        logger.info("当前开启的下载器中间件: {}".format(DOWNLOADER_MIDDLEWARES))
        logger.info("当前开启的爬虫中间件: {}".format(SPIDER_MIDDLEWARES))
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时
        # 在引擎的调用执行结束后, 打印总的请求数量和总的响应数量.
        # logger.info("总的请求数量: {}个".format(self.total_request_num))
        logger.info("总的请求数量: {}个".format(self.collector.request_num))
        # logger.info("总的响应数量: {}个".format(self.total_response_num))
        logger.info("总的响应数量: {}个".format(self.collector.response_num))
        # logger.info("总的重复数量: {}个".format(self.scheduler.repeat_request_num))
        logger.info("总的重复数量: {}个".format(self.collector.duplicate_request_num))
        # 完成的 start_requests 函数的数量
        logger.info("总的 start_requests 数量: {}个".format(self.collector.finished_start_requests_num))

        # 爬虫运行结束时, 清空 redis 中用于统计数量的 键. 如果程序正常运行并退出, 这里的键就会被清理, 只留下 "redis_set" 这个键, 其中保存着请求的指纹, 如果程序运行的过程中退出了, 就不会清空统计数量的键, redis 中会多出来 "baidu_qiubai_request_num", "baidu_qiubai_duplicate_request_num", "baidu_qiubai_response_num", "request_queue", 这几个键.
        self.collector.clear()

    def _callback_total_finished_start_requests_num(self, temp):
        '''记录完成的 start_requests 的数量
        在 _start_request 函数中每调用一次 _func 方法, 就会执行一次该函数, 执行的次数就是爬虫的个数, 每一个爬虫中都有一个 start_requests 方法, 执行完一个 start_requests 方法, 就让 finished_start_requests_num_key 加 1
        '''
        self.collector.incr(self.collector.finished_start_requests_num_key)

    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''

        def _func(spider_name, spider):
            for start_request in spider.start_requests():
                # 2. 把初始请求添加给调度器
                # 利用爬虫中间件预处理请求对象
                for spider_mid in self.spider_mids:
                    start_request = spider_mid.process_request(start_request)
                # 在把初始请求添加到调度器中之前, 给它添加一个属性 spider_name, 记录它是哪个爬虫产生的请求, 以方便后面 _execute_request_response_item 中通过这个属性获取到对应的爬虫, 进而获取爬虫的 parse方法
                start_request.spider_name = spider_name

                # 2. 调用调度器的add_request方法, 添加request对象到调度器中
                self.scheduler.add_request(start_request)
                # 把request添加到调度器中之后, 把总请求数加1
                # self.total_request_num += 1
                # 对 redis 中的请求数量进行加 1 操作
                self.collector.incr(self.collector.request_num_key)

        # 1. 爬虫模块发出初始请求
        # 遍历 spiders 字典, 获取每个spider对象
        # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历. 但如果 spider.start_requests() 方法中存在着 while True 死循环, 就会发生阻塞, 一直会卡在这里执行死循环. 所以要把这里的代码改为异步执行
        for spider_name, spider in self.spiders.items():
            self.pool.apply_async(_func, args=(spider_name, spider), callback=self._callback_total_finished_start_requests_num)    # 把执行每个爬虫的start_requests方法，设置为异步的. 每次都会使用一个子线程来处理. 这样, 就算某个爬虫的 start_requests 方法中存在死循环, 只会对执行这个死循环的子线程产生堵塞, 不会对主线程造成堵塞.

    def _execute_request_response_item(self):
        '''处理单个请求, 从调度器取出, 发送请求, 获取响应, parse函数处理, 调度器处理'''
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        if request is None:  # 判断从调度器中取出来的request是否是None, 如果是None, 表示调度器为空, 就不进行任何进一步的处理
            return
        for downloader_mid in self.downloader_mids:
            # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
            request = downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)

        # 为了把 request中的meta传递给 response, 在调用下载器获取响应后, 给response添加一个meta属性即可
        response.meta = request.meta

        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        for downloader_mid in self.downloader_mids:
            response = downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        for spider_mid in self.spider_mids:
            response = spider_mid.process_response(response)

        # 根据请求对象的 spider_name 属性, 获取爬虫实例, 进而获取爬虫的 parse 方法
        spider = self.spiders.get(request.spider_name)
        # 获取 request 对象对应的响应的parse方法. getattr 从 self.spiders 中查找并返回 request的parse属性指定的方法
        # 对于糗事百科爬虫来说, 1-13页列表页中, 由于request对象没有指定parse方法, 所以会使用默认的 parse="parse", 而对于详情页, 则使用 request对象指定的 "parse_detail" 方法.
        parse = getattr(spider, request.parse)

        # 5. 利用爬虫的parse方法，处理响应
        # 因为 spiders 的 parse 方法已经修改为生成器, 所以这里要进行遍历
        for result in parse(response):
            # 6. 判断结果的类型
            # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
            if isinstance(result, Request):
                for spider_mid in self.spider_mids:
                    # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
                    result = spider_mid.process_request(result)

                # 对于新的请求, 在保存到调度器之间也添加 spider_name 属性
                result.spider_name = request.spider_name

                self.scheduler.add_request(result)
                # self.total_request_num += 1  # 请求加1
                # 对 redis 中的请求数量进行加 1 操作
                self.collector.incr(self.collector.request_num_key)

            # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
            else:
                # 遍历所有的管道, 对item进行处理
                for pipeline in self.pipelines:
                    # 必须要把处理的结果重新赋值给 result, 下一个管道才能在上一个管道的基础上进一步处理
                    result = pipeline.process_item(result, spider)

        # 整个函数都是处理单个请求, 整个函数执行完了, 单个请求才处理完, 此时总的响应数加1
        # self.total_response_num += 1
        # 对 redis 中的响应数量进行加 1 操作
        self.collector.incr(self.collector.response_num_key)

        # 一个请求处理成功之后就在备份容器中删除该请求
        print("删除请求")
        self.scheduler._backup_request.delete_request(request.fp)
        print(self.scheduler._backup_request.get_backup_request_length())

    def _error_callback(self, exception):
        '''异常回调函数'''
        try:
            raise exception  # 抛出异常后, 才能被日志进行完整记录下来
        except Exception as e:
            logger.exception(e)

    def _callback(self, temp):  # 必须有 temp 参数
        '''执行新的请求的回调函数, 实现循环'''
        if self.is_running is True:  # 如果还没满足退出条件, 那么继续添加新任务, 否则不继续添加, 终止回调函数, 达到退出循环的目的
            self.pool.apply_async(self._execute_request_response_item, callback=self._callback, error_callback=self._error_callback)

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self.is_running = True  # 启动引擎时, 设置 is_running 状态为True
        # self._start_request()  # 初始化请求

        # 向调度器添加初始请求, 初始化请求
        self.pool.apply_async(self._start_request, error_callback=self._error_callback)  # 使用异步, 当主线程执行到这里时, 会使用线程池中的一个子线程来执行这个函数, 主线程继续向下执行

        # 虽然调用的是异步的 apply_async 方法, 但调用的过程依然是同步的, 执行完一个 "请求-响应-数据" 的流程之后, 才调用 _callback 方法, 这时的并发量还是非常低的, 还是1. 为了提高并发量, 可以把这句话放到一个循环中执行. 如 for i in range(3): 这样就会有 3 个并发线程同时去执行
        for i in range(CONCOURRENT_REQUEST):
            # 利用回调实现循环. 同样会使用一个子线程来执行这个函数
            self.pool.apply_async(self._execute_request_response_item, callback=self._callback, error_callback=self._error_callback)

        # 设置循环, 处理多个请求
        # 使用循环让主线程处理堵塞状态, 一直等到子线程执行结束才退出循环
        while True:
            time.sleep(0.001)  # 避免主线程 cpu 空转, 降低资源消耗
            # self._execute_request_response_item()   # 处理单个请求
            # 循环结束的条件
            # 成功的响应数 + 重复的响应数量 >= 总的请求数量, 程序结束
            # if self.collector.request_num != 0:  # 刚开始时总的请求数量为0, 只有当总请求数不为0时, 即至少有一个请求或响应后, 才有可能退出
            if self.collector.finished_start_requests_num == len(self.spiders):  # 当处理完的起始请求数量等于爬虫的数量时, 表示每个爬虫都被处理过一遍了, 这时再判断请求数和响应数的关系
                if self.collector.response_num + self.collector.duplicate_request_num >= self.collector.request_num:
                    print(self.collector.request_num, self.collector.duplicate_request_num, self.collector.request_num)
                    self.is_running = False  # 满足循环退出条件后, 设置运行状态为 False
                    break

        # 不断的从备份中取出来数据, 添加到请求队列中
        while True:
            self.scheduler.add_lost_requests()
            for i in range(CONCOURRENT_REQUEST):
                # 利用回调实现循环. 同样会使用一个子线程来执行这个函数
                self.pool.apply_async(self._execute_request_response_item, callback=self._callback, error_callback=self._error_callback)
            print("备份中请求个数: ", self.scheduler._backup_request.get_backup_request_length())
            if self.scheduler._backup_request.get_backup_request_length() == 0:
                break

        # 在爬虫的运行结束后, 可能线程池与服务器链接还没有断开, 相当于子线程的执行还未完成, 程序会处于等待状态. 所以在爬虫中一般不会去执行 pool.close() 和 pool.join()
        self.pool.close()
        self.pool.join()


if __name__ == '__main__':
    engine = Engine()
    engine.start()

import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO    # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'   # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = 'log.log'    # 默认日志文件名称

# 设置最大并发数量
CONCOURRENT_REQUEST = 5

# 异步方式  thread, coroutine
ASYNC_TYPE = 'coroutine'
# ASYNC_TYPE = 'thread'

# redis队列默认配置, 存储 request 请求
REDIS_QUEUE_NAME = 'request_queue'
REDIS_QUEUE_HOST = 'localhost'
REDIS_QUEUE_PORT = 6379
REDIS_QUEUE_DB = 0    # 默认使用 0 号数据库

# 设置是否需要持久化和分布式
# 设置调度器的内容, 即请求对象是否要持久化
# 如果是 True, 那么就是使用分布式, 同时也是基于请求的增量式爬虫
# 如果是 False, 不会使用 redis 队列, 而是使用 python 的 set 存储指纹和请求
SCHEDULER_PERSIST = True

# redis 指纹集合的位置, 存储 request 请求的指纹
REDIS_SET_NAME = 'redis_set'
REDIS_SET_HOST = 'localhost'
REDIS_SET_PORT = 6379
REDIS_SET_DB = 0

# request 请求备份的设置
REDIS_BACKUP_NAME = 'request_backup'
REDIS_BACKUP_HOST = 'localhost'
REDIS_BACKUP_PORT = 6379
REDIS_BACKUP_DB = 0

# 请求的最大重试次数
MAX_RETRY_TIMES = 3
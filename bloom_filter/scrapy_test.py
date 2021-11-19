from memory_bloom_filter import BloomFilterMemory
from redis_bloom_filter import BloomFilterRedis

# 对 1000W 数据进行去重, 误判率 十万分之一, 使用 60M 内存
# n = 10114610
# p = 0.00001 (1 in 100000)
# m = 480000000 (57.22MiB)
# k = 5
bf_config_memory = dict(
    data_size_per_filter=10 ** 7,
    memory_size=100,
    hash_seeds_num=5,
    error_rate_threshold=1e-6
)

bf_memory = BloomFilterMemory(bf_config_memory)

# redis 数据库配置信息
redis_db_config = dict(
    host='127.0.0.1',
    port=6379,
    db=0,
    password=None,
)

# url 去重的 redis key 配置信息
redis_key_config_url = dict(
    bloom_filter_key='bf_url',
    redis_count_key='bf_count_url',
    redis_lock_key='bf_lock_url',
)

# 布隆过滤器 参数 配置信息
# 对 1.4 亿条数据进行去重, 使用 500M 内存, 误判率 十万分之一
# n = 141834908
# p = 0.00001 (1 in 100000)
# m = 4192000000 (499.73MiB)
# k = 8
bf_config_url = dict(
    data_size_per_key=14 * 10 ** 7,  # 期望使用 bf 去重的数据量
    memory_size=500,  # 使用的 内存量
    hash_seeds_num=8,  # 使用的 hash seeds 的数量
    error_rate_threshold=1e-5,  # 误判率阈值
)
# 实例化 url 去重的 布隆过滤器 bf_url
bf_redis_url = BloomFilterRedis(
    redis_db_config,
    redis_key_config_url,
    bf_config_url,
)

for i in range(50):
    url = "https://www.dreamingtech.net/s?kw=python{}".format(i)

    # 先使用内存型布隆过滤器进行过滤, 再使用 redis 型进行过滤
    # 如果内存型中不存在, 再使用 redis 去重, 如果 redis 中也不存在, 表示 url 不存在, 以前没有爬取过这个 url
    # 因为所有的 url 第一次出现时都会经过 内存和 redis 这两层的处理, 会添加到这两个 filter 中
    # 所以如果 内存型中已经存在, redis 中也肯定存在, 就不再使用 redis 去重, 这样就会减轻 redis 服务器的压力
    if bf_memory.exists(url):
        print('url: <{}> exists in memory filter'.format(url))
        continue
    else:
        bf_memory.add(url)
        print('url: <{}> added to memory filter, data_size of memory filter: <{}>'.format(url, bf_memory.data_saved))

        # 如果 memory filter 中不存在, 再使用 redis filter 进行过滤
        if bf_redis_url.exists(url):
            print('url: <{}> exists in redis filter'.format(url))
            continue
        else:
            bf_redis_url.add(url)
            print('url: <{}> added to redis filter, data_size of redis filter: <{}>'.format(url, bf_redis_url.data_saved))

    print("添加 url 到 scrapy 中. url: {}".format(url))

for i in range(100):
    url = "https://www.dreamingtech.net/s/python{}".format(i)

    # 先使用内存型布隆过滤器进行过滤, 再使用 redis 型进行过滤
    # 如果内存型中不存在, 再使用 redis 去重, 如果 redis 中也不存在, 表示 url 不存在,
    # 如果 内存型中已经存在, redis 中也肯定存在, 就不再使用 redis 去重
    if bf_memory.exists(url):
        print('url: <{}> exists in memory filter'.format(url))
        continue
    else:
        bf_memory.add(url)
        print('url: <{}> added to memory filter, data_size of memory filter: <{}>'.format(url, bf_memory.data_saved))

        # 如果 memory filter 中不存在, 再使用 redis filter 进行过滤
        if bf_redis_url.exists(url):
            print('url: <{}> exists in redis filter'.format(url))
            continue
        else:
            bf_redis_url.add(url)
            print('url: <{}> added to redis filter, data_size of redis filter: <{}>'.format(url, bf_redis_url.data_saved))

    print("添加 url 到 scrapy 中. url: {}".format(url))

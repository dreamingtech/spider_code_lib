# -*- coding: utf-8 -*-
# 基于 redis 的布隆过滤器
# redis based bloom filter

import math
import redis
import mmh3


def singleton(cls, *args, **kwargs):
    """ 单例模式 """
    instances = {}

    def _singleton(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return _singleton


@singleton
class RedisConn(object):
    """ redis 客户端连接 """

    def __init__(self, redis_config):

        self.pool_redis = redis.ConnectionPool(
            host=redis_config.get('host', '127.0.0.1'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 0),
            password=redis_config.get('password'),
        )

    def get_redis_cli(self):
        """ 获取redis 客户端连接 """
        return redis.StrictRedis(connection_pool=self.pool_redis)


class BloomFilterRedis(object):
    """ redis 版布隆过滤器 """
    def __init__(self, redis_db_config, redis_key_config, bf_config):
        """
        初始化布隆过滤器
        - bf_config 中包含的内容
          - data_size_per_key: 期望向每个 key 中保存的数据量
          - memory_size: redis 中每个 key 使用的内存量
          - hash_seeds_num: hash 种子的数量
          - error_rate_threshold: 误判率的最大值

        :param redis_db_config: redis 数据库的配置信息
        :param redis_key_config: redis 中保存 bloom filter 内容的 key
        :param bf_config: bloom filter 配置信息
        """
        # 要保存到 redis 每个 key 中的数据量的大小/要使用每个 redis_key 进行过滤的数据量的大小
        self.data_size_per_key = bf_config.get("data_size_per_key")
        # bloom 过滤器 使用的内存量
        memory_size = bf_config.get("memory_size")
        # hash 种子数量
        self.hash_seeds_num = bf_config.get("hash_seeds_num")
        # 误判率阈值, 保证给定的 data_size, hash_num, bit_size 计算得到的 error_rate 小于给定的 error_rate_threshold
        self.error_rate_threshold = bf_config.get("error_rate_threshold")

        if not (isinstance(self.data_size_per_key, int) and self.data_size_per_key > 0):
            raise ValueError("data_size_per_key must be greater than 0")
        if not (0 < self.error_rate_threshold < 1):
            raise ValueError("error_rate_threshold must be between 0 and 1")
        if not (isinstance(memory_size, int) and 0 < memory_size < 512):
            raise Exception('memory_size for redis must be integer and between (0 512MB)')
        if not (isinstance(self.hash_seeds_num, int) and 0 < self.hash_seeds_num < 10):
            raise Exception('hash_seeds_num for redis must be integer and between (0 10)')

        # 计算 memory_size 对应的 即一个 redis_key 对应的 bit 位的长度
        self.bit_num = memory_size * 1024 * 1024 * 8
        # 计算误判率
        self.error_rate = self._cal_error_rate()
        # 检查给定的参数计算得到的误判率 error_rate 能否小于误判率阈值 error_rate_threshold
        self._check_error_rate()

        # 实例化 redis 客户端
        self.redis_cli = RedisConn(redis_db_config).get_redis_cli()

        # redis 中布隆过滤器的 key, 因为可能会使用多个 内存块, 故可能有多个 redis_key
        # 把 redis_config 中定义的 bloom_filter 作为基础, 在后面添加数字作为 bloom_filter_key
        # 如 bloom_filter_01, bloom_filter_02
        self.redis_filter_key_base = redis_key_config.get('bloom_filter_key', 'bloom_filter')
        # redis 中记录 bloom_filter 中保存数据量的 key
        self.redis_count_key = redis_key_config.get('redis_count_key', 'bloom_filter_count')
        # redis 分布式锁, 以免出现同时判断, 同时添加的情况
        self.redis_lock_key = redis_key_config.get('redis_lock_key', 'bloom_filter_lock')

        self._filter_list = None
        self.data_saved = None
        # 获取 _filter_list 和 data_saved 参数
        self._get_init_params()

        # 计算一个 memory_size 能够保存的 data_size
        self.max_data_size = self._cal_max_data_size()

        # 获取多个 hash 种子
        self._hash_seeds_list = self.get_hash_seeds()

    def _cal_error_rate(self):
        """
        通过传入的数据量 data_size (n), 内存量 bit_size (m), hash 种子数量 hash_seeds_num (k), 计算出能够达到的 误判率 (p)
        n 为数据量
        p 为误报率
        k 为哈希函数个数
        m 为 bit 位长度
        n = ceil(m / (-k / log(1 - exp(log(p) / k))))
        p = pow(1 - exp(-k / (m / n)), k)
        m = ceil((n * log(p)) / log(1 / pow(2, log(2))))
        k = round((m / n) * log(2))
        计算公式来自: https://hur.st/bloomfilter/
        """
        n = self.data_size_per_key
        k = self.hash_seeds_num
        m = self.bit_num
        # pow(*args, **kwargs)
        # Equivalent to x**y (with two arguments) or x**y % z (with three arguments)
        p = pow(1 - math.exp(-k / (m / n)), k)
        return p

    def _check_error_rate(self):
        """
        检测给定数量的 hash 种子能否实现指定的 误判率
        """
        if self.error_rate > self.error_rate_threshold:
            raise Exception(
                'calculated error_rate: <{:.10f}> is smaller than error_rate_threshold: <{:.10f}>, ' 
                'please add hash_num or increase memory_size.'.format(self.error_rate, self.error_rate_threshold)
            )

    def _get_init_params(self):
        """
        从 redis 中读取出所有的 redis_key, 保存到列表中, 如果不存在, 就设置为 ['bf_url_1'] 或 ['bf_title_1']
        从 redis 中读取出已经保存的 数据量, 如果不存在, 就设置为 0
        """
        # 以列表的形式保存所有的 redis_filter_key, 如 [bf_url_1, bf_url_2], 用来进行去重判断
        # 如果是 url 去重, redis_key 的形式为 [bf_url_1, bf_url_2]
        if self.redis_filter_key_base.startswith('bf_url'):
            # 从 redis 中读取出所有 匹配 bf_url_0 - bf_url_9 的 key
            # 如果没有获取到, 表示之前没有运行过此布隆过滤器, 就把 _filter_list 就设置为 ['bf_url_1']
            self._filter_list = [_i.decode() for _i in self.redis_cli.keys(pattern='bf_url_[0-9]')] if \
                self.redis_cli.keys(pattern='bf_url_[0-9]') else ['bf_url_1']
        # 如果是 title 去重, redis_key 的形式为 [bf_title_1, bf_title_2]
        elif self.redis_filter_key_base.startswith('bf_title'):
            self._filter_list = [_i.decode() for _i in self.redis_cli.keys(pattern='bf_title_[0-9]')] if \
                self.redis_cli.keys(pattern='bf_title_[0-9]') else ['bf_title_1']

        # 从 redis 中读取到的 keys 可能是乱序排列的, 要对其进行升序排列
        self._filter_list.sort()

        # 初始化时从 redis 中读取出已经保存的数据量, 如果未读取到数据, 就设置为 0
        # 从 redis 中获取 _data_saved, 每次向 redis add 后都把 redis 中的这个键的值加 1
        self.data_saved = int(self.redis_cli.get(self.redis_count_key).decode('utf-8')) if \
            self.redis_cli.get(self.redis_count_key) else 0

    def _cal_max_data_size(self):
        """
        计算在给定的 p, m, k 时, 一个 filter 能够保存的最大数据量 n
        既然已经有了 data_size_per_filter, 为什么还要再计算 max_data_size 呢?
        1. data_size_per_filter 是每一个过滤器中 *期望/想要* 使用 bf 过滤的数据量,
        用它来保证 *实际* 过滤数据时的误判率 小于 *期望* 的误判率阈值,
        是实例化 bloom_filter 时的第一层保证, 也可以说是从 *理论* 上进行的保证.
        2. 而 max_data_size 则是每一个过滤器在 *期望的* 误判率阈值 下, 能够 *实际* 存入/过滤的数据量,
        当存入/过滤 的数据量大于 max_data_size 时, 却依然可以继续存入数据, 只是此时的 *实际* 误判率,
        就要大于设定的误判率阈值了, 计算 max_data_size, 当存入的数据量 data_saved 大于等于 max_data_size 时,
        就新建 过滤器来进行过滤. 这样, 就从 *实际* 上保证了 bloom_filter 整体上的误判率小于给定的 误判率阈值了
        n = ceil(m / (-k / log(1 - exp(log(p) / k))))
        """
        k = self.hash_seeds_num
        m = self.bit_num
        p = self.error_rate_threshold
        n = math.ceil(m / (-k / math.log(1-math.exp(math.log(p) / k))))
        return n

    def _safe_data(self, data):
        """
        把传入的 data 转换为 str 类型
        """
        if not isinstance(data, str):
            try:
                data = str(data)
            except:
                raise Exception('data type must be str or can be converted to str')
        return data

    def get_hash_seeds(self):
        """
        获取指定数量的 hash 种子
        """
        # 将哈希种子固定为 1, 2, 3 , ... ,hash_num
        _seeds = [_i for _i in range(1, self.hash_seeds_num + 1)]
        return _seeds

    def get_hash_indexes(self, data):
        """
        计算一个给定的数据 data 使用所有的 hash_seeds_list 得到的在 bitarray 中的索引值
        """
        # 把 str 数据转换为 bytes
        data = self._safe_data(data)
        _hash_indexes = [mmh3.hash(data, self._hash_seeds_list[_i]) % self.bit_num for _i in range(self.hash_seeds_num)]
        return _hash_indexes

    def _check_and_add_new_filter(self):
        """
        检查 redis 中保存的 所有数据量 是否大于 总的 data_size, 如果大于, 就增加一个新的过滤器,
        即增加一个 redis_filter_key, 并在 _filter_list 中添加新增的 redis_filter_key
        add 数据时, 只需要向列表中最后一个元素代表的 redis_key 中添加就可以了
        """
        if self.data_saved >= self.max_data_size * len(self._filter_list):
            print('max data_size reached, add one more filter. data_size: {}'.format(self.data_saved))
            _redis_filter_new = "{}_{}".format(self.redis_filter_key_base, len(self._filter_list) + 1)
            self._filter_list.append(_redis_filter_new)

    def add(self, data):
        """
        redis 版布隆过滤器不需要初始化 bitmap/bitarray, 只需要用 setbit 把 redis 的 key 中某个 index 处的值置为 1 即可
        随着数据量的增加, 如果 redis 中保存的数据量 _data_saved 大于 指定的最大数据量,
        就动态增加一个内存块, 同时, 数据全部保存到新的内存块中, 但判断时, 还是从所有的内存块中进行判断
        """

        # 在每次向 bloom_filter 中添加数据时, 都先判断一下 已经保存的数据量,
        # 如果 已保存数据量 达到 每个 filter 所能保存的最大值, 就增加一个新的 filter
        self._check_and_add_new_filter()

        # get_hash_indexes 获取所有 hash 种子对应的 hash 索引值 / offset 值
        for _hash_index in self.get_hash_indexes(data):
            self.redis_cli.setbit(self._filter_list[-1], _hash_index, 1)

        # 把 data_saved 的值 加1, 同时, 把 redis 中保存 数据量的键的值 加1
        self.data_saved += 1
        self.redis_cli.incr(self.redis_count_key)

    def _is_exists_in_certain_filter(self, data, _filter):
        """
        检查给定的值 data 是否存在于某个特定的 _filter 中
        对每一个 hash 种子计算 给定的 data 的 index 值, 或称索引值, 偏移量,
        只要有一个 hash 种子计算得到的 index 不在 _filter 中, 就说明这个 data 绝对不存在
        如果所有 hash 种子计算得到的 index 在 _filter 中都存在, 在一定的误判率下, 就认为这个 data 存在
        """
        # 获取所有 hash 种子计算得到的 索引值
        hash_indexes = self.get_hash_indexes(data)
        # 对所有的索引值进行过滤
        for _hash_index in hash_indexes:
            # 只要有一个 _hash_index 为 0, 就肯定不存在, 就返回 False
            if not self.redis_cli.getbit(_filter, _hash_index):
                return False
        # 如果所有的循环都完整的执行下来没有退出, 就认为值已经存在了
        return True

    def exists(self, data):
        """
        对 _filter_list 中所有的 _filter 进行遍历,
        检测数据是否在某一个 _filter 中存在
        """
        for _filter in self._filter_list:
            _is_exists = self._is_exists_in_certain_filter(data, _filter)
            # 只要有一个 数据在某一个 _filter 中存在, 就返回 True
            if _is_exists:
                return True
        # 如果 _filter_list 中所有的 _filter 都检测过, 并且都不存在, 才返回 False
        return False

    def __len__(self):
        """"
        返回现有数据容量
        """
        return self.data_saved

    def __contains__(self, data):
        """
        用于实现 in 判断
        """
        return self.exists(data)


def main_multi_filter():
    """
    测试生成多个 filter
    注意: 因为 布隆过滤器不会自动删除之前的 redis_key, 所以测试时需要手动删除 redis 中的所有相关 key
    """
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

    # 以下面的参数, 每个 filter 中可以保存 42 个数据
    # 测试多个 filter 时需要把 data_size_per_key 设置的尽可能的小, 否则, 计算出来的误判率很可能会超过阈值
    # 布隆过滤器 参数 配置信息
    bf_config_url = dict(
        data_size_per_key=10 ** 1,    # 期望使用 bf 去重的数据量
        memory_size=1,                # 使用的 内存量
        hash_seeds_num=2,             # 使用的 hash seeds 的数量
        error_rate_threshold=1e-10,   # 误判率阈值
    )
    bf_url = BloomFilterRedis(
        redis_db_config,
        redis_key_config_url,
        bf_config_url,
    )

    print('params used can reach a error_rate of <{}>'.format(bf_url.error_rate))
    print('params used can save <{}> data in one filter'.format(bf_url.max_data_size))

    for i in range(50):
        if bf_url.exists(i):
            print('data: <{}> exist'.format(i))
            continue
        bf_url.add(i)
        print('data: <{}> added, data_size: <{}>'.format(i, bf_url.data_saved))

    for i in range(100):
        if bf_url.exists(i):
            print('data: <{}> exist'.format(i))
            continue
        bf_url.add(i)
        print('data: <{}> added, data_size: <{}>'.format(i, bf_url.data_saved))

    print("{} {} {}".format("*" * 25, "title filter 测试", "*"*25))

    # title 去重的 redis key 配置信息
    redis_key_config_title = dict(
        bloom_filter_key='bf_title',
        redis_count_key='bf_count_title',
        redis_lock_key='bf_lock_title',
    )

    # 以下面的参数, 每个 filter 中可以保存 42 个数据
    # 测试多个 filter 时需要把 data_size_per_key 设置的尽可能的小, 否则, 计算出来的误判率很可能会超过阈值
    # 布隆过滤器 参数 配置信息
    bf_config_title = dict(
        data_size_per_key=10 ** 1,    # 期望使用 bf 去重的数据量
        memory_size=1,                # 使用的 内存量
        hash_seeds_num=2,             # 使用的 hash seeds 的数量
        error_rate_threshold=1e-10,   # 误判率阈值
    )
    bf_title = BloomFilterRedis(
        redis_db_config,
        redis_key_config_title,
        bf_config_title,
    )

    print('params used can reach a error_rate of <{}>'.format(bf_title.error_rate))
    print('params used can save <{}> data in one filter'.format(bf_title.max_data_size))

    for i in range(50):
        if bf_title.exists(i):
            print('data: <{}> exist'.format(i))
            continue
        bf_title.add(i)
        print('data: <{}> added, data_size: <{}>'.format(i, bf_title.data_saved))

    for i in range(100):
        if bf_title.exists(i):
            print('data: <{}> exist'.format(i))
            continue
        bf_title.add(i)
        print('data: <{}> added, data_size: <{}>'.format(i, bf_title.data_saved))


def main_scrapy_single_node():
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
    bf_config_url = dict(
        data_size_per_key=14 * 10 ** 7,   # 期望使用 bf 去重的数据量
        memory_size=500,                  # 使用的 内存量
        hash_seeds_num=8,                 # 使用的 hash seeds 的数量
        error_rate_threshold=1e-5,        # 误判率阈值
    )
    # 实例化 url 去重的 布隆过滤器 bf_url
    bf_url = BloomFilterRedis(
        redis_db_config,
        redis_key_config_url,
        bf_config_url,
    )

    print('params used can reach a error_rate of <{}>'.format(bf_url.error_rate))
    print('params used can save <{}> data in one filter'.format(bf_url.max_data_size))

    words = ['when', 'how', 'where', 'too', 'there', 'to', 'when', 'a', 'b', 'c', 'd', 'e']

    for i in words:
        i = str(i)
        if bf_url.exists(i):
            print('data: <{}> exist'.format(i))
            continue
        bf_url.add(i)
        print('data: <{}> added, data_size: <{}>'.format(i, bf_url.data_saved))

    # test len, and in
    print('data_size of bloom_filter: <{}>'.format(len(bf_url)))
    print('is xixi in bloom_filter: ', 'xixi' in bf_url)
    print('is where in bloom_filter: ', 'where' in bf_url)

    print("{} {} {}".format("*" * 25, "title filter 测试", "*" * 25))

    # title 去重的 redis key 配置信息
    redis_key_config_title = dict(
        bloom_filter_key='bf_title',
        redis_count_key='bf_count_title',
        redis_lock_key='bf_lock_title',
    )

    # 布隆过滤器 参数 配置信息
    bf_config_title = bf_config_url

    # 实例化 标题 去重的 布隆过滤器
    bf_title = BloomFilterRedis(
        redis_db_config,
        redis_key_config_title,
        bf_config_title,
    )

    print('params used can reach a error_rate of <{}>'.format(bf_title.error_rate))
    print('params used can save <{}> data in one filter'.format(bf_title.max_data_size))

    words = ['when', 'how', 'where', 'too', 'there', 'to', 'when', 'a', 'b', 'c', 'd', 'e']

    for i in words:
        i = str(i)
        if bf_title.exists(i):
            print('data: <{}> exist'.format(i))
            continue
        bf_title.add(i)
        print('data: <{}> added, data_size: <{}>'.format(i, bf_title.data_saved))

    # test len, and in
    print('data_size of bloom_filter: <{}>'.format(len(bf_title)))
    print('is xixi in bloom_filter: ', 'xixi' in bf_title)
    print('is where in bloom_filter: ', 'where' in bf_title)


if __name__ == '__main__':
    main_multi_filter()
    # main_scrapy_single_node()



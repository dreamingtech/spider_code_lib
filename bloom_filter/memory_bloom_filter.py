# -*- coding: utf-8 -*-
# 基于内存的布隆过滤器
# memory based bloom filter

import math
import bitarray
import mmh3


class BloomFilterMemory(object):
    """基于内存的布隆过滤器"""

    def __init__(self, bf_config):
        """
        初始化布隆过滤器
        - bf_config 中包含的内容
          - data_size_per_key: 期望向每个 key 中保存的数据量
          - memory_size: 每个 filter/bitarray 使用的内存量
          - hash_seeds_num: hash 种子的数量
          - error_rate_threshold: 误判率的最大值
        :param bf_config: bloom filter 配置信息
        """
        # 每一个 bitarray/bitmap 中要存放的数据量
        self.data_size_per_filter = bf_config.get("data_size_per_filter")
        # bloom 过滤器 使用的内存量
        memory_size = bf_config.get("memory_size")
        # hash 种子数量
        self.hash_seeds_num = bf_config.get("hash_seeds_num")
        # 误判率阈值, 保证给定的 data_size, hash_num, bit_size 计算得到的 error_rate 小于给定的 error_rate_threshold
        self.error_rate_threshold = bf_config.get("error_rate_threshold")

        if not (isinstance(self.data_size_per_filter, int) and self.data_size_per_filter > 0):
            raise ValueError("data_size must be integer and greater than 0")
        if not (0 < self.error_rate_threshold < 1):
            raise ValueError("error_rate_threshold must be between 0 and 1")
        if not (isinstance(memory_size, int) and memory_size > 0):
            raise Exception('memory_size must be integer and larger than 0')

        # bit 位的长度
        self.bit_size = memory_size * 1024 * 1024 * 8

        # 计算误判率
        self.error_rate = self._cal_error_rate()
        # 检查给定的参数计算得到的误判率 error_rate 能否小于误判率阈值 error_rate_threshold
        self._check_error_rate()

        # bitarray, 用来保存布隆过滤器的 hash 索引值
        self._bitarray = None
        # 因为 bitarray 的数量可能会增加, 故要定义列表保存所有的 bitarray
        self._filter_list = []
        # 初始化 bitarray, 必须要手动初始化 bitarray, 否则在 add 中添加数据时, 因为 _filter_list 为 0,
        # self.data_saved >= self.data_size_per_filter * len(self._filter_list) 是恒成立的
        self._init_bitarray()

        # 计算一个 memory_size 能够保存的 data_size
        self.max_data_size = self._cal_max_data_size()

        # 获取多个 hash 种子, 保存到一个列表中
        self._hash_func_list = self.get_hash_seeds()

        # 已存入 hash map 中的数据量
        self.data_saved = 0

    def _cal_error_rate(self):
        """
        通过传入的数据量 data_size (n), 内存量 bit_size (m), hash 种子数量 hash_seeds_num (k), 计算出能够达到的 误判率 (p)
        n 为数据量          p 为误报率
        k 为哈希种子个数    m 为 bit 位长度
        n = ceil(m / (-k / log(1 - exp(log(p) / k))))
        p = pow(1 - exp(-k / (m / n)), k)
        m = ceil((n * log(p)) / log(1 / pow(2, log(2))))
        k = round((m / n) * log(2))
        计算公式来自: https://hur.st/bloomfilter/
        """
        n = self.data_size_per_filter
        k = self.hash_seeds_num
        m = self.bit_size
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
        m = self.bit_size
        p = self.error_rate_threshold
        n = math.ceil(m / (-k / math.log(1-math.exp(math.log(p) / k))))
        return n

    def _init_bitarray(self):
        """初始化 bit array"""
        # bitarray([initial], [endian=string])
        # 如果传入的参数为 int, 就返回 bit_size 长度的 bitarray, 但是其中的值是随机的
        self._bitarray = bitarray.bitarray(self.bit_size)
        # 把 bitarray 中的所有值都设置为 0
        self._bitarray.setall(0)
        # 把生成的 bitarray 添加到 列表中
        self._filter_list.append(self._bitarray)

    def _check_and_add_new_filter(self):
        """
        检查 布隆过滤器 中已经保存的 数据量 data_saved 是否大于 每个 bitarray 中要保存的数据量 data_size_per_filter,
        如果大于, 就增加一个新的过滤器, 直接把新增的过滤器添加到 _filter_list 列表中,
        在 add 数据时, 向 _filter_list 中最后一个元素 即最新添加的 bitarray 中添加数据
        在 判断时, 要对 _filter_list 中所有的 bitarray 进行判断
        """
        if self.data_saved >= self.max_data_size * len(self._filter_list):
            print('max data_size reached, add one more bitarray. data_size: {}'.format(self.data_saved))
            self._init_bitarray()

    def _safe_data(self, data):
        """
        把传入的 data 转换为 str 类型
        mmh3.hash 只能对 str, bytes-like obj 进行 hash 计算
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
        # 将哈希种子固定为 [1, 2, 3 , ... ,hash_num]
        _seeds = [_i for _i in range(1, self.hash_seeds_num + 1)]
        return _seeds

    def get_hash_indexes(self, data):
        """
        计算一个给定的数据 data 使用所有的 hash_funcs 得到的在 bitarray 中的索引值 / offset 值
        """
        # 把 str 数据转换为 bytes
        data = self._safe_data(data)
        _hash_indexes = [mmh3.hash(data, self._hash_func_list[_i]) % self.bit_size for _i in range(self.hash_seeds_num)]
        return _hash_indexes

    def add(self, data):
        """
        向布隆过滤器中添加数据
        :param data: 要添加的数据
        """
        # 在每次向 bloom_filter 中添加数据时, 都先判断一下 已经保存的数据量,
        # 如果 已保存数据量 达到 每个 filter 所能保存的最大值, 就增加一个新的 filter
        self._check_and_add_new_filter()

        # get_hash_indexes 获取所有 hash 种子对应的 hash 索引值 / offset 值
        for _hash_index in self.get_hash_indexes(data):
            self._bitarray[_hash_index] = 1

        # 保存的数据量加 1
        self.data_saved += 1

    def _is_exists_in_certain_filter(self, data, _filter):
        """
        检查给定的值 data 是否存在于某个特定的 bitarray 中
        对每一个 hash 种子计算 给定的 data 的 index 值, 或称索引值, 偏移量,
        只要有一个 hash 种子计算得到的 index 不在 bitarray 中, 就说明这个 data 绝对不存在
        如果所有 hash 种子计算得到的 index 在 bitarray 中都存在, 在一定的误判率下, 就认为这个 data 存在
        """
        # 获取所有种子计算得到的 索引值
        hash_indexes = self.get_hash_indexes(data)
        # 对所有的索引值进行过滤
        for _hash_index in hash_indexes:
            # 只要有一个 _hash_index 对应的 bit 位上的索引值不 为 0, 就肯定不存在, 就返回 False
            if not _filter[_hash_index]:
                return False
        # 当所有的索引值对应的 bit 位上的值都为 1 时, 就认为 data 值已经存在
        return True

    def exists(self, data):
        """
        对 _filter_list 中所有的 bitarray 进行遍历,
        检测数据是否在某一个 bitarray 中存在
        """
        for _filter in self._filter_list:
            _is_exists = self._is_exists_in_certain_filter(data, _filter)
            # 只要 数据在某一个 _filter/bitarray 中存在, 就返回 True
            if _is_exists:
                return True
        # 如果所有的 bitarray 都检测过, 并且都不存在, 才返回 False
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
    """ 测试生成多个 bitarray filter """
    import time
    # 以下面的参数, 每个 filter 中可以保存 42 个数据
    # 测试时需要把 data_size_per_key 设置的尽可能的小, 否则, 计算出来的误判率很可能会超过阈值
    bf_config = dict(
        data_size_per_filter=20,
        memory_size=1,
        hash_seeds_num=2,
        error_rate_threshold=1e-10
    )
    bf = BloomFilterMemory(bf_config)
    print('params used can reach a error_rate of <{}>'.format(bf.error_rate))
    print('params used can save <{}> data in one filter'.format(bf.max_data_size))

    for i in range(50):
        if bf.exists(i):
            print('data: <{}> exist'.format(i))
            continue
        bf.add(i)
        time.sleep(0.3)
        print('data: <{}> added, data_size: <{}>'.format(i, bf.data_saved))

    for i in range(100):
        if bf.exists(i):
            print('data: <{}> exist'.format(i))
            continue
        bf.add(i)
        time.sleep(0.3)
        print('data: <{}> added, data_size: <{}>'.format(i, bf.data_saved))


def main_scrapy_single_node():
    """
    用于 scrapy 单个爬虫节点中的内存型布隆过滤器,
    多个站点的爬虫, 每隔几分钟到一个小时会对每个站点重新抓取一遍, 有很多重复的 url,
    故先对本节点中的 url 种子进行一遍过滤, 能够大大的减少 redis 版布隆过滤器的压力
    """
    import time
    bf_config = dict(
        data_size_per_filter=10 ** 7,
        memory_size=100,
        hash_seeds_num=5,
        error_rate_threshold=1e-6
    )
    bf = BloomFilterMemory(bf_config)

    print('params used can reach a error_rate of <{}>'.format(bf.error_rate))
    print('params used can save <{}> data in one filter'.format(bf.max_data_size))

    words = ['when', 'how', 'where', 'too', 'there', 'to', 'when', 'a', 'b', 'c', 'd', 'e']

    for i in words:
        i = str(i)
        if bf.exists(i):
            print('data: <{}> exist'.format(i))
            continue
        bf.add(i)
        time.sleep(0.3)
        print('data: <{}> added, data_size: <{}>'.format(i, bf.data_saved))

    # test len, and in
    print('data_size of bloom_filter: <{}>'.format(len(bf)))
    print('is xixi in bloom_filter: ', 'xixi' in bf)
    print('is where in bloom_filter: ', 'where' in bf)


if __name__ == '__main__':
    # main_multi_filter()
    main_scrapy_single_node()

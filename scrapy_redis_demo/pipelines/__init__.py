# -*- coding: utf-8 -*-
# 自定义 item 保存到 redis 中的 redis_key
# 默认的 redis_key 是以 spider.name 进行拼接的, 如 items:jianshu, items:eastday
# 想要以 表来保存 item, 如 items:jianshu 保存到 demo 表中, items:eastday 保存到 news 表中
# 在 spider 中解析时在 item 中添加 table 字段, 使用此 pip, 就能保存到对应的 redis_key 中
from scrapy_redis.pipelines import RedisPipeline


class CustomKeyRedisPipeline(RedisPipeline):

    def item_key(self, item, spider):
        """Returns redis key based on given spider.

        Override this function to use a different key depending on the item
        and/or spider.

        """
        if 'table' in item:
            return self.key % {'spider': item.pop('table')}
        return self.key % {'spider': spider.name}


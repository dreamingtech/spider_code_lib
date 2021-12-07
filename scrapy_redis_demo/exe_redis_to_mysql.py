# -*- coding: utf-8 -*-
# 从 redis 中读取出 items, 使用 aiomysql 异步批量保存到 mysql 中
import argparse
import re
import json
import asyncio

import redis
import aiomysql

from utils import get_logger
from utils.project import get_project_settings

logger = get_logger(re.split(r"[/.\\]", __file__)[-2])


class RedisToMysql(object):

    def __init__(self, params):
        """
        :param params: 从 cmd 中获取的参数
        """
        self.params = params
        settings = get_project_settings(params["config_name"])

        mysql_configs = settings.get('MYSQL_CONFIGS', {})
        redis_config = settings.get('REDIS_CONFIG')

        if not mysql_configs or not redis_config:
            raise Exception("no MYSQL_CONFIGS or REDIS_CONFIG in settings")

        self.mysql_configs = mysql_configs
        self.redis_config = redis_config
        # 更新 redis_config, 设置 decode_response 为 True
        self.redis_config.update({"decode_responses": True, "retry_on_timeout": True})

        self.redis_cli = None

        # batch_size: 每次从 reids 中取出来多少保存到 mysql 中
        self.batch_size = params['batch_size']

        # 保存到 mysql 中的字段
        # 为了能够使用 executemany 一次性保存多条记录, 这些数据必须要整合为统一的结构
        # 以下就是每个表中要保存的字段
        columns_demo = ['url', 'url_id', 'content', 'crawl']
        columns_news = ['url', 'url_id', 'content', 'crawl']

        # 因为要保存到多个 mysql 数据库中, 所以这里要保存多个 mysql 的连接对象
        self.conn_pools = {}

        # redis_key 和 column 的对应关系
        # 一个 redis_key 保存到一张表中
        self.table_columns_mapping = {
            "items:demo": columns_demo,
            "items:news": columns_news,
        }

    def _get_redis_cli(self, redis_config: dict):
        self.redis_cli = redis.StrictRedis(**redis_config)
        # self.redis_cli = redis.from_url(self.redis_url)

    def _check_redis_cli(self):
        """
        检测 redis_cli, 如果没有连通, 就再次获取
        :return:
        """
        if not self.redis_cli.ping():
            try:
                self.redis_cli.close()
            except Exception as e:
                pass
            self._get_redis_cli(redis_config=self.redis_config)

    @staticmethod
    async def get_conn_pool(mysql_config: dict):
        """
        获取 mysql 连接池
        :param mysql_config:
        :return:
        """
        conn_pool = await aiomysql.create_pool(**mysql_config)
        if conn_pool:
            return conn_pool
        else:
            raise Exception(f"connect to mysql error. mysql: {mysql_config}")

    async def redis_to_mysql(self):
        """
        从 redis 中读取出所有的 items
        redis 是使用 rpush 保存 item 到数据库的, 取数据时就需要使用 lpop 来到数据了
        :return:
        """
        if self.redis_cli is None:
            self._get_redis_cli(redis_config=self.redis_config)

        self.redis_cli: redis.StrictRedis

        # 获取 redis 中所有的 item_key, 遍历, 读取, 保存到 mysql 中
        item_keys = self.redis_cli.keys(pattern="items:*")

        # 过滤出 table_columns_mapping 中的 定义的 item_keys
        item_keys = [k for k in item_keys if k in self.table_columns_mapping.keys()]

        if not item_keys:
            logger.info("no item key found, return")
            return

        # 对 item_keys 进行排序, 从数量最多的 key 开始读取
        # 参考: https://stackoverflow.com/questions/6618515/sorting-list-based-on-values-from-another-list
        item_key_length = [self.redis_cli.llen(item_key) for item_key in item_keys]
        item_keys = [x for y, x in sorted(zip(item_key_length, item_keys), reverse=True)]
        item_key_length = [y for y, x in sorted(zip(item_key_length, item_keys), reverse=True)]

        # 因为要把数据保存到 多个 mysql 库中, 必须要先遍历 item_keys, 取出来 items, 再遍历 mysql 数据库保存数据
        for index, item_key in enumerate(item_keys):

            logger.info(f"save items of to table [{item_key.split(':')[-1]}]. length: [{item_key_length[index]}]")
            # items:demo, items:news
            table_name = item_key.split(":")[-1]
            self._check_redis_cli()

            # 外层 while 循环判断这个 item_key 的长度是否为 0
            # 内层 for 循环从 redis 中的 item_key 中读取出 batch_size 个元素
            # 如果内层 for 循环没有读取到数据, 就会跳出 for 循环,
            # 同时 外层 while 循环的条件也不再满足, 就能正常的结束了
            while self.redis_cli.llen(item_key):

                items = []

                for i in range(self.batch_size):
                    item = self.redis_cli.lpop(item_key)
                    if not item:
                        logger.info(f"no items in redis_key: [{item_key}], continue to next")
                        break
                    else:
                        items.append(json.loads(item))

                # 只有在数据不为空时才执行保存的操作
                if len(items):

                    # 因为要同时保存到 多个 mysql 数据库中, 所以 weather_spider_settings.py 中的
                    # MYSQL_CONFIGS_DEV 和 MYSQL_CONFIGS_PRO 中设置多个 mysql, 同时保存到所有这些库中
                    for mysql_name, mysql_config in self.mysql_configs.items():

                        logger.info(f'save items to mysql: [{mysql_name}]')

                        # 因为可能要保存到多个数据库的多个表中, 需要保存所有数据库的 conn_pool
                        if mysql_name not in self.conn_pools:
                            conn_pool = await self.get_conn_pool(mysql_config=mysql_config)
                            self.conn_pools[mysql_name] = conn_pool
                        else:
                            conn_pool = self.conn_pools[mysql_name]

                        conn_pool: aiomysql.Pool

                        await self.save_items_to_mysql(
                            conn_pool, items, table_name, columns=self.table_columns_mapping[item_key])

    async def save_items_to_mysql(self, conn_pool, items, table_name, columns):
        """
        把 items 保存到 mysql 中
        """
        # 把 list of dict 转换为 list of list
        data = [[_i.get(col) for col in columns] for _i in items]

        async with conn_pool.acquire() as conn:
            conn: aiomysql.Connection
            await conn.ping(reconnect=True)
            async with conn.cursor() as cur:

                result = 0
                # https://stackoverflow.com/questions/2714587/mysql-on-duplicate-key-update-for-multiple-rows-insert-in-single-query
                # 向数据库插入数据
                sql = "INSERT INTO `{}` ({}) VALUES ({}) ON DUPLICATE KEY UPDATE {}".format(
                    table_name,
                    ','.join(['`%s`' % col for col in columns]),
                    # *号将列表内的值扩展到至N个
                    ','.join(['%s'] * len(columns)),
                    ','.join('`{}`=VALUES(`{}`)'.format(col, col) for col in columns)
                )
                try:
                    result = await cur.executemany(sql, data)
                except Exception as e:
                    logger.warning(f'error save items to table: [{table_name}], retry. error: [{e}]')
                    try:
                        result = await cur.executemany(sql, data)
                    except Exception as e:
                        logger.error(f'error save items to table: [{table_name}]. error: [{e}]')
                await conn.commit()

                logger.info(f"save [{len(items)}] item to table [{table_name}] affected rows: [{result}]")

    async def run(self):

        logger.info("start to save items to mysql")
        await self.redis_to_mysql()


def get_parser():
    """
    由于要捕捉 cmd 传递的参数, 所以必须要使用 函数,  不能使用类
    :return:
    """
    logger.info("get arg parser from cmd")
    parser = argparse.ArgumentParser(description="generate report cost spider seeds")

    # 1. ---------- project -----------
    # 要运行哪个项目, 即 scrapy.cfg 中的 project 中的 设置 demo_dev, demo_dev 等
    parser.add_argument("--project", "-p", type=str, required=True,
                        help="settings of project")

    parser.add_argument("--batch_size", "-bs", type=int, required=False, default=1000,
                        help="batch items get from redis")

    return parser


def parse_params(parser: argparse.ArgumentParser):
    """
    解析 argparse 中传递过来的参数
    """
    logger.info("parse params from arg parser")

    args = parser.parse_args()

    params = dict(
        config_name=args.project,
        batch_size=args.batch_size,
    )

    return params


async def main():

    params = parse_params(get_parser())

    rtm = RedisToMysql(params=params)
    await rtm.run()


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

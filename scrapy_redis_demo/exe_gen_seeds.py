# -*- coding: utf-8 -*-
# 生成种子并保存到 redis 中
# python exe_gen_seeds.py -p demo_dev -s jianshu
# python exe_gen_seeds.py -p news_dev -s eastday

import argparse
import logging
import re
import types


import scrapy
from scrapy_redis.scheduler import Scheduler

from utils.project import get_project_settings
from utils import get_logger

logger = get_logger(re.split(r"[/.\\]", __file__)[-2])


class SeedsScheduler(Scheduler):

    def next_request(self):
        """
        重写 Scheduler 调度器 的 next_request 方法, 不进行任务操作
        这样, 在 scrapy engine 调用 Scheduler.next_request 方法时, 就不会从 redis 中取出来保存的种子
        scrapy.core.engine.ExecutionEngine._next_request_from_scheduler
        :return:
        """
        pass


# SeedsSpider, 用于模拟 scrapy-redis.Spider 生成 Request 并发送到 redis 中
class SeedsSpider(object):
    def __init__(self, settings, name):
        """
        爬虫名, 模拟 scrapy.Spider 的 self.name,
        通过实例化时传参来生成不同的爬虫
        :param settings: scrapy.cfg 中的配置项
        :param name: 爬虫名
        """
        self.name = name
        self.settings = settings
        self._set_scheduler()

    def _set_scheduler(self):
        """
        给 spider 设置调度器
        从 settings 生成 scheduler 对象
        读取 settings 配置信息, 赋值给 Scheduler 类并返回 scheduler 对象
        """
        # 调用 Scheduler.from_settings 生成 scheduler 调度器对象
        self.scheduler = SeedsScheduler.from_settings(self.settings)
        self.scheduler.open(self)
        self.server = self.scheduler.server

    @property
    def logger(self):
        """
        复制自 scrapy.spiders.Spider.logger
        因为这里的 SeedsSpider 并没有继承 scrapy.Spider,
        所以就不具备 scrapy.Spider 的大部分方法和属性
        在 self.scheduler.open(self) > 调用 scrapy_redis/scheduler.py 的如下代码时
        spider.log("Resuming crawl (%d requests scheduled)" % len(self.queue))
        就会报错, 没有 log 方法
        :return:
        """
        return logging.LoggerAdapter(logging.getLogger(self.name), {'spider': self})

    def log(self, message, level=logging.DEBUG, **kw):
        self.logger.log(level, message, **kw)

    def parse(self):
        pass

    def set_parse_func(self, parse_func):
        """
        给 seeds_spider 动态设置 方法
        """
        if not hasattr(self, parse_func):
            bound_method = types.MethodType(lambda self: self, self)
            setattr(self, parse_func, bound_method)


class SeedsGenerator(object):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    def __init__(self, params: dict):
        self.params = params
        self.settings = get_project_settings(settings_name=params["project"])
        self.spider = SeedsSpider(settings=self.settings, name=params['spider'])

        self.total_seeds_generated = 0

    def do_gen_seeds(self, url, parse_func='parse', priority=100, handle_all=True):

        logger.info(f'do gen {self.spider.name} seeds')

        if not hasattr(self.spider, parse_func):
            self.spider.set_parse_func(parse_func)

        r = scrapy.Request(
            url=url,
            headers=self.headers,
            callback=getattr(self.spider, parse_func),
            dont_filter=True,
            priority=priority,
            meta={
                "handle_httpstatus_all": handle_all,
            }
        )

        self.spider.scheduler.enqueue_request(r)
        self.total_seeds_generated += 1

    def gen_seeds(self):
        logger.info(f"start to gen requests for spider: [{self.spider.name}]")

        if self.spider.name == 'hao123':
            url = 'http://www.hao123.com/'
            self.do_gen_seeds(url=url, handle_all=False)

        elif self.spider.name == 'jianshu':
            url = 'https://www.jianshu.com/'
            self.do_gen_seeds(url=url)

        elif self.spider.name == 'eastday':
            url = 'http://mini.eastday.com/'
            self.do_gen_seeds(url=url)

        elif self.spider.name == 'sogou':
            url = 'https://news.sogou.com/'
            self.do_gen_seeds(url=url)
        else:
            raise Exception(f'unsupported spider: {self.spider.name}')

        logger.info(f'total [{self.total_seeds_generated}] seeds generated for spider: [{self.spider.name}]')


def get_parser():
    """
    由于要捕捉 cmd 传递的参数, 所以必须要使用 函数,  不能使用类
    :return:
    """
    logger.info("get arg parser from cmd")
    parser = argparse.ArgumentParser(description="sync account infos")

    # 1. ---------- project -----------
    parser.add_argument("--project", "-p", type=str, required=True,
                        help="settings of project")

    # 2. ---------- spider -----------
    parser.add_argument("--spider", "-s", type=str, required=True,
                        help="spider to run")

    return parser


def parse_params(parser: argparse.ArgumentParser):
    """
    解析 argparse 中传递过来的参数
    """
    logger.info("parse params from arg parser")

    args = parser.parse_args()

    params = dict(
        project=args.project,
        spider=args.spider,
    )

    return params


def main():
    params = parse_params(get_parser())

    sg = SeedsGenerator(params=params)
    sg.gen_seeds()


if __name__ == '__main__':
    main()

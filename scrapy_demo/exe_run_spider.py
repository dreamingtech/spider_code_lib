# -*- coding: utf-8 -*-
import argparse

from scrapy.utils.log import configure_logging
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner, CrawlerProcess
from scrapy.commands import ScrapyCommand

from utils.project import get_project_settings


class RunSpiderProcess(ScrapyCommand):

    requires_project = True
    default_settings = {'LOG_ENABLED': True}

    def __init__(self, params):
        super().__init__()
        self.params = params
        self.settings = get_project_settings(settings_name=params['project'])
        # scrapy/cmdline.execute:144
        self.crawler_process = CrawlerProcess(self.settings)

    def short_desc(self):
        return "run spiders"

    def run(self, args, opts=None):
        spider_loader = self.crawler_process.spider_loader

        for spidername in args or spider_loader.list():
            # 把 self.params 也传递进去, 以对 spider 进行进一步的定制操作, 如添加抓取时间等
            self.crawler_process.crawl(spidername, **self.params)

        self.crawler_process.start()


class RunSpiderRunner(ScrapyCommand):

    requires_project = True
    default_settings = {'LOG_ENABLED': True}

    def __init__(self, params):
        self.params = params
        super().__init__()
        self.settings = get_project_settings(settings_name=params['project'])
        # scrapy/cmdline.execute:144
        self.crawler_process = CrawlerProcess(self.settings)

    def short_desc(self):
        return "run spiders"

    def run(self, args, opts=None):

        spider_loader = self.crawler_process.spider_loader
        configure_logging(self.settings)
        runner = CrawlerRunner(self.settings)

        @defer.inlineCallbacks
        def crawl():
            for spidername in args or spider_loader.list():
                spidercls = spider_loader.load(spidername)
                # 把 self.params 也传递进去, 以对 spider 进行进一步的定制操作, 如添加抓取时间等
                yield runner.crawl(spidercls, **self.params)
            reactor.stop()

        crawl()
        reactor.run()


def get_parser():

    parser = argparse.ArgumentParser(description="start weixin_mini spider")

    # settings_name
    parser.add_argument("--project", "-p", type=str, required=False, default="default",
                        help="settings of project")
    # spider_names
    # 可以同时运行一个项目中的多个 spider
    parser.add_argument("--spiders", "-s", type=str, required=False, nargs='+', default=[],
                        help="spiders to run")
    return parser


def parse_params(parser: argparse.ArgumentParser):
    args = parser.parse_args()

    if args.project is None:
        raise Exception("settings must not be None")

    params = dict(
        project=args.project,
        spiders=args.spiders,
    )

    return params


def main_process():
    # 1. 获取 cmd 中传入的参数
    parser = get_parser()
    # 2. 从 parser 中解析出来参数
    params = parse_params(parser)
    rsp = RunSpiderProcess(params)
    rsp.run(params['spiders'])


def main_runner():
    # 1. 获取 cmd 中传入的参数
    parser = get_parser()
    # 2. 从 parser 中解析出来参数
    params = parse_params(parser)
    rsr = RunSpiderRunner(params)
    rsr.run(params['spiders'])


if __name__ == '__main__':
    # main_process()
    main_runner()


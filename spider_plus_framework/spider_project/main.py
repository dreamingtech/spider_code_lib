# coding=utf-8

from spider_plus.core.engine import Engine  # 导入引擎
# from spiders.baidu import BaiduSpider
# from spiders.qiubai import QiubaiSpider
# from pipelines import BaiduPipeline, QiubaiPipeline, MysqlPipeline
# from spider_middlewares import TestSpiderMiddleware1, TestSpiderMiddleware2
# from downloader_middlewares import TestDownloaderMiddleware1, TestDownloaderMiddleware2

if __name__ == '__main__':
    # baidu = BaiduSpider()  # 实例化爬虫对象
    # qiubai = QiubaiSpider()  # 实例化爬虫对象
    # spiders = {baidu.name: baidu, qiubai.name: qiubai}
    # pipelines = [BaiduPipeline(), QiubaiPipeline(), MysqlPipeline()]  # 注意这里导入的是实例, 而不是类对象, 因为类对象无法使用实例方法, 也就无法调用 process_item 来处理数据
    # spider_mids = [TestSpiderMiddleware1(), TestSpiderMiddleware2()]  # 多个爬虫中间件
    # downloader_mids = [TestDownloaderMiddleware1(), TestDownloaderMiddleware2()]  # 多个下载中间件
    # engine = Engine(spiders, pipelines, spider_mids, downloader_mids)  # 创建引擎对象, 传入爬虫对象
    engine = Engine()  # 创建引擎对象
    engine.start()  # 启动引擎

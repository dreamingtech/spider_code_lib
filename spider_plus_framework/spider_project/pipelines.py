# coding=utf-8
from spiders.baidu import BaiduSpider
from spiders.qiubai import QiubaiSpider
from spiders.sina import SinaSpider


class BaiduPipeline(object):
    '''处理百度爬虫的管道'''

    def process_item(self, item, spider):
        '''
        处理item
        :param item: 爬虫文件中提取的数据
        :param spider: 传递item过来的爬虫, 以对item进行区分
        :return: item
        '''
        if isinstance(spider, BaiduSpider):
            print("百度管道处理的数据：", item.data)
        return item  # 最后必须返回item, 以便其它管道文件能够接收并处理

        # if spider.name = "baidu":
        #     # 对百度的item数据进行处理
        #     print("百度爬虫的数据", item.data)
        # return item


class QiubaiPipeline(object):
    '''处理糗百的数据的管道'''

    def process_item(self, item, spider):
        '''
        处理item
        :param item: 爬虫文件中提取的数据
        :param spider: 传递item过来的爬虫, 以对item进行区分
        :return: item
        '''
        if isinstance(spider, QiubaiSpider):
            print("糗百管道处理的数据：", item.data)
        return item  # 最后必须返回item


class SinaPipeline(object):
    '''处理糗百的数据的管道'''

    def process_item(self, item, spider):
        '''
        处理item
        :param item: 爬虫文件中提取的数据
        :param spider: 传递item过来的爬虫, 以对item进行区分
        :return: item
        '''
        if isinstance(spider, SinaSpider):
            print("新浪管道处理的数据：", item.data)
        return item  # 最后必须返回item

class MysqlPipeline(object):
    '''把数据写入到mysql数据库中'''

    def process_item(self, item, spider):
        print("把数据写入到mysql数据库", spider.name)
        return item
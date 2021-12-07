# coding=utf-8
# 管道


class Pipeline(object):
    '''完成对管道对象的封装'''

    def process_item(self, item):
        '''
        实现对item对象的处理
        :param item: item对象
        :return:
        '''
        # print("item: ", item)
        print("item: ", item.data)
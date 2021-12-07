# coding=utf-8


class Item(object):
    """完成对item对象的封装"""

    def __init__(self, data):
        '''
        初始化item
        :param data: 数据
        '''
        self._data = data

    @property  # 让data属性变成只读
    def data(self):
        return self._data


if __name__ == '__main__':
    item = Item({"name": "frank"})
    # print(item.data)
    # 不允许重新赋值
    # item.data = 20
    item.data["hello"] = "world"
    print(item.data)

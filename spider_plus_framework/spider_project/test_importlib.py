import importlib
from spider_plus.item import Item
from spiders.baidu import BaiduSpider

PIPELINES = [
    'pipelines.BaiduPipeline',
    'pipelines.QiubaiPipeline',
    'pipelines.MysqlPipeline'
]

for pipeline in PIPELINES:
    module_name = pipeline.split(".")[0]  # 模块的名字, 路径
    print(module_name)
    cls_name = pipeline.split(".")[-1]  # 类名
    print(cls_name)
    module = importlib.import_module(module_name)  # 导入模块
    print(module)
    cls = getattr(module, cls_name)  # 获取module下的类
    print(cls)
    cls().process_item(Item("abc"), BaiduSpider())  # 通过类的实例, 就能调用类的方法

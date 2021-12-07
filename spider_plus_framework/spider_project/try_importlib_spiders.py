import importlib

SPIDERS = [
    'spiders.baidu.BaiduSpider',
    'spiders.qiubai.QiubaiSpider'
]

for spider in SPIDERS:
    module_name = spider.rsplit(".",1)[0]  # 模块的名字, 路径
    print(module_name)
    cls_name = spider.rsplit(".",1)[-1]  # 类名
    print(cls_name)
    module = importlib.import_module(module_name)  # 导入模块
    print(module)
    cls = getattr(module, cls_name)  # 获取module下的类
    print(cls().name)

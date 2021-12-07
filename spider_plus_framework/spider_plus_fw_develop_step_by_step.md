## 新建项目

新建目录spider_plus_fw, 保存所有项目

设计代码结构
首先给框架起一个名称, 如: 

spider_plus

## 继续分类以及解耦的设计思想: 

把核心模块放置在一起
请求对象模块和响应对象模块统一作为http模块
数据对象单独作为一个分类

新建python包 spider_plus_fw/spider_plus 

新建python包 spider_plus/core
新建python包 spider_plus/http

-- spider_plus
  -- __init__.py
  -- core
    -- __init__.py
    -- spider.py
    -- scheduler.py
    -- downloader.py
    -- pipeline.py
    -- engine.py
  -- http
    -- __init__.py
    -- request.py
    -- response.py
  -- item.py


## 完成HTTP相关模块的封装

### 完成request模块的基础封装

```python
# spider_plus/http/request.py

# coding=utf-8


class Request(object):
    """完成请求对象的封装"""

    def __init__(self, url, method="GET", headers=None, params=None, data=None):
        '''
        初始化request对象
        :param url: url地址
        :param method: 请求方法
        :param headers:请求头
        :param params: 请求的参数, 查询字符串
        :param data: 请求体, 表单数据
        '''
        self.url = url
        self.method = method
        self.headers = headers
        self.params = params
        self.data = data
```


### 完成respons模块的封装

```python
# spider_plus/http/response.py

# coding=utf-8

class Response(object):
    """完成响应对象的封装"""

    def __init__(self, url, body, headers, status_code):
        '''
        初始化response对象
        :param url: 响应的url地址
        :param body: 响应体
        :param headers: 响应头
        :param status_code: 状态码
        '''
        self.url = url
        self.body = body
        self.headers = headers
        self.status_code = status_code
```

## item对象的封装

```python
# spider_plus/item.py

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
```


## 对5个核心模块进行封装

### spider模块

1.1 爬虫组件功能: 
构建请求信息(初始的), 也就是生成请求对象(Request)
解析响应对象, 返回数据对象(Item)或者新的请求对象(Request)

1.2 实现方案: 
实现 start_requests 方法, 返回请求对象
实现parse方法, 返回Item对象或者新的请求对象

```python
# spider_plus/core/spider.py


# coding=utf-8
from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.item import Item  # 导入Item对象


class Spider(object):
    '''完成对spider的封装'''
    start_url = 'http://www.baidu.com'  # 爬虫最开始请求的url地址, 默认初始请求地址, 这里以请求百度首页为例

    def start_requests(self):
        '''
        构建start_url地址的初始请求对象并返回
        :return: request对象
        '''
        return Request(self.start_url)

    def parse(self, response):
        '''
        默认处理start_url地址对应的响应
        :param response: response响应对象
        :return: item数据或者是request对象
        '''
        return Item(response.body)  # 返回item对象
```

### 调度器模块的封装

2.1 调度器功能: 
缓存请求对象(Request), 并为下载器提供请求对象, 实现请求的调度: 
对请求对象进行去重判断: 实现去重方法 _filter_request, 该方法对内提供, 因此设置为私有方法

2.2 实现方案: 
利用先进先出队列 FIFO 存储请求；
实现 add_request 方法添加请求, 接收请求对象作为参数；
实现 get_request 方法对外提供从队列取出的请求对象

```python

# spider_plus/core/scheduler.py

'''调度器模块封装'''
# 利用six模块实现py2和py3兼容
from six.moves.queue import Queue


class Scheduler(object):
    '''完成调试器模块的封装'''
    def __init__(self):
        self.queue = Queue()

    def add_request(self, request):
        '''
        添加request到队列中
        :param request: 请求对象
        :return: None
        '''
        # 调用 _filter_request 来实现对请求对象的去重
        # self._filter_request(request)
        self.queue.put(request)

    def get_request(self):
        '''
        获取队列中的request对象
        :return: 请求对象
        '''
        request = self.queue.get()
        return request

    def _filter_request(self, request):
        '''
        对请求对象进行去重
        :param request: 请求对象
        :return: bool
        '''
        pass
```

### 下载器模块

3.1 下载器功能: 
根据请求对象(Request), 发起 HTTP、HTTPS 网络请求, 拿到 HTTP、HTTPS 响应, 构建响应对象(Response)并返回

3.1 实现方案: 
利用 requests、urllib2 等模块发请求, 这里使用 requests 模块
实现 get_response 方法, 接收 request 请求对象作为参数, 发起请求, 获取响应

```python
# spider_plus/core/downloader.py

# coding=utf-8
# 下载器

import requests
from spider_plus.http.response import Response


class Downloader(object):
    '''完成对下载器对象的封装'''

    def get_response(self, request):
        '''
        接收请求对象, 发送请求, 获取响应
        :param request: 请求对象
        :return: response响应对象
        '''
        if request.method.upper() == 'GET':
            resp = requests.get(request.url, headers=request.headers, params=request.params)
        elif request.method.upper() == 'POST':
            resp = requests.post(request.url, headers=request.headers, params=request.params, data=request.data)
        else:
            # 如果方法不是get或者post, 抛出一个异常
            raise Exception("不支持的请求方法: <{}>".format(request.method))
        # 2. 构建响应对象,并返回
        return Response(url=resp.url, body=resp.content, headers=resp.headers, status_code=resp.status_code)
```

### 管道模块

4.1 管道组件功能: 
负责处理数据对象

4.2 实现方案: 
实现 process_item 方法, 接收数据对象作为参数

```python
# spider_plus/core/pipeline.py

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
        print("item: ", item)
```


### 引擎模块

```python
# spider_plus/core/engine.py

# coding=utf-8
# 引擎
from spider_plus.http.request import Request  # 导入Request对象

from .scheduler import Scheduler
from .downloader import Downloader
from .pipeline import Pipeline
from .spider import Spider


class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        self.spider = Spider()  # 接收外部传入的爬虫对象
        self.scheduler = Scheduler()  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipeline = Pipeline()  # 初始化管道对象

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        self._start_engine()

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        start_request = self.spider.start_requests()
        # 2. 调用调度器的add_request方法, 添加request对象到调度器中
        self.scheduler.add_request(start_request)
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)
        # 5. 利用爬虫的parse方法, 处理响应
        result = self.spider.parse(response)
        # 6. 判断结果的类型
        # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
        if isinstance(result, Request):
            self.scheduler.add_request(result)
        # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
        else:
            self.pipeline.process_item(result)


if __name__ == '__main__':
    engine = Engine()
    engine.start()
```

## 安装框架
安装框架的目的
利用setup.py将框架安装到python环境中, 在编写爬虫时候, 作为第三方模块来调用, 

### 1. 框架安装第一步: 完成setup.py的编写

以下代码相当于一个模板, 只用更改name字段出, 改为对应的需要安装的模块名称就可以, 比如这里是: spider_plus

将setup.py文件放到spider_plus的同级目录下

```python
# spider_plus_fw/setup.py

from os.path import dirname, join
# from pip.req import parse_requirements

from setuptools import (
    find_packages,
    setup,
)

def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]

with open(join(dirname(__file__), './VERSION.txt'), 'rb') as f:
    version = f.read().decode('ascii').strip()

setup(
    name='spider_plus',  # 模块名称
    version=version,
    description='A mini spider framework, like Scrapy',  # 描述
    packages=find_packages(exclude=[]),
    author='DreamingTech',
    author_email='your@email.com',
    license='Apache License v2',
    package_data={'': ['*.*']},
    url='#',
    install_requires=parse_requirements("requirements.txt"),  # 所需的运行环境
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
```
注意:  
1. 上面代码中可能会报错需要额外安装packaging模块, 更新setuptools

```shell
pip install packaging
pip install --upgrade setuptools
```

2. pip.req可能不存在, 对应的可以自定义 parse_requiremnts 函数

```python
def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]
```


### 3.框架安装第二步: 完成 requirements.txt 的编写

功能: 
写明依赖环境所支持的模块及其版本

使用: 
在setup.py中使用
放置在setup.py同级目录下

文件内容: 
requests>=2.18.4
six>=1.11.0

### 4.框架安装第三步: 完成VERSION.txt的编写

功能: 
标明当前版本, 一个合格的模块, 应当具备相应的版本号

使用: 
在setup.py中使用
放置在setup.py同级目录下

文件内容: 
1.0

### 4.框架安装第四步: 执行安装命令

步骤: 
切换到setup.py所在目录
切换到对应需要python虚拟环境下
在终端执行 python setup.py install

注意: 
1. 如果已经安装过, 可以先卸载再重新安装, 或者直接重新安装覆盖即可.
pip list
pip uninstall spider_plus

2. 每次修改 spider_plus 的源码后都要重新安装才能使用


## 运行整个框架

### 1. 编写main.py

新在其他路径下创建一个项目文件夹 spider_project

```python
# spider_project/main.py

from spider_plus.core.engine import Engine    # 导入引擎

if __name__ == '__main__':
    engine = Engine()    # 创建引擎对象
    engine.start()    # 启动引擎
```

```python
# 运行结果: 管道中打印的item对象
# item对象:<spider_plus.item.Item object at 0x10759eef0>
```

### 2. 修改管道文件, 对数据进行处理

打印 item.data, 这时就会打印出响应体的二进制内容

```python
# spider_plus/core/pipeline.py 
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
        print("item: ", item.data)
```

为什么会打印出二进制格式的响应体的内容? 

item.data中的data上 Ctrl+B

item.py > return self._data > 看在哪里实例化了 Item

在 spider.py 中实例化了 Item > return Item(response.body) > 在下载器 downloader.py 中返回了response 对象, 查看 response 对象 > body=resp.content


## 完成中间件模块


### 内置中间件的代码结构: 

- spider_plus
  -- __init__.py
  -- core
    -- __init__.py
    -- spider.py
    -- scheduler.py
    -- downloader.py
    -- pipeline.py
    -- engine.py
  -- http
    -- __init__.py
    -- request.py
    -- response.py
  -- middlewares
    -- __init__.py
    -- spider_middlewares.py
    -- downloader_middlewares.py
  -- item.py

### 2.完成爬虫中间件 spider_middlewares

```python

# spider_plus/middlewares/spider_middlewares.py


class SpiderMiddleware(object):
    '''爬虫中间件基类'''

    def process_request(self, request):
        '''预处理请求对象'''
        print("爬虫中间件: process_request方法")
        return request

    def process_response(self, response):
        '''预处理数据对象'''
        print("爬虫中间件: process_response方法")
        return response
```

### 3.完成下载 downloader_middlewares

```python
# spider_plus/middlewares/downloader_middlewares.py


class DownloaderMiddleware(object):
    '''下载器中间件基类'''

    def process_request(self, request):
        '''预处理请求对象'''
        print("下载器中间件: process_request方法")
        return request

    def process_response(self, response):
        '''预处理响应对象'''
        print("下载器中间件: process_response方法")
        return response
```

### 3.修改 engine.py, 加入中间件模块
先安装一次, 然后再修改, 这样, 就能自动补全了


```python
# spider_plus/core/engine.py
# coding=utf-8
# 引擎
from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.middlewares.downloader_middlewares import DownloaderMiddleware
from spider_plus.middlewares.spider_middlewares import SpiderMiddleware

from .scheduler import Scheduler
from .downloader import Downloader
from .pipeline import Pipeline
from .spider import Spider


class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        self.spider = Spider()  # 接收外部传入的爬虫对象
        self.scheduler = Scheduler()  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipeline = Pipeline()  # 初始化管道对象
        self.spider_mid = SpiderMiddleware()    # 初始化爬虫中间件对象
        self.downloader_mid = DownloaderMiddleware()    # 初始化下载器中间件对象

    def start(self):
        '''
        提供引擎启动的入口
        :return: None
        '''
        self._start_engine()

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return: None
        '''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        start_request = self.spider.start_requests()
        # 对start_request初始请求经过爬虫中间件进行处理
        start_request = self.spider_mid.process_request(start_request)
        # 2. 调用调度器的add_request方法, 添加request对象到调度器中
        self.scheduler.add_request(start_request)
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
        request = self.downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)
        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        response = self.downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        response = self.spider_mid.process_response(response)
        # 5. 利用爬虫的parse方法, 处理响应
        result = self.spider.parse(response)
        # 6. 判断结果的类型
        # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
        if isinstance(result, Request):
            # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
            result = self.spider_mid.process_request(result)
            self.scheduler.add_request(result)
        # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
        else:
            self.pipeline.process_item(result)


if __name__ == '__main__':
    engine = Engine()
    engine.start()
```


### 4.观察中间件的使用效果

再次安装模块, 运行main.py文件, 查看结果

运行结果: 

爬虫中间件: process_request方法
下载器中间件: process_request方法
下载器中间件: process_response方法
爬虫中间件: process_response方法
item:  <spider_plus.item.Item object at 0x000001A6020D9828>

## 框架完善

### 分析

项目中除了实现main.py以外, 还需要实现: 

项目配置文件
爬虫文件
管道文件
中间件文件
框架中还需要实现: 

框架配置文件, 并且需要实现导入项目配置文件, 同时覆盖默认配置文件的属性
支持多个爬虫的传入以及使用
支持多个管道的传入以及使用
支持多个中间件的传入以及使用


框架完善的内容
1. 日志的使用
2. 配置文件的实现
3. 具备较高的通用性: 尽可能多的使用多数爬虫场景
4. 具备较好的扩展性: 自定义功能或者组件的新增和维护
5. 请求的去重
6. 异步实现

### 日志的使用

#### 利用logger封装日志模块
在spider_plus目录下建立utils包 (utility: 工具), 专门放置工具类型模块, 如日志模块log.py 下面的代码内容是固定的, 在任何地方都可以使用下面的代码实习日志内容的输出

```python
# spider_plus/utils/log.py
# coding=utf-8
# 日志功能的实现

import sys
import logging

# 默认的配置
DEFAULT_LOG_LEVEL = logging.INFO    # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s: %(message)s'   # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = 'log.log'    # 默认日志文件名称


class Logger(object):

    def __init__(self):
        # 1. 获取一个logger对象
        self._logger = logging.getLogger()
        # 2. 设置format对象
        self.formatter = logging.Formatter(fmt=DEFAULT_LOG_FMT,datefmt=DEFUALT_LOG_DATEFMT)
        # 3. 设置日志输出
        # 3.1 设置文件日志模式
        self._logger.addHandler(self._get_file_handler(DEFAULT_LOG_FILENAME))
        # 3.2 设置终端日志模式
        self._logger.addHandler(self._get_console_handler())
        # 4. 设置日志等级
        self._logger.setLevel(DEFAULT_LOG_LEVEL)

    def _get_file_handler(self, filename):
        '''返回一个文件日志handler'''
        # 1. 获取一个文件日志handler
        filehandler = logging.FileHandler(filename=filename,encoding="utf-8")
        # 2. 设置日志格式
        filehandler.setFormatter(self.formatter)
        # 3. 返回
        return filehandler

    def _get_console_handler(self):
        '''返回一个输出到终端日志handler'''
        # 1. 获取一个输出到终端日志handler
        console_handler = logging.StreamHandler(sys.stdout)
        # 2. 设置日志格式
        console_handler.setFormatter(self.formatter)
        # 3. 返回handler
        return console_handler

    @property
    def logger(self):
        return self._logger

# 初始化并配一个logger对象, 达到单例的
# 使用时, 直接导入logger就可以使用
logger = Logger().logger

if __name__ == '__main__':
    logger.debug('DEBUG')
    logger.info('INFO')
    logger.warning('WARNING')
    logger.error('ERROR')
    logger.critical('CRITICAL')
```


#### 4. 在框架中使用日志模块
重新安装模块

```python
# spider_plus/core/engine.py
# coding=utf-8
# 引擎
from datetime import datetime

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.middlewares.downloader_middlewares import DownloaderMiddleware
from spider_plus.middlewares.spider_middlewares import SpiderMiddleware
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from .pipeline import Pipeline
from .spider import Spider


class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        self.spider = Spider()  # 接收外部传入的爬虫对象
        self.scheduler = Scheduler()  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipeline = Pipeline()  # 初始化管道对象
        self.spider_mid = SpiderMiddleware()  # 初始化爬虫中间件对象
        self.downloader_mid = DownloaderMiddleware()  # 初始化下载器中间件对象

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        start_request = self.spider.start_requests()
        # 对start_request初始请求经过爬虫中间件进行处理
        start_request = self.spider_mid.process_request(start_request)
        # 2. 调用调度器的add_request方法, 添加request对象到调度器中
        self.scheduler.add_request(start_request)
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
        request = self.downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)
        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        response = self.downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        response = self.spider_mid.process_response(response)
        # 5. 利用爬虫的parse方法, 处理响应
        result = self.spider.parse(response)
        # 6. 判断结果的类型
        # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
        if isinstance(result, Request):
            # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
            result = self.spider_mid.process_request(result)
            self.scheduler.add_request(result)
        # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
        else:
            self.pipeline.process_item(result)


if __name__ == '__main__':
    engine = Engine()
    engine.start()
```

安装模块, 执行main.py


#### 实现用户自定义配置覆盖框架默认配置

想要实现爬虫中修改日志的等级和保存位置, 不用每次都修改框架的代码

1. 实现框架的默认配置文件
在 spider_plus 下建立 conf 包文件夹, 在它下面建立 default_settings.py: 设置默认配置的配置

```python
# spider_plus/conf/default_settings.py
import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO    # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'   # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = 'log.log'    # 默认日志文件名称
```

再在conf下创建settings.py文件

```python
# spider_plus/conf/settings

from .default_settings import *  # 导入框架中的默认配置
```

2.在框架中使用

利用框架配置文件改写 log.py, 把log 模块的相关配置放到 settings.py 文件中

```python
# spider_plus/utils/log.py
# coding=utf-8
# 日志功能的实现

import sys
import logging

from spider_plus.conf.settings import DEFAULT_LOG_LEVEL, DEFAULT_LOG_FMT, DEFUALT_LOG_DATEFMT, DEFAULT_LOG_FILENAME

# # 默认的配置
# DEFAULT_LOG_LEVEL = logging.INFO    # 默认等级
# DEFAULT_LOG_FMT = '%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s: %(message)s'   # 默认日志格式
# DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
# DEFAULT_LOG_FILENAME = 'log.log'    # 默认日志文件名称


class Logger(object):

    def __init__(self):
        # 1. 获取一个logger对象
        self._logger = logging.getLogger()
        # 2. 设置format对象
        self.formatter = logging.Formatter(fmt=DEFAULT_LOG_FMT,datefmt=DEFUALT_LOG_DATEFMT)
        # 3. 设置日志输出
        # 3.1 设置文件日志模式
        self._logger.addHandler(self._get_file_handler(DEFAULT_LOG_FILENAME))
        # 3.2 设置终端日志模式
        self._logger.addHandler(self._get_console_handler())
        # 4. 设置日志等级
        self._logger.setLevel(DEFAULT_LOG_LEVEL)

    def _get_file_handler(self, filename):
        '''返回一个文件日志handler'''
        # 1. 获取一个文件日志handler
        filehandler = logging.FileHandler(filename=filename,encoding="utf-8")
        # 2. 设置日志格式
        filehandler.setFormatter(self.formatter)
        # 3. 返回
        return filehandler

    def _get_console_handler(self):
        '''返回一个输出到终端日志handler'''
        # 1. 获取一个输出到终端日志handler
        console_handler = logging.StreamHandler(sys.stdout)
        # 2. 设置日志格式
        console_handler.setFormatter(self.formatter)
        # 3. 返回handler
        return console_handler

    @property
    def logger(self):
        return self._logger

# 初始化并配一个logger对象, 达到单例的
# 使用时, 直接导入logger就可以使用
logger = Logger().logger

if __name__ == '__main__':
    logger.debug('DEBUG')
    logger.info('INFO')
    logger.warning('WARNING')
    logger.error('ERROR')
    logger.critical('CRITICAL')
```

3. 创建项目配置文件, 并实现修改框架默认配置文件属性

项目文件夹下创建项目的配置文件 settings.py:

```python
# spider_project/settings.py
# 修改默认日志文件名称
DEFAULT_LOG_FILENAME = '日志.log'    # 默认日志文件名称
```

修改框架的 settings.py文件, 实现修改默认配置文件属性的目的

```python
# spider_plus/conf/settings
from .default_settings import *    # 全部导入默认配置文件的属性

# 执行爬虫时执行的是 main.py, 是在用户的爬虫项目中的 settings.py 的同级目录下执行的, 所以会优先导入用户自定义的 settings 中的配置, 这里的设置后覆盖掉前面 default_settings 中的设置
from settings import *
```


### 多爬虫实现之一 -- 多请求实现

#### 需求分析:
爬虫文件应该放在用户的项目文件夹下, 这样就不用每次去修改框架中的spider文件了

#### 2. 项目中实现爬虫文件
在main.py同级目录下建立spiders.py, 存放定义的爬虫类

```python
# spider_project/spiders.py
# coding=utf-8
from spider_plus.core.spider import Spider


# 继承框架的爬虫基类
class BaiduSpider(Spider):
    start_url = 'http://www.baidu.com'  # 设置初始请求url

```

修改main.py

```python
# spider_project/main.py
from spider_plus.core.engine import Engine  # 导入引擎
from spiders import BaiduSpider

if __name__ == '__main__':
    baidu_spider = BaiduSpider()  # 实例化爬虫对象
    engine = Engine(baidu_spider)  # 创建引擎对象, 传入爬虫对象
    engine.start()  # 启动引擎

```


修改engine.py, 设置为接收外部传入的爬虫对象

```python
# spider_plus/core/engine.py
# coding=utf-8
# 引擎
from datetime import datetime

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.middlewares.downloader_middlewares import DownloaderMiddleware
from spider_plus.middlewares.spider_middlewares import SpiderMiddleware
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from .pipeline import Pipeline
from .spider import Spider


class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self, spider):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        self.spider = spider  # 接收外部传入的爬虫对象
        self.scheduler = Scheduler()  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipeline = Pipeline()  # 初始化管道对象
        self.spider_mid = SpiderMiddleware()  # 初始化爬虫中间件对象
        self.downloader_mid = DownloaderMiddleware()  # 初始化下载器中间件对象

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        start_request = self.spider.start_requests()
        # 对start_request初始请求经过爬虫中间件进行处理
        start_request = self.spider_mid.process_request(start_request)
        # 2. 调用调度器的add_request方法, 添加request对象到调度器中
        self.scheduler.add_request(start_request)
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
        request = self.downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)
        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        response = self.downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        response = self.spider_mid.process_response(response)
        # 5. 利用爬虫的parse方法, 处理响应
        result = self.spider.parse(response)
        # 6. 判断结果的类型
        # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
        if isinstance(result, Request):
            # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
            result = self.spider_mid.process_request(result)
            self.scheduler.add_request(result)
        # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
        else:
            self.pipeline.process_item(result)


if __name__ == '__main__':
    engine = Engine()
    engine.start()
```

重新安装模块
运行main.py

```python
# 2019-04-25 08:56:13 engine.py[line:36] INFO: 爬虫启动: 2019-04-25 08:56:13.720996
# 爬虫中间件: process_request方法
# 下载器中间件: process_request方法
# 下载器中间件: process_response方法
# 爬虫中间件: process_response方法
# item:  <spider_plus.item.Item object at 0x0000024109F0F748>
# 2019-04-25 08:56:13 engine.py[line:39] INFO: 爬虫结束: 2019-04-25 08:56:13.830998
# 2019-04-25 08:56:13 engine.py[line:40] INFO: 爬虫运行时间: 0.110002
```


由于不显示哪个请求发送成功了, 可以在downloader.py 中添加 log 信息

修改 core/downloader.py

重新安装模块
运行main.py

```
# 2019-04-25 08:59:43 engine.py[line:36] INFO: 爬虫启动: 2019-04-25 08:59:43.520046
# 爬虫中间件: process_request方法
# 下载器中间件: process_request方法
# 2019-04-25 08:59:43 downloader.py[line:26] INFO: <200 http://www.baidu.com/>
# 下载器中间件: process_response方法
# 爬虫中间件: process_response方法
# item:  <spider_plus.item.Item object at 0x0000022A1E5CE7F0>
# 2019-04-25 08:59:43 engine.py[line:39] INFO: 爬虫结束: 2019-04-25 08:59:43.626051
# 2019-04-25 08:59:43 engine.py[line:40] INFO: 爬虫运行时间: 0.106005
```

修改 main.py 中的 start_url 地址 为 http://www.douban.com, 验证是执行的 用户的爬虫项目中的 baidu, 还是执行框架中的 baidu

```
# 2019-04-25 09:02:25 engine.py[line:36] INFO: 爬虫启动: 2019-04-25 09:02:25.494640
# 爬虫中间件: process_request方法
# 下载器中间件: process_request方法
# 2019-04-25 09:02:26 downloader.py[line:26] INFO: <200 https://www.douban.com/>
# 下载器中间件: process_response方法
# 爬虫中间件: process_response方法
# item:  <spider_plus.item.Item object at 0x000001E5A5491748>
# 2019-04-25 09:02:26 engine.py[line:39] INFO: 爬虫结束: 2019-04-25 09:02:26.049640
# 2019-04-25 09:02:26 engine.py[line:40] INFO: 爬虫运行时间: 0.555
```

2. 实现发起多个请求

2.1 修改框架的爬虫组件文件 spider.py:
设置为初始请求url为多个
修改start_requests方法, 将返回多个请求对象
利用生成器方式实现start_requests, 提高程序的资源消耗

```python
# spider_plus/core/spider.py
# coding=utf-8
# 爬虫

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.item import Item  # 导入Item对象


class Spider(object):
    '''完成对spider的封装'''
    start_urls = []  # 爬虫最开始请求的url地址, 默认初始请求地址

    def start_requests(self):
        '''
        构建start_url地址的初始请求对象并返回
        :return: request对象
        '''
        # 因为初始请求有多个, 所以要进行遍历
        for start_url in self.start_urls:
            # 因为有多个请求, 所以无法使用 return, 需要修改为生成器yield
            yield Request(start_url)

    def parse(self, response):
        '''
        默认处理start_url地址对应的响应
        :param response: response响应对象
        :return: item数据或者是request对象
        '''
        # 因为解析出来的数据可能有多个, 所以不能使用 return, 需要修改为生成器 yield
        yield Item(response.body)  # 返回item对象

```

2.2 修改引擎 engine.py:

引擎代码拆分
将 _start_engine 方法的代码拆分为两个方法, 便于维护, 提高代码可读性
_start_requests  添加多个初始请求, 调用爬虫的 start_request 方法, 向调度器中添加初始请求
_execute_request_response_item  逐个处理单个请求. 根据请求、发起请求获取响应、解析响应、处理响应结果


统计总共完成的响应数
设置程序退出条件: 当总响应数等于总请求数时, 退出

实现处理start_requests方法返回多个请求的功能
实现处理parse解析函数返回多个对象的功能

```python
# scheduler/core/engine.py
# coding=utf-8
# 引擎
from datetime import datetime

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.middlewares.downloader_middlewares import DownloaderMiddleware
from spider_plus.middlewares.spider_middlewares import SpiderMiddleware
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from .pipeline import Pipeline
from .spider import Spider


class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self, spider):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        self.spider = spider  # 接收外部传入的爬虫对象
        self.scheduler = Scheduler()  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipeline = Pipeline()  # 初始化管道对象
        self.spider_mid = SpiderMiddleware()  # 初始化爬虫中间件对象
        self.downloader_mid = DownloaderMiddleware()  # 初始化下载器中间件对象
        # 为了使处理请求响应数据的方法能够正常退出, 定义两个变量, 当总的响应数量大于等于总的请求数量时, 所有请求都已经处理完毕, 就可以退出了
        self.total_request_num = 0  # 总的请求数
        self.total_response_num = 0  # 总的响应数

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时

    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历
        for start_request in self.spider.start_requests():
            # 对start_request初始请求经过爬虫中间件进行处理
            start_request = self.spider_mid.process_request(start_request)
            # 2. 调用调度器的add_request方法, 添加request对象到调度器中
            self.scheduler.add_request(start_request)
            # 把request添加到调度器中之后, 把总请求数加1
            self.total_request_num += 1

    def _execute_request_response_item(self):
        '''处理单个请求, 从调度器取出, 发送请求, 获取响应, parse函数处理, 调度器处理'''
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
        request = self.downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)
        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        response = self.downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        response = self.spider_mid.process_response(response)
        # 5. 利用爬虫的parse方法, 处理响应
        # 因为 spider 的 parse 方法已经修改为生成器, 所以这里要进行遍历
        for result in self.spider.parse(response):
            # 6. 判断结果的类型
            # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
            if isinstance(result, Request):
                # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
                result = self.spider_mid.process_request(result)
                self.scheduler.add_request(result)
                self.total_request_num += 1   # 请求加1
            # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
            else:
                self.pipeline.process_item(result)

        # 整个函数都是处理单个请求, 整个函数执行完了, 单个请求才处理完, 此时总的响应数加1
        self.total_response_num += 1

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self._start_request()   # 初始化请求
        while True:
            self._execute_request_response_item()
            # 循环结束的条件
            if self.total_response_num >= self.total_request_num:
                break


if __name__ == '__main__':
    engine = Engine()
    engine.start()
```

2.3 修改调度器 scheduler.py: 
将从队列获取请求对象设置为非阻塞, 否则会造成程序无法退出

```python
# coding=utf-8
# 调度器

# 利用six模块实现py2和py3兼容
from six.moves.queue import Queue


class Scheduler(object):
    '''完成调试器模块的封装'''
    def __init__(self):
        self.queue = Queue()

    def add_request(self, request):
        '''
        实现添加request到队列中
        :param request: 请求对象
        :return: None
        '''
        # 调用_filter_request来实现对请求对象的去重
        # self._filter_request(request)
        self.queue.put(request)

    def get_request(self):
        '''
        实现获取队列中的request对象
        :return: 请求对象
        '''
        # queue.get(), 默认 block=Ture, 即是堵塞的, 如果队列中没有对象, 就堵塞在这里. 需要修改为非堵塞的.
        # 非堵塞状态可以会报错, 所以使用try...except...
        try:
            return self.queue.get(block=False)
        except:
            return None

    def _filter_request(self, request):
        '''
        实现对请求对象的去重
        :param request: 请求对象
        :return: bool
        '''
        pass
```

由于 scheduler.get_request 方法可能会返回 None 值, 所以需要修改engine中 调用 get_request方法的地方, 进行判断

```python
# coding=utf-8
# 引擎
from datetime import datetime

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.middlewares.downloader_middlewares import DownloaderMiddleware
from spider_plus.middlewares.spider_middlewares import SpiderMiddleware
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from .pipeline import Pipeline
from .spider import Spider


class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self, spider):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        self.spider = spider  # 接收外部传入的爬虫对象
        self.scheduler = Scheduler()  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipeline = Pipeline()  # 初始化管道对象
        self.spider_mid = SpiderMiddleware()  # 初始化爬虫中间件对象
        self.downloader_mid = DownloaderMiddleware()  # 初始化下载器中间件对象
        # 为了使处理请求响应数据的方法能够正常退出, 定义两个变量, 当总的响应数量大于等于总的请求数量时, 所有请求都已经处理完毕, 就可以退出了
        self.total_request_num = 0  # 总的请求数
        self.total_response_num = 0  # 总的响应数

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时
        # 在引擎的调用执行结束后, 打印总的请求数量和总的响应数量.
        logger.info("总的请求数量: {}个".format(self.total_request_num))
        logger.info("总的响应数量: {}个".format(self.total_response_num))

    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历
        for start_request in self.spider.start_requests():
            # 对start_request初始请求经过爬虫中间件进行处理
            start_request = self.spider_mid.process_request(start_request)
            # 2. 调用调度器的add_request方法, 添加request对象到调度器中
            self.scheduler.add_request(start_request)
            # 把request添加到调度器中之后, 把总请求数加1
            self.total_request_num += 1

    def _execute_request_response_item(self):
        '''处理单个请求, 从调度器取出, 发送请求, 获取响应, parse函数处理, 调度器处理'''
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        if request is None:  # 判断从调度器中取出来的request是否是None, 如果是None, 表示调度器为空, 就不进行任何进一步的处理
            return
        # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
        request = self.downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)
        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        response = self.downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        response = self.spider_mid.process_response(response)
        # 5. 利用爬虫的parse方法, 处理响应
        # 因为 spider 的 parse 方法已经修改为生成器, 所以这里要进行遍历
        for result in self.spider.parse(response):
            # 6. 判断结果的类型
            # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
            if isinstance(result, Request):
                # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
                result = self.spider_mid.process_request(result)
                self.scheduler.add_request(result)
                self.total_request_num += 1   # 请求加1
            # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
            else:
                self.pipeline.process_item(result)

        # 整个函数都是处理单个请求, 整个函数执行完了, 单个请求才处理完, 此时总的响应数加1
        self.total_response_num += 1

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self._start_request()   # 初始化请求
        while True:
            self._execute_request_response_item()
            # 循环结束的条件
            if self.total_response_num >= self.total_request_num:
                break


if __name__ == '__main__':
    engine = Engine()
    engine.start()
```

修改用户项目文件夹中的 spider.py 文件, 把 start_urls 修改为列表格式

```python
# coding=utf-8
from spider_plus.core.spider import Spider


# 继承框架的爬虫基类
class BaiduSpider(Spider):
    start_urls = ['http://www.douban.com']  # 设置初始请求url

```

重新安装模块
执行爬虫
```
# 2019-04-25 09:57:20 engine.py[line:39] INFO: 爬虫启动: 2019-04-25 09:57:20.750848
# 爬虫中间件: process_request方法
# 下载器中间件: process_request方法
# 2019-04-25 09:57:21 downloader.py[line:26] INFO: <200 https://www.douban.com/>
# 下载器中间件: process_response方法
# 爬虫中间件: process_response方法
# item:  <spider_plus.item.Item object at 0x000001533FFCF940>
# 2019-04-25 09:57:21 engine.py[line:42] INFO: 爬虫结束: 2019-04-25 09:57:21.298830
# 2019-04-25 09:57:21 engine.py[line:43] INFO: 爬虫运行时间: 0.547982
# 2019-04-25 09:57:21 engine.py[line:45] INFO: 总的请求数量: 1个
# 2019-04-25 09:57:21 engine.py[line:46] INFO: 总的响应数量: 1个
```

在用户项目文件的爬虫文件中添加多个start_url地址, 再次运行爬虫

```python
# spider_project/spider.py
# coding=utf-8
from spider_plus.core.spider import Spider


# 继承框架的爬虫基类
class BaiduSpider(Spider):
    start_urls = [
    'http://www.douban.com',
    'http://www.douban.com',
    'http://www.baidu.com',
    ]  # 设置初始请求url
```

```
# 2019-04-25 09:59:10 engine.py[line:39] INFO: 爬虫启动: 2019-04-25 09:59:10.813828
# 爬虫中间件: process_request方法
# 爬虫中间件: process_request方法
# 爬虫中间件: process_request方法
# 下载器中间件: process_request方法
# 2019-04-25 09:59:11 downloader.py[line:26] INFO: <200 https://www.douban.com/>
# 下载器中间件: process_response方法
# 爬虫中间件: process_response方法
# item:  <spider_plus.item.Item object at 0x00000270E28F0898>
# 下载器中间件: process_request方法
# 2019-04-25 09:59:12 downloader.py[line:26] INFO: <200 https://www.douban.com/>
# 下载器中间件: process_response方法
# 爬虫中间件: process_response方法
# item:  <spider_plus.item.Item object at 0x00000270E227EB00>
# 下载器中间件: process_request方法
# 2019-04-25 09:59:12 downloader.py[line:26] INFO: <200 http://www.baidu.com/>
# 下载器中间件: process_response方法
# 爬虫中间件: process_response方法
# item:  <spider_plus.item.Item object at 0x00000270E312A7F0>
# 2019-04-25 09:59:12 engine.py[line:42] INFO: 爬虫结束: 2019-04-25 09:59:12.190838
# 2019-04-25 09:59:12 engine.py[line:43] INFO: 爬虫运行时间: 1.37701
# 2019-04-25 09:59:12 engine.py[line:45] INFO: 总的请求数量: 3个
# 2019-04-25 09:59:12 engine.py[line:46] INFO: 总的响应数量: 3个
```



(可选)在 scheduler 中统计请求总数, 用于判断程序退出

```python
# spider_plus/core/scheduler.py
'''调度器模块封装'''
# 利用six模块实现py2和py3兼容
from six.moves.queue import Queue


class Scheduler(object):
    '''
    1. 缓存请求对象(Request), 并为下载器提供请求对象, 实现请求的调度
    2. 对请求对象进行去重判断
    '''
    def __init__(self):
        self.queue = Queue()
        # 记录总共的请求数
        self.total_request_number = 0

    def add_request(self, request):
        '''添加请求对象'''
        self.queue.put(request)
        self.total_request_number += 1    # 统计请求总数

    def get_request(self):
        '''获取一个请求对象并返回'''
        try:
            request = self.queue.get(False)
        except:
            return None
        else:
            return request

    def _filter_request(self):
        '''请求去重'''
        pass
```

### 爬虫实现多个解析函数

掌握 getattr 的方法  hasattr 方法

完成通过meta在不通过的解析函数中传递数据的方法


2. 响应对象的解析方法封装
为response对象封装xpath、正则、json、等方法和属性, 以支持对数据的解析和提取

```python
# spider_plus/http/response.py
# coding=utf-8
# 响应对象
from lxml import etree
import json
import re


class Response(object):
    """完成响应对象的封装"""

    def __init__(self, url, body, headers, status_code):
        '''
        初始化response对象
        :param url: 响应的url地址
        :param body: 响应体
        :param headers: 响应头
        :param status_code: 状态码
        '''
        self.url = url
        self.body = body
        self.headers = headers
        self.status_code = status_code

    def xpath(self, rule):
        '''
        给response对象添加xpath方法, 能够使用xpath提取数据
        :param rule: xpath匹配规则的字符串
        :return: 列表, 包含element对象或者是字符串的列表
        '''
        html = etree.HTML(self.body)
        return html.xpath(rule)

    @property
    def json(self):
        '''
        给response对象添加json属性, 能够直接把响应的json字符串转换为python数据类型
        :return: python数据类型
        '''
        return json.loads(self.body.decode())

    def re_findall(self, rule, data=None):
        '''
        给response对象添加re_findall方法, 能够使用正则从响应中提取数据
        :param rule: 正则表达式的字符串
        :param data:
        :return: 列表
        '''
        # 如果用户没有传递过来data, 就默认从响应体中进行内容的匹配
        if data is None:
            data = self.body
        return re.findall(rule, data)
```

修改 requirements.txt , 添加 lxml

six>=1.11.0
requests>=2.18.4
lxml>=4.2.1


增加爬虫, 糗事百科爬虫

```python
# spider_project/spiders.py

# coding=utf-8
from spider_plus.core.spider import Spider
from spider_plus.http.request import Request
from spider_plus.item import Item
import urllib.parse


# 继承框架的爬虫基类
class BaiduSpider(Spider):
    start_urls = ['http://www.douban.com', 'http://www.douban.com', 'http://www.baidu.com', ]  # 设置初始请求url


class QiubaiSpider(Spider):
    start_urls = []

    # 因为 start_requests 方法的作用是 发送 start_urls 中url地址的请求, 所以如果不想把地址写入到 start_urls 中, 也可以重写 start_requests 方法
    def start_requests(self):
        url_temp = "https://www.qiushibaike.com/8hr/page/{}/"
        # 糗事百科一共有13页的内容
        for i in range(1, 14):
            yield Request(url_temp.format(i))

    def parse(self, response):  # 提取页面的数据
        # 先分组, 再提取
        div_list = response.xpath('//div[@class="recmd-right"]')
        for div in div_list:
            item = {}
            item["name"] = div.xpath('.//span[@class="recmd-name"]/text()')[0]
            print(item["name"])
            item["title"] = "".join(div.xpath('./a[@class="recmd-content"]//text()'))
            item["url"] = urllib.parse.urljoin(response.url, div.xpath('./a/@href')[0])
            yield Item(item)
```


修改spider_plus/core/pipeline.py
打印item中的数据

```python
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
```

修改 spider_project/main.py

```python

from spider_plus.core.engine import Engine  # 导入引擎
from spiders import BaiduSpider
from spiders import QiubaiSpider

if __name__ == '__main__':
    baidu = BaiduSpider()  # 实例化爬虫对象
    qiubai = QiubaiSpider()  # 实例化爬虫对象
    engine = Engine(qiubai)  # 创建引擎对象, 传入爬虫对象
    engine.start()  # 启动引擎
```


重新安装模块
运行main.py


4. 实现多个解析函数

想要提取出帖子的url地址, 进而请求并提取出帖子的详情信息, 需要设置多个解析函数
依照 scrapy 中的 spider, 每次 yield Request 时都指定解析函数, 并传递 meta 信息

spider_project/spiders.py

想要提取出帖子的url地址, 进而请求并提取出帖子的详情信息, 需要设置多个解析函数

```python
# coding=utf-8
from spider_plus.core.spider import Spider
from spider_plus.http.request import Request
from spider_plus.item import Item
import urllib.parse


# 继承框架的爬虫基类
class BaiduSpider(Spider):
    start_urls = ['http://www.douban.com', 'http://www.douban.com', 'http://www.baidu.com', ]  # 设置初始请求url


class QiubaiSpider(Spider):
    start_urls = []

    # 因为 start_requests 方法的作用是 发送 start_urls 中url地址的请求, 所以如果不想把地址写入到 start_urls 中, 也可以重写 start_requests方法
    def start_requests(self):
        url_temp = "https://www.qiushibaike.com/8hr/page/{}/"
        # 糗事百科一共有13页的内容
        for i in range(1, 14):
            yield Request(url_temp.format(i))

    def parse(self, response):  # 提取页面的数据
        # 先分组, 再提取
        div_list = response.xpath('//div[@class="recmd-right"]')
        for div in div_list:
            item = {}
            item["name"] = div.xpath('.//span[@class="recmd-name"]/text()')[0]
            print(item["name"])
            item["title"] = "".join(div.xpath('./a[@class="recmd-content"]//text()'))
            item["url"] = urllib.parse.urljoin(response.url, div.xpath('./a/@href')[0])
            # yield Item(item)
            # 构造详情页的请求对象, 并指定解析函数和meta信息
            yield Request(item["url"], parse="parse_detail", meta={"item": item})
            # 测试代码
            break

    def parse_detail(self, response):
        item = response.meta["item"]
        item["pub_time"] = response.xpath('//span[@class="stats-time"]/text()')[0].strip()
        item["vote_num"] = response.xpath('//span[@class="stats-vote"]/i/text()')[0].strip()
        yield Item(item)
```

由于现在不同的请求对应不同的解析函数, 因此需要为请求对象指明它的解析函数, 因此为请求对象增加一个属性 parse, 记录这个请求对应的响应的解析函数, 默认为 parse 函数

同时, 为了实现在不同的解析函数之间传递数据, 给 request 对象 添加一个 meta 属性

```python
# spider_plus/http/request.py
# coding=utf-8
# 请求对象

class Request(object):
    """完成请求对象的封装"""

    def __init__(self, url, method="GET", headers=None, params=None, data=None, parse="parse", meta={}):
        '''
        初始化request对象
        :param url: url地址
        :param method: 请求方法
        :param headers:请求头
        :param params: 请求的参数, 查询字符串
        :param data: 请求体, 表单数据
        :param parse: 请求对象对应的响应的解析函数
        :param meta: 字典, 在不同的解析函数之间传递数据
        '''
        self.url = url
        self.method = method
        self.headers = headers
        self.params = params
        self.data = data
        self.parse = parse
        self.meta = meta

```

同样, 需要给 response 对象也添加一个meta 属性

```python
# coding=utf-8
# 响应对象
from lxml import etree
import json
import re


class Response(object):
    """完成响应对象的封装"""

    def __init__(self, url, body, headers, status_code, meta={}):
        '''
        初始化response对象
        :param url: 响应的url地址
        :param body: 响应体
        :param headers: 响应头
        :param status_code: 状态码
        :param meta: 接收request对象中的meta值
        '''
        self.url = url
        self.body = body
        self.headers = headers
        self.status_code = status_code
        self.meta = meta

    def xpath(self, rule):
        '''
        给response对象添加xpath方法, 能够使用xpath提取数据
        :param rule: xpath匹配规则的字符串
        :return: 列表, 包含element对象或者是字符串的列表
        '''
        html = etree.HTML(self.body)
        return html.xpath(rule)

    @property
    def json(self):
        '''
        给response对象添加json属性, 能够直接把响应的json字符串转换为python数据类型
        :return: python数据类型
        '''
        return json.loads(self.body.decode())

    def re_findall(self, rule, data=None):
        '''
        给response对象添加re_findall方法, 能够使用正则从响应中提取数据
        :param rule: 正则表达式的字符串
        :param data:
        :return: 列表
        '''
        # 如果用户没有传递过来data, 就默认从响应体中进行内容的匹配
        if data is None:
            data = self.body
        return re.findall(rule, data)
```

修改 core/engine.py, 在引擎中需要动态的判断和获取对应的解析函数. 
根据 request 对象的 parse 属性来确定其对应的 response 对象的解析函数. 同时, 把 request.meta 赋值给 response.meta, 实现不同解析函数之间数据的传递

getattr(baidu_spider, "parse")
在 baidu_spider 这个对象中查找名称为 "parse" 的方法, 返回一个方法, 可以直接调用该方法
parse = getattr(baidu_spider, "parse")
parse()

```python
# coding=utf-8
# 引擎
from datetime import datetime

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.middlewares.downloader_middlewares import DownloaderMiddleware
from spider_plus.middlewares.spider_middlewares import SpiderMiddleware
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from .pipeline import Pipeline
from .spider import Spider


class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self, spider):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        self.spider = spider  # 接收外部传入的爬虫对象
        self.scheduler = Scheduler()  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipeline = Pipeline()  # 初始化管道对象
        self.spider_mid = SpiderMiddleware()  # 初始化爬虫中间件对象
        self.downloader_mid = DownloaderMiddleware()  # 初始化下载器中间件对象
        # 为了使处理请求响应数据的方法能够正常退出, 定义两个变量, 当总的响应数量大于等于总的请求数量时, 所有请求都已经处理完毕, 就可以退出了
        self.total_request_num = 0  # 总的请求数
        self.total_response_num = 0  # 总的响应数

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时
        # 在引擎的调用执行结束后, 打印总的请求数量和总的响应数量.
        logger.info("总的请求数量: {}个".format(self.total_request_num))
        logger.info("总的响应数量: {}个".format(self.total_response_num))

    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历
        for start_request in self.spider.start_requests():
            # 对start_request初始请求经过爬虫中间件进行处理
            start_request = self.spider_mid.process_request(start_request)
            # 2. 调用调度器的add_request方法, 添加request对象到调度器中
            self.scheduler.add_request(start_request)
            # 把request添加到调度器中之后, 把总请求数加1
            self.total_request_num += 1

    def _execute_request_response_item(self):
        '''处理单个请求, 从调度器取出, 发送请求, 获取响应, parse函数处理, 调度器处理'''
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        if request is None:  # 判断从调度器中取出来的request是否是None, 如果是None, 表示调度器为空, 就不进行任何进一步的处理
            return
        # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
        request = self.downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)

        # 为了把 request中的meta传递给 response, 在调用下载器获取响应后, 给response添加一个meta属性即可
        response.meta = request.meta

        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        response = self.downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        response = self.spider_mid.process_response(response)

        # 获取 request 对象对应的响应的parse方法. getattr 从 self.spider 中查找并返回 request的parse属性指定的方法
        # 对于糗事百科爬虫来说, 1-13页列表页中, 由于request对象没有指定parse方法, 所以会使用默认的 parse="parse", 而对于详情页, 则使用 request对象指定的 "parse_detail" 方法.
        parse = getattr(self.spider, request.parse)

        # 5. 利用爬虫的parse方法, 处理响应
        # 因为 spider 的 parse 方法已经修改为生成器, 所以这里要进行遍历
        for result in parse(response):
            # 6. 判断结果的类型
            # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
            if isinstance(result, Request):
                # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
                result = self.spider_mid.process_request(result)
                self.scheduler.add_request(result)
                self.total_request_num += 1  # 请求加1
            # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
            else:
                self.pipeline.process_item(result)

        # 整个函数都是处理单个请求, 整个函数执行完了, 单个请求才处理完, 此时总的响应数加1
        self.total_response_num += 1

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self._start_request()  # 初始化请求
        while True:
            self._execute_request_response_item()
            # 循环结束的条件
            if self.total_response_num >= self.total_request_num:
                break


if __name__ == '__main__':
    engine = Engine()
    engine.start()
```


5. 在引擎中需要动态的判断和获取对应的解析函数

```python
# spider_plus/core/engine.py
class Engine(object):

    ......

    def _execute_request_response_item(self):
        '''根据请求、发起请求获取响应、解析响应、处理响应结果'''

        ......

        # 5. 利用爬虫的解析响应的方法, 处理响应, 得到结果
        parse = getattr(self.spider, request.parse)    # 获取对应的解析函数
        results = parse(response)    # parse函数的返回值是一个容器, 如列表或者生成器对象
        results.meta = request.meta

        ......

```
6. 修改豆瓣爬虫, 发起详情页的请求: 

```python

# spider_project/spiders.py
......

class DoubanSpider(Spider):

    start_urls = []  # 重写start_requests方法后, 这个属性就没有设置的必要了

    def start_requests(self):
        # 重写start_requests方法, 返回多个请求
        base_url = 'http://movie.douban.com/top250?start='
        for i in range(0, 250, 25):    # 逐个返回第1-10页的请求属相
            url = base_url + str(i)
            yield Request(url)

    def parse(self, response):
        '''解析豆瓣电影top250列表页'''
        title_list = []    # 存储所有的
        for li in response.xpath("//ol[@class='grid_view']/li"):    # 遍历每一个li标签
            # title = li.xpath(".//span[@class='title'][1]/text()")    # 提取该li标下的 标题
            # title_list.append(title[0])
            detail_url = li.xpath(".//div[@class='info']/div[@class='hd']/a/@href")[0]
            yield Request(detail_url, parse="parse_detail")    # 发起详情页的请求, 并指定解析函数是parse_detail方法
        # yield Item(title_list)    # 返回标题

    def parse_detail(self, response):
        '''解析详情页'''
        print('详情页url: ', response.url)    # 打印一下响应的url
        return []    # 由于必须返回一个容器, 这里返回一个空列表

```

多爬虫实现之三 -- 多爬虫文件

目标
优化现有的爬虫结构, 实现同时开始执行多个爬虫

1. 为什么需要优化现有的爬虫结构

当爬虫比较少的时候, 我们的项目结构相对合理, 但是当要抓取的网站比较多的时候, 可以借鉴scrapy的方法, 把不同网站的爬虫分别在不同的py文件中编写, 之后放在一个目录下；
同时, 我们很多时候还希望能够有同时启动项目中的所有的爬虫

2. 将多个爬虫类分离为多个爬虫文件爬虫文件

为了解耦合, 应将每个站点的爬虫写为单独一个py文件, 因此更改一下放置爬虫的模块, 结构如下: 

- 项目文件夹
  -- main.py
  -- spiders
     -- __init__.py
     -- baidu.py
     -- qiubai.py
  -- settings.py

其中 baidu.py 和 qiubai.py 分别是抓取百度和 qiushibaike 的爬虫文件

baidu.py:

```python
# spider_project/spiders/baidu.py
# coding=utf-8
from spider_plus.core.spider import Spider
from spider_plus.http.request import Request
from spider_plus.item import Item
import urllib.parse


# 继承框架的爬虫基类
class BaiduSpider(Spider):
    start_urls = ['http://www.douban.com', 'http://www.douban.com', 'http://www.baidu.com', ]  # 设置初始请求url
```



qiubai.py: 抓取糗事百科每一页的帖子

```python
# spider_project/spiders/qiubai.py


# coding=utf-8
from spider_plus.core.spider import Spider
from spider_plus.http.request import Request
from spider_plus.item import Item
import urllib.parse


class QiubaiSpider(Spider):
    start_urls = []

    # 因为 start_requests 方法的作用是 发送 start_urls 中url地址的请求, 所以如果不想把地址写入到 start_urls 中, 也可以重写 start_requests方法
    def start_requests(self):
        url_temp = "https://www.qiushibaike.com/8hr/page/{}/"
        # 糗事百科一共有13页的内容
        for i in range(1, 14):
            yield Request(url_temp.format(i))

    def parse(self, response):  # 提取页面的数据
        # 先分组, 再提取
        div_list = response.xpath('//div[@class="recmd-right"]')
        for div in div_list:
            item = {}
            item["name"] = div.xpath('.//span[@class="recmd-name"]/text()')[0]
            print(item["name"])
            item["title"] = "".join(div.xpath('./a[@class="recmd-content"]//text()'))
            item["url"] = urllib.parse.urljoin(response.url, div.xpath('./a/@href')[0])
            # yield Item(item)
            # 构造详情页的请求对象, 并指定解析函数和meta信息
            yield Request(item["url"], parse="parse_detail", meta={"item": item})
            # 测试代码
            break

    def parse_detail(self, response):
        item = response.meta["item"]
        item["pub_time"] = response.xpath('//span[@class="stats-time"]/text()')[0].strip()
        item["vote_num"] = response.xpath('//span[@class="stats-vote"]/i/text()')[0].strip()
        yield Item(item)
```

对main.py进行相应修改, 测试新增的 qiushi 爬虫

```python
# spider_project/main.py

from spider_plus.core.engine import Engine  # 导入引擎
from spiders.baidu import BaiduSpider
from spiders.qiubai import QiubaiSpider

if __name__ == '__main__':
    baidu = BaiduSpider()  # 实例化爬虫对象
    qiubai = QiubaiSpider()  # 实例化爬虫对象
    engine = Engine(qiubai)  # 创建引擎对象, 传入爬虫对象
    engine.start()  # 启动引擎
```


3. 同时执行多个不同的爬虫
如把豆瓣爬虫和百度爬虫一起启动并执行

传入形式: 并用字典的形式传入多个爬虫: 

```python
# spider_project/main.py

from spider_plus.core.engine import Engine  # 导入引擎
from spiders.baidu import BaiduSpider
from spiders.qiubai import QiubaiSpider

if __name__ == '__main__':
    baidu = BaiduSpider()  # 实例化爬虫对象
    qiubai = QiubaiSpider()  # 实例化爬虫对象
    spiders = {'baidu': baidu, 'qiubai': qiubai}
    engine = Engine(spiders)  # 创建引擎对象, 传入爬虫对象
    engine.start()  # 启动引擎
```


在引擎中用到爬虫对象的地方都要做相应的修改

engine.py: 

```python
# coding=utf-8
# 引擎
from datetime import datetime

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.middlewares.downloader_middlewares import DownloaderMiddleware
from spider_plus.middlewares.spider_middlewares import SpiderMiddleware
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from .pipeline import Pipeline
from .spider import Spider


class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self, spiders):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        self.spiders = spiders  # 接收外部传入的爬虫对象
        self.scheduler = Scheduler()  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipeline = Pipeline()  # 初始化管道对象
        self.spider_mid = SpiderMiddleware()  # 初始化爬虫中间件对象
        self.downloader_mid = DownloaderMiddleware()  # 初始化下载器中间件对象
        # 为了使处理请求响应数据的方法能够正常退出, 定义两个变量, 当总的响应数量大于等于总的请求数量时, 所有请求都已经处理完毕, 就可以退出了
        self.total_request_num = 0  # 总的请求数
        self.total_response_num = 0  # 总的响应数

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时
        # 在引擎的调用执行结束后, 打印总的请求数量和总的响应数量.
        logger.info("总的请求数量: {}个".format(self.total_request_num))
        logger.info("总的响应数量: {}个".format(self.total_response_num))

    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        for spider_name, spider in self.spiders.items():  # 遍历 spiders 字典, 获取每个spider对象
            # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历
            for start_request in spider.start_requests():
                # 对start_request初始请求经过爬虫中间件进行处理
                start_request = self.spider_mid.process_request(start_request)

                # 在把初始请求添加到调度器中之前, 给它添加一个属性 spider_name, 记录它是哪个爬虫产生的请求, 以方便后面 _execute_request_response_item 中通过这个属性获取到对应的爬虫, 进而获取爬虫的 parse方法
                start_request.spider_name = spider_name

                # 2. 调用调度器的add_request方法, 添加request对象到调度器中
                self.scheduler.add_request(start_request)
                # 把request添加到调度器中之后, 把总请求数加1
                self.total_request_num += 1

    def _execute_request_response_item(self):
        '''处理单个请求, 从调度器取出, 发送请求, 获取响应, parse函数处理, 调度器处理'''
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        if request is None:  # 判断从调度器中取出来的request是否是None, 如果是None, 表示调度器为空, 就不进行任何进一步的处理
            return
        # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
        request = self.downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)

        # 为了把 request中的meta传递给 response, 在调用下载器获取响应后, 给response添加一个meta属性即可
        response.meta = request.meta

        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        response = self.downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        response = self.spider_mid.process_response(response)

        # 根据请求对象的 spider_name 属性, 获取爬虫实例, 进而获取爬虫的 parse 方法
        spider = self.spiders.get(request.spider_name)
        # 获取 request 对象对应的响应的parse方法. getattr 从 self.spiders 中查找并返回 request的parse属性指定的方法
        # 对于糗事百科爬虫来说, 1-13页列表页中, 由于request对象没有指定parse方法, 所以会使用默认的 parse="parse", 而对于详情页, 则使用 request对象指定的 "parse_detail" 方法.
        parse = getattr(spider, request.parse)

        # 5. 利用爬虫的parse方法, 处理响应
        # 因为 spiders 的 parse 方法已经修改为生成器, 所以这里要进行遍历
        for result in parse(response):
            # 6. 判断结果的类型
            # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
            if isinstance(result, Request):
                # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
                result = self.spider_mid.process_request(result)

                # 对于新的请求, 在保存到调度器之间也添加 spider_name 属性
                result.spider_name = request.spider_name

                self.scheduler.add_request(result)
                self.total_request_num += 1  # 请求加1
            # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
            else:
                self.pipeline.process_item(result)

        # 整个函数都是处理单个请求, 整个函数执行完了, 单个请求才处理完, 此时总的响应数加1
        self.total_response_num += 1

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self._start_request()  # 初始化请求
        while True:
            self._execute_request_response_item()
            # 循环结束的条件
            if self.total_response_num >= self.total_request_num:
                break


if __name__ == '__main__':
    engine = Engine()
    engine.start()
```


修改 baidu.py, 只返回响应体的一部分内容

```python
# coding=utf-8
from spider_plus.core.spider import Spider
from spider_plus.http.request import Request
from spider_plus.item import Item
import urllib.parse


# 继承框架的爬虫基类
class BaiduSpider(Spider):
    start_urls = ['http://www.douban.com', 'http://www.douban.com', 'http://www.baidu.com', ]  # 设置初始请求url

    def parse(self, response):
        yield Item(response.body[:20])
```


重新安装框架, 并运行main.py, 直到调试成功


4. 再次改进, 将每个爬虫的名称直接设置为爬虫类的一个属性

baidu.py

```python
# coding=utf-8
from spider_plus.core.spider import Spider
from spider_plus.http.request import Request
from spider_plus.item import Item
import urllib.parse


# 继承框架的爬虫基类
class BaiduSpider(Spider):
    name = "baidu"
    start_urls = ['http://www.douban.com', 'http://www.douban.com', 'http://www.baidu.com', ]  # 设置初始请求url

    def parse(self, response):
        yield Item(response.body[:20])

qiubai.py

# coding=utf-8
from spider_plus.core.spider import Spider
from spider_plus.http.request import Request
from spider_plus.item import Item
import urllib.parse


class QiubaiSpider(Spider):
    name = "qiubai"
    start_urls = []

    # 因为 start_requests 方法的作用是 发送 start_urls 中url地址的请求, 所以如果不想把地址写入到 start_urls 中, 也可以重写 start_requests方法
    def start_requests(self):
        url_temp = "https://www.qiushibaike.com/8hr/page/{}/"
        # 糗事百科一共有13页的内容
        for i in range(1, 14):
            yield Request(url_temp.format(i))

    def parse(self, response):  # 提取页面的数据
        # 先分组, 再提取
        div_list = response.xpath('//div[@class="recmd-right"]')
        for div in div_list:
            item = {}
            item["name"] = div.xpath('.//span[@class="recmd-name"]/text()')[0]
            print(item["name"])
            item["title"] = "".join(div.xpath('./a[@class="recmd-content"]//text()'))
            item["url"] = urllib.parse.urljoin(response.url, div.xpath('./a/@href')[0])
            # yield Item(item)
            # 构造详情页的请求对象, 并指定解析函数和meta信息
            yield Request(item["url"], parse="parse_detail", meta={"item": item})
            # 测试代码
            break

    def parse_detail(self, response):
        item = response.meta["item"]
        item["pub_time"] = response.xpath('//span[@class="stats-time"]/text()')[0].strip()
        item["vote_num"] = response.xpath('//span[@class="stats-vote"]/i/text()')[0].strip()
        yield Item(item)


main.py

from spider_plus.core.engine import Engine  # 导入引擎
from spiders.baidu import BaiduSpider
from spiders.qiubai import QiubaiSpider

if __name__ == '__main__':
    baidu = BaiduSpider()  # 实例化爬虫对象
    qiubai = QiubaiSpider()  # 实例化爬虫对象
    spiders = {baidu.name: baidu, qiubai.name: qiubai}
    engine = Engine(spiders)  # 创建引擎对象, 传入爬虫对象
    engine.start()  # 启动引擎
```


实现多个管道
目标
实现对引擎的修改, 达到数据通过多个管道的目的
1. 为什么需要多个管道
同爬虫文件一样, 不同的爬虫可能需要不同的管道文件, 因此管道文件需要在项目中进行实现

实现多个管道

2. 项目文件夹中实现管道文件
在项目文件夹下建立pipelines.py文件, 不同在于: 

这里的process_item必须把item对象最后再返回回来, 因为是多个管道文件的设置了
需要增加一个参数, 也就是传入爬虫对象, 以此来判断当前item是属于那个爬虫对象的

```python
# spider_project/pipelines.py

# coding=utf-8
from spiders.baidu import BaiduSpider
from spiders.qiubai import QiubaiSpider


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
            print("百度管道处理的数据: ", item.data)
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
            print("糗百管道处理的数据: ", item.data)
        return item  # 最后必须返回item
```


3.修改main.py
为引擎传入项目中的管道对象:

```python

# spider_project/main.py
from spider_plus.core.engine import Engine  # 导入引擎
from spiders.baidu import BaiduSpider
from spiders.qiubai import QiubaiSpider
from pipelines import BaiduPipeline, QiubaiPipeline

if __name__ == '__main__':
    baidu = BaiduSpider()  # 实例化爬虫对象
    qiubai = QiubaiSpider()  # 实例化爬虫对象
    spiders = {baidu.name: baidu, qiubai.name: qiubai}
    pipelines = [BaiduPipeline(), QiubaiPipeline()]   # 注意这里导入的是实例, 而不是类对象, 因为类对象无法使用实例方法, 也就无法调用 process_item 来处理数据
    engine = Engine(spiders, pipelines)  # 创建引擎对象, 传入爬虫对象
    engine.start()  # 启动引擎

```

2. 修改引擎的代码
管道对象将从外部传入
调用管道的process_item方法时, 需要遍历出管道
并且需要传递第二个参数, 爬虫对象

```python

# spider_plus/core/engine.py
# coding=utf-8
# 引擎
from datetime import datetime

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.middlewares.downloader_middlewares import DownloaderMiddleware
from spider_plus.middlewares.spider_middlewares import SpiderMiddleware
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from .pipeline import Pipeline
from .spider import Spider


class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self, spiders, pipelines=[]):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        self.spiders = spiders  # 接收外部传入的爬虫对象
        self.scheduler = Scheduler()  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipelines = pipelines  # 初始化管道对象
        self.spider_mid = SpiderMiddleware()  # 初始化爬虫中间件对象
        self.downloader_mid = DownloaderMiddleware()  # 初始化下载器中间件对象
        # 为了使处理请求响应数据的方法能够正常退出, 定义两个变量, 当总的响应数量大于等于总的请求数量时, 所有请求都已经处理完毕, 就可以退出了
        self.total_request_num = 0  # 总的请求数
        self.total_response_num = 0  # 总的响应数

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时
        # 在引擎的调用执行结束后, 打印总的请求数量和总的响应数量.
        logger.info("总的请求数量: {}个".format(self.total_request_num))
        logger.info("总的响应数量: {}个".format(self.total_response_num))

    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        for spider_name, spider in self.spiders.items():  # 遍历 spiders 字典, 获取每个spider对象
            # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历
            for start_request in spider.start_requests():
                # 对start_request初始请求经过爬虫中间件进行处理
                start_request = self.spider_mid.process_request(start_request)

                # 在把初始请求添加到调度器中之前, 给它添加一个属性 spider_name, 记录它是哪个爬虫产生的请求, 以方便后面 _execute_request_response_item 中通过这个属性获取到对应的爬虫, 进而获取爬虫的 parse方法
                start_request.spider_name = spider_name

                # 2. 调用调度器的add_request方法, 添加request对象到调度器中
                self.scheduler.add_request(start_request)
                # 把request添加到调度器中之后, 把总请求数加1
                self.total_request_num += 1

    def _execute_request_response_item(self):
        '''处理单个请求, 从调度器取出, 发送请求, 获取响应, parse函数处理, 调度器处理'''
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        if request is None:  # 判断从调度器中取出来的request是否是None, 如果是None, 表示调度器为空, 就不进行任何进一步的处理
            return
        # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
        request = self.downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)

        # 为了把 request中的meta传递给 response, 在调用下载器获取响应后, 给response添加一个meta属性即可
        response.meta = request.meta

        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        response = self.downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        response = self.spider_mid.process_response(response)

        # 根据请求对象的 spider_name 属性, 获取爬虫实例, 进而获取爬虫的 parse 方法
        spider = self.spiders.get(request.spider_name)
        # 获取 request 对象对应的响应的parse方法. getattr 从 self.spiders 中查找并返回 request的parse属性指定的方法
        # 对于糗事百科爬虫来说, 1-13页列表页中, 由于request对象没有指定parse方法, 所以会使用默认的 parse="parse", 而对于详情页, 则使用 request对象指定的 "parse_detail" 方法.
        parse = getattr(spider, request.parse)

        # 5. 利用爬虫的parse方法, 处理响应
        # 因为 spiders 的 parse 方法已经修改为生成器, 所以这里要进行遍历
        for result in parse(response):
            # 6. 判断结果的类型
            # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
            if isinstance(result, Request):
                # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
                result = self.spider_mid.process_request(result)

                # 对于新的请求, 在保存到调度器之间也添加 spider_name 属性
                result.spider_name = request.spider_name

                self.scheduler.add_request(result)
                self.total_request_num += 1  # 请求加1
            # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
            else:
                # 遍历所有的管道, 对item进行处理
                for pipeline in self.pipelines:
                    # 必须要把处理的结果重新赋值给 result, 下一个管道才能在上一个管道的基础上进一步处理
                    result = pipeline.process_item(result, spider)

        # 整个函数都是处理单个请求, 整个函数执行完了, 单个请求才处理完, 此时总的响应数加1
        self.total_response_num += 1

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self._start_request()  # 初始化请求
        while True:
            self._execute_request_response_item()
            # 循环结束的条件
            if self.total_response_num >= self.total_request_num:
                break


if __name__ == '__main__':
    engine = Engine()
    engine.start()

```

添加一个管道, 模拟数据写入到数据库的过程

修改 spider_project/pipelines.py

```python

# coding=utf-8
from spiders.baidu import BaiduSpider
from spiders.qiubai import QiubaiSpider


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
            print("百度管道处理的数据: ", item.data)
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
            print("糗百管道处理的数据: ", item.data)
        return item  # 最后必须返回item


class MysqlPipeline(object):
    '''把数据写入到mysql数据库中'''

    def process_item(self, item, spider):
        print("把数据写入到mysql数据库", spider.name)
        return item
```

修改 spider_project/main.py

```python

from spider_plus.core.engine import Engine  # 导入引擎
from spiders.baidu import BaiduSpider
from spiders.qiubai import QiubaiSpider
from pipelines import BaiduPipeline, QiubaiPipeline, MysqlPipeline

if __name__ == '__main__':
    baidu = BaiduSpider()  # 实例化爬虫对象
    qiubai = QiubaiSpider()  # 实例化爬虫对象
    spiders = {baidu.name: baidu, qiubai.name: qiubai}
    pipelines = [BaiduPipeline(), QiubaiPipeline(), MysqlPipeline()]   # 注意这里导入的是实例, 而不是类对象, 因为类对象无法使用实例方法, 也就无法调用 process_item 来处理数据
    engine = Engine(spiders, pipelines)  # 创建引擎对象, 传入爬虫对象
    engine.start()  # 启动引擎

```

实现项目中传入多个中间件

目标
完成代码的重构, 实现多个中间件的效果

1. 为什么需要多个中间件
不同的中间件可以实现对请求或者是响应对象进行不同的处理, 实现结构, 让逻辑更加清晰

2. 在项目文件夹中创建middlewares文件

项目文件夹中的spider_middlewares.py: 

```python

class TestSpiderMiddleware1(object):

    def process_request(self, request):
        '''处理请求头, 添加默认的user-agent'''
        print("TestSpiderMiddleware1: process_request")
        return request

    def process_response(self, item):
        '''处理数据对象'''
        print("TestSpiderMiddleware1: process_response")
        return item


class TestSpiderMiddleware2(object):

    def process_request(self, request):
        '''处理请求头, 添加默认的user-agent'''
        print("TestSpiderMiddleware2: process_request")
        return request

    def process_response(self, item):
        '''处理数据对象'''
        print("TestSpiderMiddleware2: process_response")
        return item

```

项目文件夹中的downloader_middlewares.py:

```python

class TestDownloaderMiddleware1(object):

    def process_request(self, request):
        '''处理请求头, 添加默认的user-agent'''
        print("TestDownloaderMiddleware1: process_request")
        return request

    def process_response(self, item):
        '''处理数据对象'''
        print("TestDownloaderMiddleware1: process_response")
        return item


class TestDownloaderMiddleware2(object):

    def process_request(self, request):
        '''处理请求头, 添加默认的user-agent'''
        print("TestDownloaderMiddleware2: process_request")
        return request

    def process_response(self, item):
        '''处理数据对象'''
        print("TestDownloaderMiddleware2: process_response")
        return item

```

2. 修改项目文件夹中的main.py
为引擎传入多个中间件

```python
# spider_project/main.py
from spider_plus.core.engine import Engine    # 导入引擎

from spiders.baidu import BaiduSpider
from spiders.douban import DoubanSpider
from pipeline import BaiduPipeline, DoubanPipeline
from spider_middlewares import TestSpiderMiddleware1, TestSpiderMiddleware2
from downloader_middlewares import TestDownloaderMiddleware1, TestDownloaderMiddleware2


if __name__ == '__main__':
    baidu_spider = BaiduSpider()    # 实例化爬虫对象
    douban_spider = DoubanSpider()    # 实例化爬虫对象

    spiders = {BaiduSpider.name: baidu_spider, DoubanSpider.name: douban_spider}    # 爬虫们
    pipelines = [BaiduPipeline(), DoubanPipeline()]    # 管道们
    spider_mids = [TestSpiderMiddleware1(), TestSpiderMiddleware2()]    # 多个爬虫中间件
    downloader_mids = [TestDownloaderMiddleware1(), TestDownloaderMiddleware2()]    # 多个下载中间件

    engine = Engine(spiders, pipelines=pipelines, spider_mids=spider_mids, downloader_mids=downloader_mids)    # 传入爬虫对象
    engine.start()    # 启动引擎
```


3. 因此相应的的修改 engine.py
改为使用多个中间件

```python

# spider_plus/core/engine.py
# coding=utf-8
# 引擎
from datetime import datetime

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.middlewares.downloader_middlewares import DownloaderMiddleware
from spider_plus.middlewares.spider_middlewares import SpiderMiddleware
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from .pipeline import Pipeline
from .spider import Spider


class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self, spiders, pipelines=[], spider_mids=[], downloader_mids=[]):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        self.spiders = spiders  # 接收外部传入的爬虫对象, 字典
        self.scheduler = Scheduler()  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipelines = pipelines  # 初始化管道对象, 列表
        self.spider_mids = spider_mids  # 初始化爬虫中间件对象, 列表
        self.downloader_mids = downloader_mids  # 初始化下载器中间件对象, 列表
        # 为了使处理请求响应数据的方法能够正常退出, 定义两个变量, 当总的响应数量大于等于总的请求数量时, 所有请求都已经处理完毕, 就可以退出了
        self.total_request_num = 0  # 总的请求数
        self.total_response_num = 0  # 总的响应数

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时
        # 在引擎的调用执行结束后, 打印总的请求数量和总的响应数量.
        logger.info("总的请求数量: {}个".format(self.total_request_num))
        logger.info("总的响应数量: {}个".format(self.total_response_num))

    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        for spider_name, spider in self.spiders.items():  # 遍历 spiders 字典, 获取每个spider对象
            # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历
            for start_request in spider.start_requests():
                # 对start_request初始请求经过爬虫中间件进行处理
                for spider_mid in self.spider_mids:
                    start_request = spider_mid.process_request(start_request)

                # 在把初始请求添加到调度器中之前, 给它添加一个属性 spider_name, 记录它是哪个爬虫产生的请求, 以方便后面 _execute_request_response_item 中通过这个属性获取到对应的爬虫, 进而获取爬虫的 parse方法
                start_request.spider_name = spider_name

                # 2. 调用调度器的add_request方法, 添加request对象到调度器中
                self.scheduler.add_request(start_request)
                # 把request添加到调度器中之后, 把总请求数加1
                self.total_request_num += 1

    def _execute_request_response_item(self):
        '''处理单个请求, 从调度器取出, 发送请求, 获取响应, parse函数处理, 调度器处理'''
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        if request is None:  # 判断从调度器中取出来的request是否是None, 如果是None, 表示调度器为空, 就不进行任何进一步的处理
            return
        for downloader_mid in self.downloader_mids:
            # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
            request = downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)

        # 为了把 request中的meta传递给 response, 在调用下载器获取响应后, 给response添加一个meta属性即可
        response.meta = request.meta

        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        for downloader_mid in self.downloader_mids:
            response = downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        for spider_mid in self.spider_mids:
            response = spider_mid.process_response(response)

        # 根据请求对象的 spider_name 属性, 获取爬虫实例, 进而获取爬虫的 parse 方法
        spider = self.spiders.get(request.spider_name)
        # 获取 request 对象对应的响应的parse方法. getattr 从 self.spiders 中查找并返回 request的parse属性指定的方法
        # 对于糗事百科爬虫来说, 1-13页列表页中, 由于request对象没有指定parse方法, 所以会使用默认的 parse="parse", 而对于详情页, 则使用 request对象指定的 "parse_detail" 方法.
        parse = getattr(spider, request.parse)

        # 5. 利用爬虫的parse方法, 处理响应
        # 因为 spiders 的 parse 方法已经修改为生成器, 所以这里要进行遍历
        for result in parse(response):
            # 6. 判断结果的类型
            # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
            if isinstance(result, Request):
                for spider_mid in self.spider_mids:
                    # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
                    result = spider_mid.process_request(result)

                # 对于新的请求, 在保存到调度器之间也添加 spider_name 属性
                result.spider_name = request.spider_name

                self.scheduler.add_request(result)
                self.total_request_num += 1  # 请求加1
            # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
            else:
                # 遍历所有的管道, 对item进行处理
                for pipeline in self.pipelines:
                    # 必须要把处理的结果重新赋值给 result, 下一个管道才能在上一个管道的基础上进一步处理
                    result = pipeline.process_item(result, spider)

        # 整个函数都是处理单个请求, 整个函数执行完了, 单个请求才处理完, 此时总的响应数加1
        self.total_response_num += 1

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self._start_request()  # 初始化请求
        while True:
            self._execute_request_response_item()
            # 循环结束的条件
            if self.total_response_num >= self.total_request_num:
                break


if __name__ == '__main__':
    engine = Engine()
    engine.start()

```


动态导入模块

完成对现有代码的重构
1. 目前代码存在的问题
通过前面的代码编写, 我们已经能够完成大部分的任务, 但是在main.py 中的代码非常臃肿, 对应的我们可以在 settings.py 配置哪些爬虫, 管道, 中间件需要开启, 能够让整个代码的逻辑更加清晰

2. 模块动态导入的方法

利用 importlib.import_module 能够传入模块的路径, 即可实现根据模块的位置的字符串, 导入该模块的功能
在项目路径下新建 test.py, 插入如下代码观察现象

```python
class Test(object):
    def func(self):
        print("this is func")
```


新建 test_importlib.py

```python

import importlib

path = "test"
ret = importlib.import_module(path)
print(ret)

# importlib.import_module 结合 getattr 可以实现动态的导入模块中的类和方法
```

修改 test_importlib.py

```python
import importlib

path = "test"
ret = importlib.import_module(path)
print(ret)

cls = getattr(ret, "Test")
print(cls)

func = getattr(cls(), "func")
print(func)
```

如果把管道, 中间件的配置都放在 settings.py 中, 是以字符串的形式配置的, 就可以使用以上的方法来动态的加载对应的配置

新建 spider_project/test_importlib.py

```python
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


# pipelines
# BaiduPipeline
# <module 'pipelines' from 'D:\\David\\Desktop\\spider_plus_fw\\spider_project\\pipelines.py'>
# <class 'pipelines.BaiduPipeline'>
# 百度管道处理的数据:  abc
# pipelines
# QiubaiPipeline
# <module 'pipelines' from 'D:\\David\\Desktop\\spider_plus_fw\\spider_project\\pipelines.py'>
# <class 'pipelines.QiubaiPipeline'>
# pipelines
# MysqlPipeline
# <module 'pipelines' from 'D:\\David\\Desktop\\spider_plus_fw\\spider_project\\pipelines.py'>
# <class 'pipelines.MysqlPipeline'>
# 把数据写入到mysql数据库 baidu
```

对于 spider 爬虫类似的设置

新建 spider_project/try_importlib_spiders.py

```python
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


# spiders.baidu
# BaiduSpider
# <module 'spiders.baidu' from 'D:\\David\\Desktop\\spider_plus_fw\\spider_project\\spiders\\baidu.py'>
# baidu
# spiders.qiubai
# QiubaiSpider
# <module 'spiders.qiubai' from 'D:\\David\\Desktop\\spider_plus_fw\\spider_project\\spiders\\qiubai.py'>
# qiubai

```

2. 在settings中设置SPIDER, MIDDLEWARES
利用在配置文件中设置需要启用的爬虫类、管道类、中间件类, 如下: 

# 项目中的 settings.py

```python

import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO  # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'  # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = '日志.log'  # 默认日志文件名称

# 启用的爬虫
SPIDERS = [
    'spiders.baidu.BaiduSpider',
    'spiders.qiubai.QiubaiSpider'
]

# 启用的管道类
PIPELINES = [
    'pipelines.BaiduPipeline',
    'pipelines.QiubaiPipeline'
]

# 启用的爬虫中间件类
SPIDER_MIDDLEWARES = [
    'downloader_middlewares.TestDownloaderMiddleware2'
]

# 启用的下载器中间件类
DOWNLOADER_MIDDLEWARES = [
    'spider_middlewares.TestSpiderMiddleware1'
]

```


利用importlib模块, 在引擎中动态导入并实例化

```python
# coding=utf-8
# 引擎
import importlib

from datetime import datetime

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from spider_plus.conf.settings import SPIDERS, PIPELINES, DOWNLOADER_MIDDLEWARES, SPIDER_MIDDLEWARES


class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        self.spiders = self._auto_import_instances(SPIDERS, is_spider=True)  # 接收外部传入的爬虫对象, 字典
        self.scheduler = Scheduler()  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipelines = self._auto_import_instances(PIPELINES)  # 初始化管道对象, 列表
        self.spider_mids = self._auto_import_instances(SPIDER_MIDDLEWARES)  # 初始化爬虫中间件对象, 列表
        self.downloader_mids = self._auto_import_instances(DOWNLOADER_MIDDLEWARES)  # 初始化下载器中间件对象, 列表
        # 为了使处理请求响应数据的方法能够正常退出, 定义两个变量, 当总的响应数量大于等于总的请求数量时, 所有请求都已经处理完毕, 就可以退出了
        self.total_request_num = 0  # 总的请求数
        self.total_response_num = 0  # 总的响应数

    def _auto_import_instances(self, path=[], is_spider=False):
        '''
        根据配置文件, 实现模块的动态导入, 传入模块路径列表, 返回类的实例
        :param path: settings 中配置的要导入类的路径. 包含模块位置字符串的列表
        :param is_spider: 是否是爬虫. 爬虫是字典的形式, 所以需要进行单独的判断和处理
        :return: 返回爬虫, 管道, 中间件的实例
        '''
        if is_spider is True:
            instances = {}
        else:
            instances = []  # 存储对应类的实例对象

        for p in path:
            module_name = p[:p.rfind(".")]  # 取出模块名称
            module_name = p.rsplit(".", 1)[0]
            cls_name = p[p.rfind(".") + 1:]  # 取出类名称
            cls_name = p.rsplit(".", 1)[-1]
            module = importlib.import_module(module_name)  # 导入模块
            cls = getattr(module, cls_name)  # 根据类名称获取module下的类对象
            if is_spider is True:
                instances[cls.name] = cls()
            else:
                instances.append(cls())  # 实例化类对象
        return instances  # 返回类对象

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时
        # 在引擎的调用执行结束后, 打印总的请求数量和总的响应数量.
        logger.info("总的请求数量: {}个".format(self.total_request_num))
        logger.info("总的响应数量: {}个".format(self.total_response_num))

    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        for spider_name, spider in self.spiders.items():  # 遍历 spiders 字典, 获取每个spider对象
            # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历
            for start_request in spider.start_requests():
                # 对start_request初始请求经过爬虫中间件进行处理
                for spider_mid in self.spider_mids:
                    start_request = spider_mid.process_request(start_request)

                # 在把初始请求添加到调度器中之前, 给它添加一个属性 spider_name, 记录它是哪个爬虫产生的请求, 以方便后面 _execute_request_response_item 中通过这个属性获取到对应的爬虫, 进而获取爬虫的 parse方法
                start_request.spider_name = spider_name

                # 2. 调用调度器的add_request方法, 添加request对象到调度器中
                self.scheduler.add_request(start_request)
                # 把request添加到调度器中之后, 把总请求数加1
                self.total_request_num += 1

    def _execute_request_response_item(self):
        '''处理单个请求, 从调度器取出, 发送请求, 获取响应, parse函数处理, 调度器处理'''
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        if request is None:  # 判断从调度器中取出来的request是否是None, 如果是None, 表示调度器为空, 就不进行任何进一步的处理
            return
        for downloader_mid in self.downloader_mids:
            # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
            request = downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)

        # 为了把 request中的meta传递给 response, 在调用下载器获取响应后, 给response添加一个meta属性即可
        response.meta = request.meta

        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        for downloader_mid in self.downloader_mids:
            response = downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        for spider_mid in self.spider_mids:
            response = spider_mid.process_response(response)

        # 根据请求对象的 spider_name 属性, 获取爬虫实例, 进而获取爬虫的 parse 方法
        spider = self.spiders.get(request.spider_name)
        # 获取 request 对象对应的响应的parse方法. getattr 从 self.spiders 中查找并返回 request的parse属性指定的方法
        # 对于糗事百科爬虫来说, 1-13页列表页中, 由于request对象没有指定parse方法, 所以会使用默认的 parse="parse", 而对于详情页, 则使用 request对象指定的 "parse_detail" 方法.
        parse = getattr(spider, request.parse)

        # 5. 利用爬虫的parse方法, 处理响应
        # 因为 spiders 的 parse 方法已经修改为生成器, 所以这里要进行遍历
        for result in parse(response):
            # 6. 判断结果的类型
            # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
            if isinstance(result, Request):
                for spider_mid in self.spider_mids:
                    # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
                    result = spider_mid.process_request(result)

                # 对于新的请求, 在保存到调度器之间也添加 spider_name 属性
                result.spider_name = request.spider_name

                self.scheduler.add_request(result)
                self.total_request_num += 1  # 请求加1
            # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
            else:
                # 遍历所有的管道, 对item进行处理
                for pipeline in self.pipelines:
                    # 必须要把处理的结果重新赋值给 result, 下一个管道才能在上一个管道的基础上进一步处理
                    result = pipeline.process_item(result, spider)

        # 整个函数都是处理单个请求, 整个函数执行完了, 单个请求才处理完, 此时总的响应数加1
        self.total_response_num += 1

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self._start_request()  # 初始化请求
        while True:
            self._execute_request_response_item()
            # 循环结束的条件
            if self.total_response_num >= self.total_request_num:
                break


if __name__ == '__main__':
    engine = Engine()
    engine.start()
```

3. 修改main.py
这样main.py就不用再导入并传入那么多对象了: 

```python
# spider_project/main.py

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

```

去重原理

1. 去重的理解
其实就只是对以往数据进行一个比对, 判断是否已经存在

可大致分为: 对原始数据比对、对利用原始数据生成的特征值进行比对两种方式

原始数据比对很好理解, 就是比对的时候参照值就是原始数据；而利用特征值比对, 比如最典型的就是利用原始数据生成一个指纹, 比对的参照值就是这个指纹, 不是原始数据本身, 主要应用于单个原始数据比较大的情况, 另外一种常用就是布隆过滤器, 这种方式原始利用一种"特征值", 应用场景是海量数据的去重(但具有一定几率的误判)。

2. 爬虫请求去重原理和实现

根据请求的url、请求方法、请求参数、请求体进行唯一标识, 进行比对, 由于这四个数据加到一起, 内容较长, 因此使用求指纹的方式来进行去重判断。


指纹计算方法, 最常用的就是md5、sha1等hash加密算法, 来求指纹

具体实现如下: 

```python
# spider_plus/core/scheduler.py

# coding=utf-8
# 调度器

# 利用six模块实现py2和py3兼容
import six
from six.moves.queue import Queue
import w3lib.url
from hashlib import sha1

from spider_plus.utils.log import logger


class Scheduler(object):
    '''完成调试器模块的封装'''

    def __init__(self):
        self.queue = Queue()

        # 去重容器, 利用set类型存储每个请求的指纹
        self._filter_container = set()

        self.repeat_request_num = 0  # 记录重复的请求数量. 为什么要统计重复请求的数量. 之前在引擎中使用 "总的响应数量 == 总的请求数量" 来确定程序的退出, 如果有重复的请求, 就不会发送请求, 这个条件就永远不会满足. 需要把程序退出的条件修改为 "总的响应数量 + 总的重复数量 == 总的请求数量", 所以这里要记录重复的请求的数量

    def add_request(self, request):
        '''
        实现添加request到队列中
        :param request: 请求对象
        :return: None
        '''
        # 调用_filter_request来实现对请求对象的去重
        # 如果指纹不存在, 才把请求对象添加到队列中
        if self._filter_request(request):
            self.queue.put(request)

    def get_request(self):
        '''
        实现获取队列中的request对象
        :return: 请求对象
        '''
        # queue.get(), 默认 block=Ture, 即是堵塞的, 如果队列中没有对象, 就堵塞在这里. 需要修改为非堵塞的.
        # 非堵塞状态可以会报错, 所以使用try...except...
        try:
            return self.queue.get(block=False)
        except:
            return None

    def _filter_request(self, request):
        '''
        实现对请求对象的去重
        :param request: 请求对象
        :return: bool
        '''
        # 给 request对象添加一个fp属性, 保存指纹
        # 去重容器: 存储已经发过的请求的特征 url, 选用集合类型: set()
        # 利用请求的 url method data 求出一个指纹, 利用sha1
        request.fp = self._gen_fp(request)
        # 如果判断指纹不在指纹集合中, 就把它添加进去
        if request.fp not in self._filter_container:
            logger.info("添加新的请求: <%s>" % request.url)
            self._filter_container.add(request.fp)
            return True
        else:
            logger.info("发现重复的请求: <{} {}>".format(request.method, request.url))
            self.repeat_request_num += 1
            return False

    @staticmethod
    def _to_bytes(string):
        if six.PY2:  # 如果是python2环境
            if isinstance(string, str):  # str类型在py2中是字节类型
                return string
            else:  # 如果是python2的 unicode 类型, 转化为python2字节类型
                return string.encode("utf-8")
        elif six.PY3:  # 如果是python3环境
            if isinstance(string, str):
                return string.encode("utf-8")  # 转换为bytes类型
            else:
                return string  # 说明string是bytes类型, 直接返回

    def _gen_fp(self, request):
        '''
        对 url 地址, 请求体, 请求参数, 请求方法进行加密, 生成 request 对象的指纹
        :param request: request对象
        :return: 指纹字符串
        '''
        # 1. url 地址排序: 借助w3lib.url模块中的 canonicalize_url 方法
        url = w3lib.url.canonicalize_url(request.url)
        # 2. 请求方法 method, 不需要排序, 只要保持大小写一致就可以
        method = request.method.upper()  # 全大写
        # 3. 请求参数params. 排序. 如果有提供则是一个字典, 如果没有则是 None
        params = request.params if request.params is not None else {}  # 如果是None, 那么设为{}
        params = sorted(params.items(), key=lambda x: x[0])  # 按照key对字典进行排序, 结果将是一个列表
        # 4. 请求体data排序: 如果有提供则是一个字典, 如果没有则是None
        data = request.data if request.data is not None else {}  # 如果是None, 那么设为{}
        data = sorted(data.items(), key=lambda x: x[0])  # 按照key对字典进行排序, 结果将是一个列表

        # 5. 利用sha1算法, 计算指纹
        s1 = sha1()
        # 由于s1接收的只能是bytes类型(python3)、str类型(python2), 他们都是某种编码类型的(如utf-8、gbk)
        # 为了兼容py2和py3, 利用 _to_bytes 方法, 把所有的字符串转化为字节类型
        s1.update(self._to_bytes(url))  # 添加url地址
        s1.update(self._to_bytes(method))  # 添加请求方法
        s1.update(self._to_bytes(str(params)))  # 添加请求参数
        s1.update(self._to_bytes(str(data)))  # 添加请求体

        fp = s1.hexdigest()  # 提取16进制的sha1指纹字符串并返回
        return fp
```

修改 engine 模块

现在统计了总的重复数量, 所以, 在engine中阻塞的位置判断程序结束的条件: 成功的响应数 + 重复的数量 >= 总的请求数量 程序结束

```python
# spider_plus/core/engine.py

# coding=utf-8
# 引擎
import importlib

from datetime import datetime

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from spider_plus.conf.settings import SPIDERS, PIPELINES, DOWNLOADER_MIDDLEWARES, SPIDER_MIDDLEWARES


class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        self.spiders = self._auto_import_instances(SPIDERS, is_spider=True)  # 接收外部传入的爬虫对象, 字典
        self.scheduler = Scheduler()  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipelines = self._auto_import_instances(PIPELINES)  # 初始化管道对象, 列表
        self.spider_mids = self._auto_import_instances(SPIDER_MIDDLEWARES)  # 初始化爬虫中间件对象, 列表
        self.downloader_mids = self._auto_import_instances(DOWNLOADER_MIDDLEWARES)  # 初始化下载器中间件对象, 列表
        # 为了使处理请求响应数据的方法能够正常退出, 定义两个变量, 当总的响应数量大于等于总的请求数量时, 所有请求都已经处理完毕, 就可以退出了
        self.total_request_num = 0  # 总的请求数
        self.total_response_num = 0  # 总的响应数

    def _auto_import_instances(self, path=[], is_spider=False):
        '''
        根据配置文件, 实现模块的动态导入, 传入模块路径列表, 返回类的实例
        :param path: settings 中配置的要导入类的路径. 包含模块位置字符串的列表
        :param is_spider: 是否是爬虫. 爬虫是字典的形式, 所以需要进行单独的判断和处理
        :return: 返回爬虫, 管道, 中间件的实例
        '''
        if is_spider is True:
            instances = {}
        else:
            instances = []  # 存储对应类的实例对象

        for p in path:
            module_name = p[:p.rfind(".")]  # 取出模块名称
            module_name = p.rsplit(".", 1)[0]
            cls_name = p[p.rfind(".") + 1:]  # 取出类名称
            cls_name = p.rsplit(".", 1)[-1]
            module = importlib.import_module(module_name)  # 导入模块
            cls = getattr(module, cls_name)  # 根据类名称获取module下的类对象
            if is_spider is True:
                instances[cls.name] = cls()
            else:
                instances.append(cls())  # 实例化类对象
        return instances  # 返回类对象

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        logger.info("当前启动的爬虫: {}".format(SPIDERS))
        logger.info("当前开启的管道: {}".format(PIPELINES))
        logger.info("当前开启的下载器中间件: {}".format(DOWNLOADER_MIDDLEWARES))
        logger.info("当前开启的爬虫中间件: {}".format(SPIDER_MIDDLEWARES))
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时
        # 在引擎的调用执行结束后, 打印总的请求数量和总的响应数量.
        logger.info("总的请求数量: {}个".format(self.total_request_num))
        logger.info("总的响应数量: {}个".format(self.total_response_num))
        logger.info("总的重复数量: {}个".format(self.scheduler.repeat_request_num))

    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        for spider_name, spider in self.spiders.items():  # 遍历 spiders 字典, 获取每个spider对象
            # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历
            for start_request in spider.start_requests():
                # 对start_request初始请求经过爬虫中间件进行处理
                for spider_mid in self.spider_mids:
                    start_request = spider_mid.process_request(start_request)

                # 在把初始请求添加到调度器中之前, 给它添加一个属性 spider_name, 记录它是哪个爬虫产生的请求, 以方便后面 _execute_request_response_item 中通过这个属性获取到对应的爬虫, 进而获取爬虫的 parse方法
                start_request.spider_name = spider_name

                # 2. 调用调度器的add_request方法, 添加request对象到调度器中
                self.scheduler.add_request(start_request)
                # 把request添加到调度器中之后, 把总请求数加1
                self.total_request_num += 1

    def _execute_request_response_item(self):
        '''处理单个请求, 从调度器取出, 发送请求, 获取响应, parse函数处理, 调度器处理'''
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        if request is None:  # 判断从调度器中取出来的request是否是None, 如果是None, 表示调度器为空, 就不进行任何进一步的处理
            return
        for downloader_mid in self.downloader_mids:
            # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
            request = downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)

        # 为了把 request中的meta传递给 response, 在调用下载器获取响应后, 给response添加一个meta属性即可
        response.meta = request.meta

        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        for downloader_mid in self.downloader_mids:
            response = downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        for spider_mid in self.spider_mids:
            response = spider_mid.process_response(response)

        # 根据请求对象的 spider_name 属性, 获取爬虫实例, 进而获取爬虫的 parse 方法
        spider = self.spiders.get(request.spider_name)
        # 获取 request 对象对应的响应的parse方法. getattr 从 self.spiders 中查找并返回 request的parse属性指定的方法
        # 对于糗事百科爬虫来说, 1-13页列表页中, 由于request对象没有指定parse方法, 所以会使用默认的 parse="parse", 而对于详情页, 则使用 request对象指定的 "parse_detail" 方法.
        parse = getattr(spider, request.parse)

        # 5. 利用爬虫的parse方法, 处理响应
        # 因为 spiders 的 parse 方法已经修改为生成器, 所以这里要进行遍历
        for result in parse(response):
            # 6. 判断结果的类型
            # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
            if isinstance(result, Request):
                for spider_mid in self.spider_mids:
                    # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
                    result = spider_mid.process_request(result)

                # 对于新的请求, 在保存到调度器之间也添加 spider_name 属性
                result.spider_name = request.spider_name

                self.scheduler.add_request(result)
                self.total_request_num += 1  # 请求加1
            # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
            else:
                # 遍历所有的管道, 对item进行处理
                for pipeline in self.pipelines:
                    # 必须要把处理的结果重新赋值给 result, 下一个管道才能在上一个管道的基础上进一步处理
                    result = pipeline.process_item(result, spider)

        # 整个函数都是处理单个请求, 整个函数执行完了, 单个请求才处理完, 此时总的响应数加1
        self.total_response_num += 1

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self._start_request()  # 初始化请求
        while True:
            self._execute_request_response_item()
            # 循环结束的条件
            # 成功的响应数 + 重复的响应数量 >= 总的请求数量, 程序结束
            if self.total_response_num + self.scheduler.repeat_request_num >= self.total_request_num:
                break


if __name__ == '__main__':
    engine = Engine()
    engine.start()

```

修改 spider_project/spiders/baidu.py, 添加重复的请求

```python
# coding=utf-8
from spider_plus.core.spider import Spider
from spider_plus.http.request import Request
from spider_plus.item import Item
import urllib.parse


# 继承框架的爬虫基类
class BaiduSpider(Spider):
    name = "baidu"
    start_urls = ['http://www.douban.com', 'http://www.douban.com', 'http://www.baidu.com', ]  # 设置初始请求url

    def parse(self, response):
        yield Item(response.body[:20])
```

修改 spider_project/settings.py, 只启用 baidu 爬虫

```python
import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO  # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'  # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = '日志.log'  # 默认日志文件名称

# 启用的爬虫
SPIDERS = [
    'spiders.baidu.BaiduSpider',
    # 'spiders.qiubai.QiubaiSpider'
]

# 启用的管道类
PIPELINES = [
    'pipelines.BaiduPipeline',
    'pipelines.QiubaiPipeline'
]

# 启用的爬虫中间件类
SPIDER_MIDDLEWARES = [
    'downloader_middlewares.TestDownloaderMiddleware2'
]

# 启用的下载器中间件类
DOWNLOADER_MIDDLEWARES = [
    'spider_middlewares.TestSpiderMiddleware1'
]

重新安装框架, 并运行main

# 2019-04-26 15:15:54 engine.py[line:63] INFO: 爬虫启动: 2019-04-26 15:15:54.838816
# 2019-04-26 15:15:54 engine.py[line:64] INFO: 当前启动的爬虫: ['spiders.baidu.BaiduSpider']
# 2019-04-26 15:15:54 engine.py[line:65] INFO: 当前开启的管道: ['pipelines.BaiduPipeline', 'pipelines.QiubaiPipeline']
# 2019-04-26 15:15:54 engine.py[line:66] INFO: 当前开启的下载器中间件: ['spider_middlewares.TestSpiderMiddleware1']
# 2019-04-26 15:15:54 engine.py[line:67] INFO: 当前开启的爬虫中间件: ['downloader_middlewares.TestDownloaderMiddleware2']
# 2019-04-26 15:15:54 scheduler.py[line:59] INFO: 添加新的请求: <http://www.douban.com>
# 2019-04-26 15:15:54 scheduler.py[line:63] INFO: 发现重复的请求: <GET http://www.douban.com>
# 2019-04-26 15:15:54 scheduler.py[line:59] INFO: 添加新的请求: <http://www.baidu.com>
# 2019-04-26 15:15:55 downloader.py[line:26] INFO: <200 https://www.douban.com/>
# 百度管道处理的数据:  b'<!DOCTYPE HTML>\n<html lang="zh'
# 2019-04-26 15:15:55 downloader.py[line:26] INFO: <200 http://www.baidu.com/>
# 百度管道处理的数据:  b'<!DOCTYPE html>\r\n<!--STATUS OK'
# 2019-04-26 15:15:55 engine.py[line:70] INFO: 爬虫结束: 2019-04-26 15:15:55.491820
# 2019-04-26 15:15:55 engine.py[line:71] INFO: 爬虫运行时间: 0.653004
# 2019-04-26 15:15:55 engine.py[line:73] INFO: 总的请求数量: 3个
# 2019-04-26 15:15:55 engine.py[line:74] INFO: 总的响应数量: 2个
# 2019-04-26 15:15:55 engine.py[line:75] INFO: 总的重复数量: 1个
```

利用线程池实现异步

1. 异步任务分析: 
1.1. 在引擎中, 实现的主要功能如下图, 
上面的方框中是关于start_urls中的请求处理
下面的方框中是一个请求从调度器取出请求, 进行下载之后交给爬虫解析再交给管道的过程 在以上两个过程中, 他们之间没有直接的联系, 都可以通过异步多线程的方式分别实现, 加快程序执行的速度 异步任务分析
1.2 那么具体该如何实现该逻辑
multiprocessing.dummy 提供的Pool 类具有 apply_async 的方法, 能够异步的执行让他运行的函数
apply_async方法能够接收一个callback, 即其中的函数执行完成之后继续会做的事情, 在这里, 我们可以定义一个callback, 其中让他继续执行上图中下方框的任务, 同时给他一个停止条件, 
2. 利用回调实现循环
利用回调实现递归, 可以达到循环的目的

```python
# spider_plus/core/engine.py
# coding=utf-8
# 引擎
import time
import importlib

from datetime import datetime
from multiprocessing.dummy import Pool    # 导入线程池对象

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from spider_plus.conf.settings import SPIDERS, PIPELINES, DOWNLOADER_MIDDLEWARES, SPIDER_MIDDLEWARES


class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        self.spiders = self._auto_import_instances(SPIDERS, is_spider=True)  # 接收外部传入的爬虫对象, 字典
        self.scheduler = Scheduler()  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipelines = self._auto_import_instances(PIPELINES)  # 初始化管道对象, 列表
        self.spider_mids = self._auto_import_instances(SPIDER_MIDDLEWARES)  # 初始化爬虫中间件对象, 列表
        self.downloader_mids = self._auto_import_instances(DOWNLOADER_MIDDLEWARES)  # 初始化下载器中间件对象, 列表
        # 为了使处理请求响应数据的方法能够正常退出, 定义两个变量, 当总的响应数量大于等于总的请求数量时, 所有请求都已经处理完毕, 就可以退出了
        self.total_request_num = 0  # 总的请求数
        self.total_response_num = 0  # 总的响应数
        self.pool = Pool()   # 实例化线程池对象. 线程池的大小默认为cpu的个数, 电脑是单核时线程池的大小就为 1, 可以手动指定线程池的大小
        self.is_running = False  # 程序是否处理运行状态, 依据此状态来决定程序是否退出. 当程序开始运行时, 设置此参数为 Ture, 当所有的请求执行结束后, 设置此参数为 False, 此时程序就退出.

    def _auto_import_instances(self, path=[], is_spider=False):
        '''
        根据配置文件, 实现模块的动态导入, 传入模块路径列表, 返回类的实例
        :param path: settings 中配置的要导入类的路径. 包含模块位置字符串的列表
        :param is_spider: 是否是爬虫. 爬虫是字典的形式, 所以需要进行单独的判断和处理
        :return: 返回爬虫, 管道, 中间件的实例
        '''
        if is_spider is True:
            instances = {}
        else:
            instances = []  # 存储对应类的实例对象

        for p in path:
            module_name = p[:p.rfind(".")]  # 取出模块名称
            module_name = p.rsplit(".", 1)[0]
            cls_name = p[p.rfind(".") + 1:]  # 取出类名称
            cls_name = p.rsplit(".", 1)[-1]
            module = importlib.import_module(module_name)  # 导入模块
            cls = getattr(module, cls_name)  # 根据类名称获取module下的类对象
            if is_spider is True:
                instances[cls.name] = cls()
            else:
                instances.append(cls())  # 实例化类对象
        return instances  # 返回类对象

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        logger.info("当前启动的爬虫: {}".format(SPIDERS))
        logger.info("当前开启的管道: {}".format(PIPELINES))
        logger.info("当前开启的下载器中间件: {}".format(DOWNLOADER_MIDDLEWARES))
        logger.info("当前开启的爬虫中间件: {}".format(SPIDER_MIDDLEWARES))
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时
        # 在引擎的调用执行结束后, 打印总的请求数量和总的响应数量.
        logger.info("总的请求数量: {}个".format(self.total_request_num))
        logger.info("总的响应数量: {}个".format(self.total_response_num))
        logger.info("总的重复数量: {}个".format(self.scheduler.repeat_request_num))

    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        for spider_name, spider in self.spiders.items():  # 遍历 spiders 字典, 获取每个spider对象
            # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历
            for start_request in spider.start_requests():
                # 对start_request初始请求经过爬虫中间件进行处理
                for spider_mid in self.spider_mids:
                    start_request = spider_mid.process_request(start_request)

                # 在把初始请求添加到调度器中之前, 给它添加一个属性 spider_name, 记录它是哪个爬虫产生的请求, 以方便后面 _execute_request_response_item 中通过这个属性获取到对应的爬虫, 进而获取爬虫的 parse方法
                start_request.spider_name = spider_name

                # 2. 调用调度器的add_request方法, 添加request对象到调度器中
                self.scheduler.add_request(start_request)
                # 把request添加到调度器中之后, 把总请求数加1
                self.total_request_num += 1

    def _execute_request_response_item(self):
        '''处理单个请求, 从调度器取出, 发送请求, 获取响应, parse函数处理, 调度器处理'''
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        if request is None:  # 判断从调度器中取出来的request是否是None, 如果是None, 表示调度器为空, 就不进行任何进一步的处理
            return
        for downloader_mid in self.downloader_mids:
            # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
            request = downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)

        # 为了把 request中的meta传递给 response, 在调用下载器获取响应后, 给response添加一个meta属性即可
        response.meta = request.meta

        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        for downloader_mid in self.downloader_mids:
            response = downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        for spider_mid in self.spider_mids:
            response = spider_mid.process_response(response)

        # 根据请求对象的 spider_name 属性, 获取爬虫实例, 进而获取爬虫的 parse 方法
        spider = self.spiders.get(request.spider_name)
        # 获取 request 对象对应的响应的parse方法. getattr 从 self.spiders 中查找并返回 request的parse属性指定的方法
        # 对于糗事百科爬虫来说, 1-13页列表页中, 由于request对象没有指定parse方法, 所以会使用默认的 parse="parse", 而对于详情页, 则使用 request对象指定的 "parse_detail" 方法.
        parse = getattr(spider, request.parse)

        # 5. 利用爬虫的parse方法，处理响应
        # 因为 spiders 的 parse 方法已经修改为生成器, 所以这里要进行遍历
        for result in parse(response):
            # 6. 判断结果的类型
            # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
            if isinstance(result, Request):
                for spider_mid in self.spider_mids:
                    # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
                    result = spider_mid.process_request(result)

                # 对于新的请求, 在保存到调度器之间也添加 spider_name 属性
                result.spider_name = request.spider_name

                self.scheduler.add_request(result)
                self.total_request_num += 1  # 请求加1
            # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
            else:
                # 遍历所有的管道, 对item进行处理
                for pipeline in self.pipelines:
                    # 必须要把处理的结果重新赋值给 result, 下一个管道才能在上一个管道的基础上进一步处理
                    result = pipeline.process_item(result, spider)

        # 整个函数都是处理单个请求, 整个函数执行完了, 单个请求才处理完, 此时总的响应数加1
        self.total_response_num += 1

    def _callback(self, temp):   # 必须有 temp 参数
        '''执行新的请求的回调函数, 实现循环'''
        if self.is_running is True:  # 如果还没满足退出条件, 那么继续添加新任务, 否则不继续添加, 终止回调函数, 达到退出循环的目的
            self.pool.apply_async(self._execute_request_response_item, callback=self._callback)

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self.is_running = True  # 启动引擎时, 设置 is_running 状态为True
        # self._start_request()  # 初始化请求

        # 向调度器添加初始请求, 初始化请求
        self.pool.apply_async(self._start_request)  # 使用异步, 当主线程执行到这里时, 会使用线程池中的一个子线程来执行这个函数, 主线程继续向下执行

        # 虽然调用的是异步的 apply_async 方法, 但调用的过程依然是同步的, 执行完一个 "请求-响应-数据" 的流程之后, 才调用 _callback 方法, 这时的并发量还是非常低的, 还是1. 为了提高并发量, 可以把这句话放到一个循环中执行. 如 for i in range(3): 这样就会有 3 个并发线程同时去执行
        self.pool.apply_async(self._execute_request_response_item, callback=self._callback)  # 利用回调实现循环. 同样会使用一个子线程来执行这个函数

        # 设置循环, 处理多个请求
        # 使用循环让主线程处理堵塞状态, 一直等到子线程执行结束才退出循环
        while True:
            time.sleep(0.0001)  # 避免主线程 cpu 空转, 降低资源消耗
            # self._execute_request_response_item()   # 处理单个请求
            # 循环结束的条件
            # 成功的响应数 + 重复的响应数量 >= 总的请求数量, 程序结束
            if self.total_request_num != 0:  # 刚开始时总的请求数量为0, 只有当总请求数不为0时, 即至少有一个请求或响应后, 才有可能退出
                if self.total_response_num + self.scheduler.repeat_request_num >= self.total_request_num:
                    self.is_running = False  # 满足循环退出条件后, 设置运行状态为 False
                    break

        # 在爬虫的运行结束后, 可能线程池与服务器链接还没有断开, 相当于子线程的执行还未完成, 程序会处于等待状态. 所以在爬虫中一般不会去执行 pool.close() 和 pool.join()
        # self.pool.close()
        # self.pool.join()

if __name__ == '__main__':
    engine = Engine()
    engine.start()

```

3. 实现异步并发控制


虽然调用的是异步的 apply_async 方法, 但调用的过程依然是同步的, 执行完一个 "请求-响应-数据" 的流程之后, 才调用 _callback 方法, 这时的并发量还是非常低的, 还是1. 为了提高并发量, 可以把这句话放到一个循环中执行. 如 for i in range(3): 这样就会有 3 个并发线程同时去执行

在配置文件中设置最大并发数, 并在引擎中使用

修改 spider_plus/conf/default_settings.py, 设置默认的最大并发数

```python

import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO    # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'   # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = 'log.log'    # 默认日志文件名称

# 设置最大并发数量
CONCOURRENT_REQUEST = 5


修改 spider_project/settings.py, 添加用户自定义的最大并发数


import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO  # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'  # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = '日志.log'  # 默认日志文件名称

# 启用的爬虫
SPIDERS = [
    'spiders.baidu.BaiduSpider',
    # 'spiders.qiubai.QiubaiSpider'
]

# 启用的管道类
PIPELINES = [
    'pipelines.BaiduPipeline',
    'pipelines.QiubaiPipeline'
]

# 启用的爬虫中间件类
SPIDER_MIDDLEWARES = [
    'downloader_middlewares.TestDownloaderMiddleware2'
]

# 启用的下载器中间件类
DOWNLOADER_MIDDLEWARES = [
    'spider_middlewares.TestSpiderMiddleware1'
]

# 设置最大并发数量
CONCOURRENT_REQUEST = 5
```


修改引擎, 添加并发处理

```python

# spider_plus/core/engine.py

from spider_plus.conf.settings import SPIDERS, PIPELINES, DOWNLOADER_MIDDLEWARES, SPIDER_MIDDLEWARES, CONCOURRENT_REQUEST


class Engine(object):

    ......

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self.is_running = True  # 启动引擎时, 设置 is_running 状态为True
        # self._start_request()  # 初始化请求

        # 向调度器添加初始请求, 初始化请求
        self.pool.apply_async(self._start_request)  # 使用异步, 当主线程执行到这里时, 会使用线程池中的一个子线程来执行这个函数, 主线程继续向下执行

        # 虽然调用的是异步的 apply_async 方法, 但调用的过程依然是同步的, 执行完一个 "请求-响应-数据" 的流程之后, 才调用 _callback 方法, 这时的并发量还是非常低的, 还是1. 为了提高并发量, 可以把这句话放到一个循环中执行. 如 for i in range(3): 这样就会有 3 个并发线程同时去执行
        for i in range(CONCOURRENT_REQUEST):
            # 利用回调实现循环. 同样会使用一个子线程来执行这个函数
            self.pool.apply_async(self._execute_request_response_item, callback=self._callback)

        # 设置循环, 处理多个请求
        # 使用循环让主线程处理堵塞状态, 一直等到子线程执行结束才退出循环
        while True:
            time.sleep(0.0001)  # 避免主线程 cpu 空转, 降低资源消耗
            # self._execute_request_response_item()   # 处理单个请求
            # 循环结束的条件
            # 成功的响应数 + 重复的响应数量 >= 总的请求数量, 程序结束
            if self.total_request_num != 0:  # 刚开始时总的请求数量为0, 只有当总请求数不为0时, 即至少有一个请求或响应后, 才有可能退出
                if self.total_response_num + self.scheduler.repeat_request_num >= self.total_request_num:
                    self.is_running = False  # 满足循环退出条件后, 设置运行状态为 False
                break
```


4. 对异步任务进行异常控制, 增加异常回调函数 error_callback

error_callback 处理线程执行过程中的异常

```python
# spider_plus/core/engine.py
class Engine(object):

    ......


    def _error_callback(self, exception):
        '''异常回调函数'''
        try:
            raise exception  # 抛出异常后, 才能被日志进行完整记录下来
        except Exception as e:
            logger.exception(e)

    def _callback(self, temp):  # 必须有 temp 参数
        '''执行新的请求的回调函数, 实现循环'''
        if self.is_running is True:  # 如果还没满足退出条件, 那么继续添加新任务, 否则不继续添加, 终止回调函数, 达到退出循环的目的
            self.pool.apply_async(self._execute_request_response_item, callback=self._callback,
                                  error_callback=self._error_callback)

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self.is_running = True  # 启动引擎时, 设置 is_running 状态为True
        # self._start_request()  # 初始化请求

        # 向调度器添加初始请求, 初始化请求
        self.pool.apply_async(self._start_request, error_callback=self._error_callback)  # 使用异步, 当主线程执行到这里时, 会使用线程池中的一个子线程来执行这个函数, 主线程继续向下执行

        # 虽然调用的是异步的 apply_async 方法, 但调用的过程依然是同步的, 执行完一个 "请求-响应-数据" 的流程之后, 才调用 _callback 方法, 这时的并发量还是非常低的, 还是1. 为了提高并发量, 可以把这句话放到一个循环中执行. 如 for i in range(3): 这样就会有 3 个并发线程同时去执行
        for i in range(CONCOURRENT_REQUEST):
            # 利用回调实现循环. 同样会使用一个子线程来执行这个函数
            self.pool.apply_async(self._execute_request_response_item, callback=self._callback, error_callback=self._error_callback)

        # 设置循环, 处理多个请求
        # 使用循环让主线程处理堵塞状态, 一直等到子线程执行结束才退出循环
        while True:
            time.sleep(0.0001)  # 避免主线程 cpu 空转, 降低资源消耗
            # self._execute_request_response_item()   # 处理单个请求
            # 循环结束的条件
            # 成功的响应数 + 重复的响应数量 >= 总的请求数量, 程序结束
            if self.total_request_num != 0:  # 刚开始时总的请求数量为0, 只有当总请求数不为0时, 即至少有一个请求或响应后, 才有可能退出
                if self.total_response_num + self.scheduler.repeat_request_num >= self.total_request_num:
                    self.is_running = False  # 满足循环退出条件后, 设置运行状态为 False
                    break

        # 在爬虫的运行结束后, 可能线程池与服务器链接还没有断开, 相当于子线程的执行还未完成, 程序会处于等待状态. 所以在爬虫中一般不会去执行 pool.close() 和 pool.join()
        # self.pool.close()
        # self.pool.join()
```

修改 spider_project/settings.py, 设置 CONCOURRENT_REQUEST = 1, 运行爬虫, 再 设置 CONCOURRENT_REQUEST = 5, 再次运行爬虫, 观察二者运行的不同



使用gevent的Pool实现异步并发

1. 为什么使用gevent
对于I/O密集型任务，gevent能对性能做很大提升的，协程的创建、调度开销都比线程小的多。

2. 通过配置文件设置属性，来判断所使用的异步方式

修改 spider_plus/default_settings.py, 添加异步方式的设置项

```python
import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO    # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'   # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = 'log.log'    # 默认日志文件名称

# 设置最大并发数量
CONCOURRENT_REQUEST = 5

# 异步方式  thread, coroutine
ASYNC_TYPE = 'coroutine'
# ASYNC_TYPE = 'thread'
```

修改 spider_project/settings.py, 添加用户自定义的异步方式配置项

```python
import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO  # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'  # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = '日志.log'  # 默认日志文件名称

# 启用的爬虫
SPIDERS = [
    'spiders.baidu.BaiduSpider',
    'spiders.qiubai.QiubaiSpider'
]

# 启用的管道类
PIPELINES = [
    'pipelines.BaiduPipeline',
    'pipelines.QiubaiPipeline'
]

# 启用的爬虫中间件类
SPIDER_MIDDLEWARES = [
    'downloader_middlewares.TestDownloaderMiddleware2'
]

# 启用的下载器中间件类
DOWNLOADER_MIDDLEWARES = [
    'spider_middlewares.TestSpiderMiddleware1'
]

# 设置最大并发数量
CONCOURRENT_REQUEST = 5

# 异步方式  thread, coroutine
ASYNC_TYPE = 'coroutine'
# ASYNC_TYPE = 'thread'
```

3. 让gevent的Pool和线程池Pool的接口一致
因此需要单独对gevent的Pool进行一下修改，具体如下:  在spider_plus下创建async包，随后创建coroutine.py模块

```python
# spider_plus/async/coroutine.py

from gevent.pool import Pool as BasePool
import gevent.monkey
gevent.monkey.patch_all()    # 打补丁，替换内置的模块


class Pool(BasePool):
    '''
    由于gevent的Pool的没有close方法，也没有异常回调函数, 需要对gevent的Pool进行一些处理，实现与线程池一样接口，实现线程和协程的无缝转换
    重写 apply_async 方法, 添加 error_callback, 使其具有和线程池一样的接口
    添加 close 方法
    '''
    def apply_async(self, func, args=None, kwds=None, callback=None, error_callback=None):
        return super().apply_async(func, args=args, kwds=kwds, callback=callback)

    def close(self):
        '''什么都不需要执行'''
        pass
```

4. 在引擎中使用上: 

```python
# spider_plus/core/engine.py

# coding=utf-8
# 引擎
import time
import importlib

from datetime import datetime

# 为什么要把导入 gevent.Pool 的操作放在最前面, 由于打patch补丁是为了替换掉socket为非阻塞的, 而下载器 Downloader 中正好使用了requests模块，如果在这之后导入协程池，会导致requests中使用的socket没有被替换成功, 从而有可能导致使用出现问题
from spider_plus.conf.settings import ASYNC_TYPE
# 判断使用什么异步模式，改用对应的异步池
if ASYNC_TYPE == 'thread':
    from multiprocessing.dummy import Pool    # 导入线程池对象
elif ASYNC_TYPE == 'coroutine':
    from spider_plus.async.coroutine import Pool
    # from gevent.monkey import patch_all
    # patch_all()
else:
    raise Exception("不支持的异步类型: {},".format(ASYNC_TYPE))

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from spider_plus.conf.settings import SPIDERS, PIPELINES, DOWNLOADER_MIDDLEWARES, SPIDER_MIDDLEWARES, CONCOURRENT_REQUEST


class Engine(object):
    ......

```

重装安装框架, 运行 main.py, 修改 spider_project/settings.py 中的异步方式, 修改为 thread, 再次运行. 查看效果的不同



框架升级 -- 分布式爬虫设计原理及其实现

1. 分布式爬虫原理
分布式爬虫设计原理:  多台服务器同时抓取数据, 请求和指纹存储在同一个redis中

2. 实现方案
利用redis实现队列

注意pickle模块的使用: 如果将对象存入redis中，需要先将request对象序列化为二进制数据，取出后反序列化就可以再得到原始对象

接口定义一致性: 利用 redis 实现一个队列 Queue，类似于使用线程还是协程实现分布式一样, 使其接口同 python 的内置队列接口一致，可以实现无缝转换

```python

# spider_plus/utils/queue.py

import time
import pickle

import redis
from six.moves import queue as BaseQueue

# redis队列默认配置
REDIS_QUEUE_NAME = 'request_queue'   # 在实际运行的过程中, 队列名是根据爬虫名称自己定义的, 所以这个字段可有可无
REDIS_QUEUE_HOST = 'localhost'
REDIS_QUEUE_PORT = 6379
REDIS_QUEUE_DB = 10


# 利用redis实现一个Queue，使其接口同python的内置队列接口一致，可以实现无缝转换
class Queue(object):
    """
    A Queue like message built over redis
    """

    Empty = BaseQueue.Empty  # BaseQueue 即为 python 中内置的队列. BaseQueue.Empty 即为 queue 的 Empty 属性, 即队列满了的属性
    Full = BaseQueue.Full
    max_timeout = 0.3

    def __init__(self, maxsize=0, name=REDIS_QUEUE_NAME, host=REDIS_QUEUE_HOST, port=REDIS_QUEUE_PORT, db=REDIS_QUEUE_DB,
                lazy_limit=True, password=None):
        """
        Constructor for RedisQueue
        maxsize:    an integer that sets the upperbound limit on the number of
                    items that can be placed in the queue.
        lazy_limit: redis queue is shared via instance, a lazy size limit is used
                    for better performance.
        """
        self.name = name
        self.redis = redis.StrictRedis(host=host, port=port, db=db, password=password)
        self.maxsize = maxsize
        self.lazy_limit = lazy_limit
        self.last_qsize = 0

    def qsize(self):
        self.last_qsize = self.redis.llen(self.name)
        return self.last_qsize

    def empty(self):
        if self.qsize() == 0:
            return True
        else:
            return False

    def full(self):
        if self.maxsize and self.qsize() >= self.maxsize:
            return True
        else:
            return False

    def put_nowait(self, obj):
        if self.lazy_limit and self.last_qsize < self.maxsize:
            pass
        elif self.full():
            raise self.Full
        # pickle.dumps 把一个对象转换为二进制字节, 然后添加到redis的列表中
        self.last_qsize = self.redis.rpush(self.name, pickle.dumps(obj))
        return True

    def put(self, obj, block=True, timeout=None):   # block=Ture, 如果队列已满, 就会处理堵塞和等待状态
        if not block:
            return self.put_nowait(obj)

        start_time = time.time()
        while True:
            try:
                return self.put_nowait(obj)
            except self.Full:
                if timeout:
                    lasted = time.time() - start_time
                    if timeout > lasted:
                        time.sleep(min(self.max_timeout, timeout - lasted))
                    else:
                        raise
                else:
                    time.sleep(self.max_timeout)

    def get_nowait(self):
        ret = self.redis.lpop(self.name)
        if ret is None:
            raise self.Empty  # 如果队列为空, 就抛出队列为空的异常
        # 把二进制的数据反序列化为 python 对象
        return pickle.loads(ret)

    def get(self, block=True, timeout=None):
        if not block:
            return self.get_nowait()

        start_time = time.time()
        while True:
            try:
                return self.get_nowait()
            except self.Empty:
                if timeout:
                    lasted = time.time() - start_time
                    if timeout > lasted:
                        time.sleep(min(self.max_timeout, timeout - lasted))
                    else:
                        raise
                else:
                    time.sleep(self.max_timeout)

```


把 redis 的相关配置放在 settings 文件中

修改 spider_plus/conf/default_settings.py

```python

import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO    # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'   # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = 'log.log'    # 默认日志文件名称

# 设置最大并发数量
CONCOURRENT_REQUEST = 5

# 异步方式  thread, coroutine
ASYNC_TYPE = 'coroutine'
# ASYNC_TYPE = 'thread'

# redis队列默认配置, 存储 request 请求
REDIS_QUEUE_NAME = 'request_queue'   # 在实际运行的过程中, 队列名是根据爬虫名称自己定义的, 所以这个字段可有可无
REDIS_QUEUE_HOST = 'localhost'
REDIS_QUEUE_PORT = 6379
REDIS_QUEUE_DB = 0    # 默认使用 0 号数据库

```


修改 spider_project/settings.py

```python

import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO  # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'  # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = '日志.log'  # 默认日志文件名称

# 启用的爬虫
SPIDERS = [
    'spiders.baidu.BaiduSpider',
    'spiders.qiubai.QiubaiSpider'
]

# 启用的管道类
PIPELINES = [
    'pipelines.BaiduPipeline',
    'pipelines.QiubaiPipeline'
]

# 启用的爬虫中间件类
SPIDER_MIDDLEWARES = [
    'downloader_middlewares.TestDownloaderMiddleware2'
]

# 启用的下载器中间件类
DOWNLOADER_MIDDLEWARES = [
    'spider_middlewares.TestSpiderMiddleware1'
]

# 设置最大并发数量
CONCOURRENT_REQUEST = 5

# 异步方式  thread, coroutine
# ASYNC_TYPE = 'coroutine'
ASYNC_TYPE = 'thread'


# redis队列默认配置
REDIS_QUEUE_NAME = 'request_queue'   # 在实际运行的过程中, 队列名是根据爬虫名称自己定义的, 所以这个字段可有可无
REDIS_QUEUE_HOST = 'localhost'
REDIS_QUEUE_PORT = 6379
REDIS_QUEUE_DB = 10

```

修改 utils.py, 从 settings 中导入 redis 数据库的配置

```python
import time
import pickle

import redis
from six.moves import queue as BaseQueue
from spider_plus.conf.settings import REDIS_QUEUE_NAME, REDIS_QUEUE_HOST, REDIS_QUEUE_PORT, REDIS_QUEUE_DB


# 利用redis实现一个Queue，使其接口同python的内置队列接口一致，可以实现无缝转换
class Queue(object):
    """
    A Queue like message built over redis
    """

    Empty = BaseQueue.Empty  # BaseQueue 即为 python 中内置的队列. BaseQueue.Empty 即为 queue 的 Empty 属性, 即队列满了的属性
    Full = BaseQueue.Full
    max_timeout = 0.3

    def __init__(self, maxsize=0, name=REDIS_QUEUE_NAME, host=REDIS_QUEUE_HOST, port=REDIS_QUEUE_PORT, db=REDIS_QUEUE_DB, lazy_limit=True, password=None):
        """
        Constructor for RedisQueue
        maxsize:    an integer that sets the upperbound limit on the number of
                    items that can be placed in the queue.
        lazy_limit: redis queue is shared via instance, a lazy size limit is used
                    for better performance.
        """
        self.name = name
        self.redis = redis.StrictRedis(host=host, port=port, db=db, password=password)
        self.maxsize = maxsize
        self.lazy_limit = lazy_limit
        self.last_qsize = 0

    def qsize(self):
        self.last_qsize = self.redis.llen(self.name)
        return self.last_qsize

    def empty(self):
        if self.qsize() == 0:
            return True
        else:
            return False

    def full(self):
        if self.maxsize and self.qsize() >= self.maxsize:
            return True
        else:
            return False

    def put_nowait(self, obj):
        if self.lazy_limit and self.last_qsize < self.maxsize:
            pass
        elif self.full():
            raise self.Full
        # pickle.dumps 把一个对象转换为二进制字节, 然后添加到redis的列表中
        self.last_qsize = self.redis.rpush(self.name, pickle.dumps(obj))
        return True

    def put(self, obj, block=True, timeout=None):  # block=Ture, 如果队列已满, 就会处理堵塞和等待状态
        if not block:
            return self.put_nowait(obj)

        start_time = time.time()
        while True:
            try:
                return self.put_nowait(obj)
            except self.Full:
                if timeout:
                    lasted = time.time() - start_time
                    if timeout > lasted:
                        time.sleep(min(self.max_timeout, timeout - lasted))
                    else:
                        raise
                else:
                    time.sleep(self.max_timeout)

    def get_nowait(self):
        ret = self.redis.lpop(self.name)
        if ret is None:
            raise self.Empty  # 如果队列为空, 就抛出队列为空的异常
        # 把二进制的数据反序列化为 python 对象
        return pickle.loads(ret)

    def get(self, block=True, timeout=None):
        if not block:
            return self.get_nowait()

        start_time = time.time()
        while True:
            try:
                return self.get_nowait()
            except self.Empty:
                if timeout:
                    lasted = time.time() - start_time
                    if timeout > lasted:
                        time.sleep(min(self.max_timeout, timeout - lasted))
                    else:
                        raise
                else:
                    time.sleep(self.max_timeout)

```

2.通过配置文件选择是否启用分布式: 

修改 spider_plus/conf/default_settings.py

```python

import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO    # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'   # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = 'log.log'    # 默认日志文件名称

# 设置最大并发数量
CONCOURRENT_REQUEST = 5

# 异步方式  thread, coroutine
ASYNC_TYPE = 'coroutine'
# ASYNC_TYPE = 'thread'

# redis队列默认配置
REDIS_QUEUE_NAME = 'request_queue'   # 在实际运行的过程中, 队列名是根据爬虫名称自己定义的, 所以这个字段可有可无
REDIS_QUEUE_HOST = 'localhost'
REDIS_QUEUE_PORT = 6379
REDIS_QUEUE_DB = 10

# 设置是否需要持久化和分布式
# 设置调度器的内容, 即请求对象是否要持久化
# 如果是 True, 那么就是使用分布式, 同时也是基于请求的增量式爬虫
# 如果是 False, 不会使用 redis 队列, 而是使用 python 的 set 存储指纹和请求
SCHEDULER_PERSIST = True

```

修改 spider_project/settings.py

```python

import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO  # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'  # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = '日志.log'  # 默认日志文件名称

# 启用的爬虫
SPIDERS = [
    'spiders.baidu.BaiduSpider',
    'spiders.qiubai.QiubaiSpider'
]

# 启用的管道类
PIPELINES = [
    'pipelines.BaiduPipeline',
    'pipelines.QiubaiPipeline'
]

# 启用的爬虫中间件类
SPIDER_MIDDLEWARES = [
    'downloader_middlewares.TestDownloaderMiddleware2'
]

# 启用的下载器中间件类
DOWNLOADER_MIDDLEWARES = [
    'spider_middlewares.TestSpiderMiddleware1'
]

# 设置最大并发数量
CONCOURRENT_REQUEST = 5

# 异步方式  thread, coroutine
# ASYNC_TYPE = 'coroutine'
ASYNC_TYPE = 'thread'

# redis队列默认配置
REDIS_QUEUE_NAME = 'request_queue'   # 在实际运行的过程中, 队列名是根据爬虫名称自己定义的, 所以这个字段可有可无
REDIS_QUEUE_HOST = 'localhost'
REDIS_QUEUE_PORT = 6379
REDIS_QUEUE_DB = 10

# 设置是否需要持久化和分布式
# 设置调度器的内容, 即请求对象是否要持久化
# 如果是 True, 那么就是使用分布式, 同时也是基于请求的增量式爬虫
# 如果是 False, 不会使用 redis 队列, 而是使用 python 的 set 存储指纹和请求
SCHEDULER_PERSIST = True

```


4.在调度器中判断是否启用持久化并选择不同的队列: 

```python
# spider_plus/core/scheduler.py
# coding=utf-8
# 调度器

# 利用six模块实现py2和py3兼容
import six
from six.moves.queue import Queue
import w3lib.url
from hashlib import sha1

from spider_plus.utils.log import logger
from spider_plus.utils.queue import Queue as ReidsQueue
from spider_plus.conf.settings import SCHEDULER_PERSIST

class Scheduler(object):
    '''完成调试器模块的封装'''

    def __init__(self):
        # 如果不需要持久化, 就使用python内置的 Queue, 如果需要持久化, 就使用基于 Reids 的 RedisQueue
        if not SCHEDULER_PERSIST:
            self.queue = Queue()  # 存储的是待抓取的请求
        else:
            self.queue = ReidsQueue()
        # 去重容器, 利用set类型存储每个请求的指纹
        self._filter_container = set()

        self.repeat_request_num = 0  # 记录重复的请求数量. 为什么要统计重复请求的数量. 之前在引擎中使用 "总的响应数量 == 总的请求数量" 来确定程序的退出, 如果有重复的请求, 就不会发送请求, 这个条件就永远不会满足. 需要把程序退出的条件修改为 "总的响应数量 + 总的重复数量 == 总的请求数量", 所以这里要记录重复的请求的数量

    def add_request(self, request):
        '''
        实现添加request到队列中
        :param request: 请求对象
        :return: None
        '''
        # 调用_filter_request来实现对请求对象的去重
        # 如果指纹不存在, 才把请求对象添加到队列中
        if self._filter_request(request):
            self.queue.put(request)

    def get_request(self):
        '''
        实现获取队列中的request对象
        :return: 请求对象
        '''
        # queue.get(), 默认 block=Ture, 即是堵塞的, 如果队列中没有对象, 就堵塞在这里. 需要修改为非堵塞的.
        # 非堵塞状态可以会报错, 所以使用try...except...
        try:
            return self.queue.get(block=False)
        except:
            return None

    def _filter_request(self, request):
        '''
        实现对请求对象的去重
        :param request: 请求对象
        :return: bool
        '''
        # 给 request对象添加一个fp属性, 保存指纹
        # 去重容器: 存储已经发过的请求的特征 url, 选用集合类型: set()
        # 利用请求的 url method data 求出一个指纹, 利用sha1
        request.fp = self._gen_fp(request)
        # 如果判断指纹不在指纹集合中, 就把它添加进去
        if request.fp not in self._filter_container:
            logger.info("添加新的请求: <%s>" % request.url)
            self._filter_container.add(request.fp)
            return True
        else:
            logger.info("发现重复的请求：<{} {}>".format(request.method, request.url))
            self.repeat_request_num += 1
            return False

    @staticmethod
    def _to_bytes(string):
        if six.PY2:  # 如果是python2环境
            if isinstance(string, str):  # str类型在py2中是字节类型
                return string
            else:  # 如果是python2的 unicode 类型, 转化为python2字节类型
                return string.encode("utf-8")
        elif six.PY3:  # 如果是python3环境
            if isinstance(string, str):
                return string.encode("utf-8")  # 转换为bytes类型
            else:
                return string  # 说明string是bytes类型，直接返回

    def _gen_fp(self, request):
        '''
        对 url 地址, 请求体, 请求参数, 请求方法进行加密, 生成 request 对象的指纹
        :param request: request对象
        :return: 指纹字符串
        '''
        # 1. url 地址排序：借助w3lib.url模块中的 canonicalize_url 方法
        url = w3lib.url.canonicalize_url(request.url)
        # 2. 请求方法 method, 不需要排序，只要保持大小写一致就可以
        method = request.method.upper()  # 全大写
        # 3. 请求参数params. 排序. 如果有提供则是一个字典，如果没有则是 None
        params = request.params if request.params is not None else {}  # 如果是None，那么设为{}
        params = sorted(params.items(), key=lambda x: x[0])  # 按照key对字典进行排序，结果将是一个列表
        # 4. 请求体data排序：如果有提供则是一个字典，如果没有则是None
        data = request.data if request.data is not None else {}  # 如果是None，那么设为{}
        data = sorted(data.items(), key=lambda x: x[0])  # 按照key对字典进行排序，结果将是一个列表

        # 5. 利用sha1算法，计算指纹
        s1 = sha1()
        # 由于s1接收的只能是bytes类型(python3)、str类型(python2)，他们都是某种编码类型的(如utf-8、gbk)
        # 为了兼容py2和py3, 利用 _to_bytes 方法, 把所有的字符串转化为字节类型
        s1.update(self._to_bytes(url))  # 添加url地址
        s1.update(self._to_bytes(method))  # 添加请求方法
        s1.update(self._to_bytes(str(params)))  # 添加请求参数
        s1.update(self._to_bytes(str(data)))  # 添加请求体

        fp = s1.hexdigest()  # 提取16进制的sha1指纹字符串并返回
        return fp
```

```python

# # 项目文件夹/settings.py

# ......

# # 设置程序运行的角色
# # 三个值: None、'master'、'slave'
# # 如果是None，那么就是不使用分布式，既不是master，也不是slave
# # 如果是'master', 代表主端，也就是只负责请求队列的维护
# # 如果是'slave'，代表从端，也就是只负责从请求队列获取请求，并进行处理
# ROLE = 'master'


# 3.在引擎中进行判断使用: 
# # spider_plus/core/engine.py

#     ......

#     def _start_engine(self):
#         self.running = True
#         '''依次调用其他组件对外提供的接口，实现整个框架的运作(驱动)'''
#         if settings.ROLE is None or settings.ROLE == 'master':    # 如果是None代表非分布式; 如果是'master'就只负责执行_start_requests
#             # 向调度器添加初始请求
#             self.pool.apply_async(self._start_requests, error_callback=self._error_callback)    # 使用异步

#         if settings.ROLE is None or settings.ROLE == 'slave':    # 如果是None代表非分布式; 如果是'slave'就只负责执行_execute_request_response_item:
#             for i in range(settings.MAX_ASYNC_NUMBER):
#                 self.pool.apply_async(self._execute_request_response_item, callback=self._callback, error_callback=self._error_callback)    # 利用回调实现循环

#     ......

```




这个时候基本实现了分布式，但是还存在一个问题，也就是，请求去重问题(这个必须处理)，还有就是自动退出判断问题(分布式的话通常不需要自动退出)

如果分布式中请求去重的去重容器各个从端以及主端用的不是同一个，那么就无法达到去重的目的，因此这里同样的需要使用redis来实现去重容器，也就是把所有的去重指纹都存储在redis中，所有的主从端都是通过同一台redis来进行判断请求的重复与否


5. 利用 Redis 的集合类型实现去重, 实现一个自定义的set: 

```python

# spider_plus/utils/set.py

import redis
from spider_plus.conf import settings

class BaseFilterContainer(object):

    def add_fp(self, fp):
        '''往去重容器添加一个指纹'''
        pass

    def exists(self, fp):
        '''判断指纹是否在去重容器中'''
        pass


class NoramlFilterContainer(BaseFilterContainer):
    '''利用python的集合类型'''
    def __init__(self):
        self._filter_container = set()

    def add_fp(self, fp):
        '''向python中的集合去重容器中添加一个指纹'''
        self._filter_container.add(fp)

    def exists(self, fp):
        '''判断指纹是否在去重容器中'''
        if fp in self._filter_container:
            return True
        else:
            return False

class RedisFilterContainer(BaseFilterContainer):

    REDIS_SET_NAME = settings.REDIS_SET_NAME
    REDIS_SET_HOST = settings.REDIS_SET_HOST
    REDIS_SET_PORT = settings.REDIS_SET_PORT
    REDIS_SET_DB = settings.REDIS_SET_DB

    def __init__(self):
        self._redis = redis.StrictRedis(host=self.REDIS_SET_HOST, port=self.REDIS_SET_PORT ,db=self.REDIS_SET_DB)
        self._name = self.REDIS_SET_NAME

    def add_fp(self, fp):
        '''往redis去重容器添加一个指纹'''
        self._redis.sadd(self._name, fp)

    def exists(self, fp):
        '''判断指纹是否在去重容器中'''
        return self._redis.sismember(self._name, fp)
```

把 redis_set 相应的设置放在 default_settings 和 settings.py 文件中

```python
# redis 指纹集合的位置, 存储 request 请求的指纹
REDIS_SET_NAME = 'redis_set'
REDIS_SET_HOST = 'localhost'
REDIS_SET_PORT = 6379
REDIS_SET_DB = 0

```


在调度器中使用这个set.py， 使得分布式模式下的去重功能正常运作

```python
# spider_plus/core/scheduler.py

# coding=utf-8
# 调度器

# 利用six模块实现py2和py3兼容
import six
from six.moves.queue import Queue
import w3lib.url
from hashlib import sha1

from spider_plus.utils.log import logger
from spider_plus.utils.queue import Queue as ReidsQueue
from spider_plus.conf.settings import SCHEDULER_PERSIST
from spider_plus.utils.set import NoramlFilterContainer, RedisFilterContainer


class Scheduler(object):
    '''完成调试器模块的封装'''

    def __init__(self):
        # 如果不需要持久化, 就使用python内置的 Queue, 如果需要持久化, 就使用基于 Reids 的 RedisQueue
        if not SCHEDULER_PERSIST:
            self.queue = Queue()  # 存储的是待抓取的请求
            # 不使用分布式的时候, 使用 python 的集合存储指纹
            self._filter_container = NoramlFilterContainer()
        else:
            self.queue = ReidsQueue()
            # 使用分布式的时候, 使用 redis 的集合存储指纹
            self._filter_container = RedisFilterContainer()

        # 去重容器, 利用set类型存储每个请求的指纹
        # self._filter_container = set()

        self.repeat_request_num = 0  # 记录重复的请求数量. 为什么要统计重复请求的数量. 之前在引擎中使用 "总的响应数量 == 总的请求数量" 来确定程序的退出, 如果有重复的请求, 就不会发送请求, 这个条件就永远不会满足. 需要把程序退出的条件修改为 "总的响应数量 + 总的重复数量 == 总的请求数量", 所以这里要记录重复的请求的数量

    def add_request(self, request):
        '''
        实现添加request到队列中
        :param request: 请求对象
        :return: None
        '''
        # 调用_filter_request来实现对请求对象的去重
        # 如果指纹不存在, 才把请求对象添加到队列中
        if self._filter_request(request):
            self.queue.put(request)

    def get_request(self):
        '''
        实现获取队列中的request对象
        :return: 请求对象
        '''
        # queue.get(), 默认 block=Ture, 即是堵塞的, 如果队列中没有对象, 就堵塞在这里. 需要修改为非堵塞的.
        # 非堵塞状态可以会报错, 所以使用try...except...
        try:
            return self.queue.get(block=False)
        except:
            return None

    def _filter_request(self, request):
        '''
        实现对请求对象的去重
        :param request: 请求对象
        :return: bool
        '''
        # 给 request对象添加一个fp属性, 保存指纹
        # 去重容器: 存储已经发过的请求的特征 url, 选用集合类型: set()
        # 利用请求的 url method data 求出一个指纹, 利用sha1
        request.fp = self._gen_fp(request)
        # 如果判断指纹不在指纹集合中, 就把它添加进去
        if not  self._filter_container.exists(request.fp):
            logger.info("添加新的请求: <%s>" % request.url)
            self._filter_container.add_fp(request.fp)
            return True
        else:
            logger.info("发现重复的请求：<{} {}>".format(request.method, request.url))
            self.repeat_request_num += 1
            return False

    @staticmethod
    def _to_bytes(string):
        if six.PY2:  # 如果是python2环境
            if isinstance(string, str):  # str类型在py2中是字节类型
                return string
            else:  # 如果是python2的 unicode 类型, 转化为python2字节类型
                return string.encode("utf-8")
        elif six.PY3:  # 如果是python3环境
            if isinstance(string, str):
                return string.encode("utf-8")  # 转换为bytes类型
            else:
                return string  # 说明string是bytes类型，直接返回

    def _gen_fp(self, request):
        '''
        对 url 地址, 请求体, 请求参数, 请求方法进行加密, 生成 request 对象的指纹
        :param request: request对象
        :return: 指纹字符串
        '''
        # 1. url 地址排序：借助w3lib.url模块中的 canonicalize_url 方法
        url = w3lib.url.canonicalize_url(request.url)
        # 2. 请求方法 method, 不需要排序，只要保持大小写一致就可以
        method = request.method.upper()  # 全大写
        # 3. 请求参数params. 排序. 如果有提供则是一个字典，如果没有则是 None
        params = request.params if request.params is not None else {}  # 如果是None，那么设为{}
        params = sorted(params.items(), key=lambda x: x[0])  # 按照key对字典进行排序，结果将是一个列表
        # 4. 请求体data排序：如果有提供则是一个字典，如果没有则是None
        data = request.data if request.data is not None else {}  # 如果是None，那么设为{}
        data = sorted(data.items(), key=lambda x: x[0])  # 按照key对字典进行排序，结果将是一个列表

        # 5. 利用sha1算法，计算指纹
        s1 = sha1()
        # 由于s1接收的只能是bytes类型(python3)、str类型(python2)，他们都是某种编码类型的(如utf-8、gbk)
        # 为了兼容py2和py3, 利用 _to_bytes 方法, 把所有的字符串转化为字节类型
        s1.update(self._to_bytes(url))  # 添加url地址
        s1.update(self._to_bytes(method))  # 添加请求方法
        s1.update(self._to_bytes(str(params)))  # 添加请求参数
        s1.update(self._to_bytes(str(data)))  # 添加请求体

        fp = s1.hexdigest()  # 提取16进制的sha1指纹字符串并返回
        return fp
```


5. 程序结束的条件

在之前的单机版本的代码中, 通过 总的响应 + 总的重复数 >= 总的请求 来判断程序结束, 但是在分布式的版本中, 每个服务器的请求数量和响应数量不再相同.

因为每个服务器存入队列的请求, 和成功发送的请求中间可能很多请求被其他的服务器发送了, 导致数量不一致, 所以可以把总的请求, 总的响应, 总的重复请求等信息记录在 redis 中, 那么所有的服务器端修改的数据的位置是同一个 redis 中的内容, 所有的服务央判断退出的时候也是通过比较同一个 redis 中的这些数据来决定.

因此, 在 utils 中新建 status_collector.py 文件, 来实现对各种数量的统计, 包括总的请求数量, 总的响应数量, 总的重复数量.


```python
# 进行数量状态的统计
import redis
from spider_plus.conf.settings import REDIS_QUEUE_NAME, REDIS_QUEUE_HOST, REDIS_QUEUE_PORT, REDIS_QUEUE_DB


# redis 队列默认配置
# REDIS_QUEUE_NAME = 'request_queue'
# REDIS_QUEUE_HOST = 'localhost'
# REDIS_QUEUE_PORT = 6379
# REDIS_QUEUE_DB = 10


class StatusCollector(object):

    def __init__(self, spider_names=[], host=REDIS_QUEUE_HOST, port=REDIS_QUEUE_PORT, db=REDIS_QUEUE_DB, password=None):

        self.redis = redis.StrictRedis(host=host, port=port, db=db, password=password)
        # 存储请求数量的键. 通过爬虫名来区分不同的爬虫的键
        self.request_num_key = "_".join(spider_names) + "_request_num"
        # 存储响应数量的键
        self.response_num_key = "_".join(spider_names) + "_response_num"
        # 存储重复请求的键
        self.duplicate_request_num_key = "_".join(spider_names) + "_duplicate_request_num"


    def incr(self, key):
        '''
        给键 key 对应的值增加 1, 不存在会自动创建, 并且值为1
        :param key:
        :return:
        '''
        self.redis.incr(key)

    def get(self, key):
        '''
        获取键 key 对应的值, 不存在时为 0, 存在时则获取并转化为 int 类型
        :param key:
        :return:
        '''
        ret = self.redis.get(key)
        if not ret:
            ret = 0
        else:
            ret = int(ret)
        return ret

    def clear(self):
        '''
        程序结束后清空所有的值
        :return:
        '''
        self.redis.delete(self.request_num_key, self.response_num_key, self.duplicate_request_num_key, self.finished_start_requests_num_key)

    @property
    def request_num(self):
        '''获取请求数量'''
        return self.get(self.request_num_key)

    @property
    def response_num(self):
        '''获取响应数量'''
        return self.get(self.response_num_key)

    @property
    def duplicate_request_num(self):
        '''获取重复请求数量'''
        return self.get(self.duplicate_request_num_key)
```


修改 spider_plus/core/engine.py, 使用基于 redis 的 status_collector 来统计请求, 响应和重复请求的数量

```python
# coding=utf-8
# 引擎
import time
import importlib

from datetime import datetime

# 为什么要把导入 gevent.Pool 的操作放在最前面, 由于打patch补丁是为了替换掉socket为非阻塞的, 而下载器 Downloader 中正好使用了requests模块，如果在这之后导入协程池，会导致requests中使用的socket没有被替换成功, 从而有可能导致使用出现问题
from spider_plus.conf.settings import ASYNC_TYPE
# 判断使用什么异步模式，改用对应的异步池
if ASYNC_TYPE == 'thread':
    from multiprocessing.dummy import Pool    # 导入线程池对象
elif ASYNC_TYPE == 'coroutine':
    from spider_plus.async.coroutine import Pool
    # from gevent.monkey import patch_all
    # patch_all()
else:
    raise Exception("不支持的异步类型：{},".format(ASYNC_TYPE))

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from spider_plus.conf.settings import SPIDERS, PIPELINES, DOWNLOADER_MIDDLEWARES, SPIDER_MIDDLEWARES, CONCOURRENT_REQUEST
from spider_plus.utils.status_collector import StatusCollector

class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        # 把统计数量的容器放在调度器之前实例化, 因为重复请求的数量是在调度器中进行统计的, 并且在引擎最后面使用到调度器中的重复请求的数量. self.scheduler.repeat_request_num, 所以要把 collector 也传递到调度器中, 经过调度器统计重复请求的数量后才能使用
        self.collector = StatusCollector()
        self.spiders = self._auto_import_instances(SPIDERS, is_spider=True)  # 接收外部传入的爬虫对象, 字典
        self.scheduler = Scheduler(self.collector)  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipelines = self._auto_import_instances(PIPELINES)  # 初始化管道对象, 列表
        self.spider_mids = self._auto_import_instances(SPIDER_MIDDLEWARES)  # 初始化爬虫中间件对象, 列表
        self.downloader_mids = self._auto_import_instances(DOWNLOADER_MIDDLEWARES)  # 初始化下载器中间件对象, 列表
        # 为了使处理请求响应数据的方法能够正常退出, 定义两个变量, 当总的响应数量大于等于总的请求数量时, 所有请求都已经处理完毕, 就可以退出了
        # self.total_request_num = 0  # 总的请求数
        # self.total_response_num = 0  # 总的响应数
        self.pool = Pool(5)  # 实例化线程池对象. 线程池的大小默认为cpu的个数, 电脑是单核时线程池的大小就为 1, 可以手动指定线程池的大小
        self.is_running = True  # 程序是否处理运行状态, 依据此状态来决定程序是否退出. 当程序开始运行时, 设置此参数为 Ture, 当所有的请求执行结束后, 设置此参数为 False, 此时程序就退出.


    def _auto_import_instances(self, path=[], is_spider=False):
        '''
        根据配置文件, 实现模块的动态导入, 传入模块路径列表, 返回类的实例
        :param path: settings 中配置的要导入类的路径. 包含模块位置字符串的列表
        :param is_spider: 是否是爬虫. 爬虫是字典的形式, 所以需要进行单独的判断和处理
        :return: 返回爬虫, 管道, 中间件的实例
        '''
        if is_spider is True:
            instances = {}
        else:
            instances = []  # 存储对应类的实例对象

        for p in path:
            module_name = p[:p.rfind(".")]  # 取出模块名称
            module_name = p.rsplit(".", 1)[0]
            cls_name = p[p.rfind(".") + 1:]  # 取出类名称
            cls_name = p.rsplit(".", 1)[-1]
            module = importlib.import_module(module_name)  # 导入模块
            cls = getattr(module, cls_name)  # 根据类名称获取module下的类对象
            if is_spider is True:
                instances[cls.name] = cls()
            else:
                instances.append(cls())  # 实例化类对象
        return instances  # 返回类对象

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        logger.info("当前启动的爬虫: {}".format(SPIDERS))
        logger.info("当前开启的管道: {}".format(PIPELINES))
        logger.info("当前开启的下载器中间件: {}".format(DOWNLOADER_MIDDLEWARES))
        logger.info("当前开启的爬虫中间件: {}".format(SPIDER_MIDDLEWARES))
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时
        # 在引擎的调用执行结束后, 打印总的请求数量和总的响应数量.
        # logger.info("总的请求数量: {}个".format(self.total_request_num))
        logger.info("总的请求数量: {}个".format(self.collector.request_num_key))
        # logger.info("总的响应数量: {}个".format(self.total_response_num))
        logger.info("总的响应数量: {}个".format(self.collector.response_num_key))
        # logger.info("总的重复数量: {}个".format(self.scheduler.repeat_request_num))
        logger.info("总的重复数量: {}个".format(self.collector.duplicate_request_num_key))

    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        for spider_name, spider in self.spiders.items():  # 遍历 spiders 字典, 获取每个spider对象
            # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历
            for start_request in spider.start_requests():
                # 对start_request初始请求经过爬虫中间件进行处理
                for spider_mid in self.spider_mids:
                    start_request = spider_mid.process_request(start_request)

                # 在把初始请求添加到调度器中之前, 给它添加一个属性 spider_name, 记录它是哪个爬虫产生的请求, 以方便后面 _execute_request_response_item 中通过这个属性获取到对应的爬虫, 进而获取爬虫的 parse方法
                start_request.spider_name = spider_name

                # 2. 调用调度器的add_request方法, 添加request对象到调度器中
                self.scheduler.add_request(start_request)
                # 把request添加到调度器中之后, 把总请求数加1
                # self.total_request_num += 1
                # 对 redis 中的请求数量进行加 1 操作
                self.collector.incr(self.collector.request_num_key)

    def _execute_request_response_item(self):
        '''处理单个请求, 从调度器取出, 发送请求, 获取响应, parse函数处理, 调度器处理'''
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        if request is None:  # 判断从调度器中取出来的request是否是None, 如果是None, 表示调度器为空, 就不进行任何进一步的处理
            return
        for downloader_mid in self.downloader_mids:
            # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
            request = downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)

        # 为了把 request中的meta传递给 response, 在调用下载器获取响应后, 给response添加一个meta属性即可
        response.meta = request.meta

        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        for downloader_mid in self.downloader_mids:
            response = downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        for spider_mid in self.spider_mids:
            response = spider_mid.process_response(response)

        # 根据请求对象的 spider_name 属性, 获取爬虫实例, 进而获取爬虫的 parse 方法
        spider = self.spiders.get(request.spider_name)
        # 获取 request 对象对应的响应的parse方法. getattr 从 self.spiders 中查找并返回 request的parse属性指定的方法
        # 对于糗事百科爬虫来说, 1-13页列表页中, 由于request对象没有指定parse方法, 所以会使用默认的 parse="parse", 而对于详情页, 则使用 request对象指定的 "parse_detail" 方法.
        parse = getattr(spider, request.parse)

        # 5. 利用爬虫的parse方法，处理响应
        # 因为 spiders 的 parse 方法已经修改为生成器, 所以这里要进行遍历
        for result in parse(response):
            # 6. 判断结果的类型
            # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
            if isinstance(result, Request):
                for spider_mid in self.spider_mids:
                    # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
                    result = spider_mid.process_request(result)

                # 对于新的请求, 在保存到调度器之间也添加 spider_name 属性
                result.spider_name = request.spider_name

                self.scheduler.add_request(result)
                # self.total_request_num += 1  # 请求加1
                # 对 redis 中的请求数量进行加 1 操作
                self.collector.incr(self.collector.request_num_key)

            # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
            else:
                # 遍历所有的管道, 对item进行处理
                for pipeline in self.pipelines:
                    # 必须要把处理的结果重新赋值给 result, 下一个管道才能在上一个管道的基础上进一步处理
                    result = pipeline.process_item(result, spider)

        # 整个函数都是处理单个请求, 整个函数执行完了, 单个请求才处理完, 此时总的响应数加1
        # self.total_response_num += 1
        # 对 redis 中的响应数量进行加 1 操作
        self.collector.incr(self.collector.response_num_key)

    def _error_callback(self, exception):
        '''异常回调函数'''
        try:
            raise exception  # 抛出异常后, 才能被日志进行完整记录下来
        except Exception as e:
            logger.exception(e)

    def _callback(self, temp):  # 必须有 temp 参数
        '''执行新的请求的回调函数, 实现循环'''
        if self.is_running is True:  # 如果还没满足退出条件, 那么继续添加新任务, 否则不继续添加, 终止回调函数, 达到退出循环的目的
            self.pool.apply_async(self._execute_request_response_item, callback=self._callback, error_callback=self._error_callback)

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self.is_running = True  # 启动引擎时, 设置 is_running 状态为True
        # self._start_request()  # 初始化请求

        # 向调度器添加初始请求, 初始化请求
        self.pool.apply_async(self._start_request, error_callback=self._error_callback)  # 使用异步, 当主线程执行到这里时, 会使用线程池中的一个子线程来执行这个函数, 主线程继续向下执行

        # 虽然调用的是异步的 apply_async 方法, 但调用的过程依然是同步的, 执行完一个 "请求-响应-数据" 的流程之后, 才调用 _callback 方法, 这时的并发量还是非常低的, 还是1. 为了提高并发量, 可以把这句话放到一个循环中执行. 如 for i in range(3): 这样就会有 3 个并发线程同时去执行
        for i in range(CONCOURRENT_REQUEST):
            # 利用回调实现循环. 同样会使用一个子线程来执行这个函数
            self.pool.apply_async(self._execute_request_response_item, callback=self._callback, error_callback=self._error_callback)

        # 设置循环, 处理多个请求
        # 使用循环让主线程处理堵塞状态, 一直等到子线程执行结束才退出循环
        while True:
            time.sleep(0.001)  # 避免主线程 cpu 空转, 降低资源消耗
            # self._execute_request_response_item()   # 处理单个请求
            # 循环结束的条件
            # 成功的响应数 + 重复的响应数量 >= 总的请求数量, 程序结束
            if self.collector.request_num != 0:  # 刚开始时总的请求数量为0, 只有当总请求数不为0时, 即至少有一个请求或响应后, 才有可能退出
                if self.collector.response_num + self.collector.duplicate_request_num >= self.collector.request_num:
                    self.is_running = False  # 满足循环退出条件后, 设置运行状态为 False
                    break

        # 在爬虫的运行结束后, 可能线程池与服务器链接还没有断开, 相当于子线程的执行还未完成, 程序会处于等待状态. 所以在爬虫中一般不会去执行 pool.close() 和 pool.join()
        self.pool.close()
        self.pool.join()


if __name__ == '__main__':
    engine = Engine()
    engine.start()
```


由于 重复的请求是在 调度器中进行统计的, 所以也要修改 调度器, 使用 status_collector 来统计重复请求的数量

```python
# coding=utf-8
# 调度器

# 利用six模块实现py2和py3兼容
import six
from six.moves.queue import Queue
import w3lib.url
from hashlib import sha1

from spider_plus.utils.log import logger
from spider_plus.utils.queue import Queue as ReidsQueue
from spider_plus.conf.settings import SCHEDULER_PERSIST
from spider_plus.utils.set import NoramlFilterContainer, RedisFilterContainer


class Scheduler(object):
    '''完成调试器模块的封装'''

    def __init__(self, collector):
        # 如果不需要持久化, 就使用python内置的 Queue, 如果需要持久化, 就使用基于 Reids 的 RedisQueue
        if not SCHEDULER_PERSIST:
            self.queue = Queue()  # 存储的是待抓取的请求
            # 不使用分布式的时候, 使用 python 的集合存储指纹
            self._filter_container = NoramlFilterContainer()
        else:
            self.queue = ReidsQueue()
            # 使用分布式的时候, 使用 redis 的集合存储指纹
            self._filter_container = RedisFilterContainer()

        # 去重容器, 利用set类型存储每个请求的指纹
        # self._filter_container = set()

        # self.repeat_request_num = 0  # 记录重复的请求数量. 为什么要统计重复请求的数量. 之前在引擎中使用 "总的响应数量 == 总的请求数量" 来确定程序的退出, 如果有重复的请求, 就不会发送请求, 这个条件就永远不会满足. 需要把程序退出的条件修改为 "总的响应数量 + 总的重复数量 == 总的请求数量", 所以这里要记录重复的请求的数量
        self.collector = collector

    def add_request(self, request):
        '''
        实现添加request到队列中
        :param request: 请求对象
        :return: None
        '''
        # 调用_filter_request来实现对请求对象的去重
        # 如果指纹不存在, 才把请求对象添加到队列中
        if self._filter_request(request):
            self.queue.put(request)

    def get_request(self):
        '''
        实现获取队列中的request对象
        :return: 请求对象
        '''
        # queue.get(), 默认 block=Ture, 即是堵塞的, 如果队列中没有对象, 就堵塞在这里. 需要修改为非堵塞的.
        # 非堵塞状态可以会报错, 所以使用try...except...
        try:
            return self.queue.get(block=False)
        except:
            return None

    def _filter_request(self, request):
        '''
        实现对请求对象的去重
        :param request: 请求对象
        :return: bool
        '''
        # 给 request对象添加一个fp属性, 保存指纹
        # 去重容器: 存储已经发过的请求的特征 url, 选用集合类型: set()
        # 利用请求的 url method data 求出一个指纹, 利用sha1
        request.fp = self._gen_fp(request)
        # 如果判断指纹不在指纹集合中, 就把它添加进去
        if not  self._filter_container.exists(request.fp):
            logger.info("添加新的请求: <%s>" % request.url)
            self._filter_container.add_fp(request.fp)
            return True
        else:
            logger.info("发现重复的请求：<{} {}>".format(request.method, request.url))
            # self.repeat_request_num += 1
            self.collector.incr(self.collector.duplicate_request_num_key)
            return False

    @staticmethod
    def _to_bytes(string):
        if six.PY2:  # 如果是python2环境
            if isinstance(string, str):  # str类型在py2中是字节类型
                return string
            else:  # 如果是python2的 unicode 类型, 转化为python2字节类型
                return string.encode("utf-8")
        elif six.PY3:  # 如果是python3环境
            if isinstance(string, str):
                return string.encode("utf-8")  # 转换为bytes类型
            else:
                return string  # 说明string是bytes类型，直接返回

    def _gen_fp(self, request):
        '''
        对 url 地址, 请求体, 请求参数, 请求方法进行加密, 生成 request 对象的指纹
        :param request: request对象
        :return: 指纹字符串
        '''
        # 1. url 地址排序：借助w3lib.url模块中的 canonicalize_url 方法
        url = w3lib.url.canonicalize_url(request.url)
        # 2. 请求方法 method, 不需要排序，只要保持大小写一致就可以
        method = request.method.upper()  # 全大写
        # 3. 请求参数params. 排序. 如果有提供则是一个字典，如果没有则是 None
        params = request.params if request.params is not None else {}  # 如果是None，那么设为{}
        params = sorted(params.items(), key=lambda x: x[0])  # 按照key对字典进行排序，结果将是一个列表
        # 4. 请求体data排序：如果有提供则是一个字典，如果没有则是None
        data = request.data if request.data is not None else {}  # 如果是None，那么设为{}
        data = sorted(data.items(), key=lambda x: x[0])  # 按照key对字典进行排序，结果将是一个列表

        # 5. 利用sha1算法，计算指纹
        s1 = sha1()
        # 由于s1接收的只能是bytes类型(python3)、str类型(python2)，他们都是某种编码类型的(如utf-8、gbk)
        # 为了兼容py2和py3, 利用 _to_bytes 方法, 把所有的字符串转化为字节类型
        s1.update(self._to_bytes(url))  # 添加url地址
        s1.update(self._to_bytes(method))  # 添加请求方法
        s1.update(self._to_bytes(str(params)))  # 添加请求参数
        s1.update(self._to_bytes(str(data)))  # 添加请求体

        fp = s1.hexdigest()  # 提取16进制的sha1指纹字符串并返回
        return fp
```


重新安装框架, 运行代码, 

爬虫运行结束时, 会清空 redis 中用于统计数量的 键. 如果程序正常运行并退出, 这里的键就会被清理, 只留下 "redis_set" 这个键, 其中保存着请求的指纹, 如果程序运行的过程中退出了, 就不会清空统计数量的键, redis 中会多出来 "baidu_qiubai_request_num", "baidu_qiubai_duplicate_request_num", "baidu_qiubai_response_num", "request_queue", 这几个键.

1) "baidu_qiubai_request_num"
2) "baidu_qiubai_duplicate_request_num"
3) "baidu_qiubai_response_num"
4) "redis_set"
5) "request_queue"

在第一次运行过程中中断程序的运行, 此时可能会出现因为响应未来得及处理而丢失的情况, 但此时请求已经发送, 并把该请求的指纹保存在 redis_set 键中, 同时 redis 中的 request_num 键会 加 1, 但响应未能接收和处理, response_num 这个键未能执行 加 1 的操作. 然后再次运行程序, 就不会再次对此请求进行处理, 出现请求不完整的情况. 可以通过增量爬虫来解决这个问题



框架升级 -- 增量爬虫设计原理及其实现


1. 增量爬虫设计原理
增量抓取，意即针对某个站点的数据抓取，当网站的新增数据或者该站点的数据发生了变化后，自动地抓取它新增的或者变化后的数据

设计原理：

增量爬虫设计原理

1.1 实现关闭请求去重
为Request对象增加属性filter字段, 类似于 scrapy 中的 dont_filter 字段

```python
# scrapy/http/reqeust.py

# coding=utf-8
# 请求对象

class Request(object):
    """完成请求对象的封装"""

    def __init__(self, url, method="GET", headers=None, params=None, data=None, parse="parse", meta={}, filter=True):
        '''
        初始化request对象
        :param url: url地址
        :param method: 请求方法
        :param headers:请求头
        :param params: 请求的参数, 查询字符串
        :param data: 请求体, 表单数据
        :param parse: 请求对象对应的响应的解析函数
        :param meta: 字典, 在不同的解析函数之间传递数据
        :param filter: 是否对该请求进行去重, 默认会对请求进行去生
        '''
        self.url = url
        self.method = method
        self.headers = headers
        self.params = params
        self.data = data
        self.parse = parse
        self.meta = meta
        self.filter = filter

```



修改调度器，进行判断

```python
# spider_plus/core/scheduler.py

# coding=utf-8
# 调度器

# 利用six模块实现py2和py3兼容
import six
from six.moves.queue import Queue
import w3lib.url
from hashlib import sha1

from spider_plus.utils.log import logger
from spider_plus.utils.queue import Queue as ReidsQueue
from spider_plus.conf.settings import SCHEDULER_PERSIST
from spider_plus.utils.set import NoramlFilterContainer, RedisFilterContainer


class Scheduler(object):
    '''完成调试器模块的封装'''

    def __init__(self, collector):
        # 如果不需要持久化, 就使用python内置的 Queue, 如果需要持久化, 就使用基于 Reids 的 RedisQueue
        if not SCHEDULER_PERSIST:
            self.queue = Queue()  # 存储的是待抓取的请求
            # 不使用分布式的时候, 使用 python 的集合存储指纹
            self._filter_container = NoramlFilterContainer()
        else:
            self.queue = ReidsQueue()
            # 使用分布式的时候, 使用 redis 的集合存储指纹
            self._filter_container = RedisFilterContainer()

        # 去重容器, 利用set类型存储每个请求的指纹
        # self._filter_container = set()

        # self.repeat_request_num = 0  # 记录重复的请求数量. 为什么要统计重复请求的数量. 之前在引擎中使用 "总的响应数量 == 总的请求数量" 来确定程序的退出, 如果有重复的请求, 就不会发送请求, 这个条件就永远不会满足. 需要把程序退出的条件修改为 "总的响应数量 + 总的重复数量 == 总的请求数量", 所以这里要记录重复的请求的数量
        self.collector = collector

    def add_request(self, request):
        '''
        实现添加request到队列中
        :param request: 请求对象
        :return: None
        '''
        # 判断请求是否需要进行去重, 如果不需要, 直接添加到队列
        if not request.filter:  # 不需要进行去重
            request.fp = self._gen_fp(request)  # 手动给 request 对象添加指纹属性
            self.queue.put(request)
            return   # 必须return. 如果不需要进行去重, 那么就直接返回, 后面生成指纹并把指纹保存到去重容器中的操作就不会去执行了. 但是这样做的话 request 对象就没有 fp 的属性, 在以后可能会用到 fp 属性的地方就会出错. 需要在向队列中添加该请求之间给该请求添加一个fp的属性.

        # 调用_filter_request来实现对请求对象的去重
        # 如果指纹不存在, 才把请求对象添加到队列中
        if self._filter_request(request):
            self.queue.put(request)

    def get_request(self):
        '''
        实现获取队列中的request对象
        :return: 请求对象
        '''
        # queue.get(), 默认 block=Ture, 即是堵塞的, 如果队列中没有对象, 就堵塞在这里. 需要修改为非堵塞的.
        # 非堵塞状态可以会报错, 所以使用try...except...
        try:
            return self.queue.get(block=False)
        except:
            return None

    def _filter_request(self, request):
        '''
        实现对请求对象的去重
        :param request: 请求对象
        :return: bool
        '''
        # 给 request对象添加一个fp属性, 保存指纹
        # 去重容器: 存储已经发过的请求的特征 url, 选用集合类型: set()
        # 利用请求的 url method data 求出一个指纹, 利用sha1
        request.fp = self._gen_fp(request)
        # 如果判断指纹不在指纹集合中, 就把它添加进去
        if not  self._filter_container.exists(request.fp):
            logger.info("添加新的请求: <%s>" % request.url)
            self._filter_container.add_fp(request.fp)
            return True
        else:
            logger.info("发现重复的请求：<{} {}>".format(request.method, request.url))
            # self.repeat_request_num += 1
            self.collector.incr(self.collector.duplicate_request_num_key)
            return False

    @staticmethod
    def _to_bytes(string):
        if six.PY2:  # 如果是python2环境
            if isinstance(string, str):  # str类型在py2中是字节类型
                return string
            else:  # 如果是python2的 unicode 类型, 转化为python2字节类型
                return string.encode("utf-8")
        elif six.PY3:  # 如果是python3环境
            if isinstance(string, str):
                return string.encode("utf-8")  # 转换为bytes类型
            else:
                return string  # 说明string是bytes类型，直接返回

    def _gen_fp(self, request):
        '''
        对 url 地址, 请求体, 请求参数, 请求方法进行加密, 生成 request 对象的指纹
        :param request: request对象
        :return: 指纹字符串
        '''
        # 1. url 地址排序：借助w3lib.url模块中的 canonicalize_url 方法
        url = w3lib.url.canonicalize_url(request.url)
        # 2. 请求方法 method, 不需要排序，只要保持大小写一致就可以
        method = request.method.upper()  # 全大写
        # 3. 请求参数params. 排序. 如果有提供则是一个字典，如果没有则是 None
        params = request.params if request.params is not None else {}  # 如果是None，那么设为{}
        params = sorted(params.items(), key=lambda x: x[0])  # 按照key对字典进行排序，结果将是一个列表
        # 4. 请求体data排序：如果有提供则是一个字典，如果没有则是None
        data = request.data if request.data is not None else {}  # 如果是None，那么设为{}
        data = sorted(data.items(), key=lambda x: x[0])  # 按照key对字典进行排序，结果将是一个列表

        # 5. 利用sha1算法，计算指纹
        s1 = sha1()
        # 由于s1接收的只能是bytes类型(python3)、str类型(python2)，他们都是某种编码类型的(如utf-8、gbk)
        # 为了兼容py2和py3, 利用 _to_bytes 方法, 把所有的字符串转化为字节类型
        s1.update(self._to_bytes(url))  # 添加url地址
        s1.update(self._to_bytes(method))  # 添加请求方法
        s1.update(self._to_bytes(str(params)))  # 添加请求参数
        s1.update(self._to_bytes(str(data)))  # 添加请求体

        fp = s1.hexdigest()  # 提取16进制的sha1指纹字符串并返回
        return fp

```


1.2 实现无限发起请求:
新增爬虫抓取：新浪滚动新闻

在 start_reqeusts 中改成无限循环，并设置对应请求为非去重模式。（注意）

```python
# spiders/sina.py
import time

from spider_plus.core.spider import Spider
from spider_plus.http.request import Request
from spider_plus.item import Item

class SinaSpider(Spider):

    name = "sina"

    def start_requests(self):
        while True:
            url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=50&page=1&r=0.4002104982344896&_=1556415569224"
            yield Request(url, parse='parse', filter=False)
            time.sleep(10)     # 每10秒发起一次请求

    def parse(self, response):
        for news in response.json.get("result").get("data"):
            item = {
                "title": news.get("title"),
                "intro": news.get("intro"),
                "keywords": news.get("keywords")
            }
        yield Item(item)

```


在引擎中调用 spider.start_requests 的方法的代码为: 

```python
    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''
        # 1. 调用爬虫的start_request方法, 获取初始request对象
        for spider_name, spider in self.spiders.items():  # 遍历 spiders 字典, 获取每个spider对象
            # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历
            for start_request in spider.start_requests():
                # 对start_request初始请求经过爬虫中间件进行处理
                for spider_mid in self.spider_mids:
                    start_request = spider_mid.process_request(start_request)
```

由于是 for 循环, 处理完一个后接着处理下一下, 所以框架调用 spider.start_requests 方法时是以同步的方式调用的，如果 spider.start_requests() 方法设置为死循环后，那么位于之后代码就不会被调用, 所以程序会一直卡在这里，因此需要在调用每个爬虫的 start_reqeusts 时设置为异步的

```python

# spider_plus/core/engine.py
class Engine(object):

    ......


    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''

        def _func(spider_name, spider):
            for start_request in spider.start_requests():
                # 2. 把初始请求添加给调度器
                # 利用爬虫中间件预处理请求对象
                for spider_mid in self.spider_mids:
                    start_request = spider_mid.process_request(start_request)
                # 在把初始请求添加到调度器中之前, 给它添加一个属性 spider_name, 记录它是哪个爬虫产生的请求, 以方便后面 _execute_request_response_item 中通过这个属性获取到对应的爬虫, 进而获取爬虫的 parse方法
                start_request.spider_name = spider_name

                # 2. 调用调度器的add_request方法, 添加request对象到调度器中
                self.scheduler.add_request(start_request)
                # 把request添加到调度器中之后, 把总请求数加1
                # self.total_request_num += 1
                # 对 redis 中的请求数量进行加 1 操作
                self.collector.incr(self.collector.request_num_key)

        # 1. 爬虫模块发出初始请求
        # 遍历 spiders 字典, 获取每个spider对象
        # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历. 但如果 spider.start_requests() 方法中存在着 while True 死循环, 就会发生阻塞, 一直会卡在这里执行死循环. 所以要把这里的代码改为异步执行
        for spider_name, spider in self.spiders.items():
            self.pool.apply_async(_func, args=(spider_name, spider), callback=self._callback_total_finished_start_requests_num)    # 把执行每个爬虫的start_requests方法，设置为异步的. 每次都会使用一个子线程来处理. 这样, 就算某个爬虫的 start_requests 方法中存在死循环, 只会对执行这个死循环的子线程产生堵塞, 不会对主线程造成堵塞.

    ......

```


让程序的主线程在，多个start_reqeusts方法都没执行完毕前，不要进行退出判断，避免退出过早：

在 status_collector 中添加一个键, finished_start_requests_num_key, 和对应的方法 finished_start_requests_num 用来统计执行 成功的 spider.start_requests 的数量

```python
# 进行数量状态的统计
import redis
from spider_plus.conf.settings import REDIS_QUEUE_NAME, REDIS_QUEUE_HOST, REDIS_QUEUE_PORT, REDIS_QUEUE_DB


# redis 队列默认配置
# REDIS_QUEUE_NAME = 'request_queue'
# REDIS_QUEUE_HOST = 'localhost'
# REDIS_QUEUE_PORT = 6379
# REDIS_QUEUE_DB = 10


class StatusCollector(object):

    def __init__(self, spider_names=[], host=REDIS_QUEUE_HOST, port=REDIS_QUEUE_PORT, db=REDIS_QUEUE_DB, password=None):

        self.redis = redis.StrictRedis(host=host, port=port, db=db, password=password)
        # 存储请求数量的键. 通过爬虫名来区分不同的爬虫的键
        self.request_num_key = "_".join(spider_names) + "_request_num"
        # 存储响应数量的键
        self.response_num_key = "_".join(spider_names) + "_response_num"
        # 存储重复请求的键
        self.duplicate_request_num_key = "_".join(spider_names) + "_duplicate_request_num"
        # 存储 start_requests 数量的键, 用来统计总的完成的 start_requests 函数的数量, 每次执行完 一个 start_requests 函数之后, 该键的值都加 1
        self.finished_start_requests_num_key = "_".join(spider_names) + "_start_requests_num"

    def incr(self, key):
        '''
        给键 key 对应的值增加 1, 不存在会自动创建, 并且值为1
        :param key:
        :return:
        '''
        self.redis.incr(key)

    def get(self, key):
        '''
        获取键 key 对应的值, 不存在时为 0, 存在时则获取并转化为 int 类型
        :param key:
        :return:
        '''
        ret = self.redis.get(key)
        if not ret:
            ret = 0
        else:
            ret = int(ret)
        return ret

    def clear(self):
        '''
        程序结束后清空所有的值
        :return:
        '''
        self.redis.delete(self.request_num_key, self.response_num_key, self.duplicate_request_num_key, self.finished_start_requests_num_key)

    @property
    def request_num(self):
        '''获取请求数量'''
        return self.get(self.request_num_key)

    @property
    def response_num(self):
        '''获取响应数量'''
        return self.get(self.response_num_key)

    @property
    def duplicate_request_num(self):
        '''获取重复请求数量'''
        return self.get(self.duplicate_request_num_key)

    @property
    def finished_start_requests_num(self):
        '''获取 start_requests 数量'''
        return self.get(self.finished_start_requests_num_key)
```


修改引擎, 在每一个执行 spider.start_requests 方法的地方添加回调函数, 使每次完成 spider.start_requests 方法时, 给 collector.finshed_start_requests_number 加 1

```python
# spider_plus/core/engine.py

# coding=utf-8
# 引擎
import time
import importlib

from datetime import datetime

# 为什么要把导入 gevent.Pool 的操作放在最前面, 由于打patch补丁是为了替换掉socket为非阻塞的, 而下载器 Downloader 中正好使用了requests模块，如果在这之后导入协程池，会导致requests中使用的socket没有被替换成功, 从而有可能导致使用出现问题
from spider_plus.conf.settings import ASYNC_TYPE
# 判断使用什么异步模式，改用对应的异步池
if ASYNC_TYPE == 'thread':
    from multiprocessing.dummy import Pool    # 导入线程池对象
elif ASYNC_TYPE == 'coroutine':
    from spider_plus.async.coroutine import Pool
    # from gevent.monkey import patch_all
    # patch_all()
else:
    raise Exception("不支持的异步类型：{},".format(ASYNC_TYPE))

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from spider_plus.conf.settings import SPIDERS, PIPELINES, DOWNLOADER_MIDDLEWARES, SPIDER_MIDDLEWARES, CONCOURRENT_REQUEST
from spider_plus.utils.status_collector import StatusCollector

class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        # 实例化 collector 时要传递爬虫的名字, 所以要把 spiders 的实例化放在前面
        self.spiders = self._auto_import_instances(SPIDERS, is_spider=True)  # 接收外部传入的爬虫对象, 字典
        # 把统计数量的容器放在调度器之前实例化, 因为重复请求的数量是在调度器中进行统计的, 并且在引擎最后面使用到调度器中的重复请求的数量. self.scheduler.repeat_request_num, 所以要把 collector 也传递到调度器中, 经过调度器统计重复请求的数量后才能使用
        self.collector = StatusCollector(list(self.spiders.keys()))
        self.scheduler = Scheduler(self.collector)  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipelines = self._auto_import_instances(PIPELINES)  # 初始化管道对象, 列表
        self.spider_mids = self._auto_import_instances(SPIDER_MIDDLEWARES)  # 初始化爬虫中间件对象, 列表
        self.downloader_mids = self._auto_import_instances(DOWNLOADER_MIDDLEWARES)  # 初始化下载器中间件对象, 列表
        # 为了使处理请求响应数据的方法能够正常退出, 定义两个变量, 当总的响应数量大于等于总的请求数量时, 所有请求都已经处理完毕, 就可以退出了
        # self.total_request_num = 0  # 总的请求数
        # self.total_response_num = 0  # 总的响应数
        self.pool = Pool(5)  # 实例化线程池对象. 线程池的大小默认为cpu的个数, 电脑是单核时线程池的大小就为 1, 可以手动指定线程池的大小
        self.is_running = True  # 程序是否处理运行状态, 依据此状态来决定程序是否退出. 当程序开始运行时, 设置此参数为 Ture, 当所有的请求执行结束后, 设置此参数为 False, 此时程序就退出.

    def _auto_import_instances(self, path=[], is_spider=False):
        '''
        根据配置文件, 实现模块的动态导入, 传入模块路径列表, 返回类的实例
        :param path: settings 中配置的要导入类的路径. 包含模块位置字符串的列表
        :param is_spider: 是否是爬虫. 爬虫是字典的形式, 所以需要进行单独的判断和处理
        :return: 返回爬虫, 管道, 中间件的实例
        '''
        if is_spider is True:
            instances = {}
        else:
            instances = []  # 存储对应类的实例对象

        for p in path:
            module_name = p[:p.rfind(".")]  # 取出模块名称
            module_name = p.rsplit(".", 1)[0]
            cls_name = p[p.rfind(".") + 1:]  # 取出类名称
            cls_name = p.rsplit(".", 1)[-1]
            module = importlib.import_module(module_name)  # 导入模块
            cls = getattr(module, cls_name)  # 根据类名称获取module下的类对象
            if is_spider is True:
                instances[cls.name] = cls()
            else:
                instances.append(cls())  # 实例化类对象
        return instances  # 返回类对象

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        logger.info("当前启动的爬虫: {}".format(SPIDERS))
        logger.info("当前开启的管道: {}".format(PIPELINES))
        logger.info("当前开启的下载器中间件: {}".format(DOWNLOADER_MIDDLEWARES))
        logger.info("当前开启的爬虫中间件: {}".format(SPIDER_MIDDLEWARES))
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时
        # 在引擎的调用执行结束后, 打印总的请求数量和总的响应数量.
        # logger.info("总的请求数量: {}个".format(self.total_request_num))
        logger.info("总的请求数量: {}个".format(self.collector.request_num))
        # logger.info("总的响应数量: {}个".format(self.total_response_num))
        logger.info("总的响应数量: {}个".format(self.collector.response_num))
        # logger.info("总的重复数量: {}个".format(self.scheduler.repeat_request_num))
        logger.info("总的重复数量: {}个".format(self.collector.duplicate_request_num))
        # 完成的 start_requests 函数的数量
        logger.info("总的 start_requests 数量: {}个".format(self.collector.finished_start_requests_num))

        # 爬虫运行结束时, 清空 redis 中用于统计数量的 键. 如果程序正常运行并退出, 这里的键就会被清理, 只留下 "redis_set" 这个键, 其中保存着请求的指纹, 如果程序运行的过程中退出了, 就不会清空统计数量的键, redis 中会多出来 "baidu_qiubai_request_num", "baidu_qiubai_duplicate_request_num", "baidu_qiubai_response_num", "request_queue", 这几个键.
        self.collector.clear()

    def _callback_total_finished_start_requests_num(self, temp):
        '''记录完成的 start_requests 的数量
        在 _start_request 函数中每调用一次 _func 方法, 就会执行一次该函数, 执行的次数就是爬虫的个数, 每一个爬虫中都有一个 start_requests 方法, 执行完一个 start_requests 方法, 就让 finished_start_requests_num_key 加 1
        '''
        self.collector.incr(self.collector.finished_start_requests_num_key)

    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''

        def _func(spider_name, spider):
            for start_request in spider.start_requests():
                # 2. 把初始请求添加给调度器
                # 利用爬虫中间件预处理请求对象
                for spider_mid in self.spider_mids:
                    start_request = spider_mid.process_request(start_request)
                # 在把初始请求添加到调度器中之前, 给它添加一个属性 spider_name, 记录它是哪个爬虫产生的请求, 以方便后面 _execute_request_response_item 中通过这个属性获取到对应的爬虫, 进而获取爬虫的 parse方法
                start_request.spider_name = spider_name

                # 2. 调用调度器的add_request方法, 添加request对象到调度器中
                self.scheduler.add_request(start_request)
                # 把request添加到调度器中之后, 把总请求数加1
                # self.total_request_num += 1
                # 对 redis 中的请求数量进行加 1 操作
                self.collector.incr(self.collector.request_num_key)

        # 1. 爬虫模块发出初始请求
        # 遍历 spiders 字典, 获取每个spider对象
        # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历. 但如果 spider.start_requests() 方法中存在着 while True 死循环, 就会发生阻塞, 一直会卡在这里执行死循环. 所以要把这里的代码改为异步执行
        for spider_name, spider in self.spiders.items():
            self.pool.apply_async(_func, args=(spider_name, spider), callback=self._callback_total_finished_start_requests_num)    # 把执行每个爬虫的start_requests方法，设置为异步的. 每次都会使用一个子线程来处理. 这样, 就算某个爬虫的 start_requests 方法中存在死循环, 只会对执行这个死循环的子线程产生堵塞, 不会对主线程造成堵塞.

    def _execute_request_response_item(self):
        '''处理单个请求, 从调度器取出, 发送请求, 获取响应, parse函数处理, 调度器处理'''
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        if request is None:  # 判断从调度器中取出来的request是否是None, 如果是None, 表示调度器为空, 就不进行任何进一步的处理
            return
        for downloader_mid in self.downloader_mids:
            # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
            request = downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)

        # 为了把 request中的meta传递给 response, 在调用下载器获取响应后, 给response添加一个meta属性即可
        response.meta = request.meta

        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        for downloader_mid in self.downloader_mids:
            response = downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        for spider_mid in self.spider_mids:
            response = spider_mid.process_response(response)

        # 根据请求对象的 spider_name 属性, 获取爬虫实例, 进而获取爬虫的 parse 方法
        spider = self.spiders.get(request.spider_name)
        # 获取 request 对象对应的响应的parse方法. getattr 从 self.spiders 中查找并返回 request的parse属性指定的方法
        # 对于糗事百科爬虫来说, 1-13页列表页中, 由于request对象没有指定parse方法, 所以会使用默认的 parse="parse", 而对于详情页, 则使用 request对象指定的 "parse_detail" 方法.
        parse = getattr(spider, request.parse)

        # 5. 利用爬虫的parse方法，处理响应
        # 因为 spiders 的 parse 方法已经修改为生成器, 所以这里要进行遍历
        for result in parse(response):
            # 6. 判断结果的类型
            # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
            if isinstance(result, Request):
                for spider_mid in self.spider_mids:
                    # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
                    result = spider_mid.process_request(result)

                # 对于新的请求, 在保存到调度器之间也添加 spider_name 属性
                result.spider_name = request.spider_name

                self.scheduler.add_request(result)
                # self.total_request_num += 1  # 请求加1
                # 对 redis 中的请求数量进行加 1 操作
                self.collector.incr(self.collector.request_num_key)

            # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
            else:
                # 遍历所有的管道, 对item进行处理
                for pipeline in self.pipelines:
                    # 必须要把处理的结果重新赋值给 result, 下一个管道才能在上一个管道的基础上进一步处理
                    result = pipeline.process_item(result, spider)

        # 整个函数都是处理单个请求, 整个函数执行完了, 单个请求才处理完, 此时总的响应数加1
        # self.total_response_num += 1
        # 对 redis 中的响应数量进行加 1 操作
        self.collector.incr(self.collector.response_num_key)

    def _error_callback(self, exception):
        '''异常回调函数'''
        try:
            raise exception  # 抛出异常后, 才能被日志进行完整记录下来
        except Exception as e:
            logger.exception(e)

    def _callback(self, temp):  # 必须有 temp 参数
        '''执行新的请求的回调函数, 实现循环'''
        if self.is_running is True:  # 如果还没满足退出条件, 那么继续添加新任务, 否则不继续添加, 终止回调函数, 达到退出循环的目的
            self.pool.apply_async(self._execute_request_response_item, callback=self._callback, error_callback=self._error_callback)

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self.is_running = True  # 启动引擎时, 设置 is_running 状态为True
        # self._start_request()  # 初始化请求

        # 向调度器添加初始请求, 初始化请求
        self.pool.apply_async(self._start_request, error_callback=self._error_callback)  # 使用异步, 当主线程执行到这里时, 会使用线程池中的一个子线程来执行这个函数, 主线程继续向下执行

        # 虽然调用的是异步的 apply_async 方法, 但调用的过程依然是同步的, 执行完一个 "请求-响应-数据" 的流程之后, 才调用 _callback 方法, 这时的并发量还是非常低的, 还是1. 为了提高并发量, 可以把这句话放到一个循环中执行. 如 for i in range(3): 这样就会有 3 个并发线程同时去执行
        for i in range(CONCOURRENT_REQUEST):
            # 利用回调实现循环. 同样会使用一个子线程来执行这个函数
            self.pool.apply_async(self._execute_request_response_item, callback=self._callback, error_callback=self._error_callback)

        # 设置循环, 处理多个请求
        # 使用循环让主线程处理堵塞状态, 一直等到子线程执行结束才退出循环
        while True:
            time.sleep(0.001)  # 避免主线程 cpu 空转, 降低资源消耗
            # self._execute_request_response_item()   # 处理单个请求
            # 循环结束的条件
            # 成功的响应数 + 重复的响应数量 >= 总的请求数量, 程序结束
            # if self.collector.request_num != 0:  # 刚开始时总的请求数量为0, 只有当总请求数不为0时, 即至少有一个请求或响应后, 才有可能退出
            if self.collector.finished_start_requests_num == len(self.spiders):  # 当处理完的起始请求数量等于爬虫的数量时, 表示每个爬虫都被处理过一遍了, 这时再判断请求数和响应数的关系
                if self.collector.response_num + self.collector.duplicate_request_num >= self.collector.request_num:
                    self.is_running = False  # 满足循环退出条件后, 设置运行状态为 False
                    break

        # 在爬虫的运行结束后, 可能线程池与服务器链接还没有断开, 相当于子线程的执行还未完成, 程序会处于等待状态. 所以在爬虫中一般不会去执行 pool.close() 和 pool.join()
        self.pool.close()
        self.pool.join()


if __name__ == '__main__':
    engine = Engine()
    engine.start()

```

修改 spider_project/pipelines.py, 添加新浪的管道

```python
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

```

修改 spider_project/settings.py, 激活 SinaSpider, SinaPipeline

```python
import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO  # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'  # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = '日志.log'  # 默认日志文件名称

# 启用的爬虫
SPIDERS = [
    'spiders.baidu.BaiduSpider',
    'spiders.qiubai.QiubaiSpider',
    'spiders.sina.SinaSpider'
]

# 启用的管道类
PIPELINES = [
    'pipelines.BaiduPipeline',
    'pipelines.QiubaiPipeline',
    'pipelines.SinaPipeline',
]

# 启用的爬虫中间件类
SPIDER_MIDDLEWARES = [
    'downloader_middlewares.TestDownloaderMiddleware2'
]

# 启用的下载器中间件类
DOWNLOADER_MIDDLEWARES = [
    'spider_middlewares.TestSpiderMiddleware1'
]

# 设置最大并发数量
CONCOURRENT_REQUEST = 5

# 异步方式  thread, coroutine
# ASYNC_TYPE = 'coroutine'
ASYNC_TYPE = 'thread'

# redis队列默认配置
REDIS_QUEUE_NAME = 'request_queue'   # 在实际运行的过程中, 队列名是根据爬虫名称自己定义的, 所以这个字段可有可无
REDIS_QUEUE_HOST = 'localhost'
REDIS_QUEUE_PORT = 6379
REDIS_QUEUE_DB = 0

# 设置是否需要持久化和分布式
# 设置调度器的内容, 即请求对象是否要持久化
# 如果是 True, 那么就是使用分布式, 同时也是基于请求的增量式爬虫
# 如果是 False, 不会使用 redis 队列, 而是使用 python 的 set 存储指纹和请求
SCHEDULER_PERSIST = True

# redis 指纹集合的位置, 存储 request 请求的指纹
REDIS_SET_NAME = 'redis_set'
REDIS_SET_HOST = 'localhost'
REDIS_SET_PORT = 6379
REDIS_SET_DB = 0

```

redis_cli
flushdb
运行爬虫



3.4.3. 框架升级--断点续爬设计原理及其实现


1. 断点续爬设计分析
•   断点续爬设计原理介绍： 

断点续爬的效果: 爬虫程序中止后, 再次启动, 对已经发起的请求不再发起, 而是直接从之前的队列中获取请求继续执行.

这也就意味着需要实现以下两点:
    1. 去重标记 (历史请求的指纹) 持久化存储, 使得新的请求可以和以前的请求进行去重比对
    2. 请求队列也需要持久化存储
其实也就是程序的中止不会造成请求队列和去重容器的消失, 再次启动程序后, 还能继续访问它们.

前面的分布式设计其实正好就满足了以上两点, 也就是说其实已经实现了断点续爬, 只需要开启分布式.

•   只实现持久化存储队列完成断点续爬可能出现的问题: 

如果分布式爬取节点部分或全部执行体被手动关掉或者异常终止, 那么正在挪的 Request 对象就会发生丢失. 

所以如果对极个别请求的丢失不敏感的爬虫, 那么之前的分布式设计已经足以满足断点续爬的需求了; 但如果对这种极个别请求的丢失很敏感的爬虫, 前面的设计就不能满足这样的灾难性问题了.


•   现有断点续爬方案的问题解决方案分析一: 

使用 "请求备份容器", 把 Request 对象同时添加到请求队列和请求备份容器中, 当执行线程或分布式爬取节点执行正常时, 才从备份容器中删除请求, 当队列执行完毕, 队列中没有数据时, "备份容器" 中剩下的请求就是 "丢失的请求对象", 接下来只需要再把它们放回请求队列就可以重新执行了.


•   现有断点续爬方案的问题解决方案分析二: 

但是, 如果某个 Request 请求无论如何都无法执行成功, 那么这里很可能会造成一个 "死循环", 因此, 可以考虑给 Request 对象设置一个 "重试次数" 的属性:
    1. 每次从队列里弹出一个 Request 时, 就把它在 "备份容器" 中的对应请求的 "重试次数"+1
    2. 如果从队列里弹出一个 Request 后, 先判断它的 "重试次数" 是否超过了配置文件中设置的 "最大重试次数", 如果超过, 那么就不再处理这个请求对象, 并把它记录到日志中, 同时从请求备份容器中删除掉, 否则就继续执行.



2. 断点续爬无丢失方案的实现
•   断点续爬无丢失的实现方案分析： 

•   断点续爬无丢失的代码实现：
    o   添加备份容器：利用redis的hash类型类对每一个请求对象进行存储
    o   为Request对象设置重试次数属性
    o   在调度器的get_request方法中实现响应的逻辑判断
    o   实现delete_request方法：从备份中删除对应的Reqeust对象
    o   实现add_lost_request方法
    o   在引擎中调用这些方法，完成断点续爬无丢失需求

```python
# spider_plus/redis_hash.py

'''实现一个对redis哈希类型的操作封装'''
import redis
import pickle

from spider_plus.http.request import Request
from spider_plus.conf import settings


class RedisBackupRequest(object):
    '''利用hash类型，存储每一个请求对象，key是指纹，值就是请求对象'''

    REDIS_BACKUP_NAME = settings.REDIS_BACKUP_NAME
    REDIS_BACKUP_HOST = settings.REDIS_BACKUP_HOST
    REDIS_BACKUP_PORT = settings.REDIS_BACKUP_PORT
    REDIS_BACKUP_DB = settings.REDIS_BACKUP_DB


    def __init__(self):
        self._redis = redis.StrictRedis(host=self.REDIS_BACKUP_HOST, port=self.REDIS_BACKUP_PORT ,db=self.REDIS_BACKUP_DB)
        self._name = self.REDIS_BACKUP_NAME

    # 增删改查
    def save_request(self, fp, request):
        '''将请求对象备份到redis的hash中'''
        bytes_data = pickle.dumps(request)
        # 指纹作为键, 真正的request对象作为值保存下来, 删除时使用 fp 为键进行删除即可
        self._redis.hset(self._name, fp, bytes_data)

    def delete_request(self, fp):
        '''根据请求的指纹，将其删除'''
        self._redis.hdel(self._name, fp)

    def update_request(self, fp, request):
        '''更新已有的fp'''
        self.save_request(fp, request)

    def get_requests(self):
        '''返回全部的请求对象'''
        for fp, bytes_request in self._redis.hscan_iter(self._name):
            request = pickle.loads(bytes_request)
            yield request

    def get_backup_request_length(self):
        return self._redis.hlen(self.REDIS_BACKUP_NAME)
```


修改 spider_plus/conf/default_settings.py, 添加 request 请求备份的 redis 配置

```python
import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO    # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'   # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = 'log.log'    # 默认日志文件名称

# 设置最大并发数量
CONCOURRENT_REQUEST = 5

# 异步方式  thread, coroutine
ASYNC_TYPE = 'coroutine'
# ASYNC_TYPE = 'thread'

# redis队列默认配置, 存储 request 请求
REDIS_QUEUE_NAME = 'request_queue'
REDIS_QUEUE_HOST = 'localhost'
REDIS_QUEUE_PORT = 6379
REDIS_QUEUE_DB = 0    # 默认使用 0 号数据库

# 设置是否需要持久化和分布式
# 设置调度器的内容, 即请求对象是否要持久化
# 如果是 True, 那么就是使用分布式, 同时也是基于请求的增量式爬虫
# 如果是 False, 不会使用 redis 队列, 而是使用 python 的 set 存储指纹和请求
SCHEDULER_PERSIST = True

# redis 指纹集合的位置, 存储 request 请求的指纹
REDIS_SET_NAME = 'redis_set'
REDIS_SET_HOST = 'localhost'
REDIS_SET_PORT = 6379
REDIS_SET_DB = 0

# request 请求备份的设置
REDIS_BACKUP_NAME = 'request_backup'
REDIS_BACKUP_HOST = 'localhost'
REDIS_BACKUP_PORT = 6379
REDIS_BACKUP_DB = 0
```


修改 spider_project/settings.py, 添加 request 请求备份的 redis 配置

```python
import logging

# 默认的日志配置
DEFAULT_LOG_LEVEL = logging.INFO  # 默认等级
DEFAULT_LOG_FMT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'  # 默认日志格式
DEFUALT_LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'  # 默认时间格式
DEFAULT_LOG_FILENAME = '日志.log'  # 默认日志文件名称

# 启用的爬虫
SPIDERS = [
    'spiders.baidu.BaiduSpider',
    'spiders.qiubai.QiubaiSpider',
    'spiders.sina.SinaSpider'
]

# 启用的管道类
PIPELINES = [
    'pipelines.BaiduPipeline',
    'pipelines.QiubaiPipeline',
    'pipelines.SinaPipeline',
]

# 启用的爬虫中间件类
SPIDER_MIDDLEWARES = [
    'downloader_middlewares.TestDownloaderMiddleware2'
]

# 启用的下载器中间件类
DOWNLOADER_MIDDLEWARES = [
    'spider_middlewares.TestSpiderMiddleware1'
]

# 设置最大并发数量
CONCOURRENT_REQUEST = 5

# 异步方式  thread, coroutine
# ASYNC_TYPE = 'coroutine'
ASYNC_TYPE = 'thread'

# redis队列默认配置
REDIS_QUEUE_NAME = 'request_queue'   # 在实际运行的过程中, 队列名是根据爬虫名称自己定义的, 所以这个字段可有可无
REDIS_QUEUE_HOST = 'localhost'
REDIS_QUEUE_PORT = 6379
REDIS_QUEUE_DB = 0

# 设置是否需要持久化和分布式
# 设置调度器的内容, 即请求对象是否要持久化
# 如果是 True, 那么就是使用分布式, 同时也是基于请求的增量式爬虫
# 如果是 False, 不会使用 redis 队列, 而是使用 python 的 set 存储指纹和请求
SCHEDULER_PERSIST = True

# redis 指纹集合的位置, 存储 request 请求的指纹
REDIS_SET_NAME = 'redis_set'
REDIS_SET_HOST = 'localhost'
REDIS_SET_PORT = 6379
REDIS_SET_DB = 0

# request 请求备份的设置
REDIS_BACKUP_NAME = 'request_backup'
REDIS_BACKUP_HOST = 'localhost'
REDIS_BACKUP_PORT = 6379
REDIS_BACKUP_DB = 0

```


•   为Request对象增加重试次数属性：

```python
# coding=utf-8
# 请求对象

class Request(object):
    """完成请求对象的封装"""

    def __init__(self, url, method="GET", headers=None, params=None, data=None, parse="parse", meta={}, filter=True):
        '''
        初始化request对象
        :param url: url地址
        :param method: 请求方法
        :param headers:请求头
        :param params: 请求的参数, 查询字符串
        :param data: 请求体, 表单数据
        :param parse: 请求对象对应的响应的解析函数
        :param meta: 字典, 在不同的解析函数之间传递数据
        :param filter: 是否对该请求进行去重, 默认会对请求进行去生
        '''
        self.url = url
        self.method = method
        self.headers = headers
        self.params = params
        self.data = data
        self.parse = parse
        self.meta = meta
        self.filter = filter
        self.retry_time = 0  # 重试次数

```


•   修改调度器，实现对应的逻辑以及方法：

```python
spider_plus/core/scheduler.py

# coding=utf-8
# 调度器

# 利用six模块实现py2和py3兼容
import six
from six.moves.queue import Queue
import w3lib.url
from hashlib import sha1

from spider_plus.utils.log import logger
from spider_plus.utils.queue import Queue as ReidsQueue
from spider_plus.conf.settings import SCHEDULER_PERSIST
from spider_plus.utils.set import NoramlFilterContainer, RedisFilterContainer
from spider_plus.utils.redis_hash import RedisBackupRequest
from spider_plus.conf.settings import MAX_RETRY_TIMES

class Scheduler(object):
    '''完成调试器模块的封装'''

    def __init__(self, collector):
        # 如果不需要持久化, 就使用python内置的 Queue, 如果需要持久化, 就使用基于 Reids 的 RedisQueue
        if not SCHEDULER_PERSIST:
            self.queue = Queue()  # 存储的是待抓取的请求
            # 不使用分布式的时候, 使用 python 的集合存储指纹
            self._filter_container = NoramlFilterContainer()
        else:
            self.queue = ReidsQueue()
            # 使用分布式的时候, 使用 redis 的集合存储指纹
            self._filter_container = RedisFilterContainer()

        # 去重容器, 利用set类型存储每个请求的指纹
        # self._filter_container = set()

        # self.repeat_request_num = 0  # 记录重复的请求数量. 为什么要统计重复请求的数量. 之前在引擎中使用 "总的响应数量 == 总的请求数量" 来确定程序的退出, 如果有重复的请求, 就不会发送请求, 这个条件就永远不会满足. 需要把程序退出的条件修改为 "总的响应数量 + 总的重复数量 == 总的请求数量", 所以这里要记录重复的请求的数量
        self.collector = collector
        self._backup_request = RedisBackupRequest()

    def add_request(self, request):
        '''
        实现添加request到队列中
        :param request: 请求对象
        :return: None
        '''
        # 判断请求是否需要进行去重, 如果不需要, 直接添加到队列
        if not request.filter:  # 不需要进行去重
            request.fp = self._gen_fp(request)  # 手动给 request 对象添加指纹属性
            self.queue.put(request)
            self._backup_request.save_request(request.fp, request)  # 对请求进行备份
            logger.info("添加不去重的请求: <{} {}>".format(request.method, request.url))
            return   # 必须return. 如果不需要进行去重, 那么就直接返回, 后面生成指纹并把指纹保存到去重容器中的操作就不会去执行了. 但是这样做的话 request 对象就没有 fp 的属性, 在以后可能会用到 fp 属性的地方就会出错. 需要在向队列中添加该请求之间给该请求添加一个fp的属性.

        # 调用_filter_request来实现对请求对象的去重
        # 如果指纹不存在, 才把请求对象添加到队列中
        if self._filter_request(request):
            self.queue.put(request)
            self._backup_request.save_request(request.fp, request)  # 对请求进行备份

    def get_request(self):
        '''
        实现获取队列中的request对象
        :return: 请求对象
        '''
        # queue.get(), 默认 block=Ture, 即是堵塞的, 如果队列中没有对象, 就堵塞在这里. 需要修改为非堵塞的.
        # 非堵塞状态可以会报错, 所以使用try...except...
        try:
            request = self.queue.get(block=False)
        except:
            return None
        else:  # 如果try中的语句没有报错
            # 先判断 是否需要进行去重, 如果对请求启用了过滤, 并且启用了请求持久化的功能
            if request.filter is True and SCHEDULER_PERSIST:
                # 判断重试次数是否超过了规定
                request.fp = self._gen_fp(request)
                if request.retry_time >= MAX_RETRY_TIMES:
                    self._backup_request.delete_request(request.fp)    # 如果超过，那么直接删除
                    logger.warnning("出现异常请求，且超过最大尝试的次数：<{} {}>".format(request.method, request.url))
                request.retry_time += 1   # 重试次数+1
                self._backup_request.update_request(request.fp, request)  # 把更新的重试次数更新到备份中
            return request

    def delete_request(self, request):
        '''根据请求从备份删除对应的请求对象'''
        if SCHEDULER_PERSIST:
            request.fp = self._gen_fp(request)
            self._backup_request.delete_request(request.fp)

    def add_lost_requests(self):
        '''将丢失的请求对象再添加到队列中'''
        # 从备份容器取出来，放到队列中
        if SCHEDULER_PERSIST:
            for request in self._backup_request.get_requests():
                self.queue.put(request)

    def _filter_request(self, request):
        '''
        实现对请求对象的去重
        :param request: 请求对象
        :return: bool
        '''
        # 给 request对象添加一个fp属性, 保存指纹
        # 去重容器: 存储已经发过的请求的特征 url, 选用集合类型: set()
        # 利用请求的 url method data 求出一个指纹, 利用sha1
        request.fp = self._gen_fp(request)
        # 如果判断指纹不在指纹集合中, 就把它添加进去
        if not self._filter_container.exists(request.fp):
            logger.info("添加新的请求: <%s>" % request.url)
            # 如果是新的请求, 那么就添加到去重容器中, 表示请求已经添加到了队列中
            self._filter_container.add_fp(request.fp)
            return True
        else:
            logger.info("发现重复的请求：<{} {}>".format(request.method, request.url))
            self.collector.incr(self.collector.duplicate_request_num_key)
            return False

    @staticmethod
    def _to_bytes(string):
        if six.PY2:  # 如果是python2环境
            if isinstance(string, str):  # str类型在py2中是字节类型
                return string
            else:  # 如果是python2的 unicode 类型, 转化为python2字节类型
                return string.encode("utf-8")
        elif six.PY3:  # 如果是python3环境
            if isinstance(string, str):
                return string.encode("utf-8")  # 转换为bytes类型
            else:
                return string  # 说明string是bytes类型，直接返回

    def _gen_fp(self, request):
        '''
        对 url 地址, 请求体, 请求参数, 请求方法进行加密, 生成 request 对象的指纹
        :param request: request对象
        :return: 指纹字符串
        '''
        # 1. url 地址排序：借助w3lib.url模块中的 canonicalize_url 方法
        url = w3lib.url.canonicalize_url(request.url)
        # 2. 请求方法 method, 不需要排序，只要保持大小写一致就可以
        method = request.method.upper()  # 全大写
        # 3. 请求参数params. 排序. 如果有提供则是一个字典，如果没有则是 None
        params = request.params if request.params is not None else {}  # 如果是None，那么设为{}
        params = sorted(params.items(), key=lambda x: x[0])  # 按照key对字典进行排序，结果将是一个列表
        # 4. 请求体data排序：如果有提供则是一个字典，如果没有则是None
        data = request.data if request.data is not None else {}  # 如果是None，那么设为{}
        data = sorted(data.items(), key=lambda x: x[0])  # 按照key对字典进行排序，结果将是一个列表

        # 5. 利用sha1算法，计算指纹
        s1 = sha1()
        # 由于s1接收的只能是bytes类型(python3)、str类型(python2)，他们都是某种编码类型的(如utf-8、gbk)
        # 为了兼容py2和py3, 利用 _to_bytes 方法, 把所有的字符串转化为字节类型
        s1.update(self._to_bytes(url))  # 添加url地址
        s1.update(self._to_bytes(method))  # 添加请求方法
        s1.update(self._to_bytes(str(params)))  # 添加请求参数
        s1.update(self._to_bytes(str(data)))  # 添加请求体

        fp = s1.hexdigest()  # 提取16进制的sha1指纹字符串并返回
        return fp
```


修改引擎代码, 添加 从备份容器取出请求, 放入队列中, 以及下载完成后从备份容器中删除请求的功能

```python

# coding=utf-8
# 引擎
import time
import importlib

from datetime import datetime

# 为什么要把导入 gevent.Pool 的操作放在最前面, 由于打patch补丁是为了替换掉socket为非阻塞的, 而下载器 Downloader 中正好使用了requests模块，如果在这之后导入协程池，会导致requests中使用的socket没有被替换成功, 从而有可能导致使用出现问题
from spider_plus.conf.settings import ASYNC_TYPE
# 判断使用什么异步模式，改用对应的异步池
if ASYNC_TYPE == 'thread':
    from multiprocessing.dummy import Pool    # 导入线程池对象
elif ASYNC_TYPE == 'coroutine':
    from spider_plus.async.coroutine import Pool
    # from gevent.monkey import patch_all
    # patch_all()
else:
    raise Exception("不支持的异步类型：{},".format(ASYNC_TYPE))

from spider_plus.http.request import Request  # 导入Request对象
from spider_plus.utils.log import logger

from .scheduler import Scheduler
from .downloader import Downloader
from spider_plus.conf.settings import SPIDERS, PIPELINES, DOWNLOADER_MIDDLEWARES, SPIDER_MIDDLEWARES, CONCOURRENT_REQUEST
from spider_plus.utils.status_collector import StatusCollector

class Engine(object):
    '''完成对引擎模块的封装'''

    def __init__(self):
        '''
        实例化其他的组件, 在引擎中能够通过调用组件的方法实现功能
        '''
        # 实例化 collector 时要传递爬虫的名字, 所以要把 spiders 的实例化放在前面
        self.spiders = self._auto_import_instances(SPIDERS, is_spider=True)  # 接收外部传入的爬虫对象, 字典
        # 把统计数量的容器放在调度器之前实例化, 因为重复请求的数量是在调度器中进行统计的, 并且在引擎最后面使用到调度器中的重复请求的数量. self.scheduler.repeat_request_num, 所以要把 collector 也传递到调度器中, 经过调度器统计重复请求的数量后才能使用
        self.collector = StatusCollector(list(self.spiders.keys()))
        self.scheduler = Scheduler(self.collector)  # 初始化调度器对象
        self.downloader = Downloader()  # 初始化下载器对象
        self.pipelines = self._auto_import_instances(PIPELINES)  # 初始化管道对象, 列表
        self.spider_mids = self._auto_import_instances(SPIDER_MIDDLEWARES)  # 初始化爬虫中间件对象, 列表
        self.downloader_mids = self._auto_import_instances(DOWNLOADER_MIDDLEWARES)  # 初始化下载器中间件对象, 列表
        # 为了使处理请求响应数据的方法能够正常退出, 定义两个变量, 当总的响应数量大于等于总的请求数量时, 所有请求都已经处理完毕, 就可以退出了
        # self.total_request_num = 0  # 总的请求数
        # self.total_response_num = 0  # 总的响应数
        self.pool = Pool(5)  # 实例化线程池对象. 线程池的大小默认为cpu的个数, 电脑是单核时线程池的大小就为 1, 可以手动指定线程池的大小
        self.is_running = True  # 程序是否处理运行状态, 依据此状态来决定程序是否退出. 当程序开始运行时, 设置此参数为 Ture, 当所有的请求执行结束后, 设置此参数为 False, 此时程序就退出.

    def _auto_import_instances(self, path=[], is_spider=False):
        '''
        根据配置文件, 实现模块的动态导入, 传入模块路径列表, 返回类的实例
        :param path: settings 中配置的要导入类的路径. 包含模块位置字符串的列表
        :param is_spider: 是否是爬虫. 爬虫是字典的形式, 所以需要进行单独的判断和处理
        :return: 返回爬虫, 管道, 中间件的实例
        '''
        if is_spider is True:
            instances = {}
        else:
            instances = []  # 存储对应类的实例对象

        for p in path:
            module_name = p[:p.rfind(".")]  # 取出模块名称
            module_name = p.rsplit(".", 1)[0]
            cls_name = p[p.rfind(".") + 1:]  # 取出类名称
            cls_name = p.rsplit(".", 1)[-1]
            module = importlib.import_module(module_name)  # 导入模块
            cls = getattr(module, cls_name)  # 根据类名称获取module下的类对象
            if is_spider is True:
                instances[cls.name] = cls()
            else:
                instances.append(cls())  # 实例化类对象
        return instances  # 返回类对象

    def start(self):
        '''
        提供引擎启动的入口
        :return:
        '''
        start_time = datetime.now()  # 起始时间
        logger.info("爬虫启动: {}".format(start_time))  # 使用日志记录起始运行时间
        logger.info("当前启动的爬虫: {}".format(SPIDERS))
        logger.info("当前开启的管道: {}".format(PIPELINES))
        logger.info("当前开启的下载器中间件: {}".format(DOWNLOADER_MIDDLEWARES))
        logger.info("当前开启的爬虫中间件: {}".format(SPIDER_MIDDLEWARES))
        self._start_engine()
        end_time = datetime.now()  # 结束时间
        logger.info("爬虫结束: {}".format(end_time))  # 使用日志记录结束运行时间
        logger.info("爬虫运行时间: {}".format((end_time - start_time).total_seconds()))  # 使用日志记录运行耗时
        # 在引擎的调用执行结束后, 打印总的请求数量和总的响应数量.
        # logger.info("总的请求数量: {}个".format(self.total_request_num))
        logger.info("总的请求数量: {}个".format(self.collector.request_num))
        # logger.info("总的响应数量: {}个".format(self.total_response_num))
        logger.info("总的响应数量: {}个".format(self.collector.response_num))
        # logger.info("总的重复数量: {}个".format(self.scheduler.repeat_request_num))
        logger.info("总的重复数量: {}个".format(self.collector.duplicate_request_num))
        # 完成的 start_requests 函数的数量
        logger.info("总的 start_requests 数量: {}个".format(self.collector.finished_start_requests_num))

        # 爬虫运行结束时, 清空 redis 中用于统计数量的 键. 如果程序正常运行并退出, 这里的键就会被清理, 只留下 "redis_set" 这个键, 其中保存着请求的指纹, 如果程序运行的过程中退出了, 就不会清空统计数量的键, redis 中会多出来 "baidu_qiubai_request_num", "baidu_qiubai_duplicate_request_num", "baidu_qiubai_response_num", "request_queue", 这几个键.
        self.collector.clear()

    def _callback_total_finished_start_requests_num(self, temp):
        '''记录完成的 start_requests 的数量
        在 _start_request 函数中每调用一次 _func 方法, 就会执行一次该函数, 执行的次数就是爬虫的个数, 每一个爬虫中都有一个 start_requests 方法, 执行完一个 start_requests 方法, 就让 finished_start_requests_num_key 加 1
        '''
        self.collector.incr(self.collector.finished_start_requests_num_key)

    def _start_request(self):
        '''初始化请求, 调用爬虫的start_request方法, 把所有的请求添加到调度器'''

        def _func(spider_name, spider):
            for start_request in spider.start_requests():
                # 2. 把初始请求添加给调度器
                # 利用爬虫中间件预处理请求对象
                for spider_mid in self.spider_mids:
                    start_request = spider_mid.process_request(start_request)
                # 在把初始请求添加到调度器中之前, 给它添加一个属性 spider_name, 记录它是哪个爬虫产生的请求, 以方便后面 _execute_request_response_item 中通过这个属性获取到对应的爬虫, 进而获取爬虫的 parse方法
                start_request.spider_name = spider_name

                # 2. 调用调度器的add_request方法, 添加request对象到调度器中
                self.scheduler.add_request(start_request)
                # 把request添加到调度器中之后, 把总请求数加1
                # self.total_request_num += 1
                # 对 redis 中的请求数量进行加 1 操作
                self.collector.incr(self.collector.request_num_key)

        # 1. 爬虫模块发出初始请求
        # 遍历 spiders 字典, 获取每个spider对象
        # 因为spider的start_requests方法已经修改为生成器, 所以这里要进行遍历. 但如果 spider.start_requests() 方法中存在着 while True 死循环, 就会发生阻塞, 一直会卡在这里执行死循环. 所以要把这里的代码改为异步执行
        for spider_name, spider in self.spiders.items():
            self.pool.apply_async(_func, args=(spider_name, spider), callback=self._callback_total_finished_start_requests_num)    # 把执行每个爬虫的start_requests方法，设置为异步的. 每次都会使用一个子线程来处理. 这样, 就算某个爬虫的 start_requests 方法中存在死循环, 只会对执行这个死循环的子线程产生堵塞, 不会对主线程造成堵塞.

    def _execute_request_response_item(self):
        '''处理单个请求, 从调度器取出, 发送请求, 获取响应, parse函数处理, 调度器处理'''
        # 3. 调用调度器的get_request方法, 获取request对象
        request = self.scheduler.get_request()
        if request is None:  # 判断从调度器中取出来的request是否是None, 如果是None, 表示调度器为空, 就不进行任何进一步的处理
            return
        for downloader_mid in self.downloader_mids:
            # 从调度器中取出来的request对象经过下载器中间件的process_request进行处理
            request = downloader_mid.process_request(request)
        # 4. 调用下载器的get_response方法, 获取响应
        response = self.downloader.get_response(request)

        # 为了把 request中的meta传递给 response, 在调用下载器获取响应后, 给response添加一个meta属性即可
        response.meta = request.meta

        # 从下载器中返回的response对象经过下载器中间件的process_response进行处理
        for downloader_mid in self.downloader_mids:
            response = downloader_mid.process_response(response)
        # 从下载器中返回的response对象要返回spider, 就要经过爬虫器中间件的process_response进行处理
        for spider_mid in self.spider_mids:
            response = spider_mid.process_response(response)

        # 根据请求对象的 spider_name 属性, 获取爬虫实例, 进而获取爬虫的 parse 方法
        spider = self.spiders.get(request.spider_name)
        # 获取 request 对象对应的响应的parse方法. getattr 从 self.spiders 中查找并返回 request的parse属性指定的方法
        # 对于糗事百科爬虫来说, 1-13页列表页中, 由于request对象没有指定parse方法, 所以会使用默认的 parse="parse", 而对于详情页, 则使用 request对象指定的 "parse_detail" 方法.
        parse = getattr(spider, request.parse)

        # 5. 利用爬虫的parse方法，处理响应
        # 因为 spiders 的 parse 方法已经修改为生成器, 所以这里要进行遍历
        for result in parse(response):
            # 6. 判断结果的类型
            # 6.1 如果是request请求对象, 重新调用调度器的add_request方法
            if isinstance(result, Request):
                for spider_mid in self.spider_mids:
                    # 如果经过爬虫解析之后得到的是request对象, 把request对象保存到调度器之前也要经过爬虫中间件进行处理
                    result = spider_mid.process_request(result)

                # 对于新的请求, 在保存到调度器之间也添加 spider_name 属性
                result.spider_name = request.spider_name

                self.scheduler.add_request(result)
                # self.total_request_num += 1  # 请求加1
                # 对 redis 中的请求数量进行加 1 操作
                self.collector.incr(self.collector.request_num_key)

            # 6.2 如果是数据, 调用pipeline管道的process_item方法对数据进行处理
            else:
                # 遍历所有的管道, 对item进行处理
                for pipeline in self.pipelines:
                    # 必须要把处理的结果重新赋值给 result, 下一个管道才能在上一个管道的基础上进一步处理
                    result = pipeline.process_item(result, spider)

        # 整个函数都是处理单个请求, 整个函数执行完了, 单个请求才处理完, 此时总的响应数加1
        # self.total_response_num += 1
        # 对 redis 中的响应数量进行加 1 操作
        self.collector.incr(self.collector.response_num_key)

        # 一个请求处理成功之后就在备份容器中删除该请求
        print("删除请求")
        self.scheduler._backup_request.delete_request(request.fp)
        print(self.scheduler._backup_request.get_backup_request_length())

    def _error_callback(self, exception):
        '''异常回调函数'''
        try:
            raise exception  # 抛出异常后, 才能被日志进行完整记录下来
        except Exception as e:
            logger.exception(e)

    def _callback(self, temp):  # 必须有 temp 参数
        '''执行新的请求的回调函数, 实现循环'''
        if self.is_running is True:  # 如果还没满足退出条件, 那么继续添加新任务, 否则不继续添加, 终止回调函数, 达到退出循环的目的
            self.pool.apply_async(self._execute_request_response_item, callback=self._callback, error_callback=self._error_callback)

    def _start_engine(self):
        '''
        实现引擎具体的功能
        :return:
        '''
        self.is_running = True  # 启动引擎时, 设置 is_running 状态为True
        # self._start_request()  # 初始化请求

        # 向调度器添加初始请求, 初始化请求
        self.pool.apply_async(self._start_request, error_callback=self._error_callback)  # 使用异步, 当主线程执行到这里时, 会使用线程池中的一个子线程来执行这个函数, 主线程继续向下执行

        # 虽然调用的是异步的 apply_async 方法, 但调用的过程依然是同步的, 执行完一个 "请求-响应-数据" 的流程之后, 才调用 _callback 方法, 这时的并发量还是非常低的, 还是1. 为了提高并发量, 可以把这句话放到一个循环中执行. 如 for i in range(3): 这样就会有 3 个并发线程同时去执行
        for i in range(CONCOURRENT_REQUEST):
            # 利用回调实现循环. 同样会使用一个子线程来执行这个函数
            self.pool.apply_async(self._execute_request_response_item, callback=self._callback, error_callback=self._error_callback)

        # 设置循环, 处理多个请求
        # 使用循环让主线程处理堵塞状态, 一直等到子线程执行结束才退出循环
        while True:
            time.sleep(0.001)  # 避免主线程 cpu 空转, 降低资源消耗
            # self._execute_request_response_item()   # 处理单个请求
            # 循环结束的条件
            # 成功的响应数 + 重复的响应数量 >= 总的请求数量, 程序结束
            # if self.collector.request_num != 0:  # 刚开始时总的请求数量为0, 只有当总请求数不为0时, 即至少有一个请求或响应后, 才有可能退出
            if self.collector.finished_start_requests_num == len(self.spiders):  # 当处理完的起始请求数量等于爬虫的数量时, 表示每个爬虫都被处理过一遍了, 这时再判断请求数和响应数的关系
                if self.collector.response_num + self.collector.duplicate_request_num >= self.collector.request_num:
                    print(self.collector.request_num, self.collector.duplicate_request_num, self.collector.request_num)
                    self.is_running = False  # 满足循环退出条件后, 设置运行状态为 False
                    break

        # 不断的从备份中取出来数据, 添加到请求队列中
        while True:
            self.scheduler.add_lost_requests()
            for i in range(CONCOURRENT_REQUEST):
                # 利用回调实现循环. 同样会使用一个子线程来执行这个函数
                self.pool.apply_async(self._execute_request_response_item, callback=self._callback, error_callback=self._error_callback)
            print("备份中请求个数: ", self.scheduler._backup_request.get_backup_request_length())
            if self.scheduler._backup_request.get_backup_request_length() == 0:
                break

        # 在爬虫的运行结束后, 可能线程池与服务器链接还没有断开, 相当于子线程的执行还未完成, 程序会处于等待状态. 所以在爬虫中一般不会去执行 pool.close() 和 pool.join()
        self.pool.close()
        self.pool.join()


if __name__ == '__main__':
    engine = Engine()
    engine.start()

```


依然存在的问题: 中断程序执行, 再次运行, 无法正常退出程序

无法处理类似 "google.com" 这样的请求

未添加使用代理的功能

新建 connection 模块, 完成 mysql, postgresql, redis, mongodb 异步功能的封装


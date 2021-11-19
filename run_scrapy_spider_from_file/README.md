### 目标

- 使用 脚本而不是 scrapy crawl 命令 来运行爬虫, 以方便进行调试

### 测试 `scrapy crawl xxx` 命令

- 新建 test_crawl_spider.py, 内容如下

```python

# -*- coding: utf-8 -*-

from scrapy import cmdline

cmdline.execute('scrapy crawl report_income'.split(' '))

```
- debug 此文件, 就可以看到 scrapy 是调用的 `scrapy.commands.crawl.Command.run` 来执行的爬虫
- scrapy.commands.crawl.Command.run 是通过传入 spider name 来运行爬虫的, 所以要先获取到爬虫名
- `scrapy list` 命令可以查看所有的爬虫名, 可以通过改造此方法来获取 项目下所有的爬虫名

- 新建 test_list_spiders.py, 内容如下

```python

# -*- coding: utf-8 -*-

from scrapy import cmdline

cmdline.execute('scrapy list'.split(' '))

```

- debug 此文件, 就可以看到 scrapy 是调用的 `scrapy.commands.list.Command.run` 来获取爬虫的


### 仿照 scrapy.commands.crawl 和 scrapy.commands.list 来运行爬虫


- 复制 scrapy.commands.list.py 为 test_run_spider.py


```python
from scrapy.commands import ScrapyCommand


class Command(ScrapyCommand):

    requires_project = True
    default_settings = {'LOG_ENABLED': False}

    def short_desc(self):
        return "List available spiders"

    def run(self, args, opts):
        for s in sorted(self.crawler_process.spider_loader.list()):
            print(s)


# 尝试单独实例化并运行
def run():

    c = Command()
    c.run(None, None)


if __name__ == '__main__':
    run()

```

- 尝试直接实例化并运行, 会报如下异常

```shell

Traceback (most recent call last):
  File "/data/spider/test/scrapy_report_income/exe_run.py", line 34, in <module>
    run()
  File "/data/spider/test/scrapy_report_income/exe_run.py", line 30, in run
    c.run(None, None)
  File "/data/spider/test/scrapy_report_income/exe_run.py", line 22, in run
    for s in sorted(self.crawler_process.spider_loader.list()):
AttributeError: 'NoneType' object has no attribute 'spider_loader'

```

- 查看 ScrapyCommand 有源码, `scrapy.commands.ScrapyCommand` 

```python

class ScrapyCommand:

    requires_project = False
    crawler_process = None
    
    # default settings to be used for this command instead of global defaults
    default_settings: Dict[str, Any] = {}
    
    exitcode = 0
    
    def __init__(self):
        self.settings = None  # set in scrapy.cmdline

```

- 其中有类属性 `crawler_process = None`, 在直接实例化并运行时, 因为缺少了 scrapy cmdling 的处理, 就没有对 crawler_process 重新赋值
- 可以手动对类属性 crawler_process 赋值
- ctrl + 点击 scrapy/commands/__init__.py:17 中的 crawler_process, 查看哪里对 crawler_process 重新赋值了
- 只找到一处重新赋值的地方 scrapy/cmdline.py:144, `scrapy.cmdline.execute`, `cmd.crawler_process = CrawlerProcess(settings)`
- 仿照此对 crawler_process 赋值, test_run_spider.py 得到如下代码

```python

# -*- coding: utf-8 -*-

from scrapy.commands import ScrapyCommand
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


class Command(ScrapyCommand):

    requires_project = True
    default_settings = {'LOG_ENABLED': True}

    settings = get_project_settings()
    # scrapy/cmdline.execute:144
    crawler_process = CrawlerProcess(settings)

    def short_desc(self):
        return "List available spiders"

    def run(self, args, opts):
        for s in sorted(self.crawler_process.spider_loader.list()):
            print(s)


# 尝试单独实例化并运行
def run():

    c = Command()
    c.run(None, None)


if __name__ == '__main__':
    run()

```

- 运行, 就能获取到项目下所有的爬虫名了

- 通过 debug test_crawl_spider.py 可以得到传递到 run() 方法中的参数
- 因为 传递到 opts 中的所有参数都为空, 可以不用传递
- 通过 `self.crawler_process.crawl(spname, **opts.spargs)` 传入爬虫名来运行爬虫
- 修改 test_run_spider.py, 添加运行爬虫代码, 就可以运行爬虫了

```python
# -*- coding: utf-8 -*-

from scrapy.commands import ScrapyCommand
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


class Command(ScrapyCommand):

    requires_project = True
    default_settings = {'LOG_ENABLED': True}

    settings = get_project_settings()
    # scrapy/cmdline.execute:144
    crawler_process = CrawlerProcess(settings)

    def short_desc(self):
        return "List available spiders"

    def run(self, args, opts):
        # for s in self.crawler_process.spiders.list():
        for s in sorted(self.crawler_process.spider_loader.list()):
            print(s)
            self.crawler_process.crawl(s)
        self.crawler_process.start()


# 尝试单独实例化并运行
def run():

    c = Command()
    c.run(None, None)


if __name__ == '__main__':
    run()

```

- 查看 scrapy 的官方文档, 也能得到以上运行方式
  - https://docs.scrapy.org/en/latest/topics/practices.html#run-scrapy-from-a-script

### 通过 CrawlerRunner 来运行爬虫

- 官方文档说明如下

```python

from twisted.internet import reactor
import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging

class MySpider(scrapy.Spider):
    # Your spider definition
    ...

configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})
runner = CrawlerRunner()

d = runner.crawl(MySpider)
d.addBoth(lambda _: reactor.stop())
reactor.run() # the script will block here until the crawling is finished

```

- 是通过传入 spidercls 来运行爬虫的, 需要从 spider name 获取到 spidercls
- 可以参考 scrapy.commands.shell.Command.run 或 scrapy.commands.genspider.Command._spider_exists 中的方法
- 修改 test_run_spider.py, 添加 runner 运行爬虫的方法

```python
# -*- coding: utf-8 -*-

from scrapy.commands import ScrapyCommand
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor


class RunSpiderProcess(ScrapyCommand):

    requires_project = True
    default_settings = {'LOG_ENABLED': True}

    settings = get_project_settings()
    # scrapy/cmdline.execute:144
    crawler_process = CrawlerProcess(settings)

    def short_desc(self):
        return "run spiders"

    def run(self, args, opts):
        # for s in self.crawler_process.spiders.list():
        for s in sorted(self.crawler_process.spider_loader.list()):
            print(s)
            self.crawler_process.crawl(s)
        self.crawler_process.start()


class RunSpiderRunner(ScrapyCommand):

    requires_project = True
    default_settings = {'LOG_ENABLED': True}

    settings = get_project_settings()
    # scrapy/cmdline.execute:144
    crawler_process = CrawlerProcess(settings)

    def short_desc(self):
        return "run spiders"

    def run(self, args, opts):
        runner = CrawlerRunner()
        spider_loader = self.crawler_process.spider_loader

        for s in sorted(self.crawler_process.spider_loader.list()):
            spidercls = spider_loader.load(s)
            d = runner.crawl(spidercls)
            d.addBoth(lambda _: reactor.stop())
        reactor.run()


def run_process():

    c = RunSpiderProcess()
    c.run(None, None)


def run_runner():

    c = RunSpiderRunner()
    c.run(None, None)


if __name__ == '__main__':
    # run_process()
    run_runner()


```

- 参考 scrapy.commands.check.Command.run 优化代码

```python

# -*- coding: utf-8 -*-

from scrapy.commands import ScrapyCommand
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor


class RunSpiderProcess(ScrapyCommand):

    requires_project = True
    default_settings = {'LOG_ENABLED': True}

    settings = get_project_settings()
    # scrapy/cmdline.execute:144
    crawler_process = CrawlerProcess(settings)

    def short_desc(self):
        return "run spiders"

    def run(self, args, opts):
        spider_loader = self.crawler_process.spider_loader

        for spidername in args or spider_loader.list():
            self.crawler_process.crawl(spidername)
        self.crawler_process.start()


class RunSpiderRunner(ScrapyCommand):

    requires_project = True
    default_settings = {'LOG_ENABLED': True}

    settings = get_project_settings()
    # scrapy/cmdline.execute:144
    crawler_process = CrawlerProcess(settings)

    def short_desc(self):
        return "run spiders"

    def run(self, args, opts):
        runner = CrawlerRunner()
        spider_loader = self.crawler_process.spider_loader

        for spidername in args or spider_loader.list():
            spidercls = spider_loader.load(spidername)
            d = runner.crawl(spidercls)
            d.addBoth(lambda _: reactor.stop())
        reactor.run()


def run_process():

    c = RunSpiderProcess()
    c.run([], None)


def run_runner():

    c = RunSpiderRunner()
    c.run([], None)


if __name__ == '__main__':
    run_process()
    # run_runner()

```

- 但以上 RunSpiderRunner 只对 spiders 中有单个爬虫的情况适用, 当 spiders 中有多个爬虫时, RunSpiderRunner 运行就会报错

 ```shell script

Unhandled error in Deferred:
2021-06-18 16:16:05 [twisted] CRITICAL: Unhandled error in Deferred:
2021-06-18 16:16:05 [twisted] CRITICAL: Unhandled error in Deferred:

Traceback (most recent call last):
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/defer.py", line 1514, in gotResult
    current_context.run(_inlineCallbacks, r, g, status)
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/defer.py", line 1448, in _inlineCallbacks
    status.deferred.callback(getattr(e, "value", None))
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/defer.py", line 477, in callback
    self._startRunCallbacks(result)
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/defer.py", line 580, in _startRunCallbacks
    self._runCallbacks()
--- <exception caught here> ---
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/defer.py", line 662, in _runCallbacks
    current.result = callback(current.result, *args, **kw)
  File "/data/spider/test/scrapy_report_income/test_run_spider.py", line 48, in <lambda>
    d.addBoth(lambda _: reactor.stop())
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/base.py", line 711, in stop
    raise error.ReactorNotRunning("Can't stop reactor that isn't running.")
twisted.internet.error.ReactorNotRunning: Can't stop reactor that isn't running.

2021-06-18 16:16:05 [twisted] CRITICAL: 
Traceback (most recent call last):
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/defer.py", line 1445, in _inlineCallbacks
    result = current_context.run(g.send, result)
StopIteration

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/defer.py", line 1445, in _inlineCallbacks
    result = current_context.run(g.send, result)
StopIteration

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/defer.py", line 1445, in _inlineCallbacks
    result = current_context.run(g.send, result)
StopIteration

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/defer.py", line 662, in _runCallbacks
    current.result = callback(current.result, *args, **kw)
  File "/data/spider/test/scrapy_report_income/test_run_spider.py", line 48, in <lambda>
    d.addBoth(lambda _: reactor.stop())
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/base.py", line 711, in stop
    raise error.ReactorNotRunning("Can't stop reactor that isn't running.")
twisted.internet.error.ReactorNotRunning: Can't stop reactor that isn't running.
2021-06-18 16:16:05 [twisted] CRITICAL: 
Traceback (most recent call last):
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/defer.py", line 1445, in _inlineCallbacks
    result = current_context.run(g.send, result)
StopIteration

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/defer.py", line 1445, in _inlineCallbacks
    result = current_context.run(g.send, result)
StopIteration

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/defer.py", line 1445, in _inlineCallbacks
    result = current_context.run(g.send, result)
StopIteration

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/defer.py", line 662, in _runCallbacks
    current.result = callback(current.result, *args, **kw)
  File "/data/spider/test/scrapy_report_income/test_run_spider.py", line 48, in <lambda>
    d.addBoth(lambda _: reactor.stop())
  File "/home/spider/.pyenv/versions/income/lib/python3.8/site-packages/twisted/internet/base.py", line 711, in stop
    raise error.ReactorNotRunning("Can't stop reactor that isn't running.")
twisted.internet.error.ReactorNotRunning: Can't stop reactor that isn't running.

```

- 参考 scrapy 官方文档 修改 RunSpiderRunner 即可支持多爬虫运行
  - https://docs.scrapy.org/en/latest/topics/practices.html#running-multiple-spiders-in-the-same-process

```python

# -*- coding: utf-8 -*-

from scrapy.commands import ScrapyCommand
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer


class RunSpiderProcess(ScrapyCommand):

    requires_project = True
    default_settings = {'LOG_ENABLED': True}

    settings = get_project_settings()
    # scrapy/cmdline.execute:144
    crawler_process = CrawlerProcess(settings)

    def short_desc(self):
        return "run spiders"

    def run(self, args, opts):
        spider_loader = self.crawler_process.spider_loader

        for spidername in args or spider_loader.list():
            self.crawler_process.crawl(spidername)
        self.crawler_process.start()


class RunSpiderRunner(ScrapyCommand):

    requires_project = True
    default_settings = {'LOG_ENABLED': True}

    settings = get_project_settings()
    # scrapy/cmdline.execute:144
    crawler_process = CrawlerProcess(settings)

    def short_desc(self):
        return "run spiders"

    def run(self, args, opts):
        spider_loader = self.crawler_process.spider_loader
        configure_logging()
        runner = CrawlerRunner()

        @defer.inlineCallbacks
        def crawl():
            for spidername in args or spider_loader.list():
                spidercls = spider_loader.load(spidername)
                yield runner.crawl(spidercls)
            reactor.stop()

        crawl()
        reactor.run()


def run_process():

    c = RunSpiderProcess()
    c.run([], None)


def run_runner():

    c = RunSpiderRunner()
    c.run([], None)


if __name__ == '__main__':
    # run_process()
    run_runner()

```

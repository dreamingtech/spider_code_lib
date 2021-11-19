## 用于 scrapy 单机节点的 内存型布隆过滤器 和 用于所有节点的 redis 型布隆过滤器

- scrapy 的去重模式, 不是对 url 进行去重, 而是对 url 生成的请求对象进行去重, 这无疑会增大内存的占用
- 使用内存型布隆过滤器 在生成 请求对象之前对 url 进行去重, 如果 url 重复, 就不生成 请求对象, 方便快捷.

- 内存型布隆过滤器: 
  - 在每个节点中使用 基于内存的布隆过滤器, 对本节点的 url 进行过滤
  - 为什么进行此过滤, 对多个新闻站点进行爬取, 新闻 url 的生成是反复调用固定的 api, 通常几分钟到一个小时就要调用一次 api.
  - 很可能会存在大量重复的详情页 url, 在单机节点中使用内存型布隆过滤器进行第一步过滤, 能大大降低 redis 布隆过滤器的压力
- redis型布隆过滤器: 
  - 在 redis 中使用基于 redis 的布隆过滤器, 对所有节点的 url 进行过滤.
- 自动增加过滤器
  - 在一个过滤器中保存的种子数量达到上限时, 能够自动增加一个过滤器
  - 内存型中, 使用 bitarray, 自动增加一个内存块, 实例化 bitarray, 新的数据保存到新的 bitarray 中
  - redis 型, 自动增加一个 redis_key, 新的数据保存到新的 redis_key 中
  - 在判断时, 对所有的过滤器进行判断

## 内存型布隆过滤器 memory based bloom filter

### 综述

- 一般的思路是给定 数据量 和 误判率, 计算所需的 hash 函数数量和 使用的 bit 位的长度
- 但实际中, 1. 实例化 bitarray/bitmap 时, 必须要指定所分配的内存量,
- 2. 向 bitarray/bitmap 中添加数据或判断数据是否存在时, 必须要指定多个 hash 函数
- 所以, 这里思路是从给定的 内存大小 和 hash 函数的数量入手, 计算误判率,
- 保证给出的内存和 hash 函数数量得到的误判率小于指定的的阈值,
- 如果计算得到的 误判率大于指定的误判率的阈值, 就报错, 提醒增加内存或增加 hash 函数数量

### General Intro

- generally, for a bloom filter, capacity and error_rate is given,
- hash_func_num (seeds num) and bit size (memory used) are to be calculated
- however, 1. in order use memory based bloom filter, a bitarray/bitmap must be initialized first. thus, the memory used must be assigned first.
- 2. in order to 'add' data to bitarray or check if a certain data 'exists' in bitarray one or more hash func(s) must be given.
- so in this code, pass memory used, hash_func_num, data_size when init BloomFilter, calculate error_rate,
- if calculated error_rate is smaller than error_rate_threshold, continue.
- otherwise, raise an error to remind user to increase memory_size or increase hash_func_num

## todo list

- [ ] redis 版布隆过滤器增加 redis_lock
- [ ] 英文注释和说明
- [ ] 添加日志 logging
- [ ] 添加标题布隆过滤器, 对标题使用布隆过滤器
- [ ] 对新闻正文内容使用 simhash 去重


### 标题去重 和 新闻内容去重

- 如果标题去除掉 非中文, 非英文和非数字 之后, 长度大于特定值, 比如说 10 个字符, 就对标题单独进行去重
- 如果标题小于 10 个字符, 就不使用标题去重, 而是对新闻内容进行 simhash 去重

## 参考

- https://hur.st/bloomfilter/
- https://www.jianshu.com/p/214e96e2a781
- https://www.linuxzen.com/understanding-bloom-filter.html
- https://hackernoon.com/probabilistic-data-structures-bloom-filter-5374112a7832
- http://pages.cs.wisc.edu/~cao/papers/summary-cache/node8.html
- https://www.jasondavies.com/bloomfilter/
- https://github.com/jaybaird/python-bloomfilter
- https://github.com/Sssmeb/BloomFilter

## install bitarray error

```
C:\Users\David>workon scrapy
(scrapy) C:\Users\David>pip install bitarray
Looking in indexes: https://pypi.douban.com/simple
Collecting bitarray
  Downloading https://pypi.doubanio.com/packages/ac/b1/4e36d785d478bb7b5d02028a88e8627a10e810793d660b2b7aedd1cd146e/bitarray-2.3.4.tar.gz (88 kB)
     |████████████████████████████████| 88 kB 368 kB/s
  Preparing metadata (setup.py) ... done
Building wheels for collected packages: bitarray
  Building wheel for bitarray (setup.py) ... error
  ERROR: Command errored out with exit status 1:
   command: 'C:\Users\David\Envs\scrapy\Scripts\python.exe' -u -c 'import io, os, sys, setuptools, tokenize; sys.argv[0] = '"'"'C:\\Users\\David\\AppData\\Local\\Temp\\pip-install-p4hn2hwz\\bitarray_ce5cb7bef9414d56988e51996b61cd5b\\setup.py'"'"'; __file__='"'"'C:\\Users\\David\\AppData\\Local\\Temp\\pip-install-p4hn2hwz\\bitarray_ce5cb7bef9414d56988e51996b61cd5b\\setup.py'"'"';f = getattr(tokenize, '"'"'open'"'"', open)(__file__) if os.path.exists(__file__) else io.StringIO('"'"'from setuptools import setup; setup()'"'"');code = f.read().replace('"'"'\r\n'"'"', '"'"'\n'"'"');f.close();exec(compile(code, __file__, '"'"'exec'"'"'))' bdist_wheel -d 'C:\Users\David\AppData\Local\Temp\pip-wheel-oupsbvxl'
       cwd: C:\Users\David\AppData\Local\Temp\pip-install-p4hn2hwz\bitarray_ce5cb7bef9414d56988e51996b61cd5b\
  Complete output (19 lines):
  running bdist_wheel
  running build
  running build_py
  creating build
  creating build\lib.win-amd64-3.8
  creating build\lib.win-amd64-3.8\bitarray
  copying bitarray\test_bitarray.py -> build\lib.win-amd64-3.8\bitarray
  copying bitarray\test_util.py -> build\lib.win-amd64-3.8\bitarray
  copying bitarray\util.py -> build\lib.win-amd64-3.8\bitarray
  copying bitarray\__init__.py -> build\lib.win-amd64-3.8\bitarray
  copying bitarray\bitarray.h -> build\lib.win-amd64-3.8\bitarray
  copying bitarray\pythoncapi_compat.h -> build\lib.win-amd64-3.8\bitarray
  copying bitarray\test_data.pickle -> build\lib.win-amd64-3.8\bitarray
  copying bitarray\py.typed -> build\lib.win-amd64-3.8\bitarray
  copying bitarray\util.pyi -> build\lib.win-amd64-3.8\bitarray
  copying bitarray\__init__.pyi -> build\lib.win-amd64-3.8\bitarray
  running build_ext
  building 'bitarray._bitarray' extension
  error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/
  ----------------------------------------
  ERROR: Failed building wheel for bitarray
  Running setup.py clean for bitarray
Failed to build bitarray
Installing collected packages: bitarray
    Running setup.py install for bitarray ... error
    ERROR: Command errored out with exit status 1:
     command: 'C:\Users\David\Envs\scrapy\Scripts\python.exe' -u -c 'import io, os, sys, setuptools, tokenize; sys.argv[0] = '"'"'C:\\Users\\David\\AppData\\Local\\Temp\\pip-install-p4hn2hwz\\bitarray_ce5cb7bef9414d56988e51996b61cd5b\\setup.py'"'"'; __file__='"'"'C:\\Users\\David\\AppData\\Local\\Temp\\pip-install-p4hn2hwz\\bitarray_ce5cb7bef9414d56988e51996b61cd5b\\setup.py'"'"';f = getattr(tokenize, '"'"'open'"'"', open)(__file__) if os.path.exists(__file__) else io.StringIO('"'"'from setuptools import setup; setup()'"'"');code = f.read().replace('"'"'\r\n'"'"', '"'"'\n'"'"');f.close();exec(compile(code, __file__, '"'"'exec'"'"'))' install --record 'C:\Users\David\AppData\Local\Temp\pip-record-emwuvpb0\install-record.txt' --single-version-externally-managed --compile --install-headers 'C:\Users\David\Envs\scrapy\include\site\python3.8\bitarray'
         cwd: C:\Users\David\AppData\Local\Temp\pip-install-p4hn2hwz\bitarray_ce5cb7bef9414d56988e51996b61cd5b\
    Complete output (21 lines):
    running install
    C:\Users\David\Envs\scrapy\lib\site-packages\setuptools\command\install.py:34: SetuptoolsDeprecationWarning: setup.py install is deprecated. Use build and pip and other standards-based tools.
      warnings.warn(
    running build
    running build_py
    creating build
    creating build\lib.win-amd64-3.8
    creating build\lib.win-amd64-3.8\bitarray
    copying bitarray\test_bitarray.py -> build\lib.win-amd64-3.8\bitarray
    copying bitarray\test_util.py -> build\lib.win-amd64-3.8\bitarray
    copying bitarray\util.py -> build\lib.win-amd64-3.8\bitarray
    copying bitarray\__init__.py -> build\lib.win-amd64-3.8\bitarray
    copying bitarray\bitarray.h -> build\lib.win-amd64-3.8\bitarray
    copying bitarray\pythoncapi_compat.h -> build\lib.win-amd64-3.8\bitarray
    copying bitarray\test_data.pickle -> build\lib.win-amd64-3.8\bitarray
    copying bitarray\py.typed -> build\lib.win-amd64-3.8\bitarray
    copying bitarray\util.pyi -> build\lib.win-amd64-3.8\bitarray
    copying bitarray\__init__.pyi -> build\lib.win-amd64-3.8\bitarray
    running build_ext
    building 'bitarray._bitarray' extension
    error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/
    ----------------------------------------
ERROR: Command errored out with exit status 1: 'C:\Users\David\Envs\scrapy\Scripts\python.exe' -u -c 'import io, os, sys, setuptools, tokenize; sys.argv[0] = '"'"'C:\\Users\\David\\AppData\\Local\\Temp\\pip-install-p4hn2hwz\\bitarray_ce5cb7bef9414d56988e51996b61cd5b\\setup.py'"'"'; __file__='"'"'C:\\Users\\David\\AppData\\Local\\Temp\\pip-install-p4hn2hwz\\bitarray_ce5cb7bef9414d56988e51996b61cd5b\\setup.py'"'"';f = getattr(tokenize, '"'"'open'"'"', open)(__file__) if os.path.exists(__file__) else io.StringIO('"'"'from setuptools import setup; setup()'"'"');code = f.read().replace('"'"'\r\n'"'"', '"'"'\n'"'"');f.close();exec(compile(code, __file__, '"'"'exec'"'"'))' install --record 'C:\Users\David\AppData\Local\Temp\pip-record-emwuvpb0\install-record.txt' --single-version-externally-managed --compile --install-headers 'C:\Users\David\Envs\scrapy\include\site\python3.8\bitarray' Check the logs for full command output.

```

- 解决方法, 安装 visual studio build tools

- 2019 版(无用?)
  - 下载并安装 https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16
  - https://docs.microsoft.com/en-us/answers/questions/136985/build-tools-for-visual-studio.html

- 2015 版
  - Microsoft Visual C++ 14 is the compiler that was distributed with VS2015. The build tools for VS2015 can be downloaded from older-downloads. Expand the Other Tools, Frameworks and Redistributables to see the download link for the Build Tools.
  - https://visualstudio.microsoft.com/vs/older-downloads/#microsoft-build-tools-2015-update-3
  - https://download.microsoft.com/download/5/F/7/5F7ACAEB-8363-451F-9425-68A90F98B238/visualcppbuildtools_full.exe


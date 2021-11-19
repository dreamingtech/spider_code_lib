### TimedRotatingFileHandler 改写

#### 使用方法

- 把 ctrf_handler.py 放到 python 安装目录下的 logging 目录下.
  - 如: C:\Program Files (x86)\Python36\Lib\logging

- 导入模块

```py
from logging.ctrf_handler import CTRFHandler
```

- 使用
  - CTRFHandler 与 TimedRotatingFileHandler 的使用方法完全相同


#### TimedRotatingFileHandler 实现的原理

- TimedRotatingFileHandler 的继承关系
  - TimedRotatingFileHandler > BaseRotatingHandler > logging.FileHandler > StreamHandler

- FileHandler 的实现原理
  - `_open` 方法打开一个文件名为 filename 的日志, 
  - 调用 `StreamHandler.__init__(self, self._open())`, 把打开的日志文件的 fp 传递给 StreamHandler 进行实例化
  - 重写 emit 方法, 在其中调用 StreamHandler.emit 来向日志中写入日志

- BaseRotatingHandler 的实现原理
  - 传入 filename, 调用 `logging.FileHandler.__init__(self, filename, mode, encoding, delay)` 进行实例化
  - 重写 emit 方法, 在每次写入日志时都通过 self.shouldRollover 来计算是否需要进行日志文件的切换
    - 如果需要进行日志的切换, 调用 self.doRollover 方法实现日志文件的切换
    - 在 emit 方法中通过 logging.FileHandler.emit 实现日志的写入
    - self.shouldRollover 和 self.doRollover 都需要由子类来具体实现

- TimedRotatingFileHandler 的实现原理
  - 实例化过程
    - 传入 filename, 调用 `BaseRotatingHandler.__init__(self, filename, 'a', encoding, delay)` 方法完成实例化
      - 实际上还是打开 filename 的日志文件, 把 fp 传递给 StreamHandler 完成实例化
    - 根据设定的切换时间 when 计算日志文件的后缀
    - 根据设定的切换时间 when 和 间隔的次数 interval 来计算两次日志文件之间进行切换的时间间隔 self.interval
    - 判断 filename 指向的日志文件是否存在, 如果存在, 计算出日志文件的修改时间 t, 以此时间来通过 self.computeRollover   计算下一次日志文件的切换时间
      - 如果不存在, 则以当前的 linux 时间戳为 t 来计算下一次日志文件的切换时间 self.rolloverAt
  - 日志写入过程
    - 未重写 emit 方法, 则调用 BaseRotatingHandler 的 emit 方法写入日志
    - 每次写入日志之前都调用 TimedRotatingFileHandler.shouldRollover 来判断当前的时间是否达到了日志的切换时间 self.rolloverAt
      - 如果当前的时间到达了日志文件的切换时间 self.rolloverAt, 就调用 TimedRotatingFileHandler.doRollover 来实现日志文件的切换

  - TimedRotatingFileHandler.doRollover 日志切换的过程
    - 关闭 self.stream 并重设 self.stream=None, 相当于关闭原来的 日志文件
    - 调用 BaseRotatingHandler.rotation_filename 计算要把日志文件重名称为 的文件名 dfn (destiny file name)
    - 如果 dfn 已经存在, 就删除 dfn 文件
    - 调用 self.rotate 实现日志文件的切换. 
      - 如果没有重写 rotate 方法, 就调用 BaseRotatingHandler.rotate 来实现日志的切换
      - 即把原日志文件重命名为 dfn
    - 如果设置了最大的日志文件备份数量 backupCount, 就调用 self.getFilesToDelete() 来计算要删除的日志文件并删除
    - 再次调用 `self._open()` 方法来打开默认的日志文件, 并赋值给 self.stream, 新的日志依旧写入到 默认的日志文件中
    - 根据当前的时间计算下一次日志文件切换的时间

  - 简要过程

    - 实例化一个 filename 的 FileHandler, 日志写入到这个 filename 的文件中, 
    - 每次实例化时计算下一次的日志文件的切换时间
    - 在到达切换时间时, 对 filename 重命名, 如重命名为 filename.log.2019-10-25-13-04-24
    - 在每次重命名时再次计算切换时间, 
    - 在日志文件重命名之后, 日志依旧写入到 filename 中, 并在下一次到达切换时间时再次对文件进行重命名. 
    - 如此, 就达到了定时切换日志文件的目的.


#### TimedRotatingFileHandler 存在的问题

- 如果命名为的日志存在, 就会进行覆盖, 
- 正在写入的日志不是以最初写入日志的时间进行命名的
- 正在写入的日志文件名与已经重命名的日志文件名不匹配
- 后两点可能给后继的日志分析造成一定的麻烦


#### 改写 TimedRotatingFileHandler 要达到的目的

- 所有正在写入的日志文件以当前的时间为后缀进行创建,
- 如果文件存在, 就写入日志到文件末尾
- 在日志文件切换时, 同样创建以切换时间为后缀的日志文件


#### 实现的方法
  - 修改的最核心内容: 实例化一个名称的 filename, 但写入到的是 另一个名称的 file
  - 实例化 FileHandler 时, FileHandler 中是以 `_open` 方法打开一个文件, 把文件的 fp 传递给 SteamHandler 进行实例化, 由 SteamHandler 的 emit 方法向文件中写入数据的.
  - 只需要修改 `_open` 方法 和 emit 方法, 就能实现向以当前时间为后缀的日志文件中写入日志的目的


#### todo
-[ ] 如果日志文件已经存在, 以日志文件的修改时间来计算切换时间
-[ ] 支持其它 python 版本


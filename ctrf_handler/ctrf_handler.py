# -*- coding: UTF-8 -*-
# 改写的 TimedRotatingFileHandler > CurrentTimedRotatingFileHandler
# 基于当前时间的时间轮转日志文件处理器
import logging
import os
import time
import re

from stat import ST_DEV, ST_INO, ST_MTIME, ST_CTIME


_MIDNIGHT = 24 * 60 * 60  # number of seconds in a day


class CTRFHandler(logging.FileHandler):
    """
    Base class for handlers that rotate log files at a certain point.
    Not meant to be instantiated directly.  Instead, use RotatingFileHandler
    or TimedRotatingFileHandler.
    """
    def __init__(self, filename_base, mode='a', when='h', interval=1, backupCount=0,
                 encoding=None, delay=False, utc=False, atTime=None):
        """
        Use the specified filename for streamed logging
        """

        self.mode = mode
        self.encoding = encoding

        self.when = when.upper()
        self.backupCount = backupCount
        self.utc = utc
        self.atTime = atTime
        # Calculate the real rollover interval, which is just the number of
        # seconds between rollovers.  Also set the filename suffix used when
        # a rollover occurs.  Current 'when' events supported:
        # S - Seconds
        # M - Minutes
        # H - Hours
        # D - Days
        # midnight - roll over at midnight
        # W{0-6} - roll over on a certain day; 0 - Monday
        #
        # Case of the 'when' specifier is not important; lower or upper case
        # will work.
        if self.when == 'S':
            self.interval = 1  # one second
            self.suffix = "%Y%m%d_%H%M%S"
            # self.extMatch = self.suffix.replace("%Y", "\d{4}")
            # self.extMatch = re.sub("%.{1}", "\d{2}", self.extMatch)
            # self.extMatch = self.extMatch + "(\.\w+)?$"
            # self.extMatch = r"^\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}(\.\w+)?$"
        elif self.when == 'M':
            self.interval = 60  # one minute
            self.suffix = "%Y%m%d_%H%M"
            # self.extMatch = r"^\d{4}_\d{2}_\d{2}_\d{2}_\d{2}(\.\w+)?$"
        elif self.when == 'H':
            self.interval = 60 * 60  # one hour
            self.suffix = "%Y%m%d_%H"
            # self.extMatch = r"^\d{4}_\d{2}_\d{2}_\d{2}(\.\w+)?$"
        elif self.when == 'D' or self.when == 'MIDNIGHT':
            self.interval = 60 * 60 * 24  # one day
            self.suffix = "%Y%m%d"
            # self.extMatch = r"^\d{4}_\d{2}_\d{2}(\.\w+)?$"
        elif self.when.startswith('W'):
            self.interval = 60 * 60 * 24 * 7  # one week
            if len(self.when) != 2:
                raise ValueError("You must specify a day for weekly rollover from 0 to 6 (0 is Monday): %s" % self.when)
            if self.when[1] < '0' or self.when[1] > '6':
                raise ValueError("Invalid day specified for weekly rollover: %s" % self.when)
            self.dayOfWeek = int(self.when[1])
            self.suffix = "%Y%m%d"
            # self.extMatch = r"^\d{4}_\d{2}_\d{2}(\.\w+)?$"
        else:
            raise ValueError("Invalid rollover interval specified: %s" % self.when)

        # 根据 self.suffix 来计算 self.extMatch
        # self.extMatch = re.compile(self.extMatch, re.ASCII)
        # self.suffix = "%Y_%m_%d_%H_%M_%S"
        # self.extMatch = r"^\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}(\.\w+)?$"
        self.extMatch = self.suffix.replace("%Y", "\d{4}")
        self.extMatch = re.sub("%[mdHMS]", "\d{2}", self.extMatch)
        self.extMatch = self.extMatch + "(\.\w+)?$"

        self.interval = self.interval * interval  # multiply by units requested

        # 定义的日志文件的 "前缀",
        self.filename_base = filename_base
        # 根据当前的时间, self.filename_base 和 self.extMatch 获取日志文件名 filename
        # eg: filename_base = "goods_crawler.log"
        # filename = "goods_crawler_20191028_082527.log"
        filename = self._get_file_name()

        # 必须要把 计算 t 的操作放在 logging.FileHandler.__init__() 之前, 否则,
        # 通过 logging.FileHandler.__init__() 实例化 filename 之后, 文件一定是存在的
        # 判断 base_filename 日志文件 是否存在, 如果存在, 就获取文件的创建时间
        # 以此时间来计算日志文件的切换时间
        # 如果文件不存在, 就以当前的 linux 时间戳来计算日志文件的切换时间
        if os.path.exists(filename):
            # print("file: {} exists, use created time to calculate file rollover time".format(filename))
            # todo 以文件的修改时间来计算下一次的切换时间, 修改时间计算切换时间时, 可能会写入 "过多" 的日志. ???
            # 如定义 每天的 23:00:00 切换, 如果创建时间是 22:30:00, 修改时间是 23:20:00,
            # t = os.stat(filename)[ST_MTIME]
            # 以文件的创建时间来计算下一次的切换日期
            t = os.stat(filename)[ST_CTIME]
            # print("file: {} created time: {}".format(filename, time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(t))))
        else:
            # print("use time.time to calculate file rollover time")
            t = int(time.time())

        # 调用 FileHandler 完成实例化, 此时传入的是 filename, 日志就写入到以当前的时间为后缀的文件中
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)

        # 把 self.baseFilename 重置为 filename_base, 在 FileHandler 中,
        # self.baseFilename = os.path.abspath(filename)
        # FileHandler 实例化时传入的是 filename, 实例化的就是此 filename 的 FileHandler
        # 在这里把 self.baseFilename 修改为 filename_base, self 就会变为 filename_base 的 FileHandler
        # 这一步只是为了 debug 时看着舒服.
        self.baseFilename = os.path.abspath(filename_base)

        self.rolloverAt = self.computeRollover(t)

    def emit(self, record):
        """
        Emit a record.

        Output the record to the file, catering for rollover as described
        in doRollover().
        """
        # print("------emit------", self)
        try:
            if self.shouldRollover(record):
                self.doRollover()
            logging.FileHandler.emit(self, record)
        except Exception:
            self.handleError(record)

    def shouldRollover(self, record):
        """
        Determine if rollover should occur.

        record is not used, as we are just comparing times, but it is needed so
        the method signatures are the same
        """
        t = int(time.time())
        # print("shouldRollover-currentTime", time.strftime(self.suffix, time.localtime(t)))
        # print("shouldRollover-rolloverAt", time.strftime(self.suffix, time.localtime(self.rolloverAt)))
        if t >= self.rolloverAt:
            return 1
        return 0

    def computeRollover(self, currentTime):
        """
        Work out the rollover time based on the specified time.
        """
        result = currentTime + self.interval
        # If we are rolling over at midnight or weekly, then the interval is already known.
        # What we need to figure out is WHEN the next interval is.  In other words,
        # if you are rolling over at midnight, then your base interval is 1 day,
        # but you want to start that one day clock at midnight, not now.  So, we
        # have to fudge the rolloverAt value in order to trigger the first rollover
        # at the right time.  After that, the regular interval will take care of
        # the rest.  Note that this code doesn't care about leap seconds. :)
        if self.when == 'MIDNIGHT' or self.when.startswith('W'):
            # This could be done with less code, but I wanted it to be clear
            if self.utc:
                t = time.gmtime(currentTime)
            else:
                t = time.localtime(currentTime)

            currentHour = t[3]
            currentMinute = t[4]
            currentSecond = t[5]
            currentDay = t[6]
            # r is the number of seconds left between now and the next rotation
            if self.atTime is None:
                rotate_ts = _MIDNIGHT
            else:
                # 如果设置了 atTime, 就在原来的基础上加上对应的 秒数
                rotate_ts = ((self.atTime.hour * 60 + self.atTime.minute)*60 + self.atTime.second)

            r = rotate_ts - ((currentHour * 60 + currentMinute) * 60 + currentSecond)
            if r < 0:
                # 如果计算得到的 文件切换时间 小于当前的时间, 则切换时间为明天, 就在原来 r 的基础上加上 24*
                # Rotate time is before the current time (for example when
                # self.rotateAt is 13:45 and it now 14:15), rotation is tomorrow.
                r += _MIDNIGHT
                currentDay = (currentDay + 1) % 7
            result = currentTime + r
            # If we are rolling over on a certain day, add in the number of days until
            # the next rollover, but offset by 1 since we just calculated the time
            # until the next day starts.  There are three cases:
            # Case 1) The day to rollover is today; in this case, do nothing
            # Case 2) The day to rollover is further in the interval (i.e., today is
            #         day 2 (Wednesday) and rollover is on day 6 (Sunday).  Days to
            #         next rollover is simply 6 - 2 - 1, or 3.
            # Case 3) The day to rollover is behind us in the interval (i.e., today
            #         is day 5 (Saturday) and rollover is on day 3 (Thursday).
            #         Days to rollover is 6 - 5 + 3, or 4.  In this case, it's the
            #         number of days left in the current week (1) plus the number
            #         of days in the next week until the rollover day (3).
            # The calculations described in 2) and 3) above need to have a day added.
            # This is because the above time calculation takes us to midnight on this
            # day, i.e. the start of the next day.
            if self.when.startswith('W'):
                day = currentDay  # 0 is Monday
                if day != self.dayOfWeek:
                    if day < self.dayOfWeek:
                        daysToWait = self.dayOfWeek - day
                    else:
                        daysToWait = 6 - day + self.dayOfWeek + 1
                    newRolloverAt = result + (daysToWait * (60 * 60 * 24))
                    if not self.utc:
                        dstNow = t[-1]
                        dstAtRollover = time.localtime(newRolloverAt)[-1]
                        if dstNow != dstAtRollover:
                            if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                                addend = -3600
                            else:           # DST bows out before next rollover, so we need to add an hour
                                addend = 3600
                            newRolloverAt += addend
                    result = newRolloverAt
        return result

    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        # 关闭 self.stream,
        # self.stream 是在 StreamHandler 中实例化的
        # if stream is None:
        #     stream = sys.stderr
        # self.stream = stream
        if self.stream:
            self.stream.close()
            self.stream = None

        # get the time that this sequence started at and make it a TimeTuple
        # 第二次再次计算切换时间时, 就要以当前时间为准来计算了
        currentTime = int(time.time())

        # 是否是夏令时, 1(夏令时)、0(不是夏令时)、-1(未知)，默认 -1
        dstNow = time.localtime(currentTime)[-1]

        # 执行日志切换的时间 - 两次执行 roll 的时间间隔 = "上一次" 应该执行 roll 的时间
        # 以此时间来计算重命名时日志文件的结尾符
        # 如果原有的日志文件已经存在, self.rolloverAt = 文件修改时间 + self.interval, t 相当于文件修改时间 ??
        # 因为现在是以当前的时间为后缀来生成日志文件了, 就不再需要计算 timeTuple, 进而计算 dfn 了
        # t = self.rolloverAt - self.interval
        # if self.utc:
        #     timeTuple = time.gmtime(t)
        # else:
        #     timeTuple = time.localtime(t)
        #     print("timeTuple: ".format(time.strftime(self.suffix, timeTuple)))
        #     dstThen = timeTuple[-1]
        #     # 如果一个实行夏令时, 一个不实行夏令时
        #     if dstNow != dstThen:
        #         if dstNow:
        #             addend = 3600
        #         else:
        #             addend = -3600
        #         timeTuple = time.localtime(t + addend)

        # 因为现在是以当前的时间为后缀来生成日志文件了, 就不再需要此 dfn
        # dfn = self.rotation_filename(self.baseFilename + "." + time.strftime(self.suffix, timeTuple))

        # 如果要把 self.baseFilename 重命名为的 文件已经存在, 就先把它删除
        # if os.path.exists(dfn):
        #     os.remove(dfn)

        # 执行 文件切换的操作, 也就是把 现在有文件重命名为 上一次应该保存的日志的文件名
        # 因为要写入的日志是直接使用当前的时间为后缀, 所以不再需要进行重命名的操作
        # self.rotate(self.baseFilename, dfn)  # 重命令文件

        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        if not self.delay:
            self.stream = self._open()

        # 根据 "当前的" 时间 计算新的日志文件切换时间
        newRolloverAt = self.computeRollover(currentTime)
        # 如果新的日志文件切换时间 newRolloverAt 小于等于 当前的时间 currentTime,
        # 就在 newRolloverAt 上加 self.interval, 直到 newRolloverAt 大于 currentTime
        # 最初的 self.rolloverAt 的计算, 如果文件存在,
        # 就根据文件的修改时间来计算, 计算得到的时间有可能会小于当前的时间
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval

        #If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt

    def _open(self):
        """
        重写 FileHandler 中的 _open 文件, 实现写入到不同文件的目的
        """
        # 每次 _open 的文件都是以当前的时间戳为后缀的文件, 这样, 就实现了每次切换都写入到新文件中的目的
        filename = self._get_file_name(time.localtime())
        return open(filename, self.mode, encoding=self.encoding)

    def _get_file_name(self, local_time=time.localtime()):
        """
        根据当前的时间获取日志文件名
        base_file_name = "goods_crawler.log" > "goods_crawler_crawler_u_20191020.log"
        :param local_time:
        :return:
        """
        date_str = time.strftime(self.suffix, local_time)
        # todo 解决带路径的 filename 的问题
        if '/' in self.filename_base:
            path_name = self.filename_base.rsplit('/')[0]

        # 对 self.filename_base 进行拆分
        if '.' in self.filename_base:

            base_file_name_prefix = self.filename_base.rsplit('.')[0]
            base_file_name_suffix = self.filename_base.rsplit('.')[-1]
            filename = "{}_{}.{}".format(base_file_name_prefix, date_str, base_file_name_suffix)
        else:
            path_name = self.filename_base.rsplit('/')[0]
            filename = "{}_{}.log".format(self.filename_base, date_str)
        # print("_get_file_name", filename)

        return filename

    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.

        More specific than the earlier method, which just used glob.glob().
        """
        # self.baseFilename is goods_crawler.log
        # dirName, baseName = os.path.split(self.baseFilename)
        # 获取当前写入日志的文件名
        current_file_path = os.path.abspath(self._get_file_name())
        dirName, baseName = os.path.split(current_file_path)
        fileNames = os.listdir(dirName)
        result = []
        # 获取要删除的日志文件名的前缀
        if '.' in self.filename_base:
            base_file_name_prefix = self.filename_base.rsplit('.')[0]
            prefix = "{}_".format(base_file_name_prefix)
        else:
            prefix = "{}_".format(self.filename_base)
        # prefix = baseName + "."
        plen = len(prefix)
        for fileName in fileNames:
            if fileName[:plen] == prefix:
                suffix = fileName[plen:]
                # if self.extMatch.match(suffix):
                # 使用 re 匹配, 因为使用的是 r"{}{}".format(prefix, self.extMatch),
                # 所以不会匹配到已经存在的其它命名的文件.
                if re.match(r"{}{}".format(prefix, self.extMatch), fileName, re.ASCII):
                    result.append(os.path.join(dirName, fileName))
        if len(result) < self.backupCount:
            result = []
        else:
            result.sort()
            result = result[:len(result) - self.backupCount]
        return result


if __name__ == '__main__':

    def get_logger(base_file_name):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # 定义时间轮转文件处理器trf_handler并进行设置
        # logging.FileHandler(filename, mode='a', encoding=None, delay=False)
        # 这里使用不加扩展名的 log 文件名

        # base_file_name = "goods_crawler.log"

        trf_handler = CTRFHandler(filename_base=base_file_name,
                                  mode='a',
                                  # 每 10s 切换一个日志文件
                                  when='S',
                                  interval=10,
                                  # 每 1M 切换一个日志文件
                                  # when='M',
                                  # interval=1,
                                  # when='midnight',
                                  # interval=1,
                                  backupCount=4,
                                  # atTime=datetime.time(0, 0, 0, 0),
                                  )

        trf_handler.setLevel(logging.DEBUG)
        # 两种方式设置输出格式, 第一种, 通过handler的setFormatter方法设置
        trf_handler_formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)-8s - %(filename)s[:%(lineno)d] - %(message)s",
            datefmt="%Y/%m/%d %H:%M:%S",
        )
        trf_handler.setFormatter(trf_handler_formatter)

        # filename = '{}_{}.log'.format(os.path.splitext(__file__)[0], time.strftime("%Y%m%d", time.localtime()))
        # # 定义文件处理器f_handler并进行设置
        # f_handler = logging.FileHandler(filename, encoding='utf-8')
        # f_handler.setLevel(logging.INFO)
        # f_handler_formatter = logging.Formatter(
        #     fmt="%(asctime)s - %(levelname)-8s - %(filename)s[:%(lineno)d] - %(message)s",
        #     datefmt="%Y-%m-%d %H:%M:%S",
        # )
        # f_handler.setFormatter(f_handler_formatter)

        # 定义stream handler, stream=None等价于stream=sys.stderr, 等价于不写参数
        s_handler = logging.StreamHandler(stream=None)
        s_handler.setLevel(logging.DEBUG)
        s_handler_formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)-8s - %(filename)s[:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        s_handler.setFormatter(s_handler_formatter)

        # 如果是在 linux 上运行, 只添加 file handler
        logger.addHandler(trf_handler)
        logger.addHandler(s_handler)

        return logger

    base_file_name = "goods_crawler.log"
    test_logger = get_logger(base_file_name)

    i = 0
    while True:
        test_logger.info(i)
        i += 1
        time.sleep(1)


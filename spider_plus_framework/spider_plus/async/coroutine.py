from gevent.pool import Pool as BasePool
from gevent.monkey import patch_all
patch_all()    # 打补丁，替换内置的模块


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
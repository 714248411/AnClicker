"""Shared time formatting and small compatibility utilities."""
import datetime
import time

def timer(func):
    def func_wrapper(*args, **kwargs):
        time_start = time.time()
        result = func(*args, **kwargs)
        time_end = time.time()
        time_spend = time_end - time_start
        print("%s cost time: %.3f s" % (func.__name__, time_spend))
        return result

    return func_wrapper


def get_str_now_time():
    """获取当前时间"""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

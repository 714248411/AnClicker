"""Console timings for local release stages, with no credentials or URLs."""
import time
from contextlib import contextmanager


@contextmanager
def stage(name):
    started = time.perf_counter()
    print(f'[阶段开始] {name}', flush=True)
    try:
        yield
    except BaseException:
        print(f'[阶段失败] {name}: {time.perf_counter() - started:.1f} 秒', flush=True)
        raise
    else:
        print(f'[阶段完成] {name}: {time.perf_counter() - started:.1f} 秒', flush=True)


def run_stage(name, action, *args, **kwargs):
    with stage(name):
        return action(*args, **kwargs)

"""Cancelable cross-process locking for a shared local model runtime."""
import os
import time
from contextlib import contextmanager

@contextmanager
def service_lock(root, context=None, blocking=True):
    root.mkdir(parents=True,exist_ok=True)
    stream=(root/'service.lock').open('a+b')
    acquired=False
    try:
        stream.seek(0,2)
        if stream.tell()==0:stream.write(b'0');stream.flush()
        while True:
            if context is not None and context.stop_requested:raise InterruptedError('已停止等待模型')
            stream.seek(0)
            try:
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                acquired=True;break
            except (BlockingIOError,PermissionError,OSError) as error:
                if getattr(error,'errno',None) not in (11,13,36):raise
                if not blocking:break
                time.sleep(.1)
        yield acquired
    finally:
        if acquired:
            stream.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(),fcntl.LOCK_UN)
        stream.close()

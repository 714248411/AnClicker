# -*- coding: utf-8 -*-
"""
engine.py —— 微信 OCR（提取版）同步引擎
========================================
对外只暴露一件事：喂一张 BGR 图，拿回 [(文本, 置信度, [x0,y0,x1,y1]), ...]，
坐标语义与 RapidOCR 完全一致（输入图的像素坐标系），因此可以无痛替换
find_monster.MonsterFinder 里的 OCR 后端。

设计要点：
  1. 零第三方依赖：只用标准库 ctypes + 项目自带的 wxocr 提取版运行时。
  2. 请求/响应：mmmojo 管道传 protobuf；编码解码在 pb_lite 里手写，
     绕开 protobuf 版本地狱，也省掉 JSON 往返。
  3. 同步封装：官方接口是异步回调，这里用 task_id + threading.Event
     把回调转成阻塞调用，调用方写起来跟 RapidOCR 一样。
  4. 临时图回收：OCR 只吃文件路径，用递增编号的临时 png，回调到齐即删。
"""

import os
import shutil
import tempfile
import threading
import time

import cv2
import numpy as np

from . import pb_lite
from .mmmojo import (
    MMMojoEnvironment,
    MMMojoEnvironmentCallbackType,
    MMMojoInfoMethod,
    as_ptr,
)

# 进程内只允许一个引擎实例：mmmojo 的 DLL 全局状态 + 回调里要找回宿主对象
_ACTIVE_ENGINE = None
_ACTIVE_LOCK = threading.Lock()

# 首帧等待连接的上限（毫秒级轮询）
CONNECT_WAIT = 15.0


class WeChatOCREngine:
    """微信 OCR 提取版引擎。

    参数
    ----
    runtime_dir : 含 WeChatOCR.exe / mmmojo_64.dll / Model 的目录；
                  默认自动定位（开发环境和 PyInstaller 打包后都能找到）。
    timeout     : 单张图识别的等待上限（秒）。
    verbose     : 打印调试信息。
    """

    def __init__(self, runtime_dir=None, timeout=20.0, verbose=False):
        self.runtime_dir = os.path.abspath(runtime_dir) if runtime_dir else find_runtime_dir()
        self.timeout = float(timeout)
        self.verbose = bool(verbose)

        self._env = None
        self._connected = False
        self._lock = threading.Lock()
        self._pending = {}            # task_id -> [Event, result_list]
        self._seq = 0
        self._tmpdir = None
        self._last_error = None
        self._started = False

    # ================= 生命周期 =================
    @property
    def started(self):
        return self._started

    @property
    def connected(self):
        return self._connected

    @property
    def last_error(self):
        return self._last_error

    def start(self, wait=CONNECT_WAIT):
        """拉起 WeChatOCR.exe 并等待管道连通。成功返回 True。"""
        if self._started:
            return True
        exe = os.path.join(self.runtime_dir, "WeChatOCR.exe")
        if not os.path.isfile(exe):
            self._last_error = f"缺少 WeChatOCR.exe：{exe}"
            return False

        dll_name = "mmmojo_64.dll" if _is_64bit() else "mmmojo.dll"
        dll_path = os.path.join(self.runtime_dir, dll_name)
        if not os.path.isfile(dll_path):
            self._last_error = f"缺少 {dll_name}：{dll_path}"
            return False

        global _ACTIVE_ENGINE
        with _ACTIVE_LOCK:
            _ACTIVE_ENGINE = self

        try:
            self._tmpdir = tempfile.mkdtemp(prefix="wxocr_")
            self._clean_stale_tmp()
            self._env = MMMojoEnvironment(dll_path)
            self._env.start(exe_path=exe, user_lib_dir=self.runtime_dir, host_data=self)
        except Exception as e:                     # DLL 加载 / 拉起失败
            self._last_error = f"启动 mmmojo 失败: {e}"
            self._teardown()
            return False

        deadline = time.time() + max(0.0, float(wait))
        while time.time() < deadline:
            if self._connected:
                self._started = True
                if self.verbose:
                    print(f"[wxocr] 已连通：{exe}")
                return True
            if self._last_error:
                break
            time.sleep(0.05)

        self._last_error = self._last_error or "等待 OCR 服务连接超时"
        self._teardown()
        return False

    def stop(self):
        """关闭子进程，清理临时目录。可重复调用。"""
        global _ACTIVE_ENGINE
        self._started = False
        self._connected = False
        self._teardown()
        with _ACTIVE_LOCK:
            if _ACTIVE_ENGINE is self:
                _ACTIVE_ENGINE = None

    def _teardown(self):
        env, self._env = self._env, None
        if env is not None:
            try:
                env.stop()
            except Exception:
                pass
        if self._tmpdir and os.path.isdir(self._tmpdir):
            shutil.rmtree(self._tmpdir, ignore_errors=True)
        self._tmpdir = None
        # 回调可能还卡在等待
        for item in list(self._pending.values()):
            try:
                item[0].set()
            except Exception:
                pass
        self._pending.clear()

    def _clean_stale_tmp(self):
        """清掉上次异常退出残留的临时图。"""
        if not self._tmpdir or not os.path.isdir(self._tmpdir):
            return
        for fn in os.listdir(self._tmpdir):
            try:
                os.remove(os.path.join(self._tmpdir, fn))
            except OSError:
                pass

    def __del__(self):
        try:
            self.stop()
        except Exception:
            pass

    # ================= mmmojo 回调（在 mojo 线程执行） =================
    def on_remoteconnect(self, is_connected, user_data):
        self._connected = bool(is_connected)

    def on_remotedisconnect(self, user_data):
        self._connected = False

    def on_remoteprocesslaunched(self, user_data):
        if self.verbose:
            print("[wxocr] WeChatOCR 子进程已拉起")

    def on_remoteprocesslaunchfailed(self, error_code, user_data):
        self._last_error = f"WeChatOCR 子进程启动失败，错误码 {error_code}"

    def on_remotemojoerror(self, errorbuf, errorsize, user_data):
        self._last_error = "mmmojo 管道错误"

    def on_readpush(self, request_id, request_info, user_data):
        self._handle_read(request_info)

    def on_readpull(self, request_id, request_info, user_data):
        self._handle_read(request_info)

    def on_readshared(self, request_id, request_info, user_data):
        self._handle_read(request_info)

    def _handle_read(self, request_info):
        """收到一条推送：取数据 → 释放 → 解析 → 唤醒等待方。"""
        env = self._env
        if env is None:
            return
        try:
            data = env.read_request_bytes(request_info)
        except Exception:
            data = b""
        finally:
            try:
                env.remove_read_info(request_info)
            except Exception:
                pass
        if not data:
            return
        try:
            info, lines = pb_lite.decode_ocr_response(data)
        except Exception as e:
            if self.verbose:
                print(f"[wxocr] 解析响应失败: {e}")
            return
        self._deliver(info.get("task_id"), lines)

    def _deliver(self, task_id, lines):
        if task_id is None:
            return
        item = self._pending.get(task_id)
        if item is None:
            return                      # 初始化推送或迟到的响应
        item[1].extend(lines)
        item[0].set()

    # ================= 对外识别接口 =================
    def recognize_file(self, pic_path):
        """识别一张图片文件，返回 [(text, score, [x0,y0,x1,y1]), ...]。"""
        if not self._started and not self.start():
            raise RuntimeError(self._last_error or "微信 OCR 未就绪")
        pic_path = os.path.abspath(pic_path)
        if self.verbose:
            print(f"[wxocr] 等待服务连通… connected={self._connected}")
        with self._lock:
            if not self._wait_connected():
                raise RuntimeError(self._last_error or "微信 OCR 服务未连接")
            task_id = self._next_task_id()
            ev = threading.Event()
            holder = []
            self._pending[task_id] = (ev, holder)
            try:
                payload = pb_lite.encode_ocr_request(task_id, pic_path)
                self._env.send(payload, request_id=task_id,
                               method=MMMojoInfoMethod.kMMPush)
                if not ev.wait(self.timeout):
                    raise TimeoutError(f"OCR 超时（{self.timeout:.0f}s）")
            finally:
                self._pending.pop(task_id, None)
        return _to_items(holder)

    def recognize(self, bgr):
        """识别一张 BGR ndarray（OpenCV 格式）。

        返回 [(text, score, [x0,y0,x1,y1]), ...]，坐标为输入图像的像素坐标。
        """
        if bgr is None or getattr(bgr, "size", 0) == 0:
            return []
        if not self._started and not self.start():
            raise RuntimeError(self._last_error or "微信 OCR 未就绪")
        if self._tmpdir is None:
            self._tmpdir = tempfile.mkdtemp(prefix="wxocr_")
        self._seq += 1
        path = os.path.join(self._tmpdir, f"f{self._seq}.png")
        ok, buf = cv2.imencode(".png", bgr, [int(cv2.IMWRITE_PNG_COMPRESSION), 1])
        if not ok:
            raise RuntimeError("图片编码失败")
        with open(path, "wb") as f:
            f.write(buf.tobytes())
        try:
            return self.recognize_file(path)
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    # ================= 内部工具 =================
    def _next_task_id(self):
        # 协议要求 [2, 0x7fffffff]；1 被初始化流程占用
        self._seq_task = getattr(self, "_seq_task", 1) + 1
        if self._seq_task > 0x00FFFFFF:
            self._seq_task = 2
        return self._seq_task

    def _wait_connected(self):
        deadline = time.time() + CONNECT_WAIT
        while time.time() < deadline:
            if self._connected:
                return True
            if self._env is None:
                return False
            time.sleep(0.03)
        return self._connected


# ============================================================
# 工具函数
# ============================================================
def _is_64bit():
    import struct
    return struct.calcsize("P") == 8


def _as_ptr(request_info):
    """回调里的 request_info 可能是 int 或 c_void_p，统一成 c_void_p。"""
    return as_ptr(request_info)


def _to_items(lines):
    """[(text, score, l, t, r, b)] → [(text, score, [x0,y0,x1,y1])]，顺手丢掉空框。"""
    items = []
    for row in lines:
        text, score = row[0], row[1]
        l, t, r, b = row[2], row[3], row[4], row[5]
        if r <= l or b <= t:
            continue
        if not text.strip():
            continue
        items.append((text, float(score), [float(l), float(t), float(r), float(b)]))
    return items


def candidate_dirs():
    """按优先级列出可能存放 wxocr 运行时的目录。"""
    dirs = []
    # 1) 环境变量覆盖
    env = os.environ.get("WXOCR_DIR")
    if env:
        dirs.append(env)
    import sys
    # 2) PyInstaller onefile 解包目录
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        dirs.append(os.path.join(meipass, "wxocr"))
    # 3) 冻结后 exe 同级目录
    if getattr(sys, "frozen", False):
        dirs.append(os.path.join(os.path.dirname(sys.executable), "wxocr"))
    # 4) 本包的上层目录（开发时的项目根）
    here = os.path.dirname(os.path.abspath(__file__))
    dirs.append(os.path.join(os.path.dirname(here), "wxocr"))
    dirs.append(os.path.join(here, "wxocr"))
    return dirs


def find_runtime_dir():
    """找到第一个含 WeChatOCR.exe 的候选目录；找不到返回默认路径（便于报错）。"""
    cands = candidate_dirs()
    for d in cands:
        if d and os.path.isfile(os.path.join(d, "WeChatOCR.exe")):
            return os.path.abspath(d)
    return os.path.abspath(cands[0]) if cands else "wxocr"


def is_available(runtime_dir=None):
    """运行时文件是否齐备（不实际启动）。"""
    d = os.path.abspath(runtime_dir) if runtime_dir else find_runtime_dir()
    need = ["WeChatOCR.exe",
            "mmmojo_64.dll" if _is_64bit() else "mmmojo.dll"]
    return all(os.path.isfile(os.path.join(d, n)) for n in need)

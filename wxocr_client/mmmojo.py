# -*- coding: utf-8 -*-
"""
mmmojo.py —— 微信 mmmojo IPC 的 ctypes 绑定
============================================
WeChatOCR.exe 不是一个普通的命令行程序：它是微信二进制里剥离出来的
OCR 子进程，通过腾讯自研的 mmmojo（mojo 变体）消息管道与宿主通信。
宿主侧加载 mmmojo_64.dll，由它去拉起 WeChatOCR.exe 并建立管道，
之后双方以 protobuf 消息收发。

本文件把 mmmojo_64.dll 的导出函数与回调枚举包装成 ctypes 调用，
只保留 OCR 场景需要的部分。

调用顺序：
    InitializeMMMojo(0, None)
    env = CreateMMMojoEnvironment()
    SetMMMojoEnvironmentCallbacks(env, ...)            # 注册回调
    SetMMMojoEnvironmentInitParams(env, kMMHostProcess, 1)
    SetMMMojoEnvironmentInitParams(env, kMMExePath, "…/WeChatOCR.exe")
    AppendMMSubProcessSwitchNative(env, b"user-lib-dir", "…/wxocr")
    StartMMMojoEnvironment(env)
    ... 等 kMMRemoteConnect 回调 ...
    writeinfo = CreateMMMojoWriteInfo(kMMPush, False, req_id)
    buf = GetMMMojoWriteInfoRequest(writeinfo, size)
    memmove(buf, pb_bytes, size)
    SendMMMojoWriteInfo(env, writeinfo)

坑位提示：
    ctypes 里同一个导出函数只有一份 argtypes。SetMMMojoEnvironmentCallbacks
    与 SetMMMojoEnvironmentInitParams 都是变参 C 函数，必须在**每次调用前**
    重设 argtypes，否则第二次调用就会因为签名不匹配直接 TypeError。
"""

import os
from ctypes import (
    CDLL, CFUNCTYPE, POINTER, byref, c_bool, c_char_p, c_int, c_uint32,
    c_void_p, c_wchar_p, memmove, py_object, string_at,
)


# ============================================================
# 枚举（数值必须与微信 mmmojo.h 一致）
# ============================================================
class MMMojoInfoMethod:
    """消息投递方式。OCR 请求用 kMMPush。"""
    kMMNone = 0
    kMMPush = 1
    kMMPullReq = 2
    kMMPullResp = 3
    kMMShared = 4


class MMMojoEnvironmentCallbackType:
    """回调类型编号。"""
    kMMUserData = 0
    kMMReadPush = 1
    kMMReadPull = 2
    kMMReadShared = 3
    kMMRemoteConnect = 4
    kMMRemoteDisconnect = 5
    kMMRemoteProcessLaunched = 6
    kMMRemoteProcessLaunchFailed = 7
    kMMRemoteMojoError = 8


class MMMojoEnvironmentInitParamType:
    """环境初始化参数类型编号。"""
    kMMHostProcess = 0
    kMMLoopStartThread = 1
    kMMExePath = 2
    kMMLogPath = 3
    kMMLogToStderr = 4
    kMMAddNumMessagepipe = 5
    kMMSetDisconnectHandlers = 6
    kMMDisableDefaultPolicy = 1000
    kMMElevated = 1001
    kMMCompatible = 1002


# 回调 C 签名（对应 mmmojo.h 里的 typedef）
#   void (kMMReadXxx)(uint32_t request_id, const void* request_info, void* user_data)
#   void (kMMRemoteConnect)(bool is_connected, void* user_data)
#   void (kMMRemoteDisconnect)(void* user_data)
#   void (kMMRemoteProcessLaunched)(void* user_data)
#   void (kMMRemoteProcessLaunchFailed)(int error_code, void* user_data)
#   void (kMMRemoteMojoError)(const void* errorbuf, int errorsize, void* user_data)
CALLBACK_SIGNATURES = {
    "kMMReadPush": CFUNCTYPE(None, c_uint32, c_void_p, c_void_p),
    "kMMReadPull": CFUNCTYPE(None, c_uint32, c_void_p, c_void_p),
    "kMMReadShared": CFUNCTYPE(None, c_uint32, c_void_p, c_void_p),
    "kMMRemoteConnect": CFUNCTYPE(None, c_bool, c_void_p),
    "kMMRemoteDisconnect": CFUNCTYPE(None, c_void_p),
    "kMMRemoteProcessLaunched": CFUNCTYPE(None, c_void_p),
    "kMMRemoteProcessLaunchFailed": CFUNCTYPE(None, c_int, c_void_p),
    "kMMRemoteMojoError": CFUNCTYPE(None, c_void_p, c_int, c_void_p),
}

# 注册顺序：名称 → 回调类型编号
CALLBACK_ORDER = [
    ("kMMReadPush", MMMojoEnvironmentCallbackType.kMMReadPush),
    ("kMMReadPull", MMMojoEnvironmentCallbackType.kMMReadPull),
    ("kMMReadShared", MMMojoEnvironmentCallbackType.kMMReadShared),
    ("kMMRemoteConnect", MMMojoEnvironmentCallbackType.kMMRemoteConnect),
    ("kMMRemoteDisconnect", MMMojoEnvironmentCallbackType.kMMRemoteDisconnect),
    ("kMMRemoteProcessLaunched", MMMojoEnvironmentCallbackType.kMMRemoteProcessLaunched),
    ("kMMRemoteProcessLaunchFailed", MMMojoEnvironmentCallbackType.kMMRemoteProcessLaunchFailed),
    ("kMMRemoteMojoError", MMMojoEnvironmentCallbackType.kMMRemoteMojoError),
]


def _bind(dll, name, restype, *argtypes):
    """给 dll 的导出函数设置签名并返回函数对象。"""
    fn = getattr(dll, name)
    fn.restype = restype
    fn.argtypes = list(argtypes)
    return fn


class MMMojoEnvironment:
    """mmmojo 环境：负责拉起/关闭 WeChatOCR.exe，并收发消息。

    回调由 mmmojo 自己的线程触发，因此回调里只做轻量动作，
    复杂逻辑交给 host 对象（引擎）去做。
    """

    def __init__(self, dll_path):
        dll_path = os.path.abspath(dll_path)
        if not os.path.isfile(dll_path):
            raise FileNotFoundError(f"找不到 mmmojo dll: {dll_path}")

        # mmmojo 可能有同目录依赖，先把它加进 DLL 搜索路径
        self._dll_dirs = []
        try:
            self._dll_dirs.append(os.add_dll_directory(os.path.dirname(dll_path)))
        except (AttributeError, OSError):
            pass

        self._dll = CDLL(dll_path)
        self._env = c_void_p(None)
        self._started = False
        self._host = self
        self._callbacks = {}           # 保持引用，防止回调被 GC 回收

        self._bind_all()

    # ================= 绑定 =================
    def _bind_all(self):
        d = self._dll
        self._InitializeMMMojo = _bind(d, "InitializeMMMojo", None,
                                       c_int, POINTER(c_char_p))
        self._CreateMMMojoEnvironment = _bind(d, "CreateMMMojoEnvironment", c_void_p)
        self._AppendMMSubProcessSwitchNative = _bind(
            d, "AppendMMSubProcessSwitchNative", None, c_void_p, c_char_p, c_wchar_p)
        self._StartMMMojoEnvironment = _bind(d, "StartMMMojoEnvironment", None, c_void_p)
        self._StopMMMojoEnvironment = _bind(d, "StopMMMojoEnvironment", None, c_void_p)
        self._RemoveMMMojoEnvironment = _bind(d, "RemoveMMMojoEnvironment", None, c_void_p)
        self._CreateMMMojoWriteInfo = _bind(d, "CreateMMMojoWriteInfo", c_void_p,
                                            c_int, c_bool, c_uint32)
        self._GetMMMojoWriteInfoRequest = _bind(d, "GetMMMojoWriteInfoRequest", c_void_p,
                                                c_void_p, c_uint32)
        self._RemoveMMMojoWriteInfo = _bind(d, "RemoveMMMojoWriteInfo", None, c_void_p)
        self._SendMMMojoWriteInfo = _bind(d, "SendMMMojoWriteInfo", c_bool,
                                          c_void_p, c_void_p)
        self._GetMMMojoReadInfoRequest = _bind(d, "GetMMMojoReadInfoRequest", c_void_p,
                                               c_void_p, POINTER(c_uint32))
        self._RemoveMMMojoReadInfo = _bind(d, "RemoveMMMojoReadInfo", None, c_void_p)

        # 变参函数：只取底层函数对象，argtypes 在每次调用前现设
        self._f_SetCallbacks = d.SetMMMojoEnvironmentCallbacks
        self._f_SetCallbacks.restype = None
        self._f_SetInitParams = d.SetMMMojoEnvironmentInitParams
        self._f_SetInitParams.restype = None

    # ---------- 变参函数的安全包装 ----------
    def _set_init_params_int(self, type_id, value):
        self._f_SetInitParams.argtypes = [c_void_p, c_int, c_int]
        self._f_SetInitParams(self._env, int(type_id), int(value))

    def _set_init_params_wstr(self, type_id, value):
        self._f_SetInitParams.argtypes = [c_void_p, c_int, c_wchar_p]
        self._f_SetInitParams(self._env, int(type_id), c_wchar_p(value))

    def _set_callback(self, cb_type, cb):
        self._f_SetCallbacks.argtypes = [c_void_p, c_int, cb.__class__]
        self._f_SetCallbacks(self._env, int(cb_type), cb)

    def _set_callback_userdata(self, host):
        self._f_SetCallbacks.argtypes = [c_void_p, c_int, py_object]
        self._f_SetCallbacks(self._env, MMMojoEnvironmentCallbackType.kMMUserData,
                             py_object(host))

    # ================= 生命周期 =================
    def start(self, exe_path, user_lib_dir, host_data=None, extra_switches=None):
        """拉起子进程并建立管道。

        exe_path     : WeChatOCR.exe 的绝对路径
        user_lib_dir : mmmojo dll 所在目录（透传 --user-lib-dir）
        host_data    : 回调宿主对象，需实现 on_xxx 回调方法
        extra_switches: [(name, value)] 追加的命令行开关
        """
        if self._started:
            return
        exe_path = os.path.abspath(exe_path)
        user_lib_dir = os.path.abspath(user_lib_dir)
        if not os.path.isfile(exe_path):
            raise FileNotFoundError(f"找不到 WeChatOCR.exe: {exe_path}")

        self._host = host_data if host_data is not None else self

        self._InitializeMMMojo(0, None)
        self._env = c_void_p(self._CreateMMMojoEnvironment())
        if not self._env:
            raise RuntimeError("CreateMMMojoEnvironment 失败")

        self._set_callback_userdata(self._host)
        for name, type_id in CALLBACK_ORDER:
            handler = getattr(self._host, f"on_{name[3:].lower()}", None)
            cb = CALLBACK_SIGNATURES[name](handler if handler else (lambda *a: None))
            self._callbacks[name] = cb           # 必须保引用
            self._set_callback(type_id, cb)

        self._set_init_params_int(MMMojoEnvironmentInitParamType.kMMHostProcess, 1)
        self._set_init_params_wstr(MMMojoEnvironmentInitParamType.kMMExePath, exe_path)
        self._AppendMMSubProcessSwitchNative(self._env, b"user-lib-dir", user_lib_dir)
        for k, v in (extra_switches or []):
            self._AppendMMSubProcessSwitchNative(
                self._env, str(k).encode("utf-8"), str(v))

        self._StartMMMojoEnvironment(self._env)
        self._started = True

    def stop(self):
        """关闭子进程与管道。可重复调用。"""
        if not self._started:
            return
        env, self._env = self._env, c_void_p(None)
        self._started = False
        try:
            self._StopMMMojoEnvironment(env)
        except Exception:
            pass
        try:
            self._RemoveMMMojoEnvironment(env)
        except Exception:
            pass

    @property
    def started(self):
        return self._started

    # ================= 消息收发 =================
    def send(self, pb_bytes, request_id=0, method=MMMojoInfoMethod.kMMPush, sync=False):
        """发送一条 protobuf 消息。"""
        if not self._started:
            raise RuntimeError("mmmojo 环境未启动")
        n = len(pb_bytes)
        write_info = self._CreateMMMojoWriteInfo(int(method), bool(sync), int(request_id))
        if not write_info:
            raise RuntimeError("CreateMMMojoWriteInfo 失败")
        buf = self._GetMMMojoWriteInfoRequest(c_void_p(write_info), c_uint32(n))
        if not buf:
            self._RemoveMMMojoWriteInfo(c_void_p(write_info))
            raise RuntimeError("GetMMMojoWriteInfoRequest 失败")
        memmove(buf, pb_bytes, n)
        ok = self._SendMMMojoWriteInfo(self._env, c_void_p(write_info))
        if not ok:
            self._RemoveMMMojoWriteInfo(c_void_p(write_info))
            raise RuntimeError("SendMMMojoWriteInfo 失败")
        # 成功后不回收 write_info：消息是异步处理的，提前释放会让子进程读到野指针
        return write_info

    def read_request_bytes(self, request_info):
        """从 kMMReadPush/Pull 回调的 request_info 取出字节流。"""
        size = c_uint32(0)
        ptr = self._GetMMMojoReadInfoRequest(as_ptr(request_info), byref(size))
        if not ptr or size.value == 0:
            return b""
        return string_at(ptr, size.value)

    def remove_read_info(self, request_info):
        """释放一条 read info。"""
        self._RemoveMMMojoReadInfo(as_ptr(request_info))


def as_ptr(value):
    """回调里的 request_info 可能是 int 或 c_void_p，统一成 c_void_p。"""
    if isinstance(value, c_void_p):
        return value
    return c_void_p(value)

# -*- coding: utf-8 -*-
"""
wxocr_client —— 微信 OCR（提取版）Python 客户端
================================================
纯标准库实现，零第三方依赖，用于替换项目原有的 RapidOCR 后端。

用法::

    from wxocr_client import WeChatOCREngine

    engine = WeChatOCREngine()          # 自动定位项目内 wxocr/ 运行时
    items = engine.recognize(bgr_img)   # [(text, score, [x0,y0,x1,y1]), ...]
    engine.stop()                       # 退出前关闭 OCR 子进程

模块构成：
    engine      —— 同步识别引擎（本包入口）
    pb_lite     —— 手写 protobuf 编解码（规避 protobuf 版本冲突）
    mmmojo      —— mmmojo IPC 的 ctypes 绑定
"""

from .engine import (            # noqa: F401
    WeChatOCREngine,
    find_runtime_dir,
    is_available,
)

__all__ = ["WeChatOCREngine", "find_runtime_dir", "is_available"]

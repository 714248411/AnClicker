# -*- coding: utf-8 -*-
"""
pb_lite.py —— 极简 protobuf 线格式编解码（零第三方依赖）
=========================================================
为什么要自己写：
    微信 OCR 官方协议是 protobuf。社区现成包用 protobuf==3.20.3 生成的
    *_pb2.py，而本项目 venv 里的 protobuf 是 7.x —— 版本不匹配时
    "Descriptors cannot not be created directly" 直接报错。
    与其降级 protobuf（会牵连 onnxruntime 等一堆包），不如按协议号手写
    编码/解码。协议本身很小，收益是：不引入任何依赖、没有版本冲突、
    PyInstaller 打包也省掉 hiddenimports，而且省掉 MessageToJson 的
    JSON 往返，实时循环里更快。

协议（来自微信 WeChatOCR.exe 的 ocr_protobuf.proto 描述符）：

    message OcrRequest {
        int32  unknow  = 1;      // 0 = 执行 OCR
        int32  task_id = 2;
        PicPaths pic_path = 3;
        message PicPaths { repeated string pic_path = 1; }
    }

    message OcrResponse {
        int32 type     = 1;
        int32 task_id  = 2;
        int32 err_code = 3;
        OcrResult ocr_result = 4;
        message OcrResult {
            repeated SingleResult single_result = 1;
            int32 unknown_1 = 2;
            int32 unknown_2 = 3;
            message SingleResult {
                ResultPos single_pos = 1;
                bytes     single_str_utf8 = 2;   // 文本（UTF-8 字节）
                float     single_rate = 3;       // 置信度
                repeated OneResult one_result = 4;
                float left = 5; float top = 6; float right = 7; float bottom = 8;
                int32 unknown_0 = 9;
                ResultPos unknown_pos = 10;
            }
            message ResultPos {
                repeated PosXY pos = 1;
                message PosXY { float x = 1; float y = 2; }
            }
        }
    }
"""

import struct

# ---- wire type ----
WT_VARINT = 0
WT_FIXED64 = 1
WT_LEN = 2
WT_FIXED32 = 5


# ============================================================
# 底层读写
# ============================================================
def _write_varint(out, value):
    """把非负整数按 base-128 变长写入 out(list of int)。"""
    if value < 0:
        # protobuf 的负数 int 用 10 字节补码表示
        value &= (1 << 64) - 1
    while True:
        b = value & 0x7F
        value >>= 7
        if value:
            out.append(b | 0x80)
        else:
            out.append(b)
            return


def _read_varint(buf, pos):
    """读变长整数，返回 (值, 新位置)。"""
    result = 0
    shift = 0
    while True:
        if pos >= len(buf):
            raise ValueError("protobuf 数据被截断（varint 未结束）")
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
        if shift > 70:
            raise ValueError("protobuf varint 过长")


# ============================================================
# 编码：OcrRequest
# ============================================================
def encode_ocr_request(task_id, pic_path):
    """构造 OcrRequest 的序列化字节。

    task_id : int，取值范围建议 [2, 0x7fffffff]（1 被初始化流程占用）
    pic_path: str，待识别图片的绝对路径
    """
    out = bytearray()
    # field 1: unknow = 0（执行 OCR）
    out.append((1 << 3) | WT_VARINT)
    _write_varint(out, 0)
    # field 2: task_id
    out.append((2 << 3) | WT_VARINT)
    _write_varint(out, task_id)
    # field 3: pic_path 子消息 { field 1: repeated string pic_path }
    inner = bytearray()
    raw = pic_path.encode("utf-8")
    inner.append((1 << 3) | WT_LEN)
    _write_varint(inner, len(raw))
    inner.extend(raw)
    out.append((3 << 3) | WT_LEN)
    _write_varint(out, len(inner))
    out.extend(inner)
    return bytes(out)


# ============================================================
# 解码：通用线格式 → {字段号: [值, ...]}
# ============================================================
def parse(buf):
    """把 protobuf 字节流解析成 {字段号: [值, ...]}。

    值类型：
        wire type 0 (varint)  -> int
        wire type 5 (float32) -> float
        wire type 1 (fixed64) -> bytes（本协议用不到）
        wire type 2 (len)     -> bytes（可能是字符串 / 子消息）
    重复字段自然是列表；同号字段出现多次会按出现顺序追加。
    """
    if isinstance(buf, (bytearray, memoryview)):
        buf = bytes(buf)
    out = {}
    pos = 0
    n = len(buf)
    while pos < n:
        key, pos = _read_varint(buf, pos)
        fnum = key >> 3
        wtype = key & 0x07
        if fnum == 0:
            raise ValueError("protobuf 字段号为 0，数据非法")
        if wtype == WT_VARINT:
            val, pos = _read_varint(buf, pos)
        elif wtype == WT_LEN:
            ln, pos = _read_varint(buf, pos)
            if pos + ln > n:
                raise ValueError("protobuf 长度字段越界")
            val = buf[pos:pos + ln]
            pos += ln
        elif wtype == WT_FIXED64:
            if pos + 8 > n:
                raise ValueError("protobuf fixed64 越界")
            val = buf[pos:pos + 8]
            pos += 8
        elif wtype == WT_FIXED32:
            if pos + 4 > n:
                raise ValueError("protobuf fixed32 越界")
            val = struct.unpack_from("<f", buf, pos)[0]
            pos += 4
        else:
            raise ValueError(f"不支持的 protobuf wire type: {wtype}")
        out.setdefault(fnum, []).append(val)
    return out


def _first(fields, num, default=None):
    """取字段的第一个值（不存在返回 default）。"""
    vals = fields.get(num)
    return vals[0] if vals else default


def _as_float(v, default=0.0):
    """字段值转 float：可能已是 float(int 位) 也可能是 varint 整数。"""
    if isinstance(v, float):
        return v
    if isinstance(v, int):
        return float(v)
    return default


# ============================================================
# 解码：OcrResponse → [(text, score, left, top, right, bottom), ...]
# ============================================================
def decode_ocr_response(buf):
    """解析 OCR 响应。

    返回 (info, lines)：
        info  = {"type":int, "task_id":int, "err_code":int}
        lines = [(text:str, score:float, left, top, right, bottom), ...]
    """
    top = parse(buf)
    info = {
        "type": int(_first(top, 1, 0) or 0),
        "task_id": int(_first(top, 2, 0) or 0),
        "err_code": int(_first(top, 3, 0) or 0),
    }
    lines = []
    ocr_result = _first(top, 4)
    if not isinstance(ocr_result, (bytes, bytearray)):
        return info, lines

    res = parse(ocr_result)
    for sr_raw in res.get(1, []):
        if not isinstance(sr_raw, (bytes, bytearray)):
            continue
        sr = parse(sr_raw)
        raw_text = _first(sr, 2, b"")
        if isinstance(raw_text, str):
            text = raw_text
        else:
            text = bytes(raw_text).decode("utf-8", errors="replace")
        if not text:
            continue
        score = _as_float(_first(sr, 3, 0.0), 0.0)
        if score <= 0.0:
            score = 1.0        # 个别版本不回传 rate，缺失时视为满置信
        score = min(1.0, score)   # 实测个别条目会给出 >1 的值，夹到 [0,1] 免得干扰阈值判断
        left = _as_float(_first(sr, 5, 0.0))
        top_ = _as_float(_first(sr, 6, 0.0))
        right = _as_float(_first(sr, 7, 0.0))
        bottom = _as_float(_first(sr, 8, 0.0))
        lines.append((text, score, left, top_, right, bottom))
    return info, lines

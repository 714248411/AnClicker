# -*- coding: utf-8 -*-
"""glyph_lib —— 「截图出字库」：红字黑描边怪名的模板匹配识别。

背景：微信OCR / RapidOCR 对游戏里的「红字黑描边」小字（怪物头顶名、
顶部目标栏名）检测很差——检测阶段就把字漏了，识别再强也没用。
本模块完全绕开 OCR：用「红色掩膜 → 单字连通域 → 归一化模板比对 →
同行相邻成串」直接从截图里找出已入库的文字。

使用流程（GUI 里对应「字库取字」按钮）：
  1) 截一张游戏图，框选一段红字怪名，输入这段字（如「真理在手2」）
  2) 自动把框内红色像素切成 N 个单字模板，存入 glyphs/ 目录
  3) 之后每帧 scan() 都能在画面里找出这些字（不依赖 OCR）

模板匹配原理：
  - 每个单字模板 = 该字红色掩膜裁剪 → 补成正方形 → 缩放到 24x24 的 0/1 图
  - 匹配分数 = min(像素一致度, 前景 Dice)，1.0 完全一致，默认及格线 0.78
  - 与字号无关（先归一化再比），同一字体不同字号也能匹配

字库存放位置（见 default_dir）：
  优先用「脚本/exe 同目录」下的 glyphs/；打包 exe 放在 dist/ 时自动回退到
  上一级的 glyphs/、以及当前工作目录的 glyphs/ —— 取【第一个已有 index.json】
  的目录，都没有才在 exe 同目录新建。绝不用 __file__（打包后是临时解包目录，
  退出即被删除，字库会丢）。

优先级（见 priority.json）：
  labels() 返回优先级顺序；严格模式仅允许高置信且接近最佳分的标签优先
  （「优先读取第一个」）。顺序可在 GUI「字库查看」里上下调整。
"""
import io
import json
import os
import sys
import tempfile
import uuid

import cv2
import numpy as np

# ============ 常量 ============
GLYPH_SIZE = 24          # 模板归一化尺寸（24x24）
CHAR_H_MIN, CHAR_H_MAX = 6, 40     # 单字连通域高度范围（像素）
CHAR_W_MIN, CHAR_W_MAX = 2, 60     # 单字连通域宽度范围
CHAR_AREA_MIN = 3        # 连通域最小面积（滤孤立噪点）
RED_R_MIN = 110          # 红字掩膜：R 通道下限
RED_DIFF_MIN = 45        # 红字掩膜：R - max(B,G) 下限（把红从橙/白里分出来）
MATCH_MIN_SCORE = 0.78   # 单字模板匹配及格线（同帧同字=1.0，跨帧≈0.85+；
                         # 实测笔画碎片误匹配最高 0.74 → 0.78 能干净分开）
LINE_GAP_K = 1.8         # 成串：相邻字【字心距】<= 该值 × 字高
                         # （实测真理在手2：字心距 13.5px / 字高 12px ≈ 1.13；
                         #   取 1.8 留余量，仍远小于跨词间距）
FILL_RATIO_MAX = 0.85    # 连通块【填充率】上限：超过视为"糊成一团的实心块"
                         # （小字+花背景会把笔画糊死），彼此归一化后全是近似
                         # 实心矩形、互相 1.0 —— 不可辨识，跳过匹配防误报。
LINE_YOVER = 0.4         # 成串：两字 y 方向重叠比例至少该值

GLYPH_DIRNAME = "glyphs"      # 字库目录名
INDEX_FILENAME = "index.json"
ORDER_FILENAME = "priority.json"   # 优先级顺序 + 匹配模式（与 index.json 分开放）
PRIORITY_TIE_EPS = 0.03       # 非严格模式：分数差 <= 该值视为「并列」，按优先级取先者
STRICT_MIN_SCORE = 0.86       # 严格优先级模式的「抢答闸门」：第一个标签必须够像
                              # （默认及格线 0.78 太低——两个字都过线时，排前面的
                              #   会抢走后面的正确字，实测被回归用例抓到。0.86 只允许
                              #   【高置信】命中抢答，弱命中一律回落到最高分规则）
MIN_CELL_W = 2.5              # 等分切字时每格最少像素宽（太窄说明框小/字数多）


# ================= 字库目录定位 =================
def app_base_dir():
    """程序所在目录：打包后=exe 所在目录；源码运行=本文件所在目录。

    ⚠ 不能用 __file__ 判断——打包成 exe 后 __file__ 指向临时解包目录
    （PyInstaller 的 _MEIPASS，退出即删），在那里建字库会丢。
    """
    if getattr(sys, "frozen", False):          # PyInstaller 打包后
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def glyph_dir_candidates(base=None):
    """候选字库目录（按优先级）：程序目录 → 上级目录（exe 在 dist/ 时）→ 当前工作目录。"""
    if base is None:
        from anclicker.app.paths import DATA_FOLDER
        return [os.path.join(DATA_FOLDER, GLYPH_DIRNAME)]
    base = os.fspath(base)
    outs = [os.path.join(base, GLYPH_DIRNAME)]
    parent = os.path.dirname(os.path.abspath(base))
    if parent and parent != os.path.abspath(base):
        outs.append(os.path.join(parent, GLYPH_DIRNAME))
    try:
        cwd = os.path.abspath(os.getcwd())
    except Exception:
        cwd = ""
    if cwd:
        outs.append(os.path.join(cwd, GLYPH_DIRNAME))
    # 去重且保序
    uniq = []
    for p in outs:
        if p not in uniq:
            uniq.append(p)
    return uniq


def default_dir(base=None, create=True):
    """取实际使用的字库目录：第一个已存在 index.json 的候选；都没有则用首选项（并创建）。"""
    cands = glyph_dir_candidates(base)
    for c in cands:
        try:
            if os.path.exists(os.path.join(c, INDEX_FILENAME)):
                return c
        except Exception:
            continue
    d = cands[0]
    if create:
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
    return d


def count_templates(base_dir=None):
    """（标签数, 模板数）——供界面显示「字库已建多少」用；失败返回 (0, 0)。"""
    try:
        p = os.path.join(base_dir or default_dir(create=False), INDEX_FILENAME)
        if not os.path.exists(p):
            return 0, 0
        d = json.load(io.open(p, encoding="utf-8"))
        if not isinstance(d, dict):
            return 0, 0
        n = 0
        for v in d.values():
            if isinstance(v, (list, tuple)):
                n += len(v)
        return len(d), n
    except Exception:
        return 0, 0


def red_text_mask(img_bgr, r_min=RED_R_MIN, diff_min=RED_DIFF_MIN,
                  use_outline=True):
    """红色文字掩膜（uint8 0/1）。

    **核心：红字 + 黑描边，模糊也要认得。**

    问题：红字本体随模糊/小字 R 值骤降（实测红字 R 的 p10 只有 42），
    单一 R 阈值会把模糊小字整片切掉。

    方案（两段，都在 C 层，不引入噪声）：
      1. **降阈红芯** —— 用更低的 R 下限（r_min*0.55 ≈ 60）但【要求更强的
         红偏色差】（diff 下限不变），把模糊后被削弱、但"色相仍偏红"的像素
         也捞回来；
      2. **闭运算补形** —— 红字被黑描边割出的细缝/弱化笔画，用小核闭运算
         桥接回字形（黑描边区域的像素原本就夹在红笔画之间，闭运算能把
         红笔画与描边交界连起来，补回被侵蚀的笔画）。
    只做逐像素判据 + 形态学闭，不做梯度 → 不会像"描边梯度"那样引入海量噪声。
    """
    if img_bgr is None or img_bgr.ndim != 3:
        return None
    b, g, r = cv2.split(img_bgr)
    mx = cv2.max(b, g)
    d = cv2.subtract(r, mx)                     # 饱和减：负数 → 0（红偏色差）
    # —— 主判据：r >= r_min 且 红偏色差 >= diff_min ——
    m1 = cv2.compare(d, int(diff_min), cv2.CMP_GE)
    m2 = cv2.compare(r, int(r_min), cv2.CMP_GE)
    core = cv2.bitwise_and(m1, m2)
    if not use_outline:
        return core >> 7
    # —— 模糊补偿：更暗但更强偏红的像素也计入（R 降到 ~60 仍偏红就捞回）——
    lo_r = int(r_min * 0.55)
    m_lo = cv2.compare(r, lo_r, cv2.CMP_GE)
    m_hi_diff = cv2.compare(d, int(diff_min * 1.15), cv2.CMP_GE)
    weak = cv2.bitwise_and(m_lo, m_hi_diff)     # 暗但确实偏红的过渡像素
    merged = cv2.bitwise_or(core, weak)
    # 闭运算：桥接被黑描边割断的红笔画（小核，只连近邻，不糊成团）
    kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed = cv2.morphologyEx(merged, cv2.MORPH_CLOSE, kern)
    return closed >> 7


def _bg_color_of(img_bgr):
    """估计选区背景色：优先用【边缘一圈】的中位色（字通常在中间、边框是背景），
    退化为整体中位色。"""
    h, w = img_bgr.shape[:2]
    try:
        if h >= 6 and w >= 6:
            ring = np.concatenate([
                img_bgr[0:2].reshape(-1, 3), img_bgr[h - 2:h].reshape(-1, 3),
                img_bgr[:, 0:2].reshape(-1, 3), img_bgr[:, w - 2:w].reshape(-1, 3)])
            return np.median(ring, axis=0)
    except Exception:
        pass
    return np.median(img_bgr.reshape(-1, 3), axis=0)


def any_text_mask(img_bgr, tol=45):
    """任意颜色文字掩膜（uint8 0/1）：不限定红字，任何颜色都能取字。

    以选区【边缘背景色】为基准，偏离超过 tol 的像素视为文字笔画，
    再做一次开运算清掉孤立噪点。适合白字/黄字/蓝字等非红字场景。
    """
    if img_bgr is None or img_bgr.ndim != 3:
        return None
    try:
        bg = _bg_color_of(img_bgr)
        diff = np.abs(img_bgr.astype(np.int16) - bg.astype(np.int16))
        d = diff.max(axis=2)
        m = ((d > float(tol)).astype(np.uint8)) * 255
        if m.any():
            m = cv2.morphologyEx(m, cv2.MORPH_OPEN,
                                 np.ones((2, 2), np.uint8))
        return (m > 0).astype(np.uint8)
    except Exception:
        return None


def _char_boxes(mask):
    """掩膜里所有「字号」连通域的外接框 [(x, y, w, h)]（按 x 排序）。

    过滤条件：高度/宽度在字号范围内、面积达标——
    排掉 UI 大色块、细线、孤立噪点。
    """
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, a = int(st[i, 0]), int(st[i, 1]), int(st[i, 2]), int(st[i, 3]), int(st[i, 4])
        if not (CHAR_H_MIN <= h <= CHAR_H_MAX and CHAR_W_MIN <= w <= CHAR_W_MAX):
            continue
        if a < CHAR_AREA_MIN:
            continue
        out.append((x, y, w, h))
    out.sort(key=lambda t: t[0])
    return out


def _norm_glyph(mask, box):
    """取一个字的归一化模板（float32 0/1，GLYPH_SIZE×GLYPH_SIZE）。

    裁出连通域 bbox 内的掩膜 → 周围补成正方形（保持长宽比）→ 缩放到固定尺寸。
    """
    x, y, w, h = box
    crop = mask[y:y + h, x:x + w]
    side = max(w, h)
    canvas = np.zeros((side, side), np.uint8)
    oy, ox = (side - h) // 2, (side - w) // 2
    canvas[oy:oy + h, ox:ox + w] = crop
    g = cv2.resize(canvas, (GLYPH_SIZE, GLYPH_SIZE),
                   interpolation=cv2.INTER_AREA)
    return (g > 0).astype(np.float32)


def _glyph_score(a, b):
    """像素一致度与前景 Dice 的较小值：共享空白不能掩盖笔画不相似。"""
    a, b = np.asarray(a) > 0, np.asarray(b) > 0
    total = float(a.sum() + b.sum())
    if not total:
        return 0.0
    agreement = 1.0 - float(np.mean(a != b))
    dice = 2.0 * float(np.logical_and(a, b).sum()) / total
    return min(agreement, dice)


class GlyphLibrary:
    """单字模板库：glyphs/ 目录 + index.json（+ priority.json 存优先级）。"""

    def __init__(self, base_dir=None):
        self.dir = base_dir or default_dir()
        # ⚠ 目录必须先建出来：入库时 _save_index 要写 index.json，
        #   目录不存在会抛 FileNotFoundError —— 在 Qt 槽函数里就是「闪退」。
        self._ensure_dir()
        self.index_path = os.path.join(self.dir, INDEX_FILENAME)
        self.order_path = os.path.join(self.dir, ORDER_FILENAME)
        self.index = {}          # {label: ["xxx.png", ...]}
        self.order = []          # [label, ...] 优先级顺序（前=先读）
        self.strict = True       # True=严格按优先级（第一个达标即采用）
        self._mtime_key = None   # 文件 mtime 快照（热重载用）
        self._templates = None   # {label: [norm_glyph]}（load 后缓存）
        self._load_index()

    def _ensure_dir(self):
        try:
            os.makedirs(self.dir, exist_ok=True)
            return True
        except Exception:
            return False

    # ---------- 持久化 ----------
    def _load_index(self):
        """读 index.json（标签→样本文件名）与 priority.json（顺序+模式）。

        脏数据一律忽略（用空库/默认顺序），绝不抛异常。
        """
        idx = {}
        if os.path.exists(self.index_path):
            try:
                raw = json.load(io.open(self.index_path, encoding="utf-8"))
                if isinstance(raw, dict):
                    for k, v in raw.items():
                        if isinstance(v, (list, tuple)):
                            files = [str(x) for x in v if str(x)]
                            if files:
                                idx[str(k)] = files
            except Exception:
                idx = {}
        self.index = idx

        order, strict = [], True
        if os.path.exists(self.order_path):
            try:
                raw = json.load(io.open(self.order_path, encoding="utf-8"))
                if isinstance(raw, dict):
                    o = raw.get("order")
                    if isinstance(o, (list, tuple)):
                        order = [str(x) for x in o]
                    s = raw.get("strict")
                    if isinstance(s, bool):
                        strict = s
            except Exception:
                order, strict = [], True
        # 只保留库里还有的标签（顺序里的僵尸标签丢弃）
        self.order = [l for l in order if l in self.index]
        self.strict = strict
        self._templates = None
        try:
            self._mtime_key = self._file_key()
        except Exception:
            self._mtime_key = None

    def _file_key(self):
        """两个 json 的 mtime 快照（用于热重载判定）。"""
        keys = []
        for p in (self.index_path, self.order_path):
            try:
                stat=os.stat(p)
                keys.append((stat.st_mtime_ns,stat.st_size))
            except Exception:
                keys.append(0.0)
        return tuple(keys)

    def reload_if_changed(self):
        """index.json / priority.json 变了就重载；返回是否重载过。"""
        try:
            k = self._file_key()
        except Exception:
            return False
        if k != self._mtime_key:
            self._load_index()
            return True
        return False

    @staticmethod
    def _atomic_json(path, data):
        fd, tmp = tempfile.mkstemp(prefix=".glyph_", suffix=".tmp", dir=os.path.dirname(path))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def _save_index(self):
        """写 index.json。失败返回 False（不抛异常 —— 调用方多是 UI 槽函数）。"""
        if not self._ensure_dir():
            return False
        try:
            self._atomic_json(self.index_path, self.index)
            self._templates = None   # 下次匹配时重新加载
            self._mtime_key = self._file_key()
            return True
        except Exception:
            return False

    def save_order(self):
        """写 priority.json（顺序 + 严格模式）。失败返回 False。"""
        if not self._ensure_dir():
            return False
        try:
            self._atomic_json(self.order_path, {"order": list(self.labels()),
                                                "strict": bool(self.strict)})
            self._mtime_key = self._file_key()
            return True
        except Exception:
            return False

    # ---------- 入库 ----------
    def add_glyph(self, label, norm_glyph):
        """把单字模板入库，重复样本复用，使用唯一文件名避免覆盖。

        返回样本文件名；失败返回 None。调用方批量完成后保存索引。
        """
        label = str(label)
        if not label:
            return None
        if not self._ensure_dir():
            return None
        glyph = np.asarray(norm_glyph)
        if glyph.shape != (GLYPH_SIZE, GLYPH_SIZE) or not np.isfinite(glyph).all():
            return None
        glyph = (glyph > 0.5).astype(np.uint8)
        if not glyph.any():
            return None
        # 重复取字复用样本；UUID 防删除后序号回退、同首字标签互相覆盖。
        for fn in self.samples(label):
            try:
                existing = cv2.imdecode(np.fromfile(os.path.join(self.dir, fn), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
                if existing is not None and np.array_equal(glyph, existing > 127):
                    return fn
            except (OSError, cv2.error):
                continue
        fn = "%s_%s.png" % (ord(label[0]), uuid.uuid4().hex)
        p = os.path.join(self.dir, fn)
        try:
            ok, encoded = cv2.imencode(".png", glyph * 255)
            if not ok:
                return None
            with open(p, "xb") as f:
                f.write(encoded.tobytes())
        except Exception:
            return None
        self.index.setdefault(label, []).append(fn)
        self._templates = None
        return fn

    def add_text(self, mask, boxes, text):
        """把一段已切好字的区域入库：boxes 与 text 等长（GUI 取字流程保证）。

        返回实际入库的字数；失败返回 0（不抛异常）。
        """
        if len(boxes) != len(text):
            return 0
        n = 0
        for box, ch in zip(boxes, text):
            if not str(ch).strip():
                continue
            try:
                if self.add_glyph(str(ch), _norm_glyph(mask, box)):
                    n += 1
            except Exception:
                continue
        if n:
            self._save_index()
        return n

    # ---------- 匹配 ----------
    def _load_templates(self):
        if self._templates is None:
            self._templates = {}
            for label, files in self.index.items():
                arr = []
                for fn in dict.fromkeys(files):
                    p = os.path.join(self.dir, fn)
                    if not os.path.exists(p):
                        continue
                    try:
                        g = cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
                    except (OSError, cv2.error):
                        continue
                    if g is None or g.shape != (GLYPH_SIZE, GLYPH_SIZE) or not (g > 127).any():
                        continue
                    arr.append((g > 127).astype(np.float32))
                if arr:
                    self._templates[label] = arr
        return self._templates

    def __len__(self):
        return sum(len(v) for v in self.index.values())

    def labels(self):
        """标签列表，按【优先级顺序】返回（前面的先读）。

        显式排过序的标签按 order 排；其余按【入库顺序】（index.json 里的键序，
        = 最早录入的字在前）。
        """
        known = [l for l in self.order if l in self.index]
        rest = [l for l in self.index if l not in known]
        return known + rest

    def first_label(self):
        """优先级最高的标签（第一个被读取的），空库返回 None。"""
        labs = self.labels()
        return labs[0] if labs else None

    # ---------- 优先级调整（供 GUI「字库查看」调用） ----------
    def set_strict(self, strict):
        self.strict = bool(strict)
        return self.save_order()

    def set_first(self, label):
        """把 label 提到第一位（最高优先级）。"""
        labs = self.labels()
        if label not in labs:
            return False
        self.order = [label] + [l for l in labs if l != label]
        return self.save_order()

    def move_label(self, label, delta):
        """把 label 在优先级顺序里上移/下移 delta 位（-1 上移，+1 下移）。"""
        labs = self.labels()
        if label not in labs:
            return False
        i = labs.index(label)
        j = max(0, min(len(labs) - 1, i + int(delta)))
        if i == j:
            return False
        labs.insert(j, labs.pop(i))
        self.order = labs
        return self.save_order()

    def remove_label(self, label):
        """删除一个标签（含它的全部样本文件）。返回删除的样本数。"""
        files = self.index.pop(label, [])
        for fn in files:
            try:
                os.remove(os.path.join(self.dir, fn))
            except Exception:
                pass
        self.order = [l for l in self.order if l != label]
        self._save_index()
        self.save_order()
        return len(files)

    # ---------- 样本级管理（单个字内部的多个模板） ----------
    def samples(self, label):
        """某个字的样本文件名列表（按当前顺序）。"""
        return list(self.index.get(str(label), []) or [])

    def sample_path(self, label, filename):
        """样本图片的完整路径（供界面显示缩略图）。"""
        return os.path.join(self.dir, str(filename))

    def reorder_labels(self, new_order):
        """按给定顺序重排「所有字」的优先级（拖拽后调用）。"""
        exist = [l for l in new_order if l in self.index]
        rest = [l for l in self.labels() if l not in exist]
        self.order = exist + rest
        return self.save_order()

    def reorder_samples(self, label, new_files):
        """按给定顺序重排某个字内部样本的优先级（拖拽后调用）。

        自动去重：新顺序里重复的项只保留首次出现；未列到的样本按原顺序补在后面。
        """
        label = str(label)
        if label not in self.index:
            return False
        cur = list(self.index[label])
        ordered, seen = [], set()
        for f in new_files:
            if f in cur and f not in seen:
                seen.add(f)
                ordered.append(f)
        rest = [f for f in cur if f not in seen]
        self.index[label] = ordered + rest
        return self._save_index()

    def move_sample(self, label, idx, delta):
        """把某字内第 idx 个样本上移/下移 delta 位（-1 上移，+1 下移）。"""
        label = str(label)
        files = list(self.index.get(label, []) or [])
        i = int(idx)
        if not (0 <= i < len(files)):
            return False
        j = max(0, min(len(files) - 1, i + int(delta)))
        if i == j:
            return False
        files.insert(j, files.pop(i))
        self.index[label] = files
        return self._save_index()

    def remove_sample(self, label, idx):
        """删除某字内第 idx 个样本；若该字已无样本则整字移除。"""
        label = str(label)
        files = list(self.index.get(label, []) or [])
        i = int(idx)
        if not (0 <= i < len(files)):
            return False
        fn = files.pop(i)
        try:
            os.remove(os.path.join(self.dir, fn))
        except Exception:
            pass
        if files:
            self.index[label] = files
            return self._save_index()
        return bool(self.remove_label(label)) or True

    def rename_label(self, old, new):
        """改标签名（样本文件不动，只改索引键）。"""
        old, new = str(old), str(new).strip()
        if not new or old == new or old not in self.index or new in self.index:
            return False
        self.index[new] = self.index.pop(old)
        self.order = [new if l == old else l for l in self.order]
        self._save_index()
        self.save_order()
        return True

    def _templates_mat(self):
        """把所有模板堆成矩阵 (N, 24, 24)，并给出每行对应的标签。

        返回 (mat, labs, order)：
          mat   —— (N, GLYPH_SIZE, GLYPH_SIZE) float32，按【优先级顺序】拼接
          labs  —— 长度 N 的标签数组（第 i 行属于哪个标签）
          order —— 参与匹配的标签顺序（= labels() 过滤掉无样本的）
        向量化的基础：一次矩阵运算算完「所有框 × 所有模板」的相似度，
        取代逐框逐个模板的 Python 循环（实测 44ms → 个位数 ms）。
        """
        tmpl = self._load_templates()
        order = [l for l in self.labels() if l in tmpl]
        mats, labs = [], []
        for label in order:
            for t in tmpl[label]:
                mats.append(t)
                labs.append(label)
        if not mats:
            return None, [], []
        return np.stack(mats), labs, order

    def _label_max_scores(self, glyphs, mat, labs, order, batch=32):
        """(B, GLYPH, GLYPH) 字符 → (B, L) 每标签最高分（纯 numpy 向量化）。

        每个标签可能有多个样本（同字重复标记），取该标签下的最高分
        —— 与旧的「多样本累积只增不减召回」语义一致。
        分批算，避免大画面（框多）时 (B × N × 576) 内存峰值过高。
        """
        g_all = np.asarray(glyphs, np.float32)
        if g_all.ndim == 2:                      # 单字 → 补 batch 维
            g_all = g_all[None]
        # 每个标签占用的模板列号（mat 已按 order 顺序拼接 → 连续切片）。
        # 用 np.bincount 一次性算出每个标签的样本数（O(N)，替代逐标签 labs.count 的 O(L·N)）。
        lab_idx = {l: i for i, l in enumerate(order)}
        ids = np.array([lab_idx[l] for l in labs], np.intp)
        cnt = np.bincount(ids, minlength=len(order))
        ends = np.cumsum(cnt)                     # 每个标签在 mat 里的结束列（含）
        starts = ends - cnt                       # 起始列
        out = np.empty((len(g_all), len(order)), np.float32)
        # —— 关键提速：模板是 0/1 图，|a-b| 的均值可拆成「交集」——
        #   mean|a-b| = (非零a + 非零b - 2·(a∩b)) / 面积
        #   而 a∩b 就是两个 0/1 向量的点积 → 用一次矩阵乘法（BLAS GEMM）算完全部
        #   框×模板的相似度，比逐元素 reduce 快一个数量级（实测 7.9ms → 0.3ms）。
        side = mat.shape[1] * mat.shape[2]
        T = mat.reshape(len(mat), side)                 # (N, 576) 0/1
        nz_t = T.sum(axis=1)                            # (N,)
        for i in range(0, len(g_all), batch):
            g = g_all[i:i + batch].reshape(-1, side)    # (b, 576) 0/1
            inter = g @ T.T                             # (b, N) 交集像素数
            nz_g = g.sum(axis=1)[:, None]               # (b, 1)
            total = nz_g + nz_t[None, :]
            agreement = 1.0 - (total - 2.0 * inter) / float(side)
            dice = np.divide(2.0 * inter, total, out=np.zeros_like(inter), where=total > 0)
            sc = np.minimum(agreement, dice)
            # 按标签段取最高分：np.maximum.reduceat 对连续段向量化归约，
            # 替代逐标签的 Python 循环（标签/模板多时这是最大的常数开销）
            out[i:i + batch] = np.maximum.reduceat(
                sc, starts, axis=1)
        return out

    def match_glyph(self, norm_glyph, min_score=MATCH_MIN_SCORE):
        """单字模板匹配：返回 (label, score) 或 (None, 最高分)。

        按【优先级顺序】遍历标签（labels() 的顺序 = 优先读取顺序）：
          · strict=True（默认，「优先读取第一个」）→ 第一个【高置信】达标的标签
            获胜（要求 >= max(min_score, STRICT_MIN_SCORE)）。加闸门是因为默认
            及格线 0.78 偏低：同一笔画可能同时高于 0.78，若只按顺序抢答会把
            排后面的正确字抢走（回归用例实测）。够像才抢答，不够像退回最高分。
          · strict=False → 直接按最高分（仅几乎并列时按优先级取前面那个）。
        单个标签内多模板取最高分（多样本累积只增不减召回）。
        """
        return self.match_glyphs([norm_glyph],min_score)[0]

    def match_glyphs(self,glyphs,min_score=MATCH_MIN_SCORE):
        """Score candidate glyphs as a batch, with the same priority rules as scan."""
        if not len(glyphs):return []
        mat,labs,order=self._templates_mat()
        if mat is None:return [(None,-1.) for _ in glyphs]
        rows=self._label_max_scores(glyphs,mat,labs,order)
        result=[]
        for row in rows:
            best=float(row.max());selected=None
            if best>=min_score:
                if self.strict:
                    need=max(float(min_score),STRICT_MIN_SCORE,best-PRIORITY_TIE_EPS)
                    selected=next((i for i,value in enumerate(row) if value>=need),None)
                if selected is None:
                    selected=next(i for i,value in enumerate(row) if value>=max(float(min_score),best-PRIORITY_TIE_EPS))
            result.append((order[selected],float(row[selected])) if selected is not None else (None,best))
        return result

    # ---------- 整帧扫描 ----------
    def scan(self, img_bgr, min_score=MATCH_MIN_SCORE,
             r_min=RED_R_MIN, diff_min=RED_DIFF_MIN, color_mode="red", allow_single=False):
        """整帧扫描：返回 [(text, score, [x0, y0, x1, y1]), ...]。

        步骤：红掩膜 → 字号连通域 → 每字模板匹配 → 同行相邻成串。
        只有【每个字都匹配成功】的串才输出——宁缺勿滥，误报比漏报有害。
        score = 串内各字分数的最小值（短板决定可信度）。
        """
        mask = any_text_mask(img_bgr) if color_mode == "any" else red_text_mask(img_bgr, r_min, diff_min)
        if mask is None:
            return []
        boxes = _char_boxes(mask)
        if not boxes:
            return []
        # 每个框先做模板匹配。实心糊块（fill 超限）不能当【匹配字】（糊块之间
        # 互相 1.0 必误报），但可以当【通配块】——它没有标签、只占位成 ?，
        # 不会引入误匹配，还能在糊字场景下组成 花?? 之类的变体串。
        # 匹配用【批量向量化】：一次算完 所有框 × 所有模板（实测 44ms → 个位数 ms）。
        entries = []             # (cx, cy, h, label|None, score, box)
        pending, pend_boxes = [], []       # 待匹配的归一化字 + 对应框/位置
        for box in boxes:
            x, y, w, h = box
            crop = mask[y:y + h, x:x + w]
            fill = float(crop.sum()) / float(max(1, w * h))
            if fill > FILL_RATIO_MAX:
                entries.append((x + w / 2.0, y + h / 2.0, h, None, 0.0, box))
                continue
            pending.append(_norm_glyph(mask, box))
            pend_boxes.append(box)
        if pending:
            mat, labs, order = self._templates_mat()
            if mat is None:
                for box in pend_boxes:
                    x, y, w, h = box
                    entries.append((x + w / 2.0, y + h / 2.0, h, None, 0.0, box))
            else:
                rows = self._label_max_scores(pending, mat, labs, order)
                # 按【与 match_glyph 完全一致】的优先级规则决定每个框的标签：
                #   strict → 优先级第一个「高置信(≥need)」达标者获胜；
                #            没人达标或非 strict → 最高分（并列取优先级靠前）。
                need = max(float(min_score), STRICT_MIN_SCORE)
                for k, box in enumerate(pend_boxes):
                    x, y, w, h = box
                    row = rows[k]
                    best = float(row.max())
                    lab = None
                    if best >= min_score:
                        if getattr(self, "strict", True):
                            for j, l in enumerate(order):
                                if row[j] >= max(need, best - PRIORITY_TIE_EPS):
                                    lab = l
                                    break
                        if lab is None:
                            for j, l in enumerate(order):
                                if row[j] >= max(float(min_score), best - PRIORITY_TIE_EPS):
                                    lab = l
                                    break
                            if lab is None:
                                lab = order[int(row.argmax())]
                    selected_score = float(row[order.index(lab)]) if lab is not None else best
                    entries.append((x + w / 2.0, y + h / 2.0, h, lab, selected_score, box))
        if not entries:
            return []
        # —— 分行：y 重叠足够的归入同一行（行内顺序无关，后面按 x 排）——
        lines = []
        for m in entries:
            placed = False
            for ln in lines:
                ref = ln[-1]
                ov = 1.0 - abs(m[1] - ref[1]) / max(1.0, min(m[2], ref[2]))
                if ov >= LINE_YOVER:
                    ln.append(m)
                    placed = True
                    break
            if not placed:
                lines.append([m])
        # —— 行内按 x 排序 → 顺序扫描成串 ——
        # 已匹配字正常连接；【数字通配】：紧跟在已匹配字后面的未匹配小块
        # （高度 ≤ 已匹配字高+2px，连续 ≤3 个）按 "?" 占位接上——
        # 用于「只标过花，也能组成 花1 / 花20」（? 与任何搜索词子串匹配无关，
        # 搜索词"花"是"花??"的子串 → _is_match 命中）。
        out = []
        for ln in lines:
            ln.sort(key=lambda m: m[0])
            runs = [[ln[0]]]
            for e in ln[1:]:
                ref = runs[-1][-1]
                gap = e[0] - ref[0]
                if 0 < gap <= LINE_GAP_K * max(e[2], ref[2]):
                    if e[3] is None:
                        # 通配块：run 里必须已有匹配字、且高度与匹配字接近
                        mh = max((x[2] for x in runs[-1] if x[3] is not None),
                                 default=0)
                        wc = sum(1 for x in runs[-1] if x[3] is None)
                        if mh and wc < 3 and e[2] <= mh + 2:
                            runs[-1].append(e)
                        # 不满足 → 丢弃该块（不接也不断串，后面匹配字继续连）
                    else:
                        runs[-1].append(e)
                else:
                    runs.append([e])
            for grp in runs:
                # 串必须以【已匹配字】开头（剥掉开头的通配块）
                while grp and grp[0][3] is None:
                    grp = grp[1:]
                if len(grp) < (1 if allow_single else 2):
                    continue
                text = "".join((m[3] if m[3] is not None else "?") for m in grp)
                score = min(m[4] for m in grp if m[3] is not None)
                x0 = min(m[5][0] for m in grp)
                y0 = min(m[5][1] for m in grp)
                x1 = max(m[5][0] + m[5][2] for m in grp)
                y1 = max(m[5][1] + m[5][3] for m in grp)
                out.append((text, round(score, 3),
                            [int(x0), int(y0), int(x1), int(y1)]))
        return out

    # ---------- 取字：框选区域 → 自动切字 ----------
    MAX_CAPTURE_CHARS = 24      # 单次框选最多标几个字（怪名不会更长，防误输入刷爆字库）

    def capture_text(self, img_bgr, rect, text,
                     r_min=RED_R_MIN, diff_min=RED_DIFF_MIN, log=None,
                     color_mode="red"):
        """从截图的 rect=[x0,y0,x1,y1] 里切出 len(text) 个单字入库。

        color_mode:
          "red" — 红字掩膜（原行为，红字黑描边首选）
          "any" — 任意颜色（以背景中位色为基准，白/黄/蓝字都能取）
        切字策略（游戏字是近似等宽的）：
          1) rect 内做文字掩膜连通域；
          2) 连通域数 == 字数 → 直接用；
          3) 连通域数 > 字数 → 不断合并 x 间距最小的相邻框，直到等于字数；
          4) 连通域数 < 字数 → 按 rect 宽度等分切（等宽字体近似），
             每格再收缩到格内实际像素范围。
        返回 (入库字数, 切字框列表)；失败返回 (0, 原因字符串)。

        ⚠ 本方法【绝不抛异常】——它由 GUI 的鼠标松开槽函数调用。
        """
        try:
            return self._capture_text(img_bgr, rect, text,
                                      r_min, diff_min, log, color_mode)
        except Exception as e:                      # 兜底：任何异常都转成提示
            return 0, "切字异常：%s: %s" % (type(e).__name__, e)

    def _capture_text(self, img_bgr, rect, text,
                      r_min=RED_R_MIN, diff_min=RED_DIFF_MIN, log=None,
                      color_mode="red"):
        x0, y0, x1, y1 = [int(v) for v in rect]
        if x1 <= x0 or y1 <= y0:
            return 0, "框选区域为空"
        text = str(text).strip()
        if not text:
            return 0, "未输入文字"
        if len(text)>self.MAX_CAPTURE_CHARS:return 0, '单次最多录入24个字，请分段框选'
        if (x1-x0)*(y1-y0)>4000000:return 0, '取字区域过大，请只框选要录入的一行文字'
        sub = img_bgr[y0:y1, x0:x1]
        if str(color_mode).lower() == "any":
            mask = any_text_mask(sub)
            empty_msg = "框内没有可辨识的文字像素（试着框紧一点、或改用红字模式）"
        else:
            mask = red_text_mask(sub, r_min, diff_min)
            empty_msg = "框内没有红色像素（掩膜阈值可能不合适，或改用「任意颜色」）"
        if mask is None or not mask.any():
            return 0, empty_msg
        boxes = _char_boxes(mask)
        n_target = len(text)
        if not boxes:
            return 0, "框内没有字号连通块"
        # 防误输入：一次别标太多字（否则会把噪声/背景切成一大堆垃圾模板）
        if n_target > self.MAX_CAPTURE_CHARS:
            return 0, "一次最多标记 %d 个字（这次输入了 %d 个，怪名不会这么长）" % (
                self.MAX_CAPTURE_CHARS, n_target)
        if len(boxes)>512:return 0, '选区内容过多，请缩小到单行文字后再保存'
        if len(boxes) > n_target:
            while len(boxes) > n_target:
                # 找 x 间距最小的一对合并
                gaps = [(boxes[i + 1][0] - (boxes[i][0] + boxes[i][2]), i)
                        for i in range(len(boxes) - 1)]
                _, i = min(gaps)
                a, b = boxes[i], boxes[i + 1]
                nx, ny = min(a[0], b[0]), min(a[1], b[1])
                nw = max(a[0] + a[2], b[0] + b[2]) - nx
                nh = max(a[1] + a[3], b[1] + b[3]) - ny
                boxes[i:i + 2] = [(nx, ny, nw, nh)]
        elif len(boxes) < n_target:
            # 等宽切：把 rect 均分成 n_target 格，每格收缩到实际红像素范围
            ink_y, ink_x = np.where(mask > 0)
            ink_left, ink_width = int(ink_x.min()), int(ink_x.max()-ink_x.min()+1)
            step = ink_width / float(n_target)
            if step < MIN_CELL_W:
                return 0, ("框太窄：%d 个字至少需要 %d 像素宽（当前 %d），"
                           "把框拉大一点、或核对字数"
                           % (n_target, int(MIN_CELL_W * n_target), x1 - x0))
            boxes = []
            for k in range(n_target):
                cx0 = ink_left + int(k * step)
                cx1 = ink_left + int((k + 1) * step)
                cell = mask[:, cx0:cx1]
                ys, xs = np.where(cell > 0)
                if len(xs) == 0:
                    return 0, "第 %d 个字的位置没有红色像素（框选范围不对？）" % (k + 1)
                bx0, bx1 = int(xs.min()), int(xs.max())
                by0, by1 = int(ys.min()), int(ys.max())
                boxes.append((cx0 + bx0, by0, bx1 - bx0 + 1, by1 - by0 + 1))
        n = self.add_text(mask, boxes, text)
        if log:
            # 实心糊块统计：填充率过高的字入不了库也认不出（scan 端会跳过）
            fuzzy = [b for b in boxes
                     if float(mask[b[1]:b[1]+b[3], b[0]:b[0]+b[2]].sum())
                     / float(max(1, b[2] * b[3])) > FILL_RATIO_MAX]
            log("[字库] 切字 %d → 入库 %d（库共 %d）%s"
                % (n_target, n, len(self),
                   ("；⚠ %d 个字糊成实心块（背景干扰/字号太小），无法辨识"
                    % len(fuzzy)) if fuzzy else ""))
        return n, boxes

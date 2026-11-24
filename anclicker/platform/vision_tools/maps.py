# -*- coding: utf-8 -*-
"""home_nav.py —— 「回原点」+「自制地图」：小地图拼接 + A* 寻路（纯算法，无游戏 IO）。

背景：主画面 OCR 和小地图（雷达）都找不到怪物时，角色自动回到「挂机点（原点）」；
      同时把走过的地方、发现的怪点实时拼成一张「自制地图」，可在地图上设目标坐标、
      A* 寻路过去。

已确认的游戏机制：
  * 移动 = 点地面自动寻路（游戏自带寻路，点屏幕某处角色自己走过去）。
  * 小地图固定朝北（不随角色旋转；只有小地图里的「人物箭头」随角色转向）。
  * 原点 = 用户单独标记的「挂机点」。

关键推论（比「随旋转」简单得多）：
  * 小地图不旋转 → 世界坐标 = 小地图坐标（同向：x 右、y 下），
    「小地图拼接」= 纯平移配准（相位相关），无需估计旋转角。
  * 角色位移 d → 小地图上的固定点整体平移 -d；配准得 t，则 d = -t。
  * 点地面移动是「绝对屏幕方向」：屏幕方向 = 世界方向，与角色朝向无关。

本模块只做纯算法，CDP/截图/点击由 find_monster / attack_engine 调用方负责。
"""

import heapq
import math
import os
import time
import threading
from functools import wraps

import cv2
import numpy as np


# =========================================================================
# 坐标系约定
# -------------------------------------------------------------------------
# 世界坐标：x 向右、y 向下（图像/屏幕坐标），单位 = 像素。
# 小地图固定朝北（不旋转）→ 世界坐标与小地图像素坐标同向，纯平移关系：
#   固定世界点 P 在「以角色为中心」的小地图上的像素 = (P - pose_xy) + 图中心。
# 角色 pose：(x, y, theta)，theta 仅作朝向显示（人物箭头会转），
#   导航/地图拼接【不依赖】theta（点地面 = 绝对方向）。
# =========================================================================


def screen_click_dir(dx_world, dy_world, theta_deg=0.0):
    """世界位移方向 → 屏幕点击【单位向量】 (ux, uy)。

    游戏「点地面自动寻路」且镜头固定：点屏幕哪个方向，角色就往哪个世界方向走；
    世界坐标（初始对齐屏幕）与屏幕坐标同向，故屏幕方向 = 世界方向单位化，θ 无关。
    """
    n = math.hypot(dx_world, dy_world)
    if n < 1e-6:
        return 0.0, 0.0
    return dx_world / n, dy_world / n


# =========================================================================
# 小地图配准（纯平移）
# =========================================================================

def _window(img):
    """二维汉宁窗，减轻圆形小地图边缘在相位相关里的边缘效应。"""
    h, w = img.shape[:2]
    wy = np.hanning(h)
    wx = np.hanning(w)
    return img * np.outer(wy, wx)


def estimate_motion(prev, curr, angle_range=0.0, angle_step=2.0,
                    max_shift=None, mask=None, use_ecc=True):
    """两帧小地图配准（纯平移；小地图固定朝北，无需估计旋转）。

    两种引擎，优先 ECC、失败退回相位相关：
      * **ECC（findTransformECC，运动模型=纯平移）** —— 工业界图像对齐的常用方案：
          - 亚像素精度（基于梯度的迭代优化，比相位相关更细）；
          - 目标函数是「增强相关系数」（零均值归一化相关），
            对亮度/对比度整体漂移【不变】→ 小地图忽明忽暗也能对齐；
          - 支持 inputMask → 正好只用小地图【圆内】像素，圆外 UI 完全不参与。
      * 相位相关（phaseCorrelate）—— 无纹理/ECC 不收敛时的稳健回退。

    参数：
        prev/curr : (H, W) 灰度 float32/uint8（同尺寸）。
        mask      : 可选 bool/uint8，(H,W)，True=有效像素（小地图圆内）。
        angle_range/angle_step/max_shift : 兼容旧接口，纯平移实现忽略。

    返回：(0.0, (tu, tv), response)
        (tu, tv) : curr 相对 prev 的平移（像素）。统一语义：角色位移 d = -(tu, tv)。
        response : 置信度（ECC 系数或相位相关峰值，≈0~1，越大越可信）。

    小地图多是大块纯色背景 + 少量亮点，直接配准会被直流分量带偏，故两边都先减均值。
    """
    prev = np.asarray(prev, dtype=np.float32)
    curr = np.asarray(curr, dtype=np.float32)
    if prev.shape != curr.shape:
        raise ValueError("两帧小地图尺寸不一致")

    p = prev - float(prev.mean())
    c = curr - float(curr.mean())
    m8 = None
    if mask is not None:
        try:
            m8 = (np.asarray(mask) > 0).astype(np.uint8) * 255
        except Exception:
            m8 = None

    # —— 引擎 1：ECC（亚像素 + 光照不变 + 支持 mask）——
    if use_ecc:
        try:
            warp = np.eye(2, 3, dtype=np.float32)
            crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 50, 1e-5)
            cc, warp = cv2.findTransformECC(
                p, c, warp, cv2.MOTION_TRANSLATION, crit, m8, 5)
            tx = float(warp[0, 2])
            ty = float(warp[1, 2])
            # ECC 的 warp 把 curr 映射到 prev，其平移分量恰好就是
            # 「curr 相对 prev 的平移」——与本函数对相位相关的约定同义
            # （调用方统一按 d = -(tu,tv) 反推角色位移），故直接返回，不再取负。
            # 相关系数太低（几乎不相关）→ 不采用，退回相位相关。
            if float(cc) >= 0.3:
                return 0.0, (tx, ty), float(cc)
        except Exception:
            pass

    # —— 引擎 2：相位相关（回退）——
    try:
        (shift, resp) = cv2.phaseCorrelate(_window(p), _window(c))
    except Exception:
        return 0.0, (0.0, 0.0), 0.0
    return 0.0, (float(shift[0]), float(shift[1])), float(resp)


def _resize_center(img, r, size):
    """把 img 缩放 r 倍后，取【中心 size×size】；不足则边缘复制补齐。

    用于多尺度配准：统一到同一尺寸才能比较响应。
    """
    h, w = img.shape[:2]
    nw, nh = max(8, int(round(w * r))), max(8, int(round(h * r)))
    z = cv2.resize(img, (nw, nh), interpolation=(cv2.INTER_AREA if r < 1.0
                                                 else cv2.INTER_LINEAR))
    # 先补到不小于目标尺寸
    if nh < size or nw < size:
        py = max(0, size - nh)
        px = max(0, size - nw)
        z = cv2.copyMakeBorder(z, py // 2, py - py // 2, px // 2, px - px // 2,
                               cv2.BORDER_REPLICATE)
    h2, w2 = z.shape[:2]
    y0 = (h2 - size) // 2
    x0 = (w2 - size) // 2
    return z[y0:y0 + size, x0:x0 + size]


def estimate_motion_multiscale(prev, curr, ratios=None, use_ecc=True):
    """【多尺度配准】同时估计「缩放比 + 平移」——自适应小地图滚轮缩放。

    思路（缩放空间搜索，图像配准里的经典做法）：
      小地图是圆形，圆边/UI 会干扰配准，故只在【中心内接方形】上比较；
      对每个候选缩放比 r，把 curr 缩放 r 倍后与 prev 配准，取响应最高者。
      r < 1 → curr 里的地物比 prev 小（玩家把地图放大了）；
      r > 1 → curr 地物更大（地图缩小了）。

    返回 (r_best, resp_best, resp_at_1, (tu, tv))
        r_best    : 最优缩放比（1.0 = 与上一帧同倍率）
        resp_best : 该比例下的配准响应（0~1）
        resp_at_1 : r=1 时的响应（用于判断「是否真的变了倍率」）
        (tu, tv)  : 在 r_best 下的平移（minimap 像素）
    """
    prev = np.asarray(prev, dtype=np.float32)
    curr = np.asarray(curr, dtype=np.float32)
    if prev.shape != curr.shape:
        raise ValueError("两帧小地图尺寸不一致")
    h, w = prev.shape[:2]
    size = max(24, int(min(h, w) * 0.70))          # 中心内接方形
    y0, x0 = (h - size) // 2, (w - size) // 2
    A = prev[y0:y0 + size, x0:x0 + size]
    if ratios is None:
        ratios = [round(0.60 + 0.05 * i, 2) for i in range(22)]   # 0.60 ~ 1.65

    best_r, best_resp, best_t = 1.0, -1.0, (0.0, 0.0)
    resp_at_1 = 0.0
    for r in ratios:
        r = float(r)
        try:
            B = _resize_center(curr, r, size)
            _, t, resp = estimate_motion(A, B, use_ecc=use_ecc)
        except Exception:
            continue
        resp = float(resp)
        if abs(r - 1.0) < 1e-3:
            resp_at_1 = resp
        if resp > best_resp:
            best_r, best_resp, best_t = r, resp, (float(t[0]), float(t[1]))
    if resp_at_1 == 0.0:      # 候选里没有 1.0 时补测一次
        try:
            _, t1, r1 = estimate_motion(A, _resize_center(curr, 1.0, size),
                                        use_ecc=use_ecc)
            resp_at_1 = float(r1)
        except Exception:
            resp_at_1 = 0.0
    return best_r, best_resp, resp_at_1, best_t


def _seg_rect_param(a, b, rect):
    """Liang–Barsky：线段 a→b 落在矩形内的【参数区间】(t0,t1)；无交返回 None。

    用于「框选删除路线」：把一条折线按矩形挖掉中段，其余部分保留，
    这样被删区域的线会真正断开，而不是只删几个采样点、线还横穿过去。
    """
    x0, y0, x1, y1 = rect
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0
    ax, ay = float(a[0]), float(a[1])
    bx, by = float(b[0]), float(b[1])
    dx, dy = bx - ax, by - ay
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
        if abs(p) < 1e-12:
            if q < 0:
                return None          # 平行且在矩形外
            continue
        r = q / p
        if p < 0:
            if r > t1:
                return None
            if r > t0:
                t0 = r
        else:
            if r < t0:
                return None
            if r < t1:
                t1 = r
    if t0 > t1:
        return None
    return (t0, t1)


def _motion_to_pose(pose0, delta_deg, t, scale=1.0):
    """由配准结果更新角色 pose。小地图固定朝北 → 角色位移 d = -t，朝向不变。

    scale: 每小地图像素代表多少【世界单位】（小地图滚轮缩放后会变）。
    返回新 pose (x, y, theta_deg)。
    """
    x0, y0, th0 = pose0
    return (x0 - float(t[0]) * float(scale),
            y0 - float(t[1]) * float(scale), float(th0))


# =========================================================================
# A* 网格寻路
# =========================================================================

def astar_path(start, goal, blocked, bounds=None, prefer=None, domain=None,
               max_nodes=20000, cancel=None):
    """A* 8 邻域寻路。

    start/goal : (gx, gy) 整数格。
    blocked    : set[(gx,gy)] 不可走格子。
    bounds     : (min_gx, min_gy, max_gx, max_gy) 或 None（不设限）。
    prefer     : set[(gx,gy)] 优先走的格子（走它代价打折）。
    domain     : set[(gx,gy)] 可行域（只允许在这些格子里走）。回原点时传
                 「已探索格子」即可实现「沿来路回家」，未知格子一律当墙。
    max_nodes  : 展开节点上限（防死循环/爆炸）。

    返回：[(gx,gy), ...] 从 start 到 goal 的路径（含两端），找不到返回 None。
    """
    start = (int(start[0]), int(start[1]))
    goal = (int(goal[0]), int(goal[1]))

    def h(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def in_bounds(g):
        if bounds is None:
            return True
        return (bounds[0] <= g[0] <= bounds[2]
                and bounds[1] <= g[1] <= bounds[3])

    def allowed(g):
        if g in blocked:
            return False
        if domain is not None and g not in domain:
            return False
        return in_bounds(g)

    if not allowed(start) or not allowed(goal):
        return None
    if start == goal:
        return [start]

    # 8 邻域
    neigh = [(-1, -1), (0, -1), (1, -1), (-1, 0),
             (1, 0), (-1, 1), (0, 1), (1, 1)]
    cost_diag = math.sqrt(2)

    openq = []
    gscore = {start: 0.0}
    came = {}
    seq = 0
    heapq.heappush(openq, (h(start, goal), seq, start))
    closed = set()
    best_node = start
    best_h = h(start, goal)

    while openq:
        if cancel is not None and cancel():
            return None
        f, _seq, cur = heapq.heappop(openq)
        if cur == goal:
            path = [cur]
            while cur in came:
                cur = came[cur]
                path.append(cur)
            path.reverse()
            return path
        if cur in closed:
            continue
        closed.add(cur)
        if len(closed) > max_nodes:
            break
        cx, cy = cur
        for dx, dy in neigh:
            nxt = (cx + dx, cy + dy)
            if nxt in closed or not allowed(nxt):
                continue
            if dx and dy and (not allowed((cx + dx, cy)) or not allowed((cx, cy + dy))):
                continue  # 禁止斜穿禁区拐角
            step = cost_diag if dx != 0 and dy != 0 else 1.0
            if prefer and nxt in prefer:
                step *= 0.5          # 已探索格子打折，优先走安全路
            g = gscore[cur] + step
            if nxt not in gscore or g < gscore[nxt]:
                gscore[nxt] = g
                came[nxt] = cur
                hn = h(nxt, goal)
                if hn < best_h:
                    best_h, best_node = hn, nxt
                seq += 1
                heapq.heappush(openq, (g + hn, seq, nxt))

    return None


# =========================================================================
# 世界追踪器（小地图图像拼接 + 回原点 + 自制地图）
# =========================================================================

def _locked_map(method):
    """手动定位与后台配准/贴图互斥，避免新位置被旧帧覆盖。"""
    @wraps(method)
    def call(self, *args, **kwargs):
        with self._state_lock:
            return method(self, *args, **kwargs)
    return call


class WorldTracker:
    """维护「角色在世界上的 pose」、**拼接小地图图像**、规划路径。

    用法（调用方每帧）：
        tr = WorldTracker(cell_px=40.0)
        tr.set_origin()                       # 标记挂机点（= 当前位置）
        m = <抓取小地图方形灰度图>
        tr.update(m, response_min=0.05)       # 配准并更新 pose
        tr.add_minimap_image(<小地图彩色方形>)  # 按 pose 贴到拼接画布（自制地图）
        path = tr.plan_home()                 # A* 回原点路径（世界格）
        img = tr.stitch_image()               # 取拼接出来的地图图像

    pose 的世界单位 = 小地图像素（×cell_px 得到「格」用于 A*）。
    拼接画布：世界坐标 (wx,wy) → 画布像素 (S/2 + wx*scale, S/2 + wy*scale)，
    画布中心 = 世界原点；小地图固定朝北 → 图像可直接按平移贴上，无需旋转。
    """

    def __init__(self, cell_px=40.0, stitch_size=768, stitch_scale=1.0):
        self._state_lock = threading.RLock()
        self.load_point = None              # 用户手动选定的地图加载点
        self.position_revision = 0          # 丢弃手动定位前排队的旧画面
        self.trail_breaks = []               # 新轨迹起始下标（重定位不连跳跃线）
        self.cell_px = float(cell_px) or 40.0
        self.pose = (0.0, 0.0, 0.0)          # (x, y, theta_deg)
        self.origin = (0.0, 0.0)             # 挂机点（世界像素）
        self.prev_minimap = None             # 上一帧小地图（灰度）
        self.prev_key = None                 # 上一帧姿态（用于拒绝低置信）
        # —— 小地图缩放自适应（滚轮缩放会让「每小地图像素 = 多少世界单位」变化）——
        self.mm_scale = 1.0                  # 世界单位 / 小地图像素（世界坐标基准）
        self.auto_mm_scale = False           # 自动跟随小地图滚轮缩放（默认关，详见 _tick_scale_check）
        self.mm_scale_min = 0.15             # 允许的缩放范围（防跑飞）
        self.mm_scale_max = 6.0
        self.scale_check_every = 6           # 每隔多少帧做一次多尺度检测（≈0.20s@30fps）
        self.scale_margin = 0.10             # 新比例响应至少高出这么多才认（>resp@1）
        self.scale_confirm = 2               # 连续确认次数（约 12 帧 ≈ 0.4s 响应）
        self.scale_min_stable = 0.55         # 「同倍率」判定：r≈1 且响应不低于此值
        self.scale_min_candidate = 0.70      # 「倍率变了」判定：候选响应不低于此值
        self.scale_r_tol = 0.05             # 「同倍率」判定：r 偏离 1.0 在此以内
        self.scale_resp1_ok = 0.55           # resp@1 ≥ 此值 → 当前倍率还能配上，绝不改比例
        self.scale_ref_max_age = 40          # 参考帧最多用多少轮（走远后换锚）
        self._scale_tick = 0                 # 帧计数
        self._scale_ref = None               # 缩放检测的【参考帧】（锚定用）
        self._scale_ref_age = 0              # 参考帧年龄（检测轮次）
        self._scale_votes = []               # 连续投票
        self.last_mm_ratio = 1.0             # 最近一次检测到的缩放比（诊断）
        self.mm_scale_samples = 0            # 已确认的缩放调整次数
        self.explored = set()                # 已探索的世界格 {(gx,gy), ...}
        self.trail = []                      # 轨迹（世界像素，抽样）
        self._trail_last = None
        self.dots = {}                       # 发现的怪点 {(gx,gy): (wx,wy)}
        self.targets = {}                    # 用户目标点 {name: (wx,wy)}
        # —— 小地图图像拼接（自制地图）——
        self.stitch_size = max(128, int(stitch_size))   # 画布边长（像素）
        self.stitch_scale = float(stitch_scale) or 1.0  # 世界像素 → 画布像素
        self.canvas_sum = None               # 拼接画布加权累加（float32，BGR）
        self.canvas_wsum = None              # 拼接画布权重和（羽化权重，每像素）
        self.stitch_hits = 0                 # 已贴图帧数
        self.last_resp = 0.0                 # 最近一次配准响应（诊断用）
        # —— 拼接查重（"发现小地图动才拼接"）——
        self.stitch_dedup = True             # 查重开关（置 False 等于旧行为）
        self.stitch_min_step = 1.5           # 位移闸门（世界像素）：不足此值不重复贴
        self.stitch_skipped = 0              # 被查重跳过的帧数（省下的融合次数）
        self.stitch_dropped = 0              # 因「位移太大/重合太少」被裁剪丢弃的帧数
        self.stitch_dup_overlap = 0.97       # 重合率 ≥ 此值 → 完全重合，跳过
        self.stitch_min_overlap = 0.10       # 重合率 ≤ 此值 → 移动太大（跳变），裁剪丢弃
        self.stitch_dup_match = 0.90         # 像素级重合率 ≥ 此值 → 重复帧，跳过
        self.stitch_recover_after = 3        # 连续丢弃这么多次后强制贴一帧（防地图卡死）
        self._drop_streak = 0                # 当前连续丢弃次数
        self._last_tile_small = None         # 上一帧贴图（降采样，用于像素级重合率比对）
        # —— 分块保存（先把每帧切片单独落盘，再拼接；可事后剔除错误块并重拼）——
        self.tiles_dir = None                # 分块目录（None = 未启用）
        self.save_tiles = False              # 是否边拼边存分块
        self.tiles = []                      # [{id,file,pose,scale,r,ts}]
        self.tile_seq = 0                    # 分块序号
        self.tile_deleted = set()            # 已删除的块 id（重拼时跳过）
        self.tiles_saved = 0                 # 累计保存块数
        # —— 框选删除路线：被删矩形（蓝图在这些区域内断开不画）——
        self.trail_cuts = []
        # —— 删除黑名单：这些世界矩形【永久不再被贴图】（否则会被重新拼回来）——
        self.map_blackouts = []
        # —— 手绘路线：「画路线」按钮手动点的折线（世界点串），与自动轨迹分开存 ——
        self.drawn_paths = []
        # —— 区域限制（地图上设置/手画）——
        # fence_center / fence_r : 限制区域圆。右键菜单「设置范围中心」后，
        #   左键拖动生成虚线圆；走出圆后回到圈内缓冲位置。
        # zones_forbidden : 禁区多边形列表 [[[x,y],...], ...]（任意形状自由绘制）。
        #   落进禁区立即触发回归；回归路径 A* 把禁区格子当墙绕开。
        self.fence_center = None            # (x, y) 世界坐标 / None=未设置
        self.fence_r = 0.0                  # 限制圆半径（世界px）
        self.zones_forbidden = []
        self._forb_blocked = None           # 禁区占用寻路格缓存 {(gx,gy),...}
        self.last_overlap = None             # 最近一次几何重合率（诊断）
        self.last_match = None               # 最近一次像素重合率（诊断）
        self._last_stitch_pose = None        # 上次真正贴图时的 pose
        self._cover = None                   # 低分辨率覆盖栅格（查重②）
        self._cover_cell = 8                 # 覆盖栅格粒度（画布像素）
        self._w_map_cache = {}               # 羽化权重图缓存 {(h,w): ndarray}
        self._render_cache = None            # 渲染结果缓存（uint8）
        self._render_cache_key = None        # 缓存对应的 disp
        self._render_dirty = True            # 画布有新增 → 需要重算渲染
        # —— 步长 ↔ 小地图像素 关系自优化 ——
        self.px_per_step = None              # 学到的比例：小地图位移px / 点击步长px
        self.step_samples = 0                # 已累计的观测样本数
        self.step_ema_alpha = 0.25           # EMA 平滑系数（新样本权重）
        self._mark_explored(0.0, 0.0)
        self._append_trail(0.0, 0.0)

    # ---------- 小地图缩放自适应（滚轮缩放） ----------
    def _tick_scale_check(self, curr, disp=None):
        """检测小地图缩放：与【参考帧】做多尺度配准，连续确认后调整 mm_scale。

        **默认关闭** (auto_mm_scale=False)。原因：
          多尺度配准对「内容缩放」十分鲁棒（算法本身就抗尺度变化），
          1.2x 真实缩放下 resp_1 也能有 0.7+（不是 0.0），r 值在多次检测间
          会从 1.6 跳回 1.0，单帧级投票永远凑不齐 2 票；同时 resp_best
          又接近上限（>1.0），反而把"resp_1 低=缩放"的旧判据打穿。
          结论：自动检测在这个场景下不能稳定工作 → 默认关，让用户手动调。
        用户在配置面板里勾上"自动缩放"才会走下面的检测逻辑。

        何时仍需要自动检测：
          训练期玩家会频繁滚轮缩放小地图（看远看近），希望程序自适应；
          但前提是检测必须稳定 —— 现版本做不到，先关掉。
        """
        if not getattr(self, "auto_mm_scale", False):
            return
        every = max(1, int(self.scale_check_every))
        self._scale_tick += 1
        if self._scale_tick % every != 0:
            return
        # 大位移时「平移/缩放」混淆 → 跳过本轮，避免把移动误判成缩放
        if disp is not None:
            try:
                h, w = curr.shape[:2]
                if math.hypot(float(disp[0]), float(disp[1])) > 0.5 * min(h, w):
                    self._scale_votes.clear()
                    return
            except Exception:
                pass
        ref = self._scale_ref
        if ref is None or ref.shape != curr.shape:
            self._scale_ref, self._scale_ref_age = curr, 0
            self._scale_votes.clear()
            return
        try:
            r, resp_best, resp_1, _t = estimate_motion_multiscale(ref, curr)
        except Exception:
            return
        self.last_mm_ratio = float(r)
        need = max(2, int(self.scale_confirm))

        # 【主判据】看「最优比例 r 偏离 1.0 的绝对幅度」——而不是 resp@1。
        #    多尺度配准对内容缩放鲁棒（算法本抗尺度变化），
        #    即便真实发生 1.2x 缩放，resp_1 也能有 0.7+（不是 0.0）；
        #    所以 "resp_1 跌得多 = 缩放" 在这套算法下不可靠。
        #    真正稳定的信号是「最优比值 r」：真发生缩放时，多尺度搜索
        #    一定在某个 r!=1.0 处取得明显优于 r=1.0 的响应。
        abs_dev = abs(r - 1.0)

        # 同倍率：r 几乎==1 且响应够高 → 刷新锚，不投
        if abs_dev < float(self.scale_r_tol) and resp_best >= float(self.scale_resp1_ok):
            self._scale_ref, self._scale_ref_age = curr, 0
            self._scale_votes.clear()
            return

        # 显然变了倍率：r 明显!=1，候选响应够强，且明显优于 r=1 → 投票
        if (abs_dev >= 0.08
                and resp_best >= float(self.scale_min_candidate)
                and (resp_best - resp_1) >= float(self.scale_margin)):
            self._scale_votes.append(float(r))
        else:
            self._scale_votes.clear()
        # ③ 参考帧太旧（走远/一直不匹配）→ 换锚重来
        self._scale_ref_age += 1
        if self._scale_ref_age > int(self.scale_ref_max_age):
            self._scale_ref, self._scale_ref_age = curr, 0
            self._scale_votes.clear()
            return

        if len(self._scale_votes) < need:
            return
        rs = self._scale_votes[-need:]
        if max(rs) - min(rs) > 0.08:        # 投票不一致 → 丢弃重来
            self._scale_votes.clear()
            return
        rm = sum(rs) / float(len(rs))
        # ③ 单次调整幅度限制：一次最多 ±35%（防连续误调把比例越拉越偏）
        if not (1.0 / 1.35 <= rm <= 1.35):
            self._scale_votes.clear()
            return
        new = float(self.mm_scale) * rm
        if not (self.mm_scale_min <= new <= self.mm_scale_max):
            self._scale_votes.clear()
            return
        self.mm_scale = new
        self.mm_scale_samples += 1
        self._scale_votes.clear()
        self._scale_ref, self._scale_ref_age = curr, 0
        self.prev_minimap = None            # 比例已变，上一帧不再可比
        self._render_dirty = True

    def set_minimap_scale(self, scale):
        """手动设置「世界单位/小地图像素」（校准用）。返回是否设置成功。"""
        try:
            s = float(scale)
        except (TypeError, ValueError):
            return False
        if not (self.mm_scale_min <= s <= self.mm_scale_max):
            return False
        self.mm_scale = s
        self.prev_minimap = None
        self._scale_ref, self._scale_ref_age = None, 0
        self._scale_votes.clear()
        self._render_dirty = True
        return True

    def trail_simplified(self, eps=None, points=None):
        """轨迹【拐角连线】简化（Ramer–Douglas–Peucker，cv2.approxPolyDP）。

        原始轨迹是逐格采样，同一处来回走会糊成一团密集线；RDP 保留拐角、
        去掉共线中间点 → 只连拐角，线条干净且形状不失真。
        eps 默认 = 0.6 格（世界像素）。
        """
        pts = self.trail if points is None else points
        if not pts or len(pts) < 3:
            return [list(p) for p in pts]
        e = float(eps) if eps else max(1.0, self.cell_px * 0.6)
        try:
            arr = np.asarray(pts, dtype=np.float32).reshape(-1, 1, 2)
            ap = cv2.approxPolyDP(arr, e, False)
            out = [(float(p[0][0]), float(p[0][1])) for p in ap]
            # approxPolyDP 有时会丢首尾，补回来
            if out and math.hypot(out[0][0] - pts[0][0],
                                  out[0][1] - pts[0][1]) > e:
                out.insert(0, (float(pts[0][0]), float(pts[0][1])))
            if out and math.hypot(out[-1][0] - pts[-1][0],
                                  out[-1][1] - pts[-1][1]) > e:
                out.append((float(pts[-1][0]), float(pts[-1][1])))
            return [list(p) for p in out] if len(out) >= 2 else [list(p) for p in pts]
        except Exception:
            return [list(p) for p in pts]

    def trail_segments(self, eps=None):
        """轨迹【拐角连线】后再按「已删矩形」裁断 → 返回多段可见折线。

        关键：框选删除的是【线】，不只是采样点。若只删点在 RDP 简化后
        两侧拐角仍会被连起来、线照样横穿被删区域；这里用 Liang–Barsky
        把每条线段在矩形内的部分挖掉，框内断开、框外保留。
        返回 [[[x,y], ...], ...]（可能为空 / 单段）。
        """
        ends = [0] + sorted({i for i in self.trail_breaks if 0 < i < len(self.trail)}) + [len(self.trail)]
        out = []
        for start, end in zip(ends, ends[1:]):
            base = self.trail_simplified(eps, self.trail[start:end])
            out.extend(self._clip_trail_segment(base))
        return out

    def _clip_trail_segment(self, base):
        """裁断一条连续轨迹，不跨越手动定位的断点。"""
        if len(base) < 2:
            return []
        cuts = [tuple(r) for r in (self.trail_cuts or []) if len(r) == 4]
        for r in (self.map_blackouts or []):
            if len(r) == 4 and tuple(r) not in cuts:
                cuts.append(tuple(r))
        if not cuts:
            return [list(base)]
        out = []
        for k in range(len(base) - 1):
            a = (float(base[k][0]), float(base[k][1]))
            b = (float(base[k + 1][0]), float(base[k + 1][1]))
            spans = []
            for rect in cuts:
                sp = _seg_rect_param(a, b, rect)
                if sp and sp[1] > sp[0]:
                    spans.append(sp)
            if not spans:
                out.append([a, b])
                continue
            spans.sort()
            merged = []
            for s0, s1 in spans:
                s0 = max(0.0, min(1.0, s0))
                s1 = max(0.0, min(1.0, s1))
                if merged and s0 <= merged[-1][1] + 1e-9:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], s1))
                else:
                    merged.append((s0, s1))

            def _pt(t):
                return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]

            tcur = 0.0
            for s0, s1 in merged:
                if s0 > tcur + 1e-9:
                    out.append([_pt(tcur), _pt(s0)])
                tcur = max(tcur, s1)
            if tcur < 1.0 - 1e-9:
                out.append([_pt(tcur), _pt(1.0)])
        # 相邻子段若首尾相接 → 合并回一条折线（少画几段，看着更顺）
        merged_segs = []
        for seg in out:
            if (merged_segs and seg
                    and abs(merged_segs[-1][-1][0] - seg[0][0]) < 1e-6
                    and abs(merged_segs[-1][-1][1] - seg[0][1]) < 1e-6):
                merged_segs[-1].extend(seg[1:])
            else:
                merged_segs.append([list(p) for p in seg])
        # 丢掉零长段
        return [s for s in merged_segs
                if len(s) >= 2 and math.hypot(s[0][0] - s[-1][0],
                                              s[0][1] - s[-1][1]) > 1e-6]

    def clear_trail_cuts(self):
        """清空所有「框选删除」记录（路线裁断 + 贴图黑名单）。返回清掉的数量。"""
        n = len(self.trail_cuts or []) + len(self.map_blackouts or [])
        self.trail_cuts = []
        self.map_blackouts = []
        self._render_dirty = True
        return n

    # 语义更清晰的名字（旧名保留兼容）
    clear_erasures = clear_trail_cuts

    # ---------- 手绘路线（「画路线」按钮） ----------
    def add_drawn_path(self, points):
        """加入一条手绘路线（世界点串）。点数 < 2 时忽略。返回是否成功。"""
        try:
            pts = [[float(p[0]), float(p[1])] for p in (points or [])
                   if p is not None and len(p) >= 2]
        except Exception:
            return False
        if len(pts) < 2:
            return False
        self.drawn_paths.append(pts)
        self._render_dirty = True
        return True

    def remove_drawn_path(self, idx):
        """删除第 idx 条手绘路线。"""
        try:
            i = int(idx)
        except (TypeError, ValueError):
            return False
        if 0 <= i < len(self.drawn_paths):
            self.drawn_paths.pop(i)
            self._render_dirty = True
            return True
        return False

    def clear_drawn_paths(self):
        """清空全部手绘路线。返回清掉的数量。"""
        n = len(self.drawn_paths or [])
        self.drawn_paths = []
        self._render_dirty = True
        return n

    # ---------- 区域限制（限制圆 + 禁区多边形） ----------
    def set_fence(self, cx, cy, r):
        """设置限制区域圆（范围中心 + 半径，世界px）。r<=0 时只记中心不圈范围。"""
        self.fence_center = (float(cx), float(cy))
        self.fence_r = max(0.0, float(r))
        self._forb_blocked = None
        self._render_dirty = True
        return True

    def add_forbidden(self, pts):
        """添加禁区多边形（任意形状）。pts: [(x,y),...] 世界坐标，>=3 个点。"""
        poly = [[float(p[0]), float(p[1])] for p in (pts or [])
                if p is not None and len(p) >= 2]
        if len(poly) < 3:
            return False
        self.zones_forbidden.append(poly)
        self._forb_blocked = None
        self._render_dirty = True
        return True

    def clear_zones(self):
        """清空限制圆 + 全部禁区。返回清掉的数量。"""
        n = (1 if self.fence_center is not None else 0) + len(self.zones_forbidden)
        self.fence_center = None
        self.fence_r = 0.0
        self.zones_forbidden = []
        self._forb_blocked = None
        self._render_dirty = True
        return n

    @staticmethod
    def _pip(x, y, poly):
        """射线法：点是否在多边形内。"""
        inside = False
        j = len(poly) - 1
        for i in range(len(poly)):
            xi, yi = poly[i][0], poly[i][1]
            xj, yj = poly[j][0], poly[j][1]
            if ((yi > y) != (yj > y)) and \
                    (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi):
                inside = not inside
            j = i
        return inside

    def hit_zone(self, x, y):
        """光标处命中检测。返回 ("fence", None) / ("poly", i) / None（供右键删除）。"""
        x, y = float(x), float(y)
        for i, poly in enumerate(self.zones_forbidden):
            if self._pip(x, y, poly):
                return ("poly", i)
        if self.fence_center is not None and self.fence_r > 0:
            if math.hypot(x - self.fence_center[0], y - self.fence_center[1]) <= self.fence_r:
                return ("fence", None)
        return None

    def effective_fence(self, fallback_r=0.0):
        """统一圆形区域：指定中心优先，否则原点；半径使用同一世界单位。"""
        center = self.fence_center if self.fence_center is not None else self.origin
        radius = self.fence_r if self.fence_r > 0 else float(fallback_r or 0.0)
        return (float(center[0]), float(center[1])), max(0.0, radius)

    def zone_status(self, x=None, y=None, fallback_r=0.0, margin=0.0):
        """禁区优先；出圈返回圈内缓冲点，dist_back 始终是到目标的真实距离。"""
        if x is None or y is None:
            x, y = self.pose[:2]
        x, y = float(x), float(y)
        (cx, cy), radius = self.effective_fence(fallback_r)
        limit = max(0.0, radius - max(0.0, float(margin)))
        forbidden = any(self._pip(x, y, poly) for poly in self.zones_forbidden)
        distance = math.hypot(x - cx, y - cy)
        outside = radius > 0 and distance > limit
        if not forbidden and not outside:
            return {"ok": True, "reason": None, "target": None, "dist_back": 0.0}
        # 回到圈内 15%（最多一格），避免停在边缘受配准误差反复触发。
        inset = min(radius * 0.15, self.cell_px) if radius > 0 else 0.0
        inner = max(0.0, limit - inset)
        k = inner / max(distance, 1e-9)
        target = (cx + (x - cx) * k, cy + (y - cy) * k) if outside else (cx, cy)
        def safe(p):
            return ((radius <= 0 or math.hypot(p[0] - cx, p[1] - cy) <= inner)
                    and not any(self._pip(*p, poly) for poly in self.zones_forbidden))
        if not safe(target) or forbidden:
            candidates = [(gx * self.cell_px, gy * self.cell_px) for gx, gy in self.explored]
            candidates.append(target)
            candidates = [p for p in candidates if safe(p)]
            target = min(candidates, key=lambda p: math.hypot(p[0] - x, p[1] - y)) if candidates else None
        return {"ok": False, "reason": "in_forbidden" if forbidden else "outside_fence",
                "target": target,
                "dist_back": math.hypot(target[0] - x, target[1] - y) if target else None}

    def _forbidden_blocked(self):
        """禁区占用的寻路格集合 {(gx,gy)}（A* 当墙绕行）。多边形栅格化 + 缓存。"""
        if self._forb_blocked is not None:
            return self._forb_blocked
        blocked = set()
        c = float(self.cell_px) or 40.0
        for poly in self.zones_forbidden:
            if len(poly) < 3:
                continue
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            gx0 = int(math.floor(min(xs) / c)) - 1
            gx1 = int(math.ceil(max(xs) / c)) + 1
            gy0 = int(math.floor(min(ys) / c)) - 1
            gy1 = int(math.ceil(max(ys) / c)) + 1
            w = gx1 - gx0 + 1
            h = gy1 - gy0 + 1
            if w <= 0 or h <= 0 or w * h > 4000000:
                continue
            filled = None
            try:
                import cv2 as _cv
                import numpy as _np
                # 多边形顶点 → 局部格坐标（1格=1像素），栅格化填充
                pts = _np.array([[(p[0] / c) - gx0, (p[1] / c) - gy0]
                                 for p in poly], dtype=_np.float32)
                mask = _np.zeros((h, w), _np.uint8)
                _cv.fillPoly(mask, [pts.astype(_np.int32)], 1)
                filled = set(zip((gx0 + int(v) for v in _np.nonzero(mask)[1]),
                                 (gy0 + int(v) for v in _np.nonzero(mask)[0])))
            except Exception:
                filled = None
            if filled is None:
                # 无 cv2 时退化为逐格中心点采样
                for gy in range(gy0, gy1 + 1):
                    for gx in range(gx0, gx1 + 1):
                        if self._pip(gx * c, gy * c, poly):
                            filled = filled or set()
                            filled.add((gx, gy))
            blocked |= filled or set()
        self._forb_blocked = blocked
        return blocked

    def erase_trail_rect(self, wx0, wy0, wx1, wy1):
        """【只删路线】：把矩形记入裁断（路线在该区域断开），不动贴图、不设黑名单。

        「删路线」按钮用：只处理路线，地图画面保持原样。返回新增的裁断矩形数。
        """
        x0, x1 = (wx0, wx1) if wx0 <= wx1 else (wx1, wx0)
        y0, y1 = (wy0, wy1) if wy0 <= wy1 else (wy1, wy0)
        for (rx0, ry0, rx1, ry1) in self.map_blackouts:
            if rx0 <= x0 and ry0 <= y0 and x1 <= rx1 and y1 <= ry1:
                return 0                      # 已被黑名单覆盖，无需再加
        self.trail_cuts.append([float(x0), float(y0), float(x1), float(y1)])
        self._render_dirty = True
        return 1

    def erase_image_rect(self, wx0, wy0, wx1, wy1):
        """【只删贴图】：把画布上该世界矩形内的像素擦掉，但【不入黑名单】——
        之后角色走过该区域时，新帧仍能正常贴上去（区别于"框选删除"的永久删除）。

        用于：拼错的局部画面 → 临时擦掉，等重新走过时自然刷新；不必重拼全图。
        画布未初始化时是 no-op（没东西可擦）。返回擦掉的画布像素面积。
        """
        x0, x1 = (wx0, wx1) if wx0 <= wx1 else (wx1, wx0)
        y0, y1 = (wy0, wy1) if wy0 <= wy1 else (wy1, wy0)
        if self.canvas_sum is None or self.canvas_wsum is None:
            return 0
        half = self.stitch_size / 2.0
        sc = float(self.stitch_scale)
        cx0 = int(max(0, min(self.stitch_size, half + x0 * sc)))
        cx1 = int(max(0, min(self.stitch_size, half + x1 * sc)))
        cy0 = int(max(0, min(self.stitch_size, half + y0 * sc)))
        cy1 = int(max(0, min(self.stitch_size, half + y1 * sc)))
        if cx1 <= cx0 or cy1 <= cy0:
            return 0
        self.canvas_sum[cy0:cy1, cx0:cx1] = 0.0
        self.canvas_wsum[cy0:cy1, cx0:cx1] = 0.0
        # 覆盖栅格：把这块标成"未覆盖"，让查重判定允许后续帧再来贴
        try:
            g = self._cover_grid()
            cell = float(self._cover_cell)
            gx0 = max(0, int(cx0 / cell))
            gx1 = min(g.shape[1], int(cx1 / cell) + 1)
            gy0 = max(0, int(cy0 / cell))
            gy1 = min(g.shape[0], int(cy1 / cell) + 1)
            if gx1 > gx0 and gy1 > gy0:
                g[gy0:gy1, gx0:gx1] = 0
        except Exception:
            self._cover = None
        self._render_dirty = True
        return (cx1 - cx0) * (cy1 - cy0)

    def clear_trail_cuts_only(self):
        """只清「路线裁断」（保留贴图黑名单）。返回清掉的数量。"""
        n = len(self.trail_cuts or [])
        self.trail_cuts = []
        self._render_dirty = True
        return n

    def content_bbox(self, pad=2.0):
        """内容包围盒（世界坐标）[x0,y0,x1,y1]：轨迹/怪点/目标/原点/角色。

        供 GUI 把自制地图【自动裁剪+缩放到界面范围内】——只框住真正有内容的部分，
        地图就不会一团黑、也不会跑出窗口。pad 单位=格。
        """
        xs, ys = [], []
        for x, y in self.trail:
            xs.append(x); ys.append(y)
        for x, y in self.dots.values():
            xs.append(x); ys.append(y)
        for x, y in self.targets.values():
            xs.append(x); ys.append(y)
        # 手绘路线也要框进来（否则可能被裁到画外）
        for path in (self.drawn_paths or []):
            for x, y in path:
                xs.append(x); ys.append(y)
        # 已删除区域（红框标记）也要可见
        for r in (self.map_blackouts or []):
            if len(r) == 4:
                xs.extend([r[0], r[2]]); ys.extend([r[1], r[3]])
        if self.load_point is not None:
            xs.append(self.load_point[0]); ys.append(self.load_point[1])
        xs.extend([self.pose[0], self.origin[0]])
        ys.extend([self.pose[1], self.origin[1]])
        if not xs:
            return None
        p = max(1.0, self.cell_px * float(pad or 0))
        return [min(xs) - p, min(ys) - p, max(xs) + p, max(ys) + p]

    # ---------- 原点 / 姿态 ----------
    def set_origin(self):
        """把「当前位置」记为挂机点原点。"""
        self.origin = (float(self.pose[0]), float(self.pose[1]))
        self._mark_explored(*self.origin)

    @_locked_map
    def set_position(self, wx, wy, remember=True):
        """将当前小地图中心对齐到指定世界点，保留已有地图/范围/原点。"""
        x, y = float(wx), float(wy)
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError("人物坐标必须为有限数值")
        if self.trail and len(self.trail) not in self.trail_breaks:
            self.trail_breaks.append(len(self.trail))
        self.pose = (x, y, self.pose[2])
        if remember:
            self.load_point = (x, y)
        self.position_revision += 1
        self.prev_minimap = None
        self.prev_key = None
        self._scale_ref, self._scale_ref_age = None, 0
        self._scale_votes.clear()
        self._scale_tick = 0
        self.last_resp = 0.0
        self._last_stitch_pose = None
        self._last_tile_small = None
        self._drop_streak = 0
        self._trail_last = None
        self._mark_explored(x, y)
        self._append_trail(x, y)
        self._render_dirty = True
        return self.pose

    @_locked_map
    def reset_pose(self):
        self.load_point = None
        self.position_revision += 1
        self.trail_breaks = []
        self.pose = (0.0, 0.0, 0.0)
        self.origin = (0.0, 0.0)
        self.prev_minimap = None
        self.explored = {(0, 0)}
        self.trail = []
        self.dots = {}
        self.targets = {}
        self._trail_last = None
        self.reset_canvas()
        self._append_trail(0.0, 0.0)

    # ---------- 格子换算 ----------
    def _to_cell(self, x, y):
        return (int(round(x / self.cell_px)), int(round(y / self.cell_px)))

    def _mark_explored(self, x, y):
        self.explored.add(self._to_cell(x, y))

    def _append_trail(self, wx, wy):
        """抽样记录轨迹点（间隔 >= 1 格才记，避免轨迹点爆炸）。

        落在【删除黑名单】区域内的点直接跳过：那块区域判定为错误，
        机器人再路过也不该把路线重新画回来。
        """
        for (rx0, ry0, rx1, ry1) in (self.map_blackouts or ()):
            if rx0 <= wx <= rx1 and ry0 <= wy <= ry1:
                return
        if self._trail_last is None or \
                math.hypot(wx - self._trail_last[0], wy - self._trail_last[1]) \
                >= self.cell_px:
            self.trail.append((float(wx), float(wy)))
            self._trail_last = (float(wx), float(wy))

    # ---------- 小地图图像拼接（自制地图） ----------
    def _ensure_canvas(self):
        if self.canvas_sum is None:
            n = self.stitch_size
            self.canvas_sum = np.zeros((n, n, 3), np.float32)
            self.canvas_wsum = np.zeros((n, n), np.float32)
        return self.canvas_sum

    @staticmethod
    def _erase_yellow_dots(bgr, r_min=180, g_min=140, b_max=100):
        """拼接前抹掉黄点（怪点）：黄色像素 = R高 G高 B低，用 inpaint 填充。

        黄点代表怪物位置，会污染地图背景；这里用周边像素填充掉，
        让拼接出来的地图只保留地形/道路。
        """
        try:
            b, g, r = (bgr[:, :, 0].astype(np.int16),
                       bgr[:, :, 1].astype(np.int16),
                       bgr[:, :, 2].astype(np.int16))
            yellow = (r >= r_min) & (g >= g_min) & (b <= b_max)
            if not yellow.any():
                return bgr
            # 膨胀一点，把黄点边缘也盖住
            kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            yellow = cv2.dilate(yellow.astype(np.uint8), kern).astype(bool)
            mask = yellow.astype(np.uint8) * 255
            return cv2.inpaint(bgr, mask, 3, cv2.INPAINT_TELEA)
        except Exception:
            return bgr

    def world_to_stitch(self, wx, wy):
        """世界坐标 → 拼接画布【原始像素】坐标。"""
        half = self.stitch_size / 2.0
        s = self.stitch_scale
        return (half + wx * s, half + wy * s)

    def stitch_to_world(self, sx, sy):
        """拼接画布【原始像素】坐标 → 世界坐标。"""
        half = self.stitch_size / 2.0
        s = self.stitch_scale
        return ((sx - half) / s, (sy - half) / s)

    @_locked_map
    def add_minimap_image(self, minimap_bgr, mask=None, feather=True,
                          force=False):
        """把一帧小地图按当前 pose 融合到拼接画布（自制地图）。

        **查重（"发现小地图动才拼接"）**：默认对每帧做两道闸门，跳过的帧直接返回
        False（不融合、不计入 stitch_hits，只累计 stitch_skipped）：
          ① 位移闸门 —— 与上次贴图的 pose 距离 < stitch_min_step（默认 1.5 世界
             像素）→ 画面没动，重复融合没有新信息（站桩打怪时占绝大多数帧）；
          ② 覆盖闸门 —— 这一帧的落点已被拼过的区域【完全覆盖】（低分辨率覆盖
             栅格判定）→ 贴上去也全是重复像素。
        需要强制贴（如测试/手动补图）时传 force=True 绕过两道闸门。

        小地图固定朝北 → 图像中心 = 角色 pose，图上像素 (u,v) 对应世界
        pose+(u,v)，可直接平移贴上（无旋转）。

        融合用**【羽化加权平均】**（feather blending，图像拼接里消除接缝的经典做法）：
          * 权重 = 距圆心越近越高、越靠圆边越低（w = 1-(d/r)²，留小底 0.05）——
            小地图中心最可信（圆边常受圆边框、图标、干扰影响），
            且相邻两帧重叠区按距离平滑过渡，接缝自然消失，
            不会出现"硬切"留下的亮暗条纹；
          * 分母是权重和（canvas_wsum），所以平均是按可信度加权，而非简单等权；
          * 圆外（mask=False）不写 → 圆外固定 UI 不会在画布上留碎片。
        返回是否贴上了。
        """
        if minimap_bgr is None or getattr(minimap_bgr, "size", 0) == 0:
            return False
        if getattr(minimap_bgr, "ndim", 0) != 3:
            return False
        self._ensure_canvas()
        # —— 忽略黄点：黄点（怪）会污染地图背景，拼接前用 inpaint 抹掉 ——
        minimap_bgr = self._erase_yellow_dots(minimap_bgr)
        # 小地图像素 → 画布像素 = 世界/小地图像素(mm_scale) × 世界/画布像素(stitch_scale)
        # 这样滚轮缩放小地图后，贴图尺寸自动跟着变，拼接不会错位。
        s = self.stitch_scale * float(self.mm_scale)
        h_m, w_m = minimap_bgr.shape[:2]
        if s != 1.0:
            img = cv2.resize(minimap_bgr,
                             (max(1, int(round(w_m * s))),
                              max(1, int(round(h_m * s)))))
            msk = None
            if mask is not None:
                msk = cv2.resize(mask.astype(np.uint8),
                                 (img.shape[1], img.shape[0]),
                                 interpolation=cv2.INTER_NEAREST).astype(bool)
        else:
            img = minimap_bgr
            msk = mask
        ih, iw = img.shape[:2]
        # —— 羽化权重图（以图中心=圆心为基准，半径取半宽）——
        w_map = None
        if feather and iw > 2 and ih > 2:
            # 羽化权重只跟尺寸有关 → 缓存复用（原本每帧都重算 ogrid+clip）
            _wk = (ih, iw)
            w_map = self._w_map_cache.get(_wk)
            if w_map is None:
                cxp, cyp = (iw - 1) / 2.0, (ih - 1) / 2.0
                r_px = max(1.0, min(iw, ih) / 2.0)
                yy, xx = np.ogrid[:ih, :iw]
                d2 = (xx - cxp) ** 2 + (yy - cyp) ** 2
                w_map = np.clip(1.0 - d2 / (r_px * r_px),
                                0.05, 1.0).astype(np.float32)
                if len(self._w_map_cache) >= 8:
                    self._w_map_cache.pop(next(iter(self._w_map_cache)))
                self._w_map_cache[_wk] = w_map
        # —— 查重①：位移闸门（画面没动就不重复融合）——
        px, py = self.pose[0], self.pose[1]
        if not force and self.stitch_dedup:
            lp = self._last_stitch_pose
            if lp is not None and \
                    math.hypot(px - lp[0], py - lp[1]) < self.stitch_min_step:
                self.stitch_skipped += 1
                return False
        half = self.stitch_size // 2
        # 小地图左上角在画布上的位置（图中心 = 角色位置）
        # 世界→画布用 stitch_scale；图像自身尺寸已按 s 缩放，故偏移用 (w_m/2)*s
        sc = float(self.stitch_scale)
        x0 = int(round(half + px * sc - (w_m / 2.0) * s))
        y0 = int(round(half + py * sc - (h_m / 2.0) * s))
        # 与画布求交（超出部分裁剪）
        cx0, cy0 = max(0, x0), max(0, y0)
        cx1 = min(self.stitch_size, x0 + iw)
        cy1 = min(self.stitch_size, y0 + ih)
        if cx1 <= cx0 or cy1 <= cy0:
            # 落点【完全在画布外】：位移太大（走太远/传送）→ 裁剪丢弃。
            # 画布固定以世界原点为中心，走出去就出界；GUI 会通过
            # to_map()["out_of_canvas"] 提示把 stitch_size 调大。
            if not force:
                self.stitch_dropped += 1
                self._drop_streak += 1
                self.last_overlap = 0.0
            return False
        sx0, sy0 = cx0 - x0, cy0 - y0
        src = img[sy0:sy0 + (cy1 - cy0), sx0:sx0 + (cx1 - cx0)]
        s_hm, s_wm = src.shape[:2]
        # 有效区域权重：羽化 × 圆内 mask
        w_eff = None
        if w_map is not None:
            w_eff = w_map[sy0:sy0 + s_hm, sx0:sx0 + s_wm].copy()
        if msk is not None:
            s_msk = msk[sy0:sy0 + s_hm, sx0:sx0 + s_wm]
            if w_eff is None:
                w_eff = s_msk.astype(np.float32)
            else:
                w_eff = w_eff * s_msk.astype(np.float32)
        # —— 删除黑名单：被「框选删除」判定为错误的区域【不再往里贴图】——
        # 否则机器人继续跑动时会把删掉的画面又拼回来，看起来像"删不掉"。
        if w_eff is not None and self.map_blackouts:
            killed = False
            for (rx0, ry0, rx1, ry1) in self.map_blackouts:
                bx0 = int(max(0, min(iw, round((rx0 - px) / s + iw / 2.0))))
                bx1 = int(max(0, min(iw, round((rx1 - px) / s + iw / 2.0))))
                by0 = int(max(0, min(ih, round((ry0 - py) / s + ih / 2.0))))
                by1 = int(max(0, min(ih, round((ry1 - py) / s + ih / 2.0))))
                if bx1 > bx0 and by1 > by0:
                    w_eff[by0:by1, bx0:bx1] = 0.0
                    killed = True
            if killed and float(w_eff.max()) <= 0.0:
                if not force:
                    self.stitch_skipped += 1
                    return False
        # —— 查重②：重合率判据（边拼接边算「与已拼区域的重合率」）——
        #   几何重合率 = 落点里【已经拼过】的比例（覆盖栅格，O(格数)）：
        #     ≥ stitch_dup_overlap(0.97) → 完全重合，跳过（重复帧）；
        #     ≤ stitch_min_overlap(0.10) → 位移太大/配准跳变，【裁剪丢弃】——
        #        这种帧贴上去只会给地图拉出一条错位碎片；
        #     中间区间 → 再算【像素级重合率】（与上一帧贴图的降采样图比对），
        #         ≥ stitch_dup_match(0.90) 说明画面几乎一模一样 → 也跳过。
        #   连续丢弃 stitch_recover_after 次后强制贴一帧：防止一次大跳跃
        #   （传送/复活/换图）后新旧区域零重合、导致地图永远接不上。
        if not force and self.stitch_dedup and self.stitch_hits > 0:
            ov = self._footprint_overlap(cx0, cy0, cx1, cy1)
            self.last_overlap = ov
            if ov >= self.stitch_dup_overlap:
                self.stitch_skipped += 1
                return False
            if ov <= self.stitch_min_overlap:
                self._drop_streak += 1
                if self._drop_streak < max(1, int(self.stitch_recover_after)):
                    self.stitch_dropped += 1
                    return False
                # 连续多次零重合 → 认定为「大跳跃」，强制接上图（并保留提示标记）
                self._drop_streak = 0
            # 像素级「重合区一致率」只作【诊断】记录，不参与跳过决策：
            # 世界静止时，按位移对齐后的重叠区本来就该一致（这正是配准正确的证明），
            # 而边缘那条新露出的一小条才是要贴的新内容 —— 若拿它当"重复"跳过，
            # 正常移动就永远贴不上新区域（回归用例实测踩到）。跳过只由上面的
            # 几何重合率（完全重合 / 重合太少）决定。
            self.last_match = self._content_match_ratio(img, x0, y0)
        try:
            src_f = src.astype(np.float32)
            if w_eff is None:
                self.canvas_sum[cy0:cy1, cx0:cx1] += src_f
                self.canvas_wsum[cy0:cy1, cx0:cx1] += 1.0
            else:
                self.canvas_sum[cy0:cy1, cx0:cx1] += src_f * w_eff[:, :, None]
                self.canvas_wsum[cy0:cy1, cx0:cx1] += w_eff
        except Exception:
            return False
        # 贴图成功：更新查重状态 + 渲染缓存失效
        self._mark_cover(cx0, cy0, cx1, cy1)
        self._last_stitch_pose = (px, py)
        self._render_dirty = True
        self._drop_streak = 0
        # 留一份降采样副本，供下一帧算「像素级完全重合率」
        try:
            self._last_tile_small = cv2.resize(
                src, (32, 32), interpolation=cv2.INTER_AREA)
        except Exception:
            self._last_tile_small = None
        # 贴图成功：先把这一帧【分割保存】成独立分块（供事后剔除/重拼），再更新状态
        try:
            self._save_tile(img, msk, (px, py), s / float(self.stitch_scale or 1.0))
        except Exception:
            pass
        self.stitch_hits += 1
        return True

    # ---------- 分块保存（先分割保存每帧切片，再拼接；可事后剔除/重拼） ----------
    def set_tiles_dir(self, dirpath, enable=True):
        """启用/关闭分块保存：每帧小地图切片单独落盘，供事后剔除错误块并重拼。

        目录下 `index.json` 记录每块的 id / 文件 / 位置 / 缩放 / 半径。
        返回是否成功启用。
        """
        if not dirpath:
            self.save_tiles = False
            return False
        try:
            os.makedirs(dirpath, exist_ok=True)
        except Exception:
            self.save_tiles = False
            return False
        self.tiles_dir = dirpath
        self.save_tiles = bool(enable)
        # 载入已有分块索引（接着存 / 可重拼）
        idx_path = os.path.join(dirpath, "index.json")
        if os.path.isfile(idx_path):
            try:
                import json
                with open(idx_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                tls = raw.get("tiles") if isinstance(raw, dict) else raw
                if isinstance(tls, list):
                    self.tiles = [t for t in tls if isinstance(t, dict)]
                    ids = [int(t.get("id", -1)) for t in self.tiles]
                    self.tile_seq = (max(ids) + 1) if ids else 0
            except Exception:
                pass
        return True

    def _save_tiles_index(self):
        if not self.tiles_dir:
            return False
        try:
            import json
            with open(os.path.join(self.tiles_dir, "index.json"), "w",
                      encoding="utf-8") as f:
                json.dump({"tiles": self.tiles,
                           "deleted": sorted(self.tile_deleted)},
                          f, ensure_ascii=False, indent=1)
            return True
        except Exception:
            return False

    def _save_tile(self, img, msk, pose, scale):
        """把这一帧切片单独落盘（分割保存）。返回块记录或 None。"""
        if not (self.save_tiles and self.tiles_dir):
            return None
        try:
            tid = int(self.tile_seq)
            fn = "t%06d.png" % tid
            p = os.path.join(self.tiles_dir, fn)
            out = img
            if msk is not None:                 # 圆外置黑，不让圆外 UI 进片
                out = img.copy()
                out[~np.asarray(msk).astype(bool)] = 0
            if not cv2.imwrite(p, out):
                return None
            # 圆半径（保存图像素）：由 mask 反推；无 mask 则用半宽（等价不裁）
            r = float(min(img.shape[0], img.shape[1])) / 2.0
            if msk is not None:
                try:
                    yy, xx = np.where(np.asarray(msk).astype(bool))
                    if len(xx):
                        r = float(max(xx.max() - xx.min(),
                                      yy.max() - yy.min())) / 2.0 + 1.0
                except Exception:
                    pass
            rec = {"id": tid, "file": fn,
                   "pose": [float(pose[0]), float(pose[1])],
                   "scale": float(scale), "r": r,
                   "ts": float(time.time())}
            self.tiles.append(rec)
            self.tile_seq = tid + 1
            self.tiles_saved += 1
            self._save_tiles_index()
            return rec
        except Exception:
            return None

    def tiles_info(self):
        """分块统计（供界面显示）。"""
        n = len(self.tiles)
        dele = len([t for t in self.tiles if int(t.get("id", -1)) in self.tile_deleted])
        return {"total": n, "deleted": dele, "kept": n - dele,
                "saved": int(getattr(self, "tiles_saved", 0)),
                "dir": self.tiles_dir or "",
                "enabled": bool(self.save_tiles)}

    def rebuild_from_tiles(self, recalibrate=True, progress=None):
        """【先分块保存，再拼接】把已保存的分块重新拼一遍。

        recalibrate=True → 自动校准：每块按「当前 mm_scale / 该块拍摄时 scale」
        重新缩放后再贴，使不同缩放时期拍的块统一到同一比例，接缝与错位自动消掉。
        已删除的块（tile_deleted）跳过。返回 (使用块数, 跳过块数)。
        """
        if not self.tiles:
            return 0, 0
        # 清空画布，从零重拼
        n = self.stitch_size
        self.canvas_sum = np.zeros((n, n, 3), np.float32)
        self.canvas_wsum = np.zeros((n, n), np.float32)
        self._cover = None
        self.stitch_hits = 0
        self.stitch_skipped = 0
        self._drop_streak = 0
        self._render_dirty = True
        half = self.stitch_size / 2.0
        sc = float(self.stitch_scale)
        used = skipped = 0
        # 按 id 排序（拍摄顺序）
        for rec in sorted(self.tiles, key=lambda t: int(t.get("id", 0))):
            try:
                if int(rec.get("id", -1)) in self.tile_deleted:
                    skipped += 1
                    continue
                p = os.path.join(self.tiles_dir or "", str(rec.get("file", "")))
                img = cv2.imread(p)
                if img is None:
                    skipped += 1
                    continue
                ts = float(rec.get("scale", 1.0) or 1.0)
                px, py = float(rec["pose"][0]), float(rec["pose"][1])
                ratio = (float(self.mm_scale) / ts) if (recalibrate and ts > 0) else 1.0
                if abs(ratio - 1.0) > 1e-3:
                    img = cv2.resize(img, (max(1, int(round(img.shape[1] * ratio))),
                                           max(1, int(round(img.shape[0] * ratio)))))
                ih, iw = img.shape[:2]
                # 羽化 × 圆内 mask（圆半径随 ratio 一起缩放）
                r = float(rec.get("r", 0) or 0) * ratio
                cxp, cyp = (iw - 1) / 2.0, (ih - 1) / 2.0
                yy, xx = np.ogrid[:ih, :iw]
                d2 = (xx - cxp) ** 2 + (yy - cyp) ** 2
                w_eff = np.clip(1.0 - d2 / max(1.0, r * r), 0.05, 1.0).astype(np.float32)
                if r > 0:
                    w_eff = np.where(d2 <= r * r, w_eff, 0.0)
                # —— 删除黑名单同样作用于重拼：否则「自动校准」会把删掉的画面贴回来 ——
                wp = ts * ratio               # 该块：世界单位 / 像素
                if self.map_blackouts and wp > 0:
                    for (rx0, ry0, rx1, ry1) in self.map_blackouts:
                        bx0 = int(max(0, min(iw, round((rx0 - px) / wp + iw / 2.0))))
                        bx1 = int(max(0, min(iw, round((rx1 - px) / wp + iw / 2.0))))
                        by0 = int(max(0, min(ih, round((ry0 - py) / wp + ih / 2.0))))
                        by1 = int(max(0, min(ih, round((ry1 - py) / wp + ih / 2.0))))
                        if bx1 > bx0 and by1 > by0:
                            w_eff[by0:by1, bx0:bx1] = 0.0
                    if float(w_eff.max()) <= 0.0:
                        skipped += 1
                        continue
                # 世界坐标下，该块左边缘 = pose - (ih/2)*ts*ratio 等；直接用
                # s = ts*ratio*sc（该块 1px 对应画布 px）算落点
                s = ts * ratio * sc
                x0 = int(round(half + px * sc - (iw / 2.0) * s))
                y0 = int(round(half + py * sc - (ih / 2.0) * s))
                cx0, cy0 = max(0, x0), max(0, y0)
                cx1 = min(n, x0 + iw)
                cy1 = min(n, y0 + ih)
                if cx1 <= cx0 or cy1 <= cy0:
                    skipped += 1
                    continue
                sx0, sy0 = cx0 - x0, cy0 - y0
                src = img[sy0:sy0 + (cy1 - cy0), sx0:sx0 + (cx1 - cx0)]
                we = w_eff[sy0:sy0 + src.shape[0], sx0:sx0 + src.shape[1]]
                self.canvas_sum[cy0:cy1, cx0:cx1] += src.astype(np.float32) * we[:, :, None]
                self.canvas_wsum[cy0:cy1, cx0:cx1] += we
                self._mark_cover(cx0, cy0, cx1, cy1)
                used += 1
                if progress and (used % 20 == 0):
                    try:
                        progress(used, len(self.tiles))
                    except Exception:
                        pass
            except Exception:
                skipped += 1
                continue
        self.stitch_hits = used
        self._render_dirty = True
        return used, skipped

    def auto_calibrate_map(self, progress=None):
        """自制地图【自动校准】：按分块重拼 + 统一缩放比例（mm_scale）。

        返回统计 dict。有分块就走「重拼 + 每块按当前比例重缩放」；
        没有分块则只做状态复位（清缓存、重算渲染）。
        """
        if self.tiles:
            used, skipped = self.rebuild_from_tiles(recalibrate=True,
                                                    progress=progress)
            return {"ok": True, "mode": "tiles", "used": used,
                    "skipped": skipped, "mm_scale": float(self.mm_scale)}
        self._cover = None
        self._render_dirty = True
        return {"ok": True, "mode": "reset", "used": 0, "skipped": 0,
                "mm_scale": float(self.mm_scale)}

    def erase_world_rect(self, wx0, wy0, wx1, wy1,
                         erase_trail=False, erase_dots=True, cut_route=True):
        """在地图上【框选删除】：擦贴图、删怪点，并把路线在该区域【裁断】。

        cut_route=True 时把矩形记入 trail_cuts —— 绘制轨迹时该区域的线直接断开
        （只删采样点是不够的：RDP 会把两侧拐角重新连起来、线照样横穿）。
        erase_trail 默认 False：**只断开显示、不真删采样点**，这样「还原删除」
        能把路线完整恢复；需要彻底丢点时可显式传 True。
        返回被删的 (轨迹点数, 怪点数)。
        """
        x0, x1 = (wx0, wx1) if wx0 <= wx1 else (wx1, wx0)
        y0, y1 = (wy0, wy1) if wy0 <= wy1 else (wy1, wy0)
        # —— ① 路线裁断 + 贴图黑名单（即使画布还没拼过也要生效）——
        #    黑名单让后续帧【不再把删掉的画面拼回来】，否则机器人跑过去又复原。
        if cut_route and (x1 - x0) > 1e-6 and (y1 - y0) > 1e-6:
            rect = [float(x0), float(y0), float(x1), float(y1)]
            self.map_blackouts.append(rect)
            self.trail_cuts.append(list(rect))
        # —— ② 删该范围内的轨迹采样点（错误路线）——
        n_trail = 0
        if erase_trail and self.trail:
            kept_indices = [i for i, p in enumerate(self.trail)
                            if not (x0 <= p[0] <= x1 and y0 <= p[1] <= y1)]
            keep = [self.trail[i] for i in kept_indices]
            self.trail_breaks = sorted({sum(i < b for i in kept_indices)
                                        for b in self.trail_breaks} - {0})
            n_trail = len(self.trail) - len(keep)
            self.trail = keep
            self._trail_last = self.trail[-1] if self.trail else None
        # —— ③ 删该范围内的怪点 ——
        n_dots = 0
        if erase_dots and self.dots:
            for k in [k for k, v in self.dots.items()
                      if x0 <= v[0] <= x1 and y0 <= v[1] <= y1]:
                self.dots.pop(k, None)
                n_dots += 1
        # —— ④ 擦掉贴图（画布未初始化时跳过，不影响上面三步）——
        if self.canvas_sum is not None:
            half = self.stitch_size / 2.0
            sc = float(self.stitch_scale)
            cx0 = int(max(0, min(self.stitch_size, half + x0 * sc)))
            cx1 = int(max(0, min(self.stitch_size, half + x1 * sc)))
            cy0 = int(max(0, min(self.stitch_size, half + y0 * sc)))
            cy1 = int(max(0, min(self.stitch_size, half + y1 * sc)))
            if cx1 > cx0 and cy1 > cy0:
                self.canvas_sum[cy0:cy1, cx0:cx1] = 0.0
                self.canvas_wsum[cy0:cy1, cx0:cx1] = 0.0
                try:
                    g = self._cover_grid()
                    cell = float(self._cover_cell)
                    gx0 = max(0, int(cx0 / cell))
                    gx1 = min(g.shape[1], int(cx1 / cell) + 1)
                    gy0 = max(0, int(cy0 / cell))
                    gy1 = min(g.shape[0], int(cy1 / cell) + 1)
                    if gx1 > gx0 and gy1 > gy0:
                        g[gy0:gy1, gx0:gx1] = 0
                except Exception:
                    self._cover = None
                self._render_dirty = True
        return n_trail, n_dots

    def erase_marks_in_rect(self, wx0, wy0, wx1, wy1):
        """擦除该区域内被删除分块（把分块 id 记入删除集，供重拼时跳过）。"""
        x0, x1 = min(wx0, wx1), max(wx0, wx1)
        y0, y1 = min(wy0, wy1), max(wy0, wy1)
        n = 0
        for rec in self.tiles:
            try:
                px, py = float(rec["pose"][0]), float(rec["pose"][1])
            except Exception:
                continue
            if x0 <= px <= x1 and y0 <= py <= y1:
                self.tile_deleted.add(int(rec.get("id", -1)))
                n += 1
        if n:
            self._save_tiles_index()
        return n

    def clear_tiles(self, remove_files=False):
        """清空分块（可选连磁盘文件一起删）。"""
        n = len(self.tiles)
        if remove_files and self.tiles_dir:
            for rec in self.tiles:
                try:
                    os.remove(os.path.join(self.tiles_dir, str(rec.get("file", ""))))
                except Exception:
                    pass
        self.tiles = []
        self.tile_deleted = set()
        self.tile_seq = 0
        self._save_tiles_index()
        return n

    # ---------- 查重辅助：覆盖栅格 ----------
    def _cover_grid(self):
        """低分辨率覆盖栅格（每格 _cover_cell 画布像素）。"""
        if self._cover is None:
            n = max(1, int(math.ceil(self.stitch_size / float(self._cover_cell))))
            self._cover = np.zeros((n, n), bool)
        return self._cover

    def _cell_range(self, x0, y0, x1, y1):
        """画布矩形 → 覆盖栅格的索引范围（已裁剪到栅格内）。"""
        g = self._cover_grid()
        c = self._cover_cell
        gx0, gy0 = max(0, int(x0) // c), max(0, int(y0) // c)
        gx1 = min(g.shape[1] - 1, max(0, int(x1) - 1) // c)
        gy1 = min(g.shape[0] - 1, max(0, int(y1) - 1) // c)
        return gx0, gy0, gx1, gy1

    def _footprint_overlap(self, x0, y0, x1, y1):
        """落点里【已经拼过】的比例（0~1）—— 几何重合率。

        用覆盖栅格统计：等于「这块区域有多少比例已经被之前的帧覆盖」。
          1.0 ≈ 完全重合（画面没动/回到原地）；0 ≈ 全新区域（或跳变到别处）。
        """
        try:
            gx0, gy0, gx1, gy1 = self._cell_range(x0, y0, x1, y1)
            if gx1 < gx0 or gy1 < gy0:
                return 0.0
            blk = self._cover_grid()[gy0:gy1 + 1, gx0:gx1 + 1]
            return float(blk.sum()) / float(blk.size)
        except Exception:
            return 0.0

    def _content_match_ratio(self, img, x0, y0):
        """像素级「完全重合率」：本帧与上一帧贴图的重叠区里，像素几乎一致的比例。

        做法：两边都降采样到 32×32（上一帧已存），只比对重叠部分，统计
        「逐像素平均差 ≤ 12」的比例。返回 None 表示无法比对（首帧/尺寸异常）。
        这条判据抓的是「位移很小但画面完全没变」（例如卡住不动、贴图被 UI 遮挡），
        位移闸门抓不到的重复帧。
        """
        try:
            last = self._last_tile_small
            if last is None or img is None:
                return None
            cur = cv2.resize(img, (32, 32), interpolation=cv2.INTER_AREA)
            # 位移（世界像素）→ 32 格里偏移多少格
            lp = self._last_stitch_pose
            if lp is None:
                return None
            f = 32.0 / float(max(1, img.shape[1]))
            dx = int(round((self.pose[0] - lp[0]) * self.stitch_scale * f))
            dy = int(round((self.pose[1] - lp[1]) * self.stitch_scale * f))
            if abs(dx) >= 32 or abs(dy) >= 32:
                return None                      # 完全错开，没有重叠区
            ax0, ay0 = max(0, dx), max(0, dy)
            bx0, by0 = max(0, -dx), max(0, -dy)
            w = 32 - abs(dx)
            h = 32 - abs(dy)
            if w <= 1 or h <= 1:
                return None
            pa = cur[ay0:ay0 + h, ax0:ax0 + w].astype(np.int16)
            pb = last[by0:by0 + h, bx0:bx0 + w].astype(np.int16)
            diff = np.abs(pa - pb).mean(axis=2)
            return float((diff <= 12).mean())
        except Exception:
            return None

    def _footprint_covered(self, x0, y0, x1, y1):
        """该矩形是否已被完全覆盖（查重②的判据）。"""
        try:
            gx0, gy0, gx1, gy1 = self._cell_range(x0, y0, x1, y1)
            if gx1 < gx0 or gy1 < gy0:
                return False
            return bool(self._cover_grid()[gy0:gy1 + 1, gx0:gx1 + 1].all())
        except Exception:
            return False

    def _mark_cover(self, x0, y0, x1, y1):
        """记录「这块已经拼过了」。"""
        try:
            gx0, gy0, gx1, gy1 = self._cell_range(x0, y0, x1, y1)
            if gx1 >= gx0 and gy1 >= gy0:
                self._cover_grid()[gy0:gy1 + 1, gx0:gx1 + 1] = True
        except Exception:
            pass

    # ---------- 步长 ↔ 小地图像素 关系自优化 ----------
    def observe_step(self, step_px, moved_px):
        """记录一次观测：点了 step_px 步长 → 小地图实际位移 moved_px。

        比例 = moved_px / step_px（"每点 1 屏幕像素，小地图走多少像素"），
        用 EMA 平滑（越跑越准，不受单次被墙挡/配准抖动影响）。
        明显异常的比例（<0.05 或 >5，通常是被障碍挡住或配准失败）直接丢弃。
        返回当前比例（无有效样本时 None）。
        """
        try:
            step_px = float(step_px or 0.0)
            moved_px = float(moved_px or 0.0)
        except (TypeError, ValueError):
            return self.px_per_step
        if step_px <= 1.0 or moved_px <= 0.0:
            return self.px_per_step
        r = moved_px / step_px
        if r < 0.05 or r > 5.0:
            return self.px_per_step
        a = float(getattr(self, "step_ema_alpha", 0.25) or 0.25)
        self.px_per_step = (r if self.px_per_step is None
                            else (1.0 - a) * self.px_per_step + a * r)
        self.step_samples += 1
        return self.px_per_step

    def suggest_step(self, want_moved_px, fallback=260.0, lo=40.0, hi=600.0):
        """反推「想让小地图位移 want_moved_px」需要点多远（屏幕像素）。

        还没学到比例（样本不足）→ 返回 fallback（配置里的手动步长）。
        结果钳位到 [lo, hi]，与引擎的 home_step_px 范围一致。
        """
        try:
            want = float(want_moved_px or 0.0)
        except (TypeError, ValueError):
            want = 0.0
        r = self.px_per_step
        if not r or r <= 0.0 or want <= 0.0:
            return float(fallback)
        return float(max(lo, min(hi, want / r)))

    def stitch_image(self, disp=384):
        """返回拼接图（BGR，按羽化权重归一化）。disp>0 时缩放到 disp×disp（省传输）。

        还没贴上过有效像素 → 返回 None。未覆盖区域为黑。

        性能：两道优化，静止时接近零成本
          · **脏标记缓存** — 没有新增贴图时直接返回上次结果（GUI 每帧都要图）；
          · **先缩后除** — disp 小于画布时，先把累加图缩到 disp 再归一化，
            除法规模从 768² 降到 disp²（384² 时约省 4 倍）。
        """
        if self.canvas_sum is None or self.stitch_hits == 0:
            return None
        d = int(disp) if disp else 0
        key = (d, self.stitch_hits)
        if (not self._render_dirty and self._render_cache is not None
                and self._render_cache_key == key):
            return self._render_cache
        if d and d != self.stitch_size:
            # 先缩后除：规模从 768² 降到 d²
            s_small = cv2.resize(self.canvas_sum, (d, d),
                                 interpolation=cv2.INTER_AREA)
            w_small = cv2.resize(self.canvas_wsum, (d, d),
                                 interpolation=cv2.INTER_AREA)
            wsum = np.maximum(w_small, 1e-6)[:, :, None]
            out = np.clip(s_small / wsum, 0, 255).astype(np.uint8)
        else:
            wsum = np.maximum(self.canvas_wsum, 1e-6)[:, :, None]
            out = np.clip(self.canvas_sum / wsum, 0, 255).astype(np.uint8)
        self._render_cache = out
        self._render_cache_key = key
        self._render_dirty = False
        return out

    def stitch_coverage(self):
        """已拼接覆盖比例（0~1），供 GUI 诊断。

        用低分辨率覆盖栅格统计（O(格数) ≈ 万级，比逐像素 bool 统计快得多），
        与真实覆盖率误差 < 一格（8 画布像素）。
        """
        try:
            if self._cover is not None:
                g = self._cover
                cell_px = float(self._cover_cell)
                covered = float(g.sum()) * cell_px * cell_px
                total = float(self.stitch_size * self.stitch_size)
                return min(1.0, covered / max(1.0, total))
            if self.canvas_wsum is None:
                return 0.0
            n = float(self.stitch_size * self.stitch_size)
            return float((self.canvas_wsum > 0).sum()) / max(1.0, n)
        except Exception:
            return 0.0

    def reset_canvas(self):
        self.canvas_sum = None
        self.canvas_wsum = None
        self.stitch_hits = 0
        self.stitch_skipped = 0
        self.stitch_dropped = 0
        self._drop_streak = 0
        self._last_tile_small = None
        self.last_overlap = None
        self.last_match = None
        self._last_stitch_pose = None
        self._cover = None
        self._render_cache = None
        self._render_cache_key = None
        self._render_dirty = True

    # ---------- 怪点 / 目标点 ----------
    def role_to_world(self, u, v):
        """固定朝北的小地图偏移 → 世界坐标，与角色位移使用同一缩放。"""
        return (self.pose[0] + float(u) * self.mm_scale,
                self.pose[1] + float(v) * self.mm_scale)

    def add_role_points(self, role_pts):
        """把「角色坐标系」的怪点记录到地图（实时完善）。

        role_pts : [(u, v), ...] 怪点相对圆心的像素偏移（u 右、v 下）。
        小地图固定朝北 → 世界 = pose_xy + (u, v) * mm_scale。
        返回新增的点数。
        """
        if not role_pts:
            return 0
        n = 0
        for u, v in role_pts:
            wx, wy = self.role_to_world(u, v)
            k = self._to_cell(wx, wy)
            if k not in self.dots:
                self.dots[k] = (wx, wy)
                n += 1
        return n

    def set_target(self, name, wx, wy):
        self.targets[str(name)] = (float(wx), float(wy))

    def remove_target(self, name):
        self.targets.pop(str(name), None)

    def clear_targets(self):
        self.targets.clear()

    def target_vector(self, name):
        t = self.targets.get(str(name))
        if not t:
            return None
        return (t[0] - self.pose[0], t[1] - self.pose[1])

    # ---------- 配准更新 ----------
    @_locked_map
    def update(self, minimap, response_min=0.05, angle_range=0.0,
               angle_step=2.0, mask=None):
        """用新一帧小地图更新 pose。返回 (moved, resp, delta_deg)。

        minimap : (H, W) 灰度图（方形，圆心=角色）。None 或空则返回未更新。
        mask    : 可选 (H,W) 有效区域（小地图圆内）——传给 ECC 只用圆内像素。
        小地图固定朝北 → 纯平移配准，angle_range/angle_step 兼容旧接口（忽略）。
        """
        if minimap is None or minimap.size == 0:
            return False, 0.0, 0.0
        g = np.asarray(minimap, dtype=np.float32)
        if self.prev_minimap is None or self.prev_minimap.shape != g.shape:
            self.prev_minimap = g
            return False, 0.0, 0.0
        try:
            delta_deg, (tu, tv), resp = estimate_motion(
                self.prev_minimap, g,
                angle_range=angle_range, angle_step=angle_step,
                mask=mask)
        except Exception:
            return False, 0.0, 0.0
        # —— 缩放检测放在配准之后：知道这一帧位移多大，位移太大时跳过
        #    （大位移下「平移」与「缩放」互相混淆，很容易误判成缩放变化）——
        if getattr(self, "auto_mm_scale", True):
            try:
                self._tick_scale_check(g, (tu, tv))
            except Exception:
                pass
        self.prev_minimap = g
        self.last_resp = float(resp)
        if resp < response_min:
            return False, resp, delta_deg
        old = self.pose
        # 位移按当前「世界单位/小地图像素」换算（滚轮缩放后自动变化）
        self.pose = _motion_to_pose(old, delta_deg, (tu, tv), self.mm_scale)
        self._mark_explored(self.pose[0], self.pose[1])
        self._append_trail(self.pose[0], self.pose[1])
        moved = (math.hypot(self.pose[0] - old[0], self.pose[1] - old[1])
                 > 1.0 or abs(self.pose[2] - old[2]) > 0.5)
        return moved, resp, delta_deg

    # ---------- 回原点 / 朝目标 ----------
    def home_vector(self):
        """当前相对原点的世界位移向量 (dx, dy)。"""
        return (self.origin[0] - self.pose[0],
                self.origin[1] - self.pose[1])

    def home_dist(self):
        dx, dy = self.home_vector()
        return math.hypot(dx, dy)

    def plan_to(self, wx, wy):
        """A* 规划从当前格到目标格的路径（世界格序列，含两端）。

        只走「已探索」格子（小地图拼接出来的安全区），未知格子一律当墙 →
        等效「沿来路走」。禁区多边形占用的格子也当墙 → 回归路径自动绕开禁区。
        若已探索网络连不到目标，返回 None；有禁区时禁止直线兜底。
        """
        start = self._to_cell(self.pose[0], self.pose[1])
        goal = self._to_cell(wx, wy)
        if start == goal:
            return [start]
        try:
            blocked = self._forbidden_blocked()
        except Exception:
            blocked = set()
        return astar_path(start, goal, blocked=blocked, bounds=None,
                          domain=self.explored)

    def plan_home(self):
        """A* 规划从当前格到原点格的路径（世界格序列，含两端）。"""
        return self.plan_to(self.origin[0], self.origin[1])

    def next_step_to(self, wx, wy):
        """返回「朝世界点 (wx,wy) 走的下一步」世界目标点（像素）。

        优先 A* 路径；无禁区时可直线走一格。None 表示到达或路径受阻，调用方需检查距离。
        """
        dx, dy = wx - self.pose[0], wy - self.pose[1]
        dist = math.hypot(dx, dy)
        if dist <= self.cell_px * 0.5:
            return None
        path = self.plan_to(wx, wy)
        if path and len(path) >= 2:
            nx, ny = path[1]
            return (nx * self.cell_px, ny * self.cell_px)
        if self.zones_forbidden and not path:
            return None  # 禁区阻断时禁止直线冲；调用方区分无路和到达
        return (self.pose[0] + dx / max(dist, 1e-6) * self.cell_px,
                self.pose[1] + dy / max(dist, 1e-6) * self.cell_px)

    def next_world_target(self):
        """返回「朝原点走的下一步」世界目标点（像素），已在原点附近返回 None。"""
        return self.next_step_to(self.origin[0], self.origin[1])

    # ---------- 序列化（供 GUI 渲染自制地图） ----------
    def _path_home_points(self):
        """回原点的世界路径点（A* 最优路径；不可达时直线兜底）。

        A* 只在【已探索格】里走（未知区域当墙）→ 得到的就是「沿走过的路回去」
        的最短路线，即用户要的「最近线路回到原点」。
        """
        try:
            path = self.plan_home()
        except Exception:
            path = None
        if path and len(path) >= 2:
            c = float(self.cell_px)
            return [[float(g[0]) * c, float(g[1]) * c] for g in path]
        return [[float(self.pose[0]), float(self.pose[1])],
                [float(self.origin[0]), float(self.origin[1])]]

    @_locked_map
    def to_map(self, include_image=True, disp=384):
        """把地图状态序列化成 dict，供 GUI 实时渲染。

        含「拼接出来的地图图像」（numpy BGR，已降采样到 disp）与坐标映射参数：
          世界 (wx,wy) → 拼接画布像素 (S/2 + wx*scale, S/2 + wy*scale)
        disp 显示时再按 显示边长/stitch_size 等比缩放。
        """
        d = {
            "load_point": list(self.load_point) if self.load_point is not None else None,
            "position_revision": self.position_revision,
            "pose": [float(self.pose[0]), float(self.pose[1]),
                     float(self.pose[2])],
            "origin": [float(self.origin[0]), float(self.origin[1])],
            "cell_px": float(self.cell_px),
            "explored": [list(g) for g in self.explored],
            "trail": [list(p) for p in self.trail],
            # 轨迹【拐角连线】简化版（RDP）：线条干净，只连拐角
            "trail_simple": self.trail_simplified(),
            # 按「已删矩形」裁断后的可见路线（多段）：框选删除后线会真正断开
            "trail_segments": self.trail_segments(),
            "trail_cuts": [list(r) for r in (self.trail_cuts or [])],
            # 删除黑名单（世界矩形）：这些区域不再被贴图
            "map_blackouts": [list(r) for r in (self.map_blackouts or [])],
            # 手绘路线（世界点串列表）
            "drawn_paths": [[list(p) for p in path]
                            for path in (self.drawn_paths or [])],
            # 区域限制：限制圆（范围中心+半径）/ 禁区多边形（红框）
            "fence": (None if self.fence_center is None else
                      {"cx": float(self.fence_center[0]),
                       "cy": float(self.fence_center[1]),
                       "r": float(self.fence_r)}),
            "zones_forbidden": [[list(p) for p in poly]
                                for poly in (self.zones_forbidden or [])],
            # 回原点最优路径（A*）：蓝色回程线
            "path_home": self._path_home_points(),
            # 内容包围盒（世界坐标）：GUI 据此自动裁剪+缩放到界面内
            "view_bbox": self.content_bbox(),
            # 小地图缩放自适应
            "mm_scale": float(self.mm_scale),
            "mm_scale_samples": int(getattr(self, "mm_scale_samples", 0)),
            "last_mm_ratio": float(getattr(self, "last_mm_ratio", 1.0)),
            # 分块保存（先分割保存，再拼接；可剔除错误块重拼）
            "tiles": self.tiles_info(),
            "dots": [list(p) for p in self.dots.values()],
            "targets": {str(k): [float(v[0]), float(v[1])]
                        for k, v in self.targets.items()},
            "stitch_size": int(self.stitch_size),
            "stitch_scale": float(self.stitch_scale),
            "stitch_hits": int(self.stitch_hits),
            "stitch_skipped": int(getattr(self, "stitch_skipped", 0)),
            "stitch_dropped": int(getattr(self, "stitch_dropped", 0)),
            "last_overlap": (None if self.last_overlap is None
                             else float(self.last_overlap)),
            "last_match": (None if self.last_match is None
                           else float(self.last_match)),
            # 画布越界提示：角色离画布中心太远（>80% 半宽）→ 该把 stitch_size 调大
            "out_of_canvas": bool(
                max(abs(self.pose[0]), abs(self.pose[1])) * self.stitch_scale
                > self.stitch_size * 0.4),
            "stitch_cover": self.stitch_coverage(),
            "last_resp": float(self.last_resp),
            "px_per_step": (None if self.px_per_step is None
                            else float(self.px_per_step)),
            "step_samples": int(getattr(self, "step_samples", 0)),
            "image": None,
            "stitch_disp": 0,
        }
        if include_image:
            img = self.stitch_image(disp)
            if img is not None:
                d["image"] = img
                d["stitch_disp"] = int(img.shape[0])
        return d

    # ---------- 持久化（地图不断扩充留档，直至全部完善） ----------
    @_locked_map
    def save(self, path):
        """把当前地图状态保存到磁盘（JSON 元数据 + npy 拼接画布）。

        之后 load 会接着扩充，而不是从头重画。
        """
        import json
        import os
        meta = {
            "version": 1,
            "load_point": list(self.load_point) if self.load_point is not None else None,
            "trail_breaks": list(self.trail_breaks),
            "pose": [float(self.pose[0]), float(self.pose[1]), float(self.pose[2])],
            "origin": [float(self.origin[0]), float(self.origin[1])],
            "cell_px": float(self.cell_px),
            "explored": [list(g) for g in self.explored],
            "trail": [list(p) for p in self.trail],
            # 框选删除路线的裁断矩形（世界坐标）：重启后仍保持断开
            "trail_cuts": [list(r) for r in (self.trail_cuts or [])],
            # 删除黑名单：重启后这些区域仍不被贴图
            "map_blackouts": [list(r) for r in (self.map_blackouts or [])],
            # 手绘路线：重启后仍保留
            "drawn_paths": [[list(p) for p in path]
                            for path in (self.drawn_paths or [])],
            # 区域限制：重启后仍保留
            "fence": (None if self.fence_center is None else
                      {"cx": float(self.fence_center[0]),
                       "cy": float(self.fence_center[1]),
                       "r": float(self.fence_r)}),
            "zones_forbidden": [[list(p) for p in poly]
                                for poly in (self.zones_forbidden or [])],
            "dots": {f"{int(k[0])},{int(k[1])}": [float(v[0]), float(v[1])]
                     for k, v in self.dots.items()},
            "targets": {str(k): [float(v[0]), float(v[1])]
                        for k, v in self.targets.items()},
            "stitch_size": int(self.stitch_size),
            "stitch_scale": float(self.stitch_scale),
            "stitch_hits": int(self.stitch_hits),
            # 小地图缩放标定（世界单位/小地图像素）：重启后沿用，无需重新自适应
            "mm_scale": float(self.mm_scale),
            "px_per_step": (None if self.px_per_step is None
                            else float(self.px_per_step)),
            "step_samples": int(self.step_samples),
        }
        base = os.path.splitext(path)[0]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        # 拼接画布存 npy（float32 累加器 + 权重）
        if self.canvas_sum is not None:
            np.save(base + "_canvas_sum.npy", self.canvas_sum)
            np.save(base + "_canvas_wsum.npy", self.canvas_wsum)
        return path

    @_locked_map
    def load(self, path):
        """从磁盘恢复地图状态（接着扩充，而不是重画）。"""
        import json
        import os
        if not os.path.isfile(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self.pose = (float(meta["pose"][0]), float(meta["pose"][1]),
                         float(meta["pose"][2]))
            self.origin = (float(meta["origin"][0]), float(meta["origin"][1]))
            self.cell_px = float(meta.get("cell_px", 40.0))
            self.explored = {tuple(g) for g in meta.get("explored", [])}
            self.trail = [tuple(p) for p in meta.get("trail", [])]
            self.trail_breaks = sorted({b for b in meta.get("trail_breaks", [])
                                       if isinstance(b, int) and 0 < b <= len(self.trail)})
            lp = meta.get("load_point")
            self.load_point = None
            if isinstance(lp, (list, tuple)) and len(lp) == 2:
                point = tuple(float(v) for v in lp)
                if all(math.isfinite(v) for v in point):
                    self.load_point = point
            self.position_revision += 1
            self.prev_minimap = None
            # 框选删除路线的裁断矩形（旧档没有 → 空）
            try:
                self.trail_cuts = [[float(v) for v in r]
                                   for r in (meta.get("trail_cuts") or [])
                                   if len(r) == 4]
            except Exception:
                self.trail_cuts = []
            # 删除黑名单：旧档只有 trail_cuts → 一并当黑名单（避免删掉的画面被拼回来）
            try:
                bl = [[float(v) for v in r]
                      for r in (meta.get("map_blackouts") or []) if len(r) == 4]
                for r in self.trail_cuts:
                    if r not in bl:
                        bl.append(list(r))
                self.map_blackouts = bl
            except Exception:
                self.map_blackouts = []
            # 手绘路线：重启后仍保留
            self.drawn_paths = [[[float(p[0]), float(p[1])] for p in path]
                                for path in (meta.get("drawn_paths") or [])
                                if len(path) >= 2]
            # 区域限制：限制圆 + 禁区多边形，重启后仍保留
            # （旧版矩形 zones_allowed / 旧版矩形禁区格式一律忽略）
            try:
                fc = meta.get("fence")
                if isinstance(fc, dict) and fc.get("cx") is not None:
                    self.fence_center = (float(fc["cx"]), float(fc["cy"]))
                    self.fence_r = max(0.0, float(fc.get("r") or 0.0))
                else:
                    self.fence_center = None
                    self.fence_r = 0.0
            except Exception:
                self.fence_center = None
                self.fence_r = 0.0
            self.zones_forbidden = []
            for poly in (meta.get("zones_forbidden") or []):
                try:
                    if len(poly) >= 3 and all(
                            isinstance(p, (list, tuple)) and len(p) >= 2
                            for p in poly):
                        self.zones_forbidden.append(
                            [[float(p[0]), float(p[1])] for p in poly])
                except Exception:
                    continue
            self.dots = {tuple(map(int, k.split(","))): (v[0], v[1])
                         for k, v in meta.get("dots", {}).items()}
            self.targets = {str(k): (v[0], v[1])
                            for k, v in meta.get("targets", {}).items()}
            self.stitch_size = int(meta.get("stitch_size", self.stitch_size))
            self.stitch_scale = float(meta.get("stitch_scale", self.stitch_scale))
            self.stitch_hits = int(meta.get("stitch_hits", 0))
            # 小地图缩放标定：恢复并按范围钳位（旧档没有该字段 → 保持 1.0）
            try:
                ms = float(meta.get("mm_scale", self.mm_scale) or 1.0)
                self.mm_scale = max(self.mm_scale_min, min(self.mm_scale_max, ms))
            except (TypeError, ValueError):
                pass
            self._scale_ref, self._scale_ref_age = None, 0
            pps = meta.get("px_per_step")
            self.px_per_step = None if pps is None else float(pps)
            self.step_samples = int(meta.get("step_samples", 0))
            # 恢复拼接画布
            base = os.path.splitext(path)[0]
            if os.path.isfile(base + "_canvas_sum.npy"):
                self.canvas_sum = np.load(base + "_canvas_sum.npy")
                self.canvas_wsum = np.load(base + "_canvas_wsum.npy")
                self._render_dirty = True
            self._trail_last = self.trail[-1] if self.trail else None
            return True
        except Exception:
            return False


# =========================================================================
# 合成小地图渲染（供自测 + 实机调试对照）
# =========================================================================

def render_minimap(pose, points, size=200, scale=1.0, blur=1.0):
    """把世界固定点渲染成小地图灰度图（语义与真实小地图一致：固定朝北，供自测）。

    pose   : (x, y, theta_deg) 角色位置 + 朝向（朝向不参与渲染，小地图固定朝北）。
    points : [(px, py), ...] 世界固定点（怪/地形）。
    size   : 输出方形边长。
    scale  : 小地图像素 = 世界像素 × scale（默认 1）。
    返回   : (size, size) float32 灰度图（点处亮、其余黑）。

    小地图固定朝北：固定点 P 在「以角色为中心」图上的像素 = (P - pose_xy) + 图中心。
    """
    m = np.zeros((size, size), np.float32)
    cx = cy = size / 2.0
    for px, py in points:
        ui = int(round(cx + (px - pose[0]) * scale))
        vi = int(round(cy + (py - pose[1]) * scale))
        if 0 <= ui < size and 0 <= vi < size:
            m[vi, ui] = 255.0
    if blur and blur > 0:
        m = cv2.GaussianBlur(m, (0, 0), blur)
    return m

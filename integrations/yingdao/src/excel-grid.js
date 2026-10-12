// ============ 共享 Excel 网格组件（WPS 风格交互 · v2）============
// 供 excel-standalone（挂件窗口）/ excel-sheet-window（单 sheet 窗口）/ app.js（主界面）复用
//
// v2 相比 v1 的关键改进：
//  1. 事件委托：整表只挂 1 组监听器（原先每个单元格 3 个 → 30×12 就是 1000+ 个）
//  2. 选区 diff 重绘：拖动选区只更新受影响的单元格，不再每次遍历全表
//  3. destroy() + 同容器重复实例化自动清理：修掉容器监听器叠加泄漏
//  4. 新增 WPS 风格能力：选区统计、撤销/重做、系统剪贴板、填充柄、列宽拖拽、
//     表头右键菜单、查找替换、Ctrl+D/R 填充、Ctrl+方向键/Home/End 边缘导航、数字右对齐
(function () {
  // ---------- 样式（只注入一次） ----------
  if (!document.getElementById('__xgrid_style')) {
    const st = document.createElement('style');
    st.id = '__xgrid_style';
    st.textContent = `
.xgrid-wrap { position: relative; outline: none; background: #fff; overflow: auto; }
.xgrid { border-collapse: collapse; min-width: 100%; font-size: 13px; font-family: "Segoe UI","Microsoft YaHei",sans-serif; user-select: none; -webkit-user-select: none; }
.xgrid th, .xgrid td { border: 1px solid #e0e0e0; }
.xgrid th { background: #f5f6f7; color: #666; font-weight: 600; font-size: 11px; text-align: center; height: 24px; min-width: 80px; position: sticky; top: 0; z-index: 2; user-select: none; }
.xgrid th.corner { position: sticky; left: 0; top: 0; z-index: 5; min-width: 42px; width: 42px; background: #eceff1; cursor: pointer; }
.xgrid th.rowhead { position: sticky; left: 0; z-index: 3; min-width: 42px; width: 42px; background: #f5f6f7; cursor: pointer; }
.xgrid th.colhead { cursor: pointer; }
.xgrid th.rowhead:hover, .xgrid th.colhead:hover, .xgrid th.corner:hover { background: #e3eaf3; }
.xgrid th.headsel { background: #d8e6fb; color: #1a73e8; }
.xgrid td.xcell { min-width: 80px; height: 26px; padding: 0; position: relative; background: #fff; }
.xgrid td.xcell .xv { padding: 0 6px; line-height: 25px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.xgrid td.xcell.num .xv { text-align: right; }
.xgrid td.xcell.err .xv { color: #d93025; }
.xgrid td.xcell.sel { background: #e8f0fe; }
.xgrid td.xcell.fpv { background: #dbe6f7; }
.xgrid td.xcell.xhit { background: #fff3bf; }
.xgrid td.xcell.xhit.cur { outline: 2px solid #f0a30a; outline-offset: -2px; }
.xgrid td.xcell.active { outline: 2px solid #1a73e8; outline-offset: -2px; z-index: 1; }
.xgrid input.xinput { width: 100%; height: 100%; border: none; outline: 2px solid #1a73e8; outline-offset: -2px; padding: 0 5px; font-size: 13px; box-sizing: border-box; background: #fff; user-select: text; -webkit-user-select: text; }
.xgrid .xgrip { position: absolute; top: 0; right: -3px; width: 7px; height: 100%; cursor: col-resize; z-index: 6; }
.xgrid th.colhead { position: sticky; }
.xgrid .xfill { position: absolute; width: 7px; height: 7px; background: #1a73e8; border: 1px solid #fff; cursor: crosshair; z-index: 7; display: none; }
.xgrid-menu { position: fixed; background: #fff; border: 1px solid #d0d5dd; border-radius: 6px; box-shadow: 0 6px 22px rgba(0,0,0,.18); z-index: 20000; min-width: 168px; padding: 4px; font-size: 12px; font-family: "Segoe UI","Microsoft YaHei",sans-serif; user-select: none; }
.xgrid-menu .xmi { padding: 6px 10px; border-radius: 4px; cursor: pointer; color: #333; white-space: nowrap; }
.xgrid-menu .xmi:hover { background: #f0f4ff; color: #1a73e8; }
.xgrid-menu .xmi.dis { color: #bbb; cursor: default; }
.xgrid-menu .xmi.dis:hover { background: transparent; color: #bbb; }
.xgrid-menu .xsep { height: 1px; background: #eceff1; margin: 4px 2px; }
.xfind { position: sticky; top: 0; left: 0; z-index: 9; display: flex; align-items: center; gap: 4px; padding: 4px 6px; background: #f7f9fc; border-bottom: 1px solid #d0d5dd; font-size: 12px; }
.xfind input { border: 1px solid #d0d8e8; border-radius: 4px; padding: 2px 6px; font-size: 12px; width: 110px; user-select: text; -webkit-user-select: text; }
.xfind button { border: 1px solid #d0d8e8; background: #fff; border-radius: 4px; padding: 2px 8px; font-size: 12px; cursor: pointer; }
.xfind button:hover { background: #eef2ff; border-color: #1a73e8; }
.xfind .xfind-info { color: #888; margin-left: 4px; }
`;
    document.head.appendChild(st);
  }

  function colNameOf(c) {
    let s = ''; c += 1;
    while (c > 0) { const m = (c - 1) % 26; s = String.fromCharCode(65 + m) + s; c = Math.floor((c - 1) / 26); }
    return s;
  }
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  // 与 engine.makeCell 保持一致的数值判定：前导零（001）与超长数字（16 位以上）视为文本
  function isNumeric(v) {
    if (v === null || v === undefined || v === '') return false;
    const s = String(v).trim();
    if (!s) return false;
    if (/^[+-]?0\d/.test(s)) return false;
    if (/^[+-]?\d{16,}$/.test(s)) return false;
    return /^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/.test(s);
  }
  // 公式错误值（#DIV/0! 等）——按 WPS 那样标红
  function isErrValue(v) {
    return /^#(DIV\/0|VALUE|NAME|REF|NUM|N\/A|CIRC|ERROR|NULL)!?$/i.test(String(v == null ? '' : v).trim());
  }
  function isFormulaText(v) { return typeof v === 'string' && /^\s*=/.test(v) && v.trim().length > 1; }

  // ExcelGrid(container, opts)
  // opts:
  //   getRows():string[][]        数据源（二维数组）
  //   setCell(r,c,v)              写回单格（0 基）
  //   onEdit(r,c,v)               任一改动后回调（宿主用于同步/录制）
  //   onSelectChange(r,c)         活跃单元格变化
  //   onStats(stats)              选区统计变化
  //   onStructure(action,index,n) 结构操作（宿主映射到引擎，返回 false 表示自行处理）
  //   onRestore(rows)             整表回写（撤销/填充/内置结构操作的持久化）
  //   colName(c) minRows minCols maxUndo
  window.ExcelGrid = function (container, opts) {
    opts = opts || {};
    // 同一容器重复实例化：先销毁旧实例，避免监听器叠加
    if (container.__xgridApi && container.__xgridApi.destroy) container.__xgridApi.destroy();

    const colName = opts.colName || colNameOf;
    const minRows = opts.minRows || 30;
    const minCols = opts.minCols || 12;
    const MAX_UNDO = opts.maxUndo || 80;

    let rows = [];
    let rawRows = [];              // 与 rows 平行的原始内容（公式单元格为 "=公式"）
    let R = minRows, C = minCols;
    let selR = 0, selC = 0, selR2 = 0, selC2 = 0;
    let editing = false;
    let copied = null;              // 内部剪贴板 { rows, from:{r,c} }
    let undoStack = [], redoStack = [];
    let cellMap = new Map();        // "r_c" -> td
    let headMap = { col: new Map(), row: new Map() }; // 列头/行头
    let colW = {};                  // 列宽（px）
    let painted = null;             // 上次绘制的选区
    let activeTd = null;
    let drag = null;                // { type:'select'|'rowsel'|'colsel'|'fill'|'resize', ... }
    let fillRect = null;            // 填充预览矩形
    let cutRect = null;             // 剪切源（粘贴后清空）
    let pendingDependents = false;  // 引擎报告有依赖公式被重算 → 需要整表重读
    let findState = { hits: [], idx: -1, q: '' };
    let selStats = null;
    // 构造期间不回调宿主：宿主此时还没拿到 api 引用（否则会踩 TDZ）
    let ready = false;

    const ac = new AbortController();
    const on = (el, ev, fn, o) => el.addEventListener(ev, fn, Object.assign({ signal: ac.signal }, o || {}));

    container.classList.add('xgrid-wrap');
    container.tabIndex = 0;
    container.innerHTML = '';
    const table = document.createElement('table');
    table.className = 'xgrid';
    const fillEl = document.createElement('div');
    fillEl.className = 'xfill';
    let barEl = null, menuEl = null;   // 查找条 / 右键菜单（复用同一实例）
    container.appendChild(table);
    container.appendChild(fillEl);

    // ---------- 数据 ----------
    function loadRows() {
      try { rows = opts.getRows() || []; } catch (e) { rows = []; }
      if (!Array.isArray(rows)) rows = [];
      // 原始内容（公式单元格为 "=公式"）：用于编辑框回显与复制，显示仍用计算后的值
      rawRows = [];
      try { if (opts.getRawRows) rawRows = opts.getRawRows() || []; } catch (e) { rawRows = []; }
      calcSize();
    }
    function calcSize() {
      R = Math.max(rows.length, minRows);
      C = Math.max(rows.reduce((m, r) => Math.max(m, (r && r.length) || 0), 0), minCols);
    }
    function valueAt(r, c) {
      const v = rows[r] ? rows[r][c] : '';
      return v == null ? '' : v;
    }
    // 原始内容（公式单元格返回 =公式）——编辑框回显、复制用
    function rawTextAt(r, c) {
      if (opts.getEditText) {
        try { const t = opts.getEditText(r, c); if (t !== undefined && t !== null) return String(t); } catch (e) { }
      }
      const raw = rawRows[r] ? rawRows[r][c] : undefined;
      if (raw !== undefined && raw !== null && raw !== '') return String(raw);
      return String(valueAt(r, c));
    }
    function setData(r, c, v, silent) {
      if (!rows[r]) rows[r] = [];
      rows[r][c] = v;
      try { if (opts.setCell && opts.setCell(r, c, v)) pendingDependents = true; } catch (e) { }
      if (!silent && opts.onEdit) opts.onEdit(r, c, v);
    }
    // 依赖公式被重算过 → 从引擎重读整表，让结果立即显示（对齐 WPS）
    function flushDependents() {
      if (!pendingDependents) return false;
      pendingDependents = false;
      loadRows();
      render();
      return true;
    }
    function selRect() {
      return {
        r0: Math.min(selR, selR2), r1: Math.max(selR, selR2),
        c0: Math.min(selC, selC2), c1: Math.max(selC, selC2)
      };
    }

    // ---------- 渲染 ----------
    function render() {
      calcSize();
      let html = '<thead><tr><th class="corner" data-corner="1"></th>';
      for (let c = 0; c < C; c++) {
        html += `<th class="colhead" data-c="${c}">${colName(c)}<span class="xgrip" data-grip="${c}"></span></th>`;
      }
      html += '</tr></thead><tbody>';
      for (let r = 0; r < R; r++) {
        html += `<tr><th class="rowhead" data-r="${r}">${r + 1}</th>`;
        for (let c = 0; c < C; c++) {
          const v = valueAt(r, c);
          const cls = 'xcell' + (isNumeric(v) ? ' num' : '') + (isErrValue(v) ? ' err' : '');
          html += `<td class="${cls}" data-r="${r}" data-c="${c}"><div class="xv">${esc(v)}</div></td>`;
        }
        html += '</tr>';
      }
      html += '</tbody>';
      table.innerHTML = html;

      // 建索引（事件委托靠它做 O(1) 查找）
      cellMap = new Map();
      headMap = { col: new Map(), row: new Map() };
      table.querySelectorAll('td.xcell').forEach(td => {
        cellMap.set(td.dataset.r + '_' + td.dataset.c, td);
        const c = +td.dataset.c;
        if (colW[c]) { td.style.width = colW[c] + 'px'; td.style.minWidth = colW[c] + 'px'; }
      });
      table.querySelectorAll('th.colhead').forEach(th => {
        const c = +th.dataset.c;
        headMap.col.set(c, th);
        if (colW[c]) { th.style.width = colW[c] + 'px'; th.style.minWidth = colW[c] + 'px'; }
      });
      table.querySelectorAll('th.rowhead').forEach(th => headMap.row.set(+th.dataset.r, th));

      painted = null; activeTd = null;
      paintSelection();
    }
    function getTd(r, c) { return cellMap.get(r + '_' + c); }

    // 只重绘「变化的部分」——拖动选区时不再全表扫描
    function paintSelection() {
      const next = selRect();
      const same = painted && painted.r0 === next.r0 && painted.r1 === next.r1 &&
        painted.c0 === next.c0 && painted.c1 === next.c1;
      if (!same) {
        const prev = painted;
        if (prev) {
          for (let r = prev.r0; r <= prev.r1; r++) {
            for (let c = prev.c0; c <= prev.c1; c++) {
              if (r >= next.r0 && r <= next.r1 && c >= next.c0 && c <= next.c1) continue;
              const td = getTd(r, c);
              if (td) td.classList.remove('sel');
            }
          }
        }
        for (let r = next.r0; r <= next.r1; r++) {
          for (let c = next.c0; c <= next.c1; c++) {
            const td = getTd(r, c);
            if (td) td.classList.add('sel');
          }
        }
        painted = next;
      }
      if (activeTd) activeTd.classList.remove('active');
      activeTd = getTd(selR, selC);
      if (activeTd) activeTd.classList.add('active');
      updateFillHandle();
      computeStats();
      if (ready && opts.onSelectChange) opts.onSelectChange(selR, selC);
    }

    // 选区统计（WPS 状态栏：计数/求和/平均值）
    function computeStats() {
      const { r0, r1, c0, c1 } = selRect();
      let count = 0, numCount = 0, sum = 0, min = Infinity, max = -Infinity;
      for (let r = r0; r <= r1; r++) {
        for (let c = c0; c <= c1; c++) {
          const v = valueAt(r, c);
          if (v === '' || v == null) continue;
          count++;
          if (isNumeric(v)) {
            const n = Number(v);
            numCount++; sum += n;
            if (n < min) min = n;
            if (n > max) max = n;
          }
        }
      }
      selStats = {
        count: count, numCount: numCount,
        sum: numCount ? sum : 0,
        avg: numCount ? sum / numCount : 0,
        min: numCount ? min : 0, max: numCount ? max : 0
      };
      if (ready && opts.onStats) opts.onStats(selStats, selRect());
    }

    function scrollIntoView(r, c) {
      const td = getTd(r, c);
      if (td && td.scrollIntoView) td.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    }

    // 填充柄定位（选区右下角）
    function updateFillHandle() {
      if (editing || drag && drag.type === 'fill') { fillEl.style.display = 'none'; return; }
      const td = getTd(Math.max(selR, selR2), Math.max(selC, selC2));
      if (!td) { fillEl.style.display = 'none'; return; }
      fillEl.style.display = 'block';
      fillEl.style.left = (td.offsetLeft + td.offsetWidth - 3) + 'px';
      fillEl.style.top = (td.offsetTop + td.offsetHeight - 3) + 'px';
    }

    // ---------- 移动 ----------
    function setSel(r, c, extend) {
      if (extend) { selR2 = r; selC2 = c; }
      else { selR = selR2 = r; selC = selC2 = c; }
      paintSelection();
    }
    function move(dr, dc, extend) {
      if (editing) commitEdit();
      let r = (extend ? selR2 : selR) + dr, c = (extend ? selC2 : selC) + dc;
      if (r < 0) r = 0;
      if (c < 0) c = 0;
      if (r >= R || c >= C) {
        R = Math.max(R, r + 1); C = Math.max(C, c + 1);
        if (extend) { selR2 = r; selC2 = c; } else { selR = selR2 = r; selC = selC2 = c; }
        render();
        scrollIntoView(r, c);
        return;
      }
      if (extend) { selR2 = r; selC2 = c; } else { selR = selR2 = r; selC = selC2 = c; }
      paintSelection();
      scrollIntoView(extend ? selR2 : selR, extend ? selC2 : selC);
      container.focus();
    }
    // Ctrl+方向键：跳到数据边缘（WPS/Excel 行为）
    function jumpEdge(dr, dc) {
      let r = selR, c = selC;
      const cur = valueAt(r, c) !== '';
      let nr = r, nc = c;
      // 先越过连续的空白或有值块，再停在块边缘
      let first = true;
      while (true) {
        const tr = nr + dr, tc = nc + dc;
        if (tr < 0 || tc < 0 || tr >= R || tc >= C) break;
        const v = valueAt(tr, tc);
        const has = v !== '';
        if (first) {
          if (cur && has) { nr = tr; nc = tc; continue; }   // 还在有值块内
          if (cur && !has) { nr = tr; nc = tc; first = false; continue; } // 进入空白区
          if (!cur && has) { nr = tr; nc = tc; break; }     // 找到下一个有值
          nr = tr; nc = tc; continue;                       // 空白区继续
        }
        if (has) break;
        nr = tr; nc = tc;
      }
      move(nr - r, nc - c, false);
    }

    // ---------- 编辑 ----------
    function startEdit(r, c, initial) {
      if (editing) commitEdit();
      const td = getTd(r, c);
      if (!td) return;
      editing = true;
      updateFillHandle();
      // 编辑框回显"原始内容"：公式单元格显示 =公式（对齐 WPS），普通单元格显示值
      const cur = rawTextAt(r, c);
      td.classList.add('editing');
      td.innerHTML = `<input class="xinput" value="${esc(initial != null ? initial : cur)}" />`;
      const inp = td.querySelector('input');
      inp.focus();
      if (initial != null) inp.select();
      else inp.setSelectionRange(inp.value.length, inp.value.length);
      inp.addEventListener('keydown', onEditKey);
      inp.addEventListener('blur', () => { if (editing) commitEdit(); });
    }
    function commitEdit() {
      if (!editing) return;
      editing = false;
      const inp = table.querySelector('.xinput');
      if (inp) {
        const td = inp.closest('td');
        const r = +td.dataset.r, c = +td.dataset.c;
        const val = inp.value;
        const old = String(valueAt(r, c));
        const isFormula = isFormulaText(val);
        if (val !== old) { pushUndo(); setData(r, c, val, true); }
        if (isFormula) {
          // 公式：写入后立刻从引擎重读 → 显示计算结果，依赖它的单元格一起刷新
          loadRows();
          render();
          pendingDependents = false;
          if (opts.onEdit) opts.onEdit(r, c, val);
          updateFillHandle();
          container.focus();
          return;
        }
        td.classList.remove('editing');
        td.classList.toggle('err', isErrValue(val));
        td.innerHTML = `<div class="xv">${esc(val)}</div>`;
        td.classList.toggle('num', isNumeric(val));
        if (opts.onEdit) opts.onEdit(r, c, val);
        flushDependents();          // 改的这个单元格若被公式引用，公式结果立即刷新
      }
      updateFillHandle();
      container.focus();
    }
    function cancelEdit() {
      if (!editing) return;
      editing = false;
      const inp = table.querySelector('.xinput');
      if (inp) {
        const td = inp.closest('td');
        const r = +td.dataset.r, c = +td.dataset.c;
        const cur = String(valueAt(r, c));
        td.classList.remove('editing');
        td.innerHTML = `<div class="xv">${esc(cur)}</div>`;
      }
      updateFillHandle();
      container.focus();
    }
    function onEditKey(e) {
      if (e.key === 'Enter') {
        e.preventDefault(); commitEdit();
        if (e.shiftKey) move(-1, 0); else move(1, 0);
      } else if (e.key === 'Tab') {
        e.preventDefault(); commitEdit(); move(0, e.shiftKey ? -1 : 1);
      } else if (e.key === 'Escape') {
        e.preventDefault(); cancelEdit();
      }
      e.stopPropagation();
    }

    // ---------- 撤销 / 重做 ----------
    function snapshot() { return rows.map(r => (r || []).slice()); }
    function pushUndo() {
      undoStack.push(snapshot());
      if (undoStack.length > MAX_UNDO) undoStack.shift();
      redoStack = [];
    }
    // 整表回写（宿主的 onRestore 把二维数组落到引擎；缺省则只更新镜像）
    function restore(snap) {
      rows = snap.map(r => r.slice());
      try {
        if (opts.onRestore) opts.onRestore(rows.map(r => r.slice()));
      } catch (e) { }
      render();
      if (opts.onEdit) opts.onEdit();
    }
    function undo() {
      if (!undoStack.length) return false;
      redoStack.push(snapshot());
      const snap = undoStack.pop();
      restore(snap);
      return true;
    }
    function redo() {
      if (!redoStack.length) return false;
      undoStack.push(snapshot());
      const snap = redoStack.pop();
      restore(snap);
      return true;
    }

    // ---------- 选区数据 / 剪贴板 ----------
    function getSelData() {
      const { r0, r1, c0, c1 } = selRect();
      const out = [];
      for (let r = r0; r <= r1; r++) {
        const row = [];
        for (let c = c0; c <= c1; c++) row.push(String(valueAt(r, c)));
        out.push(row);
      }
      return out;
    }
    function selText() { return getSelRawData().map(r => r.join('\t')).join('\n'); }

    // 复制的取数：用原始内容（公式单元格带 =），这样粘贴出去仍能重算（对齐 WPS）
    function getSelRawData() {
      const { r0, r1, c0, c1 } = selRect();
      const out = [];
      for (let r = r0; r <= r1; r++) {
        const row = [];
        for (let c = c0; c <= c1; c++) row.push(rawTextAt(r, c));
        out.push(row);
      }
      return out;
    }

    // 当前选区 → "A1" 或 "A1:C5" 文本
    function rangeText() {
      const { r0, r1, c0, c1 } = selRect();
      if (r0 === r1 && c0 === c1) return colName(c0) + (r0 + 1);
      return colName(c0) + (r0 + 1) + ':' + colName(c1) + (r1 + 1);
    }

    function copySel(cut) {
      copied = getSelRawData();
      const text = copied.map(r => r.join('\t')).join('\n');
      try { if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text); } catch (e) { }
      cutRect = cut ? selRect() : null;
      if (opts.onClipboard) { try { opts.onClipboard('copy', rangeText()); } catch (e) { } }
      return text;
    }
    function clearRect(rect) {
      for (let r = rect.r0; r <= rect.r1; r++)
        for (let c = rect.c0; c <= rect.c1; c++) setData(r, c, '', true);
      cutRect = null;
      render();
      flushDependents();
      if (opts.onEdit) opts.onEdit();
    }
    // 解析外部（系统剪贴板 / Excel / 网页表格）文本 → 二维数组
    function parseClipText(text) {
      if (!text) return [];
      const t = String(text).replace(/\r\n/g, '\n').replace(/\r/g, '\n').replace(/\n$/, '');
      return t.split('\n').map(line => line.split('\t'));
    }
    function pasteMatrix(matrix, at) {
      if (!matrix || !matrix.length) return false;
      pushUndo();
      const r0 = at && at.r != null ? at.r : selR;
      const c0 = at && at.c != null ? at.c : selC;
      let hasFormula = false;
      for (let i = 0; i < matrix.length; i++) {
        for (let j = 0; j < matrix[i].length; j++) {
          if (isFormulaText(matrix[i][j])) hasFormula = true;
          setData(r0 + i, c0 + j, matrix[i][j], true);
        }
      }
      // 粘贴后选区扩展到粘贴区域（WPS 行为）
      selR = r0; selC = c0;
      selR2 = r0 + matrix.length - 1;
      selC2 = c0 + Math.max(...matrix.map(m => m.length)) - 1;
      if (selR2 >= R || selC2 >= C || hasFormula || pendingDependents) {
        R = Math.max(R, selR2 + 1); C = Math.max(C, selC2 + 1);
        pendingDependents = false;
        loadRows();          // 含公式/依赖变化时重读，显示计算结果
        render();
      } else {
        paintSelection();
      }
      if (opts.onEdit) opts.onEdit();
      return true;
    }
    function pasteSel() {
      if (!copied || !copied.length) return false;
      if (cutRect) clearRect(cutRect);
      const ok = pasteMatrix(copied.map(r => r.slice()), { r: selR, c: selC });
      if (opts.onClipboard) { try { opts.onClipboard('paste', rangeText()); } catch (e) { } }
      return ok;
    }
    function clearSel() {
      const rect = selRect();
      const has = (() => {
        for (let r = rect.r0; r <= rect.r1; r++)
          for (let c = rect.c0; c <= rect.c1; c++) if (String(valueAt(r, c)) !== '') return true;
        return false;
      })();
      if (!has) return;
      pushUndo();
      for (let r = rect.r0; r <= rect.r1; r++)
        for (let c = rect.c0; c <= rect.c1; c++) setData(r, c, '', true);
      render();
      flushDependents();
      if (opts.onEdit) opts.onEdit();
    }
    // Ctrl+D 向下填充 / Ctrl+R 向右填充（WPS 支持）
    function fillDown() {
      const { r0, r1, c0, c1 } = selRect();
      if (r1 <= r0) return;
      pushUndo();
      for (let c = c0; c <= c1; c++) {
        const v = valueAt(r0, c);
        for (let r = r0 + 1; r <= r1; r++) setData(r, c, v, true);
      }
      render();
      flushDependents();
      if (opts.onEdit) opts.onEdit();
    }
    function fillRight() {
      const { r0, r1, c0, c1 } = selRect();
      if (c1 <= c0) return;
      pushUndo();
      for (let r = r0; r <= r1; r++) {
        const v = valueAt(r, c0);
        for (let c = c0 + 1; c <= c1; c++) setData(r, c, v, true);
      }
      render();
      flushDependents();
      if (opts.onEdit) opts.onEdit();
    }

    // ---------- 填充柄拖拽（WPS 拖拽填充）----------
    function applyFill(src, tgt) {
      const vertical = tgt.r1 > src.r1;
      const horizontal = tgt.c1 > src.c1;
      if (!vertical && !horizontal) return;
      pushUndo();
      if (vertical) {
        for (let c = src.c0; c <= src.c1; c++) {
          const vals = [];
          for (let r = src.r0; r <= src.r1; r++) vals.push(String(valueAt(r, c)));
          const allNum = vals.length >= 2 && vals.every(isNumeric);
          const step = allNum ? Number(vals[1]) - Number(vals[0]) : 0;
          for (let r = src.r1 + 1; r <= tgt.r1; r++) {
            let v;
            if (allNum) v = String(Number(vals[0]) + step * (r - src.r0));
            else v = vals[(r - src.r0) % vals.length];
            setData(r, c, v, true);
          }
        }
      }
      if (horizontal) {
        for (let r = src.r0; r <= src.r1; r++) {
          const vals = [];
          for (let c = src.c0; c <= src.c1; c++) vals.push(String(valueAt(r, c)));
          const allNum = vals.length >= 2 && vals.every(isNumeric);
          const step = allNum ? Number(vals[1]) - Number(vals[0]) : 0;
          for (let c = src.c1 + 1; c <= tgt.c1; c++) {
            let v;
            if (allNum) v = String(Number(vals[0]) + step * (c - src.c0));
            else v = vals[(c - src.c0) % vals.length];
            setData(r, c, v, true);
          }
        }
      }
      selR = src.r0; selC = src.c0; selR2 = tgt.r1; selC2 = tgt.c1;
      R = Math.max(R, tgt.r1 + 1); C = Math.max(C, tgt.c1 + 1);
      render();
      flushDependents();
      if (opts.onEdit) opts.onEdit();
    }
    function clearFillPreview() {
      if (!fillRect) return;
      for (let r = fillRect.r0; r <= fillRect.r1; r++)
        for (let c = fillRect.c0; c <= fillRect.c1; c++) {
          const td = getTd(r, c);
          if (td) td.classList.remove('fpv');
        }
      fillRect = null;
    }
    function paintFillPreview(tgt) {
      clearFillPreview();
      const src = drag && drag.src ? drag.src : selRect();
      const rect = {
        r0: src.r0, c0: src.c0,
        r1: Math.max(src.r1, tgt.r1), c1: Math.max(src.c1, tgt.c1)
      };
      for (let r = src.r0; r <= rect.r1; r++)
        for (let c = src.c0; c <= rect.c1; c++) {
          if (r <= src.r1 && c <= src.c1) continue;
          const td = getTd(r, c);
          if (td) td.classList.add('fpv');
        }
      fillRect = rect;
    }

    // ---------- 列宽 ----------
    function applyColWidth(c) {
      const w = colW[c];
      if (!w) return;
      const th = headMap.col.get(c);
      if (th) { th.style.width = w + 'px'; th.style.minWidth = w + 'px'; }
      for (let r = 0; r < R; r++) {
        const td = getTd(r, c);
        if (td) { td.style.width = w + 'px'; td.style.minWidth = w + 'px'; }
      }
    }
    function autoFitCol(c) {
      let maxLen = 2;
      for (let r = 0; r < rows.length; r++) {
        const v = String((rows[r] && rows[r][c]) != null ? rows[r][c] : '');
        let len = 0;
        for (const ch of v) len += ch.charCodeAt(0) > 255 ? 2 : 1;
        if (len > maxLen) maxLen = len;
      }
      colW[c] = Math.min(400, Math.max(48, maxLen * 7 + 18));
      applyColWidth(c);
    }

    // ---------- 结构操作（插入/删除行列）----------
    // 宿主提供 onStructure 时交给宿主（可走引擎、带公式平移与录制）；否则在镜像上操作
    function structure(action, index, count) {
      count = count || 1;
      if (opts.onStructure) {
        let handled = true;
        try { handled = opts.onStructure(action, index, count) !== false; } catch (e) { handled = false; }
        if (handled) { loadRows(); render(); if (opts.onEdit) opts.onEdit(); return; }
      }
      pushUndo();
      if (action === 'insertRowBefore' || action === 'insertRowAfter') {
        const at = action === 'insertRowBefore' ? index - 1 : index;
        for (let i = 0; i < count; i++) rows.splice(at, 0, new Array(C).fill(''));
      } else if (action === 'deleteRow') {
        rows.splice(index - 1, count);
      } else if (action === 'insertColBefore' || action === 'insertColAfter') {
        const at = action === 'insertColBefore' ? index - 1 : index;
        for (let r = 0; r < Math.max(rows.length, 1); r++) {
          if (!rows[r]) rows[r] = [];
          for (let i = 0; i < count; i++) rows[r].splice(at, 0, '');
        }
      } else if (action === 'deleteCol') {
        for (let r = 0; r < rows.length; r++) if (rows[r]) rows[r].splice(index - 1, count);
      } else if (action === 'clearRow') {
        for (let c = 0; c < C; c++) setData(index - 1, c, '', true);
      } else if (action === 'clearCol') {
        for (let r = 0; r < R; r++) setData(r, index - 1, '', true);
      }
      try { if (opts.onRestore) opts.onRestore(rows.map(r => r.slice())); } catch (e) { }
      render();
      flushDependents();
      if (opts.onEdit) opts.onEdit();
    }

    // ---------- 右键菜单 ----------
    function hideMenu() {
      if (menuEl && menuEl.parentNode) menuEl.parentNode.removeChild(menuEl);
      menuEl = null;
    }
    function showMenu(x, y, items) {
      hideMenu();
      menuEl = document.createElement('div');
      menuEl.className = 'xgrid-menu';
      items.forEach(it => {
        if (it.sep) { const d = document.createElement('div'); d.className = 'xsep'; menuEl.appendChild(d); return; }
        const d = document.createElement('div');
        d.className = 'xmi' + (it.disabled ? ' dis' : '');
        d.textContent = it.label;
        if (!it.disabled) d.addEventListener('click', () => { hideMenu(); it.action(); });
        menuEl.appendChild(d);
      });
      document.body.appendChild(menuEl);
      const w = menuEl.offsetWidth, h = menuEl.offsetHeight;
      menuEl.style.left = Math.min(x, window.innerWidth - w - 4) + 'px';
      menuEl.style.top = Math.min(y, window.innerHeight - h - 4) + 'px';
    }
    function colMenu(c) {
      return [
        { label: '在左侧插入列', action: () => structure('insertColBefore', c + 1) },
        { label: '在右侧插入列', action: () => structure('insertColAfter', c + 1) },
        { sep: true },
        { label: '删除此列', action: () => structure('deleteCol', c + 1) },
        { label: '清空此列内容', action: () => structure('clearCol', c + 1) },
        { sep: true },
        { label: '自动列宽', action: () => autoFitCol(c) }
      ];
    }
    function rowMenu(r) {
      return [
        { label: '在上方插入行', action: () => structure('insertRowBefore', r + 1) },
        { label: '在下方插入行', action: () => structure('insertRowAfter', r + 1) },
        { sep: true },
        { label: '删除此行', action: () => structure('deleteRow', r + 1) },
        { label: '清空此行内容', action: () => structure('clearRow', r + 1) }
      ];
    }
    function cellMenu() {
      return [
        { label: '剪切', action: () => { copySel(true); } },
        { label: '复制', action: () => { copySel(false); } },
        { label: '粘贴', action: () => { pasteSel(); } },
        { label: '清空内容', action: () => clearSel() },
        { sep: true },
        { label: '在上方插入行', action: () => structure('insertRowBefore', selRect().r0 + 1) },
        { label: '在左侧插入列', action: () => structure('insertColBefore', selRect().c0 + 1) }
      ];
    }

    // ---------- 查找 / 替换 ----------
    function closeFind() {
      if (barEl) { barEl.remove(); barEl = null; }
      clearHits();
      container.focus();
    }
    function clearHits() {
      for (const td of cellMap.values()) td.classList.remove('xhit', 'cur');
    }
    function doFind(dir) {
      const q = barEl.querySelector('.xfind-q').value.trim();
      clearHits();
      findState.q = q;
      if (!q) { barEl.querySelector('.xfind-info').textContent = ''; findState.hits = []; return; }
      const lq = q.toLowerCase();
      const hits = [];
      for (let r = 0; r < rows.length; r++) {
        const row = rows[r] || [];
        for (let c = 0; c < row.length; c++) {
          if (String(row[c] == null ? '' : row[c]).toLowerCase().includes(lq)) hits.push({ r, c });
        }
      }
      findState.hits = hits;
      hits.forEach(h => { const td = getTd(h.r, h.c); if (td) td.classList.add('xhit'); });
      const info = barEl.querySelector('.xfind-info');
      if (!hits.length) { info.textContent = '未找到'; findState.idx = -1; return; }
      const start = dir >= 0 ? findState.idx + 1 : findState.idx - 1;
      const idx = ((start % hits.length) + hits.length) % hits.length;
      gotoHit(idx);
    }
    function gotoHit(idx) {
      const hits = findState.hits;
      if (!hits.length) return;
      findState.idx = idx;
      for (const td of cellMap.values()) td.classList.remove('cur');
      const cur = hits[idx];
      setSel(cur.r, cur.c, false);
      const td = getTd(cur.r, cur.c);
      if (td) td.classList.add('cur');
      barEl.querySelector('.xfind-info').textContent = (idx + 1) + '/' + hits.length;
    }
    function replaceOne() {
      if (findState.idx < 0 || !findState.hits.length) return;
      const { r, c } = findState.hits[findState.idx];
      const rep = barEl.querySelector('.xfind-r').value;
      pushUndo();
      setData(r, c, rep, true);
      const td = getTd(r, c);
      if (td) { td.querySelector('.xv').textContent = rep; td.classList.toggle('num', isNumeric(rep)); }
      if (opts.onEdit) opts.onEdit(r, c, rep);
      doFind(1);
    }
    function replaceAll() {
      const q = barEl.querySelector('.xfind-q').value.trim();
      const rep = barEl.querySelector('.xfind-r').value;
      if (!q) return;
      pushUndo();
      let n = 0;
      for (let r = 0; r < rows.length; r++) {
        const row = rows[r] || [];
        for (let c = 0; c < row.length; c++) {
          const v = String(row[c] == null ? '' : row[c]);
          if (v.toLowerCase().includes(q.toLowerCase())) {
            const nv = v.split(q).join(rep);
            setData(r, c, nv, true); n++;
          }
        }
      }
      render();
      if (opts.onEdit) opts.onEdit();
      barEl.querySelector('.xfind-info').textContent = '已替换 ' + n + ' 处';
    }
    function openFind() {
      if (barEl) { barEl.querySelector('.xfind-q').focus(); return; }
      barEl = document.createElement('div');
      barEl.className = 'xfind';
      barEl.innerHTML = `<input class="xfind-q" placeholder="查找"><input class="xfind-r" placeholder="替换为">
        <button data-a="prev">上一个</button><button data-a="next">下一个</button>
        <button data-a="rep">替换</button><button data-a="repall">全部替换</button>
        <button data-a="close">✕</button><span class="xfind-info"></span>`;
      container.insertBefore(barEl, container.firstChild);
      const q = barEl.querySelector('.xfind-q');
      q.value = String(valueAt(selR, selC)) || '';
      barEl.querySelectorAll('button').forEach(b => on(b, 'click', () => {
        const a = b.dataset.a;
        if (a === 'prev') doFind(-1);
        else if (a === 'next') doFind(1);
        else if (a === 'rep') replaceOne();
        else if (a === 'repall') replaceAll();
        else closeFind();
      }));
      on(q, 'keydown', (e) => {
        e.stopPropagation();
        if (e.key === 'Enter') { e.preventDefault(); doFind(e.shiftKey ? -1 : 1); }
        else if (e.key === 'Escape') closeFind();
      });
      on(barEl.querySelector('.xfind-r'), 'keydown', (e) => {
        e.stopPropagation();
        if (e.key === 'Enter') { e.preventDefault(); replaceOne(); }
        else if (e.key === 'Escape') closeFind();
      });
      q.focus();
      q.select();
    }

    // ---------- 键盘 ----------
    function onGridKey(e) {
      if (editing) return;
      const t = e.target;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA')) return; // 查找框等
      const k = e.key;
      const ctrl = e.ctrlKey || e.metaKey;
      const arrows = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
      if (arrows[k]) {
        e.preventDefault();
        const [dr, dc] = arrows[k];
        if (ctrl) jumpEdge(dr, dc);
        else move(dr, dc, e.shiftKey);
      }
      else if (k === 'Enter') { e.preventDefault(); move(e.shiftKey ? -1 : 1, 0); }
      else if (k === 'Tab') { e.preventDefault(); move(0, e.shiftKey ? -1 : 1); }
      else if (k === 'F2') { e.preventDefault(); startEdit(selR, selC); }
      else if (k === 'Delete' || k === 'Backspace') { e.preventDefault(); clearSel(); }
      else if (k === 'Home') { e.preventDefault(); move(0, -selC); }
      else if (k === 'End') { e.preventDefault(); move(0, C - 1 - selC); }
      else if (k === 'PageUp') { e.preventDefault(); move(-20, 0, e.shiftKey); }
      else if (k === 'PageDown') { e.preventDefault(); move(20, 0, e.shiftKey); }
      else if (ctrl && (k === 'c' || k === 'C')) { e.preventDefault(); copySel(false); }
      else if (ctrl && (k === 'x' || k === 'X')) { e.preventDefault(); copySel(true); }
      else if (ctrl && (k === 'v' || k === 'V')) { e.preventDefault(); pasteSel(); }
      else if (ctrl && (k === 'z' || k === 'Z')) { e.preventDefault(); if (e.shiftKey) redo(); else undo(); }
      else if (ctrl && (k === 'y' || k === 'Y')) { e.preventDefault(); redo(); }
      else if (ctrl && (k === 'd' || k === 'D')) { e.preventDefault(); fillDown(); }
      else if (ctrl && (k === 'r' || k === 'R')) { e.preventDefault(); fillRight(); }
      else if (ctrl && (k === 'f' || k === 'F')) { e.preventDefault(); openFind(); }
      else if (ctrl && (k === 'a' || k === 'A')) {
        e.preventDefault();
        selR = 0; selC = 0; selR2 = R - 1; selC2 = C - 1;
        painted = null; paintSelection();
      }
      else if (!ctrl && !e.altKey && k && k.length === 1) {
        e.preventDefault();
        startEdit(selR, selC, k);
      }
    }

    // ---------- 事件委托 ----------
    function tdFrom(e) {
      const td = e.target.closest ? e.target.closest('td.xcell') : null;
      return td;
    }
    on(table, 'mousedown', (e) => {
      // 1) 行头 / 列头（含拖拽多选）
      const rowTh = e.target.closest('th.rowhead');
      const colTh = e.target.closest('th.colhead');
      const corner = e.target.closest('th.corner');
      const grip = e.target.closest('.xgrip');
      if (grip) {
        e.preventDefault(); e.stopPropagation();
        const c = +grip.dataset.grip;
        drag = { type: 'resize', c, startX: e.clientX, startW: colW[c] || headMap.col.get(c).offsetWidth };
        return;
      }
      if (corner) {
        e.preventDefault();
        selR = 0; selC = 0; selR2 = R - 1; selC2 = C - 1;
        painted = null; paintSelection(); container.focus();
        return;
      }
      if (rowTh) {
        e.preventDefault();
        const r = +rowTh.dataset.r;
        selR = r; selR2 = r; selC = 0; selC2 = C - 1;
        drag = { type: 'rowsel', r };
        painted = null; paintSelection(); container.focus();
        return;
      }
      if (colTh) {
        e.preventDefault();
        const c = +colTh.dataset.c;
        selC = c; selC2 = c; selR = 0; selR2 = R - 1;
        drag = { type: 'colsel', c };
        painted = null; paintSelection(); container.focus();
        return;
      }
      // 2) 单元格
      const td = tdFrom(e);
      if (!td) return;
      if (e.button === 2) { // 右键：保留选中
        if (!td.classList.contains('sel')) {
          const r = +td.dataset.r, c = +td.dataset.c;
          selR = selR2 = r; selC = selC2 = c;
          painted = null; paintSelection();
        }
        return;
      }
      if (e.button !== 0) return;
      if (editing) commitEdit();
      container.focus();
      drag = { type: 'select' };
      const r = +td.dataset.r, c = +td.dataset.c;
      selR = selR2 = r; selC = selC2 = c;
      painted = null; paintSelection();
      e.preventDefault();
    });

    on(table, 'mouseover', (e) => {
      if (!drag) return;
      if (drag.type === 'rowsel') {
        const th = e.target.closest('th.rowhead') || tdFrom(e);
        if (!th) return;
        const r = +th.dataset.r;
        selR = Math.min(drag.r, r); selR2 = Math.max(drag.r, r);
        selC = 0; selC2 = C - 1;
        painted = null; paintSelection();
        return;
      }
      if (drag.type === 'colsel') {
        const th = e.target.closest('th.colhead') || tdFrom(e);
        if (!th) return;
        const c = +th.dataset.c;
        selC = Math.min(drag.c, c); selC2 = Math.max(drag.c, c);
        selR = 0; selR2 = R - 1;
        painted = null; paintSelection();
        return;
      }
      const td = tdFrom(e);
      if (!td) return;
      const r = +td.dataset.r, c = +td.dataset.c;
      if (drag.type === 'fill') {
        const src = drag.src;
        const tgt = { r0: src.r0, c0: src.c0, r1: Math.max(src.r1, r), c1: Math.max(src.c1, c) };
        paintFillPreview(tgt);
        return;
      }
      if (drag.type === 'select') {
        selR2 = r; selC2 = c;
        paintSelection();
      }
    });

    on(table, 'dblclick', (e) => {
      const grip = e.target.closest('.xgrip');
      if (grip) { autoFitCol(+grip.dataset.grip); return; }
      const td = tdFrom(e);
      if (td) startEdit(+td.dataset.r, +td.dataset.c);
    });

    on(table, 'contextmenu', (e) => {
      const rowTh = e.target.closest('th.rowhead');
      const colTh = e.target.closest('th.colhead');
      const td = tdFrom(e);
      if (rowTh) { e.preventDefault(); showMenu(e.clientX, e.clientY, rowMenu(+rowTh.dataset.r)); return; }
      if (colTh) { e.preventDefault(); showMenu(e.clientX, e.clientY, colMenu(+colTh.dataset.c)); return; }
      if (td) {
        e.preventDefault();
        const r = +td.dataset.r, c = +td.dataset.c;
        if (!td.classList.contains('sel')) { selR = selR2 = r; selC = selC2 = c; painted = null; paintSelection(); }
        showMenu(e.clientX, e.clientY, cellMenu());
      }
    });

    // 填充柄拖拽
    on(fillEl, 'mousedown', (e) => {
      e.preventDefault(); e.stopPropagation();
      drag = { type: 'fill', src: selRect() };
    });

    // 系统剪贴板：跨应用复制/粘贴（WPS 面板 ↔ 网页 ↔ 本工具）
    on(container, 'copy', (e) => {
      if (editing) return;
      const text = selText();
      e.clipboardData.setData('text/plain', text);
      copied = getSelData();
      e.preventDefault();
    });
    on(container, 'cut', (e) => {
      if (editing) return;
      const text = selText();
      e.clipboardData.setData('text/plain', text);
      copied = getSelData();
      cutRect = selRect();
      e.preventDefault();
    });
    on(container, 'paste', (e) => {
      if (editing) return;
      const text = (e.clipboardData || window.clipboardData).getData('text/plain');
      if (!text) return;
      e.preventDefault();
      if (cutRect) clearRect(cutRect);
      pasteMatrix(parseClipText(text), { r: selR, c: selC });
    });

    on(container, 'keydown', onGridKey);
    on(container, 'mousedown', (e) => {
      if (e.target.closest && e.target.closest('.xfind, .xgrid-menu')) return;
      container.focus();
    });

    // 全局：拖拽结束（每个实例自己的标记，避免相互干扰）
    on(document, 'mouseup', () => {
      if (!drag) return;
      if (drag.type === 'resize') { applyColWidth(drag.c); }
      else if (drag.type === 'fill') {
        const src = drag.src;
        const tgt = fillRect || src;
        clearFillPreview();
        applyFill(src, tgt);
      }
      drag = null;
      updateFillHandle();
    });
    on(document, 'mousemove', (e) => {
      if (!drag || drag.type !== 'resize') return;
      const w = Math.max(30, drag.startW + (e.clientX - drag.startX));
      colW[drag.c] = w;
      applyColWidth(drag.c);
    });
    on(document, 'mousedown', (e) => {
      if (menuEl && !(e.target.closest && e.target.closest('.xgrid-menu'))) hideMenu();
    });
    on(document, 'keydown', (e) => { if (e.key === 'Escape') hideMenu(); });

    // ---------- 初始化 ----------
    loadRows();
    render();

    const api = {
      reload() { loadRows(); render(); },
      refresh() { loadRows(); render(); },
      getSel() { return { r: selR, c: selC }; },
      getSelRange() {
        const { r0, r1, c0, c1 } = selRect();
        if (r0 === r1 && c0 === c1) return colName(c0) + (r0 + 1);
        return colName(c0) + (r0 + 1) + ':' + colName(c1) + (r1 + 1);
      },
      getSelValue() { return String(valueAt(selR, selC)); },
      getSelData() { return getSelData(); },
      getRows() { return rows; },
      getStats() { return selStats; },
      setSel(r, c) { setSel(r, c, false); scrollIntoView(r, c); },
      edit() { startEdit(selR, selC); },
      undo, redo,
      canUndo() { return undoStack.length > 0; },
      canRedo() { return redoStack.length > 0; },
      copy() { return copySel(false); },
      paste() { return pasteSel(); },
      clear() { clearSel(); },
      fillDown, fillRight,
      find: openFind,
      setColWidth(c, w) { colW[c] = w; applyColWidth(c); },
      destroy() { try { ac.abort(); } catch (e) { } if (barEl) barEl.remove(); hideMenu(); container.__xgridApi = null; }
    };
    container.__xgridApi = api;
    // 构造完成后（宿主已拿到 api）补发一次初始状态：
    // 放到宏任务里，确保 `const gridApi = ExcelGrid(...)` 这条赋值语句已经执行完
    setTimeout(() => {
      ready = true;
      if (opts.onSelectChange) { try { opts.onSelectChange(selR, selC); } catch (e) { } }
      if (opts.onStats && selStats) { try { opts.onStats(selStats, selRect()); } catch (e) { } }
    }, 0);
    return api;
  };

  // 宿主通用接线：把网格的结构操作/整表回写接到 Excel 引擎（三个宿主复用，避免重复代码）
  window.ExcelGrid.engineHooks = function (Engine, gridApi, after) {
    return {
      onStructure(action, index, count) {
        try {
          switch (action) {
            case 'insertRowBefore': Engine.excelInsertRow(index, count); break;
            case 'insertRowAfter': Engine.excelInsertRow(index + 1, count); break;
            case 'deleteRow': Engine.excelDeleteRow(index, count); break;
            case 'insertColBefore': Engine.excelInsertCol(index, count); break;
            case 'insertColAfter': Engine.excelInsertCol(index + 1, count); break;
            case 'deleteCol': Engine.excelDeleteCol(index, count); break;
            default: return false;
          }
        } catch (e) { return false; }
        if (after) after();
        return true;
      },
      onRestore(rows) {
        try { Engine.setSheetValues(rows); } catch (e) { }
        if (after) after();
      }
    };
  };
})();

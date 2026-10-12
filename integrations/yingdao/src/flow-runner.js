// ============ 世博自动化 流程运行器（双击 .bat 即可运行导出的流程） ============
// 独立运行时：读取同目录 flow.json，依次执行流程步骤。
// 支持：Excel 全套、文件操作、变量、循环/条件、等待、打印日志。
// 不支持：浏览器自动化、鼠标键盘（需完整版世博自动化），遇到时提示并跳过。
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
let XLSX = null;
// 依赖加载顺序：导出的 node_modules/xlsx（完整 Node 版，优先）-> 程序内置的
// xlsx.full.min.js（浏览器版，离线兜底）-> 全局 xlsx
try { XLSX = require(path.join(ROOT, 'node_modules', 'xlsx')); } catch (e) {
  try { XLSX = require(path.join(ROOT, 'xlsx.full.min.js')); } catch (e2) {
    try { XLSX = require('xlsx'); } catch (e3) { XLSX = null; }
  }
}

// ---------- xlsx 读写适配 ----------
// 上面加载到的可能是两种 xlsx：
//   a) npm 版（node_modules/xlsx）—— 内部绑定了 fs，readFile/writeFile 直接能用
//   b) 浏览器版（xlsx.full.min.js）—— 打包时把 fs 剥掉了，
//      XLSX.writeFile 会抛 "cannot save file xxx"，readFile 同样不可用
// 所以统一走下面两个包装：能用 readFile/writeFile 就用，否则退化成
// "读 Buffer / 写 Buffer"，两种版本行为一致。
let XLSX_HAS_FS = null;   // 懒探测，只做一次

function xlsxHasFs() {
  if (XLSX_HAS_FS !== null) return XLSX_HAS_FS;
  try {
    const probe = path.join(require('os').tmpdir(), '__yd_xlsx_probe_' + process.pid + '.xlsx');
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet([['probe']]), 'S');
    XLSX.writeFile(wb, probe);
    try { fs.unlinkSync(probe); } catch (e) { }
    XLSX_HAS_FS = true;
  } catch (e) {
    XLSX_HAS_FS = false;
  }
  return XLSX_HAS_FS;
}

function readBook(fp) {
  return xlsxHasFs() ? XLSX.readFile(fp) : XLSX.read(fs.readFileSync(fp), { type: 'buffer' });
}

function writeBook(book, fp) {
  if (xlsxHasFs()) { XLSX.writeFile(book, fp); return; }
  fs.writeFileSync(fp, XLSX.write(book, { bookType: 'xlsx', type: 'buffer' }));
}

// ---------- Excel 状态 ----------
let excelBooks = [];      // [{ id, book, path, activeSheet }]
let activeBookId = null;
let bookIdSeq = 1;

// ---------- 变量 & 日志 ----------
const vars = {};
let flow = null;          // 兼容旧格式：单流程数组
let flows = { '主流程': [] };  // 新格式：{ 流程名: 步骤数组 }

function log(msg) { console.log(msg); }

// ---------- 工具 ----------
function expand(text) {
  if (typeof text !== 'string') return text;
  return text.replace(/\$\{([\u4e00-\u9fa5\w]+)(?:\[(\d+)\])?\}/g, (_, k, idx) => {
    const v = vars[k];
    if (idx !== undefined) {
      if (Array.isArray(v)) return v[Number(idx)] ?? '';
      return Number(idx) === 0 ? (v ?? '') : '';
    }
    if (Array.isArray(v)) return v.length ? v[0] : '';
    if (v && typeof v === 'object') { try { return JSON.stringify(v); } catch (e) { return String(v); } }
    return v ?? '';
  });
}
function parseCell(addr) {
  const m = /^([A-Za-z]+)(\d+)$/.exec(String(addr).trim());
  if (!m) throw new Error('无效单元格地址: ' + addr);
  let col = 0;
  for (const ch of m[1].toUpperCase()) col = col * 26 + (ch.charCodeAt(0) - 64);
  return { c: col - 1, r: parseInt(m[2], 10) - 1 };
}
function colName(c) {
  let s = ''; c += 1;
  while (c > 0) { const m = (c - 1) % 26; s = String.fromCharCode(65 + m) + s; c = Math.floor((c - 1) / 26); }
  return s;
}
function parseRange(range) {
  const parts = String(range).split(':');
  const a = parseCell(parts[0]);
  const b = parts[1] ? parseCell(parts[1]) : a;
  return { r0: Math.min(a.r, b.r), c0: Math.min(a.c, b.c), r1: Math.max(a.r, b.r), c1: Math.max(a.c, b.c) };
}
function scanCells(ws) {
  let maxR = -1, maxC = -1;
  const list = [];
  Object.keys(ws).forEach(key => {
    if (key[0] === '!') return;
    let pos; try { pos = parseCell(key); } catch (e) { return; }
    if (pos.r > maxR) maxR = pos.r;
    if (pos.c > maxC) maxC = pos.c;
    list.push({ r: pos.r, c: pos.c, addr: key, cell: ws[key] });
  });
  return { maxR, maxC, list };
}
function makeCell(v) {
  const s = String(v == null ? '' : v);
  const t = s.trim();
  if (/^=/.test(t) && t.length > 1) return { t: 's', f: t.replace(/^=/, ''), v: '' };
  const numLike = /^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/.test(t);
  const leadingZero = /^[+-]?0\d/.test(t);
  const tooLong = /^[+-]?\d{16,}$/.test(t);
  if (numLike && !leadingZero && !tooLong) return { t: 'n', v: Number(t) };
  return { t: 's', v: s };
}
function getActiveBook() { return excelBooks.find(b => b.id === activeBookId) || null; }
function getWS() {
  const book = getActiveBook();
  if (!book) throw new Error('请先打开或新建Excel');
  const sheetName = book.activeSheet || book.book.SheetNames[0];
  return book.book.Sheets[sheetName];
}
function findBook(ref) {
  const s = String(ref == null ? '' : ref).trim();
  if (s === '' || s === '当前' || s === '当前表格') return getActiveBook();
  const byId = excelBooks.find(b => b.id === s); if (byId) return byId;
  const byPath = excelBooks.find(b => b.path === s); if (byPath) return byPath;
  return excelBooks.find(b => { if (!b.path) return false; const base = b.path.split(/[\\/]/).pop(); return base === s || base.replace(/\.[^.]+$/, '') === s; }) || null;
}
function refreshRef(ws) {
  const { maxR, maxC } = scanCells(ws);
  ws['!ref'] = (maxR >= 0 && maxC >= 0) ? ('A1:' + colName(maxC) + (maxR + 1)) : 'A1:A1';
}

// ---------- Excel 指令 ----------
function excelOpen(p) {
  if (!XLSX) throw new Error('缺少 xlsx 依赖：请确认本文件夹内有 xlsx.full.min.js（或 node_modules/xlsx）');
  const fp = expand(p);
  if (!fp || !fs.existsSync(fp)) throw new Error('文件不存在：' + fp);
  const book = readBook(fp);
  const id = 'e' + (bookIdSeq++);
  excelBooks.push({ id, book, path: fp, activeSheet: book.SheetNames[0] });
  activeBookId = id;
}
function excelNew(p, sheetName) {
  if (!XLSX) throw new Error('缺少 xlsx 依赖：请确认本文件夹内有 xlsx.full.min.js（或 node_modules/xlsx）');
  let fp = expand(p);
  if (!fp) fp = path.join(ROOT, '新建Excel_' + Date.now() + '.xlsx');
  const book = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(book, XLSX.utils.aoa_to_sheet([]), sheetName || 'Sheet1');
  const id = 'e' + (bookIdSeq++);
  excelBooks.push({ id, book, path: fp, activeSheet: sheetName || 'Sheet1' });
  activeBookId = id;
}
function excelRead(cell) { const ws = getWS(); return ws[cell] ? ws[cell].v : ''; }
function excelWrite(cell, value) { const ws = getWS(); ws[expand(cell)] = makeCell(expand(value)); refreshRef(ws); }
function excelReadRange(range) {
  const ws = getWS(); const { r0, c0, r1, c1 } = parseRange(range); const out = [];
  for (let r = r0; r <= r1; r++) { const row = []; for (let c = c0; c <= c1; c++) { const a = colName(c) + (r + 1); row.push(ws[a] ? ws[a].v : ''); } out.push(row); }
  return out;
}
function excelWriteRange(startCell, data) {
  const ws = getWS(); const { r, c } = parseCell(startCell);
  if (!Array.isArray(data)) throw new Error('写入区域需要二维数组变量');
  data.forEach((row, ri) => {
    if (!Array.isArray(row)) { ws[colName(c) + (r + ri + 1)] = makeCell(row); return; }
    row.forEach((val, ci) => { ws[colName(c + ci) + (r + ri + 1)] = makeCell(val); });
  });
  refreshRef(ws);
}
function excelCopyPaste(from, to, mode) {
  const ws = getWS(); const s = parseRange(from); const d = parseCell(to);
  const dr = s.r1 - s.r0, dc = s.c1 - s.c0;
  for (let r = s.r0; r <= s.r1; r++) {
    for (let c = s.c0; c <= s.c1; c++) {
      const sa = colName(c) + (r + 1); const da = colName(d.c + (c - s.c0)) + (d.r + (r - s.r0) + 1);
      const cell = ws[sa];
      if (mode === '只粘贴值') ws[da] = makeCell(cell ? (cell.v ?? '') : '');
      else if (mode === '只粘贴公式') { if (cell && cell.f) ws[da] = { t: 'n', f: cell.f, v: cell.v }; else delete ws[da]; }
      else { if (cell) ws[da] = { ...cell }; else delete ws[da]; }
    }
  }
  refreshRef(ws);
}
function excelSheetCopyPaste(fromBook, fromSheet, fromRange, toBook, toSheet, toRange, mode) {
  const srcRec = findBook(fromBook) || getActiveBook();
  const dstRec = findBook(toBook) || getActiveBook();
  const srcWs = srcRec.book.Sheets[fromSheet || srcRec.activeSheet || srcRec.book.SheetNames[0]];
  const dstWs = dstRec.book.Sheets[toSheet || dstRec.activeSheet || dstRec.book.SheetNames[0]];
  if (!srcWs || !dstWs) throw new Error('工作表不存在');
  const s = parseRange(fromRange), d = parseCell(toRange);
  for (let r = s.r0; r <= s.r1; r++) {
    for (let c = s.c0; c <= s.c1; c++) {
      const sa = colName(c) + (r + 1); const da = colName(d.c + (c - s.c0)) + (d.r + (r - s.r0) + 1);
      const cell = srcWs[sa];
      if (mode === '只粘贴值') dstWs[da] = makeCell(cell ? (cell.v ?? '') : '');
      else { if (cell) dstWs[da] = { ...cell }; else delete dstWs[da]; }
    }
  }
  refreshRef(dstWs);
}

// 指定列范围内最后一个有数据的行（0 基；无数据返回 -1）
function lastRowOf(ws, c0, c1) {
  let last = -1;
  Object.keys(ws).forEach(key => {
    if (key[0] === '!') return;
    let pos;
    try { pos = parseCell(key); } catch (e) { return; }
    if (pos.c >= c0 && pos.c <= c1 && pos.r > last) last = pos.r;
  });
  return last;
}

// ===== 白话「表格复制粘贴」：两张表之间按文件路径来（不需要先打开表格）=====
// 解析「复制哪几列/区域」，支持这些写法（多个用 , ， ; ； 或空格分隔）：
//   A1-A9 / A1:A9   区域（- 和 : 都认）    A1  单个单元格
//   A               整列（该列有数据的部分） A:C / A-C  连续多整列
//   留空            = 整个表格已用区域
function parsePickSegments(rangesText, ws) {
  const scan = scanCells(ws);
  if (scan.maxR < 0 || scan.maxC < 0) throw new Error('源表格是空的，没有内容可以复制');
  const whole = { r0: 0, c0: 0, r1: scan.maxR, c1: scan.maxC };
  const raw = String(rangesText == null ? '' : rangesText).trim();
  if (!raw) return [whole];
  const parts = raw.split(/[,，;；\s]+/).map(s => s.trim()).filter(Boolean);
  const out = [];
  for (const part of parts) {
    const t = part.replace(/[\u2010-\u2015\u2212\uFF0D]/g, '-');
    let m;
    try {
      if ((m = /^([A-Za-z]{1,3})(?:列)?$/.exec(t))) {
        // 整列 A / A列：只取该列有数据的部分
        const c = parseCell(m[1] + '1').c;
        out.push({ r0: 0, c0: c, r1: Math.max(0, lastRowOf(ws, c, c)), c1: c });
      } else if ((m = /^([A-Za-z]{1,3})[-:]([A-Za-z]{1,3})$/.exec(t))) {
        // 连续多整列 A:C：同样只取这些列有数据的部分
        const c1 = parseCell(m[1] + '1').c, c2 = parseCell(m[2] + '1').c;
        const lo = Math.min(c1, c2), hi = Math.max(c1, c2);
        out.push({ r0: 0, c0: lo, r1: Math.max(0, lastRowOf(ws, lo, hi)), c1: hi });
      } else {
        const segs = t.replace(/-/g, ':').split(':');
        const a = parseCell(segs[0]);
        const b = segs[1] ? parseCell(segs[1]) : a;
        out.push({ r0: Math.min(a.r, b.r), c0: Math.min(a.c, b.c), r1: Math.max(a.r, b.r), c1: Math.max(a.c, b.c) });
      }
    } catch (e) {
      throw new Error('看不懂「' + part + '」这种写法。正确示例：A1-A9,B2-B4（也支持 A1:A9、A、A:C）');
    }
  }
  return out.length ? out : [whole];
}

// 空格子判断：没有单元格对象、或值是空串/空值
function isEmptyCell(cell) {
  return !cell || cell.v === undefined || cell.v === null || cell.v === '';
}

// 把 srcWs 的 seg 区域按 mode 写到 dstWs 的（startR, startC）处
function pasteSegmentTo(srcWs, seg, dstWs, startR, startC, mode) {
  const h = seg.r1 - seg.r0 + 1, w = seg.c1 - seg.c0 + 1;
  for (let r = 0; r < h; r++) {
    for (let c = 0; c < w; c++) {
      const srcAddr = colName(seg.c0 + c) + (seg.r0 + r + 1);
      const dstAddr = colName(startC + c) + (startR + r + 1);
      const cell = srcWs[srcAddr];
      switch (mode) {
        case '只粘贴文本':
          // 一律落成文本：公式、数字都变成屏幕上看见的字，不会被 Excel 重新计算
          if (isEmptyCell(cell)) delete dstWs[dstAddr];
          else dstWs[dstAddr] = { t: 's', v: String(cell.v) };
          break;
        case '只粘贴值':
          if (isEmptyCell(cell)) delete dstWs[dstAddr];
          else dstWs[dstAddr] = makeCell(cell.v);
          break;
        case '只粘贴公式': if (cell && cell.f) dstWs[dstAddr] = { t: 'n', f: cell.f, v: cell.v }; else delete dstWs[dstAddr]; break;
        case '只粘贴格式': if (cell && cell.s) { if (!dstWs[dstAddr]) dstWs[dstAddr] = { t: 's', v: '' }; dstWs[dstAddr].s = cell.s; } break;
        case '保留公式':
          if (cell && cell.f) dstWs[dstAddr] = { t: 'n', f: cell.f, v: cell.v };
          else if (cell) dstWs[dstAddr] = makeCell(cell.v ?? '');
          else delete dstWs[dstAddr];
          break;
        case '值与数字格式':
          if (isEmptyCell(cell)) { delete dstWs[dstAddr]; break; }
          dstWs[dstAddr] = makeCell(cell.v);
          if (cell.s) dstWs[dstAddr].s = cell.s;
          break;
        case '公式与数字格式': if (cell && cell.f) { dstWs[dstAddr] = { t: 'n', f: cell.f, v: cell.v }; if (cell.s) dstWs[dstAddr].s = cell.s; } break;
        case '不覆盖原有内容': if (dstWs[dstAddr]) break; if (cell) dstWs[dstAddr] = makeCell(cell.v ?? ''); break;
        case '全部粘贴':
        default: if (cell) dstWs[dstAddr] = { ...cell }; else delete dstWs[dstAddr]; break;
      }
    }
  }
}

// 白话：源表格的几列/区域 → 目标表格的指定起始单元格，可选保存
// 多段区域依次横排：第 1 段从起始列开始，第 2 段接在第 1 段右边，以此类推
function excelTableCopyPaste(p) {
  if (!XLSX) throw new Error('缺少 xlsx 依赖：请确认本文件夹内有 xlsx.full.min.js（或 node_modules/xlsx）');
  p = p || {};

  const fromPath = expand(p.fromPath);
  if (!fromPath) throw new Error('请填写①源表格路径');
  if (!fs.existsSync(fromPath)) throw new Error('①源表格不存在：' + fromPath);
  let srcBook;
  try { srcBook = readBook(fromPath); }
  catch (e) { throw new Error('①源表格打不开（文件损坏或被占用）：' + fromPath); }
  const srcSheetName = (p.fromSheet && srcBook.Sheets[p.fromSheet]) ? p.fromSheet : srcBook.SheetNames[0];
  const srcWs = srcBook.Sheets[srcSheetName];
  if (!srcWs) throw new Error('①源表格里没有工作表');

  const segments = parsePickSegments(p.fromRanges, srcWs);

  const toPathIn = expand(p.toPath);
  let dstBook, dstPath, dstSheetName;
  if (toPathIn) {
    dstPath = toPathIn;
    if (fs.existsSync(dstPath)) {
      try { dstBook = readBook(dstPath); }
      catch (e) { throw new Error('④目标表格打不开（文件损坏或被占用）：' + dstPath); }
      dstSheetName = (p.toSheet && dstBook.Sheets[p.toSheet]) ? p.toSheet : dstBook.SheetNames[0];
    } else {
      dstBook = XLSX.utils.book_new();
      dstSheetName = p.toSheet || 'Sheet1';
      XLSX.utils.book_append_sheet(dstBook, XLSX.utils.aoa_to_sheet([]), dstSheetName);
    }
  } else {
    dstPath = path.join(ROOT, '表格复制粘贴_' + Date.now() + '.xlsx');
    dstBook = XLSX.utils.book_new();
    dstSheetName = p.toSheet || 'Sheet1';
    XLSX.utils.book_append_sheet(dstBook, XLSX.utils.aoa_to_sheet([]), dstSheetName);
  }
  const dstWs = dstBook.Sheets[dstSheetName];
  if (!dstWs) throw new Error('④目标表格里没有工作表：' + dstSheetName);

  const startText = String(expand(p.toCell) || 'A1').trim() || 'A1';
  let start;
  try { start = parseCell(startText); }
  catch (e) { throw new Error('⑥「' + startText + '」不是有效的起始单元格，正确示例：A1、B1、D2'); }

  const mode = p.mode || '只粘贴文本';
  let colOffset = 0, maxH = 0;
  segments.forEach(seg => {
    const h = seg.r1 - seg.r0 + 1;
    if (h > maxH) maxH = h;
    pasteSegmentTo(srcWs, seg, dstWs, start.r, start.c + colOffset, mode);
    colOffset += Math.max(1, seg.c1 - seg.c0 + 1);
  });

  const sc = scanCells(dstWs);
  dstWs['!ref'] = (sc.maxR >= 0 && sc.maxC >= 0) ? ('A1:' + colName(sc.maxC) + (sc.maxR + 1)) : 'A1:A1';

  const wantSave = p.save !== '不保存';
  if (wantSave) writeBook(dstBook, dstPath);

  const endAddr = colName(start.c + Math.max(0, colOffset - 1)) + (start.r + Math.max(1, maxH));
  log('表格复制粘贴：源「' + srcSheetName + '」' + segments.length + ' 段 → 目标「' + dstSheetName +
      '」' + startText + ':' + endAddr + '（' + mode + '）' +
      (wantSave ? '，已保存到 ' + dstPath : '，未保存'));
  vars['表格复制粘贴结果'] = dstPath;
  return dstPath;
}
function excelInsertRow(row, count) {
  const ws = getWS(); count = Math.max(1, Number(count) || 1); const { maxR, maxC } = scanCells(ws);
  for (let r = maxR; r >= row - 1; r--) for (let c = 0; c <= maxC; c++) { const s = colName(c) + (r + 1); const d = colName(c) + (r + 1 + count); if (ws[s]) { ws[d] = ws[s]; delete ws[s]; } }
  refreshRef(ws);
}
function excelInsertCol(col, count) {
  const ws = getWS(); count = Math.max(1, Number(count) || 1); const { maxR, maxC } = scanCells(ws);
  for (let c = maxC; c >= col - 1; c--) for (let r = 0; r <= maxR; r++) { const s = colName(c) + (r + 1); const d = colName(c + count) + (r + 1); if (ws[s]) { ws[d] = ws[s]; delete ws[s]; } }
  refreshRef(ws);
}
function excelDeleteRow(row, count) {
  const ws = getWS(); count = Math.max(1, Number(count) || 1); const { maxR, maxC } = scanCells(ws);
  for (let r = row - 1; r <= maxR; r++) for (let c = 0; c <= maxC; c++) { const s = colName(c) + (r + 1 + count); const d = colName(c) + (r + 1); if (ws[s]) { ws[d] = ws[s]; delete ws[s]; } }
  refreshRef(ws);
}
function excelDeleteCol(col, count) {
  const ws = getWS(); count = Math.max(1, Number(count) || 1); const { maxR, maxC } = scanCells(ws);
  for (let c = col - 1; c <= maxC; c++) for (let r = 0; r <= maxR; r++) { const s = colName(c + count) + (r + 1); const d = colName(c) + (r + 1); if (ws[s]) { ws[d] = ws[s]; delete ws[s]; } }
  refreshRef(ws);
}
function excelGetRows() { const ws = getWS(); return scanCells(ws).maxR + 1; }
// 另存为：目录默认取原表格目录；文件名按命名方式生成（默认"原名-1、原名-2…"递增，不覆盖原文件）
function resolveSaveAsPath(naming, prefix, startIndex) {
  const book = getActiveBook();
  const cur = (book && book.path) || '';
  let dir = ROOT, stem = '未命名表格', ext = '.xlsx';
  if (cur) {
    const base = String(cur).split(/[\\/]/).pop() || '未命名表格';
    const m = /^(.*?)(\.[^.]+)?$/.exec(base) || [];
    stem = m[1] || '未命名表格';
    ext = m[2] || '.xlsx';
    dir = String(cur).replace(/[\\/][^\\/]*$/, '') || ROOT;
  }
  // 末尾已带递增序号（报表-3）先剥掉，连续另存为才不会变成 报表-3-1-1…；只剥 1~999 的小序号
  stem = stem.replace(/[-_ ](\d{1,3})$/, '');
  if (naming === '覆盖' && cur) return cur;
  const join = (n) => (dir.replace(/[\\/]+$/, '') || '.') + path.sep + n;
  const pre = String(prefix == null ? '' : prefix);
  const start = Math.max(0, Number(startIndex) || 1);
  if (naming === '加前缀') {
    const first = join(pre + stem + ext);
    if (pre && !fs.existsSync(first)) return first;
    for (let n = start; n <= start + 999; n++) {
      const c = join(pre + stem + '-' + n + ext);
      if (!fs.existsSync(c)) return c;
    }
  } else {
    for (let n = start; n <= start + 999; n++) {
      const c = join(stem + '-' + n + ext);
      if (!fs.existsSync(c)) return c;
    }
  }
  throw new Error('找了 1000 个文件名都重名了，请换个前缀或起始序号');
}
function excelSaveAs(naming, prefix, startIndex) {
  const book = getActiveBook();
  if (!book) throw new Error('请先打开或新建Excel');
  const fp = resolveSaveAsPath(naming, prefix, startIndex);
  writeBook(book.book, fp);
  book.path = fp;
  return [fp];
}
function excelSave(p) {
  const book = getActiveBook(); if (!book) throw new Error('请先打开或新建Excel');
  const fp = expand(p) || book.path;
  if (!fp) throw new Error('请指定保存路径');
  writeBook(book.book, fp);
  book.path = fp;
  return [fp];
}

// ---------- 文件操作 ----------
function sortFileEntries(list, sortBy, order) {
  const arr = (Array.isArray(list) ? list : []).slice();
  const key = (sortBy === '修改时间') ? 'mtime' : ((sortBy === '大小' || sortBy === '文件大小') ? 'size' : 'name');
  const o = String(order || '');
  const dir = /逆序|从大到小|从晚到早/.test(o) ? -1 : 1;
  arr.sort((a, b) => {
    let x = a[key], y = b[key];
    if (key === 'name') { x = String(x == null ? '' : x).toLowerCase(); y = String(y == null ? '' : y).toLowerCase(); return dir * (x < y ? -1 : x > y ? 1 : 0); }
    x = Number(x) || 0; y = Number(y) || 0; return dir * (x - y);
  });
  return arr;
}
function listDirEntries(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  return entries.map(e => {
    const full = path.join(dir, e.name);
    let size = 0, mtime = 0;
    try { const st = fs.statSync(full); size = st.size; mtime = st.mtimeMs; } catch (err) { }
    return { name: e.name, isDir: e.isDirectory(), isFile: e.isFile(), size, mtime, path: full };
  });
}
// 从文件夹取排序后的第 index 个文件（正数=第N个，负数=倒数第N个）；不是目录返回 null
function pickFileFromDir(src, sortBy, order, index) {
  const idx = Number(index) || 0;
  if (idx === 0) return null;
  let list;
  try { list = listDirEntries(expand(src)); } catch (e) { return null; }
  const sorted = sortFileEntries(list.filter(f => f.isFile), sortBy || '字符', order || '顺序');
  if (!sorted.length) throw new Error('文件夹里没有文件');
  const abs = Math.abs(idx);
  if (abs > sorted.length) throw new Error(`文件夹里只有 ${sorted.length} 个文件，无法取第 ${idx} 个`);
  return (idx > 0 ? sorted[idx - 1] : sorted[sorted.length + idx]).path;
}
// 解析「第几个文件」表达式：支持 "1,3,5"、"1-3"、"1-3,5,-1"
function parseIndexList(expr) {
  const s = String(expr == null ? '' : expr).trim();
  if (!s) return [];
  const out = [];
  s.split(/[,，]/).forEach(part => {
    part = part.trim();
    if (!part) return;
    const range = /^(-?\d+)\s*[-~]\s*(-?\d+)$/.exec(part);
    if (range) {
      let a = parseInt(range[1], 10), b = parseInt(range[2], 10);
      if (a > b) { const t = a; a = b; b = t; }
      for (let n = a; n <= b; n++) out.push(n);
    } else {
      const n = parseInt(part, 10);
      if (!isNaN(n) && n !== 0) out.push(n);
    }
  });
  return out;
}
// 从文件夹按表达式取多个文件
function pickFilesFromDir(src, sortBy, order, expr) {
  const idxs = parseIndexList(expr);
  if (!idxs.length) return null;
  let list;
  try { list = listDirEntries(expand(src)); } catch (e) { return null; }
  const sorted = sortFileEntries(list.filter(f => f.isFile), sortBy || '字符', order || '顺序');
  if (!sorted.length) throw new Error('文件夹里没有文件');
  const paths = [];
  idxs.forEach(idx => {
    const abs = Math.abs(idx);
    if (abs > sorted.length) throw new Error(`文件夹里只有 ${sorted.length} 个文件，无法取第 ${idx} 个`);
    paths.push((idx > 0 ? sorted[idx - 1] : sorted[sorted.length + idx]).path);
  });
  return paths;
}
function fileReadText(fp) { const p = expand(fp); if (!p) throw new Error('请填写文件路径'); return fs.readFileSync(p, 'utf-8'); }
function fileWriteText(fp, content, append) {
  const p = expand(fp); if (!p) throw new Error('请填写文件路径');
  let text = expand(content);
  if (append === '追加') { let old = ''; try { old = fs.readFileSync(p, 'utf-8'); } catch (e) { } text = old + text; }
  fs.writeFileSync(p, text, 'utf-8');
}
function isDir(p) { try { return fs.statSync(p).isDirectory(); } catch (e) { return false; } }
function resolveCopyDst(srcFile, dst) {
  if (isDir(dst)) {
    const base = srcFile.split(/[\\/]/).pop();
    return dst.replace(/[\\/]$/, '') + '\\' + base;
  }
  return dst;
}
function fileCopy(src, dst, sortBy, order, index) {
  let s = expand(src), d = expand(dst);
  if (!s || !d) throw new Error('请填写源路径和目标路径');
  const picked = pickFileFromDir(src, sortBy, order, index);
  if (picked) s = picked;
  d = resolveCopyDst(s, d);
  fs.copyFileSync(s, d);
}
function fileMove(src, dst) { fs.renameSync(expand(src), expand(dst)); }
function fileDelete(fp, sortBy, order, index) {
  let p = expand(fp); if (!p) throw new Error('请填写文件路径');
  const picked = pickFileFromDir(fp, sortBy, order, index);
  if (picked) p = picked;
  fs.unlinkSync(p);
}
function fileExists(fp) { return fs.existsSync(expand(fp)); }
function fileMkdir(folder, name, content) {
  const f = expand(folder); if (!f) throw new Error('请填写「在哪个文件夹里新建」');
  const n = expand(name);
  const names = String(n || '').split(/[,，]/).map(s => s.trim()).filter(Boolean);
  if (!names.length) throw new Error('请填写「叫什么名字」');
  const results = [];
  for (const oneName of names) {
    const looksLikeFile = /\.[A-Za-z0-9]+$/.test(oneName);
    // 重名自动加递增数字
    let target = f + '\\' + oneName;
    if (fs.existsSync(target)) {
      const dir = target.replace(/[\\/][^\\/]*$/, '');
      const base = target.split(/[\\/]/).pop();
      const dot = base.lastIndexOf('.');
      const stem = dot > 0 ? base.slice(0, dot) : base;
      const ext = dot > 0 ? base.slice(dot) : '';
      let i = 1;
      while (fs.existsSync(target)) { target = dir + '\\' + stem + i + ext; i++; }
    }
    if (looksLikeFile) {
      fs.writeFileSync(target, expand(content) || '', 'utf-8');
    } else {
      fs.mkdirSync(target, { recursive: true });
    }
    results.push(target);
  }
  return results.length === 1 ? results[0] : results;
}
function fileListDir(p, sortBy, order) {
  const dir = expand(p); if (!dir) throw new Error('请填写目录路径');
  const sorted = sortFileEntries(listDirEntries(dir), sortBy || '字符', order || '顺序');
  return sorted.map(f => f.isDir ? '[目录] ' + f.name : f.name);
}
// 白话指令：删除/复制/移动/列出（支持多文件 index 表达式）
function fileOp(action, folder, sortBy, order, index, dst) {
  const f = expand(folder); if (!f) throw new Error('请填写「哪个文件夹」');
  const sortKey = sortBy === '文件名' ? '字符' : sortBy;
  if (action === '列出文件名') {
    const sorted = sortFileEntries(listDirEntries(f), sortKey, order);
    return sorted.map(e => e.isDir ? '[目录] ' + e.name : e.name);
  }
  let files = pickFilesFromDir(folder, sortKey, order, index);
  if (!files || !files.length) files = [f];
  const results = [];
  for (const filePath of files) {
    if (action === '删除') { fs.unlinkSync(filePath); results.push(filePath); }
    else if (action === '复制') { const d = expand(dst); if (!d) throw new Error('请填写「复制到哪」'); const rd = resolveCopyDst(filePath, d); fs.copyFileSync(filePath, rd); results.push(rd); }
    else if (action === '移动') { const d = expand(dst); if (!d) throw new Error('请填写「移动到哪」'); const rd = resolveCopyDst(filePath, d); fs.renameSync(filePath, rd); results.push(rd); }
    else throw new Error('未知操作：' + action);
  }
  return results.length === 1 ? results[0] : results;
}
function makeTag(type, idx) {
  if (type === '数字序号') return String(idx);
  if (type === '字母序号') { let s = ''; let n = idx; while (n > 0) { const m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = Math.floor((n - 1) / 26); } return s || 'A'; }
  if (type === '日期') { const d = new Date(); const p = (x) => String(x).padStart(2, '0'); return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`; }
  return '';
}
// 白话重命名：加前缀/加后缀/替换/删除/按分隔符重组（支持多文件）
function fileRename(folder, sortBy, order, index, mode, text, type, sep, parts) {
  const sortKey = sortBy === '文件名' ? '字符' : sortBy;
  const doRename = (filePath, seq) => {
    const dir = filePath.replace(/[\\/][^\\/]*$/, '');
    const base = filePath.split(/[\\/]/).pop();
    const dot = base.lastIndexOf('.');
    const stem = dot > 0 ? base.slice(0, dot) : base;
    const ext = dot > 0 ? base.slice(dot) : '';
    let tag = expand(text) || '';
    if (type && type !== '自定义文字') tag = makeTag(type, seq >= 1 ? seq : 1);
    let newStem = stem;
    if (mode === '加前缀') newStem = tag + stem;
    else if (mode === '删前缀') { const t = expand(text) || ''; newStem = t ? (stem.startsWith(t) ? stem.slice(t.length) : stem) : stem; }
    else if (mode === '加后缀') newStem = stem + tag;
    else if (mode === '删后缀') { const t = expand(text) || ''; newStem = t ? (stem.endsWith(t) ? stem.slice(0, stem.length - t.length) : stem) : stem; }
    else if (mode === '替换文字') newStem = stem.split(expand(text) || '').join(tag);
    else if (mode === '删除文字') newStem = stem.split(expand(text) || '').join('');
    else if (mode === '按分隔符重组') {
      const sp = expand(sep) || '_';
      const segs = stem.split(sp);
      const ps = String(parts || '').trim();
      if (ps) {
        const ord = ps.split(/[,，\s]+/).map(x => parseInt(x, 10)).filter(n => !isNaN(n));
        const re = []; ord.forEach(n => { if (n >= 1 && n <= segs.length) re.push(segs[n - 1]); });
        newStem = re.join(sp);
      }
    }
    const newPath = dir + '\\' + (newStem + ext);
    if (newPath === filePath) return filePath;
    fs.renameSync(filePath, newPath);
    return newPath;
  };
  let files = pickFilesFromDir(folder, sortKey, order, index);
  if (!files || !files.length) files = [expand(folder)];
  const results = [];
  for (let i = 0; i < files.length; i++) {
    let seq = i + 1;
    const idxs = parseIndexList(index);
    if (idxs.length && idxs[i] !== undefined) seq = idxs[i] >= 1 ? idxs[i] : seq;
    results.push(doRename(files[i], seq));
  }
  return results.length === 1 ? results[0] : results;
}
// 白话查找
function fileFind(folder, keyword, ext) {
  const f = expand(folder); if (!f) throw new Error('请填写「在哪个文件夹找」');
  const kw = expand(keyword) || ''; const ex = expand(ext) || '';
  let files = listDirEntries(f).filter(e => e.isFile);
  if (kw) files = files.filter(e => e.name.toLowerCase().includes(kw.toLowerCase()));
  if (ex) files = files.filter(e => e.name.toLowerCase().endsWith('.' + ex.toLowerCase().replace(/^\./, '')));
  return files.map(e => e.name);
}
// 白话统计
function fileCount(folder, ext) {
  const f = expand(folder); if (!f) throw new Error('请填写「统计哪个文件夹」');
  const ex = expand(ext) || '';
  let files = listDirEntries(f).filter(e => e.isFile);
  if (ex) files = files.filter(e => e.name.toLowerCase().endsWith('.' + ex.toLowerCase().replace(/^\./, '')));
  const total = files.reduce((s, e) => s + (Number(e.size) || 0), 0);
  return { 文件个数: files.length, 总大小字节: total };
}

// ---------- 流程执行（支持循环/条件/嵌套） ----------
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function runSteps(fromIdx, baseLevel, flowName = '主流程') {
  const steps = flows[flowName] || [];
  let i = fromIdx;
  while (i < steps.length) {
    const step = steps[i];
    const level = step.level || 0;
    if (level < baseLevel) return {};

    // 循环
    if (step.id === 'loop' || step.id === 'loopForever') {
      const isTimeMode = step.id === 'loop' && step.params.mode === '按时间';
      const count = step.id === 'loop' ? (isTimeMode ? Infinity : Math.max(0, Number(step.params.count) || 0)) : Infinity;
      const secs = isTimeMode ? (Math.max(0, Number(step.params.seconds) || 0)) : 0;
      const logDesc = step.id === 'loopForever' ? '无限循环' : (isTimeMode ? '按时间循环 ' + secs + ' 秒' : '循环 ' + count + ' 次');
      log(`▶ 执行：${step.name}（${logDesc}）`);
      const bodyLevel = level + 1;
      let bodyEnd = i + 1;
      while (bodyEnd < steps.length && (steps[bodyEnd].level || 0) >= bodyLevel) bodyEnd++;
      let iter = 0;
      const startTime = Date.now();
      while (true) {
        if (isTimeMode && (Date.now() - startTime) >= secs * 1000) break;
        const r = await runSteps(i + 1, bodyLevel, flowName);
        if (r && r.endFlow) return r;
        if (r && r.breakLoop) break;
        iter++;
        if (!isTimeMode && iter >= count) break;
      }
      i = bodyEnd;
      continue;
    }
    if (step.id === 'breakLoop') { log('▶ 执行：跳出循环'); return { breakLoop: true }; }
    if (step.id === 'end') { log('▶ 执行：结束流程'); return { endFlow: true }; }
    // 标记：仅作为跳转目标
    if (step.id === 'mark') { log(`🔖 标记：${step.params.name || ''}`); i++; continue; }
    // 跳转：支持「第N步」/「N」/「流程:名」/「标记名」
    if (step.id === 'goto') {
      const target = String(step.params.target || '').trim();
      if (target.startsWith('流程:')) {
        const fn = target.slice(3).trim();
        if (!fn || !flows[fn]) { log(`✘ 跳转流程不存在：${fn || '(空)'}`, 'error'); i++; continue; }
        log(`⤵ 跳转到流程：${fn}`);
        const r = await runSteps(0, 0, fn);
        if (r && r.endFlow) return r;
        if (r && r.breakLoop) return r;
        i++;
        continue;
      }
      let m = /^第?\s*(\d+)\s*步?$/.exec(target);
      let targetIdx = -1;
      if (m) targetIdx = Number(m[1]) - 1;
      else if (target) targetIdx = steps.findIndex(s => s.id === 'mark' && s.params && s.params.name === target);
      if (targetIdx < 0 || targetIdx >= steps.length) { log(`✘ 跳转目标不存在：${target}`, 'error'); i++; continue; }
      log(`⤵ 跳转到第 ${targetIdx + 1} 步（${steps[targetIdx].name}）`);
      i = targetIdx;
      continue;
    }
    // 调用子流程
    if (step.id === 'callFlow') {
      const fn = String(step.params.flowName || '').trim();
      if (!fn || !flows[fn]) { log(`✘ 子流程不存在：${fn || '(空)'}`, 'error'); i++; continue; }
      log(`📦 调用子流程：${fn}`);
      const r = await runSteps(0, 0, fn);
      if (r && r.endFlow) return r;
      if (r && r.breakLoop) return r;
      log(`↩ 子流程 ${fn} 执行完毕，返回`);
      i++;
      continue;
    }

    // 条件判断
    if (step.id === 'if') {
      const left = expand(step.params.left), right = expand(step.params.right);
      const op = step.params.op;
      let ok = false;
      if (op === '等于') ok = String(left) === String(right);
      else if (op === '不等于') ok = String(left) !== String(right);
      else if (op === '大于') ok = Number(left) > Number(right);
      else if (op === '小于') ok = Number(left) < Number(right);
      else if (op === '包含') ok = String(left).includes(String(right));
      log(`▶ 判断：${left} ${op} ${right} → ${ok ? '真' : '假'}`);
      const bodyLevel = level + 1;
      let bodyEnd = i + 1;
      while (bodyEnd < steps.length && (steps[bodyEnd].level || 0) >= bodyLevel) bodyEnd++;
      if (ok) { const r = await runSteps(i + 1, bodyLevel, flowName); if (r && (r.endFlow || r.breakLoop)) return r; }
      i = bodyEnd;
      continue;
    }

    // 其它指令
    log(`▶ 执行：${step.name}`);
    await runCommand(step);
    i++;
  }
  return {};
}

async function runCommand(step) {
  const p = step.params || {};
  switch (step.id) {
    case 'sleep': await sleep(Math.max(0, Number(p.seconds) || 0) * 1000); return;
    case 'setVar': vars[p.name] = expand(p.value); return;
    case 'printLog': log(expand(p.text)); return;
    case 'excelOpen': excelOpen(p.path); return;
    case 'excelNew': excelNew(p.path, p.sheetName); return;
    case 'excelRead': vars[p.varName] = excelRead(p.cell); return;
    case 'excelWrite': excelWrite(p.cell, p.value); return;
    case 'excelReadRange': vars[p.varName] = excelReadRange(p.range); return;
    case 'excelWriteRange': excelWriteRange(p.range, vars[p.data]); return;
    case 'excelCopyPaste': excelCopyPaste(p.from, p.to, p.mode); return;
    case 'excelSheetCopyPaste': excelSheetCopyPaste(p.fromBook, p.fromSheet, p.fromRange, p.toBook, p.toSheet, p.toRange, p.mode); return;
    case 'excelTableCopyPaste': await excelTableCopyPaste(p); return;
    case 'excelInsertRow': excelInsertRow(p.row, p.count); return;
    case 'excelInsertCol': excelInsertCol(p.col, p.count); return;
    case 'excelDeleteRow': excelDeleteRow(p.row, p.count); return;
    case 'excelDeleteCol': excelDeleteCol(p.col, p.count); return;
    case 'excelGetRows': vars[p.varName] = excelGetRows(); return;
    case 'excelSave': await excelSave(p.path); return;
    case 'excelSaveAs': {
      const out = excelSaveAs(p.naming, expand(p.prefix), p.startIndex);
      log('已另存为（' + (p.naming || '后缀递增') + '）：' + out.map(function (x) { return x.split(/[\\/]/).pop(); }).join('、'));
      return;
    }
    case 'fileReadText': vars[p.varName] = fileReadText(p.path); return;
    case 'fileWriteText': fileWriteText(p.path, p.content, p.append); return;
    case 'fileCopy': fileCopy(p.src, p.dst, p.sortBy, p.order, p.index); return;
    case 'fileMove': fileMove(p.src, p.dst); return;
    case 'fileDelete': fileDelete(p.path, p.sortBy, p.order, p.index); return;
    case 'fileExists': vars[p.varName] = fileExists(p.path); return;
    case 'fileMkdir': fileMkdir(p.folder, p.name, p.content); return;
    case 'fileListDir': vars[p.varName] = fileListDir(p.path, p.sortBy, p.order); return;
    case 'fileOp': vars[p.varName || '白话结果'] = fileOp(p.action, p.folder, p.sortBy, p.order, p.index, p.dst); return;
    case 'fileRename': vars['重命名结果'] = fileRename(p.folder, p.sortBy, p.order, p.index, p.mode, p.text, p.type, p.sep, p.parts); return;
    case 'fileFind': vars['查找结果'] = fileFind(p.folder, p.keyword, p.ext); return;
    case 'fileCount': vars['统计结果'] = fileCount(p.folder, p.ext); return;
    case 'openUrl': case 'click': case 'input': case 'getText': case 'waitElement':
    case 'clickXY': case 'scrapeText': case 'scrapeAttr': case 'scrapeList': case 'scrapeExport':
    case 'typeText': case 'mouseClick': case 'hotkey': case 'pressKey': case 'browserWait':
    case 'clickSelectCopy': case 'clickPaste': case 'extractTextToTable':
    case 'clipboardCopy': case 'pasteToElement': case 'pasteToCell':
    case 'pickElement': case 'screenshot': case 'waitPageReady': case 'diagnosePage':
      log(`[跳过] 「${step.name}」需要完整版世博自动化（浏览器/鼠标键盘/系统剪贴板），本运行器不支持`);
      return;
    default:
      log(`[跳过] 指令「${step.name}」暂未实现`);
  }
}

// ---------- 入口 ----------
async function main() {
  const flowPath = path.join(ROOT, 'flow.json');
  if (!fs.existsSync(flowPath)) { console.error('未找到 flow.json'); process.exit(1); }
  const raw = JSON.parse(fs.readFileSync(flowPath, 'utf-8'));
  // 兼容新旧格式：{ flows: {...} } 或纯数组
  if (raw && raw.flows && typeof raw.flows === 'object') {
    flows = raw.flows;
    if (!flows['主流程']) flows['主流程'] = [];
    flow = flows['主流程'];
  } else if (Array.isArray(raw)) {
    flow = raw;
    flows = { '主流程': raw };
  } else if (raw && Array.isArray(raw.steps)) {
    flow = raw.steps;
    flows = { '主流程': raw.steps };
  }
  log('===== 开始运行流程（' + (flows['主流程'] || []).length + ' 步） =====');
  try {
    await runSteps(0, 0, '主流程');
    log('===== 流程运行完成 =====');
  } catch (err) {
    log('✘ 运行出错：' + err.message);
  }
}

main();

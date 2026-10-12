// ============ 轻量公式引擎（对齐 WPS/Excel 常用行为）============
// 让表格里的 =公式 能立即算出结果，并支持依赖自动重算。
// 支持：
//   · 算术 + - * / ^ %，比较 = <> < > <= >=，文本连接 &
//   · 单元格引用 A1 / $A$1、区域 A1:B5、跨表 Sheet2!A1 / '我的表'!A1:B2
//   · 括号、一元正负、百分比后缀
//   · 常用函数 60+（数学/统计/逻辑/文本/日期/查找）
//   · Excel 风格错误码：#DIV/0! #VALUE! #NAME? #REF! #NUM! #N/A #CIRC!
// 不支持函数时抛 unsupported 错误（调用方保留原缓存值，避免把真实文件的公式算坏）
(function () {
  const CACHE_MAX = 600;
  const astCache = new Map();

  // ---------- 错误 ----------
  function FormulaError(code) {
    const e = new Error(code);
    e.code = code;
    e.formulaError = true;
    return e;
  }
  function unsupported(name) {
    const e = new Error('不支持的函数：' + name);
    e.unsupported = true;
    e.funcName = name;
    return e;
  }
  function isError(v) { return typeof v === 'string' && /^#(DIV\/0|VALUE|NAME|REF|NUM|N\/A|CIRC|ERROR|NULL)!/i.test(v); }
  function fail(code) { throw FormulaError(code); }

  // ---------- 词法 ----------
  const RE_SHEET_REF = /^(?:'([^']+)'|([A-Za-z_\u4e00-\u9fa5][A-Za-z0-9_.\u4e00-\u9fa5]*))!(\$?[A-Za-z]{1,3}\$?\d+)/;
  const RE_CELL = /^(\$?[A-Za-z]{1,3}\$?\d+)/;
  const RE_IDENT = /^([A-Za-z_][A-Za-z0-9_.]*)/;

  function tokenize(src) {
    const t = [];
    const s = String(src);
    let i = 0;
    while (i < s.length) {
      const ch = s[i];
      if (ch === ' ' || ch === '\t' || ch === '\n' || ch === '\r') { i++; continue; }
      if (ch === '"') {                       // 字符串字面量（内部 "" 表示一个引号）
        let j = i + 1, out = '';
        while (j < s.length) {
          if (s[j] === '"' && s[j + 1] === '"') { out += '"'; j += 2; continue; }
          if (s[j] === '"') break;
          out += s[j]; j++;
        }
        t.push({ k: 'str', v: out }); i = j + 1; continue;
      }
      if (/[0-9]/.test(ch) || (ch === '.' && /[0-9]/.test(s[i + 1] || ''))) {
        let j = i, dot = false;
        while (j < s.length && (/[0-9]/.test(s[j]) || (s[j] === '.' && !dot))) { if (s[j] === '.') dot = true; j++; }
        if (s[j] === 'e' || s[j] === 'E') {
          let k = j + 1;
          if (s[k] === '+' || s[k] === '-') k++;
          if (/[0-9]/.test(s[k] || '')) { j = k; while (/[0-9]/.test(s[j] || '')) j++; }
        }
        t.push({ k: 'num', v: parseFloat(s.slice(i, j)) }); i = j; continue;
      }
      if (/[A-Za-z_$\u4e00-\u9fa5'"]/.test(ch)) {
        const rest = s.slice(i);
        const mSheet = RE_SHEET_REF.exec(rest);
        if (mSheet) { t.push({ k: 'ref', sheet: mSheet[1] || mSheet[2], addr: mSheet[3] }); i += mSheet[0].length; continue; }
        const mCell = RE_CELL.exec(rest);
        if (mCell) {
          // 紧跟 "(" 视为函数名（如 LOG10(...)）
          const after = rest.slice(mCell[0].length).replace(/^\s+/, '');
          if (!after.startsWith('(')) { t.push({ k: 'ref', sheet: null, addr: mCell[0] }); i += mCell[0].length; continue; }
        }
        const mId = RE_IDENT.exec(rest);
        if (mId) { t.push({ k: 'id', v: mId[1] }); i += mId[0].length; continue; }
        fail('#NAME?');
      }
      const two = s.slice(i, i + 2);
      if (two === '<=' || two === '>=' || two === '<>') { t.push({ k: 'op', v: two }); i += 2; continue; }
      if ('+-*/^&=<>%'.indexOf(ch) >= 0) { t.push({ k: 'op', v: ch }); i++; continue; }
      if (ch === '(' || ch === ')') { t.push({ k: ch }); i++; continue; }
      if (ch === ',' || ch === '，' || ch === ';') { t.push({ k: ',' }); i++; continue; }
      if (ch === ':') { t.push({ k: ':' }); i++; continue; }
      fail('#NAME?');
    }
    return t;
  }

  // ---------- 语法（递归下降 + 优先级） ----------
  function parseTokens(tokens) {
    let p = 0;
    const peek = () => tokens[p];
    const eat = (k) => { const t = tokens[p]; if (t && t.k === k) { p++; return t; } return null; };
    const expect = (k) => { const t = eat(k); if (!t) fail('#NAME?'); return t; };

    function parseExpr() { return parseCompare(); }
    function parseCompare() {
      let left = parseConcat();
      while (peek() && peek().k === 'op' && ['=', '<>', '<', '>', '<=', '>='].indexOf(peek().v) >= 0) {
        const op = tokens[p++].v;
        left = { t: 'bin', op, a: left, b: parseConcat() };
      }
      return left;
    }
    function parseConcat() {
      let left = parseAdd();
      while (peek() && peek().k === 'op' && peek().v === '&') { p++; left = { t: 'bin', op: '&', a: left, b: parseAdd() }; }
      return left;
    }
    function parseAdd() {
      let left = parseMul();
      while (peek() && peek().k === 'op' && (peek().v === '+' || peek().v === '-')) {
        const op = tokens[p++].v;
        left = { t: 'bin', op, a: left, b: parseMul() };
      }
      return left;
    }
    function parseMul() {
      let left = parseUnary();
      while (peek() && peek().k === 'op' && (peek().v === '*' || peek().v === '/')) {
        const op = tokens[p++].v;
        left = { t: 'bin', op, a: left, b: parseUnary() };
      }
      return left;
    }
    function parseUnary() {
      if (peek() && peek().k === 'op' && (peek().v === '-' || peek().v === '+')) {
        const op = tokens[p++].v;
        return { t: 'un', op, a: parseUnary() };
      }
      return parsePower();
    }
    function parsePower() {
      const base = parsePostfix();
      if (peek() && peek().k === 'op' && peek().v === '^') {
        p++;
        return { t: 'bin', op: '^', a: base, b: parseUnary() };   // 右结合
      }
      return base;
    }
    function parsePostfix() {
      let node = parsePrimary();
      while (peek() && peek().k === 'op' && peek().v === '%') { p++; node = { t: 'pct', a: node }; }
      return node;
    }
    function parsePrimary() {
      const tk = peek();
      if (!tk) fail('#NAME?');
      if (tk.k === 'num') { p++; return { t: 'num', v: tk.v }; }
      if (tk.k === 'str') { p++; return { t: 'str', v: tk.v }; }
      if (tk.k === 'ref') {
        p++;
        const a = { t: 'ref', sheet: tk.sheet, addr: tk.addr };
        if (peek() && peek().k === ':') {
          const save = p;
          p++;
          const t2 = peek();
          if (t2 && t2.k === 'ref') { p++; return { t: 'range', sheet: tk.sheet || t2.sheet, a: tk.addr, b: t2.addr }; }
          p = save;                                  // 不是区域 → 回退
        }
        return a;
      }
      if (tk.k === 'id') {
        p++;
        const name = tk.v.toUpperCase();
        if (peek() && peek().k === '(') {
          p++;
          const args = [];
          if (peek() && peek().k === ')') { p++; return { t: 'call', name, args }; }
          for (;;) {
            args.push(parseExpr());
            if (eat(',')) continue;
            expect(')');
            break;
          }
          return { t: 'call', name, args };
        }
        // 无参常量
        if (name === 'TRUE') return { t: 'bool', v: true };
        if (name === 'FALSE') return { t: 'bool', v: false };
        if (name === 'PI') return { t: 'num', v: Math.PI };
        return { t: 'call', name, args: [] };
      }
      if (tk.k === '(') {
        p++;
        const e = parseExpr();
        expect(')');
        return e;
      }
      if (tk.k === 'op' && (tk.v === '-' || tk.v === '+')) return parseUnary();
      fail('#NAME?');
    }

    const ast = parseExpr();
    if (p < tokens.length) fail('#NAME?');
    return ast;
  }

  function parse(formula) {
    const key = String(formula);
    if (astCache.has(key)) return astCache.get(key);
    const ast = parseTokens(tokenize(key));
    if (astCache.size > CACHE_MAX) astCache.clear();
    astCache.set(key, ast);
    return ast;
  }

  // ---------- 值处理 ----------
  const RANGE = Symbol('range');
  function isRange(v) { return v && v[RANGE] === true; }
  function mkRange(matrix) {
    const flat = [];
    matrix.forEach(row => row.forEach(v => flat.push(v)));
    return { [RANGE]: true, matrix: matrix, flat: flat };
  }
  function isBlank(v) { return v === '' || v === null || v === undefined; }

  function toNum(v) {
    if (isError(v)) fail(v);
    if (typeof v === 'number') return v;
    if (typeof v === 'boolean') return v ? 1 : 0;
    if (v instanceof Date) return v.getTime();
    if (isBlank(v)) return 0;
    const s = String(v).trim();
    if (s === '') return 0;
    // 支持 "12%"、"1,234"、"$12" 这类
    const pct = /^-?[\d.,]+\s*%$/.test(s);
    const cleaned = s.replace(/[,\s￥$]/g, '');
    if (/^-?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?%?$/.test(cleaned)) {
      const n = parseFloat(cleaned);
      return pct ? n / 100 : n;
    }
    fail('#VALUE!');
  }
  function toStr(v) {
    if (isError(v)) fail(v);
    if (isBlank(v)) return '';
    if (typeof v === 'boolean') return v ? 'TRUE' : 'FALSE';
    return String(v);
  }
  function toBool(v) {
    if (isError(v)) fail(v);
    if (typeof v === 'boolean') return v;
    if (typeof v === 'number') return v !== 0;
    const s = String(v).trim().toUpperCase();
    if (s === 'TRUE') return true;
    if (s === 'FALSE' || s === '') return false;
    return toNum(v) !== 0;
  }
  function flat(args) {
    const out = [];
    args.forEach(a => { if (isRange(a)) a.flat.forEach(v => out.push(v)); else out.push(a); });
    return out;
  }
  // 统计类函数：忽略空值与文本
  function nums(args) {
    const out = [];
    flat(args).forEach(v => {
      if (isError(v)) fail(v);
      if (isBlank(v)) return;
      if (typeof v === 'number') { out.push(v); return; }
      if (typeof v === 'boolean') return;
      const s = String(v).trim();
      if (s === '') return;
      if (/^-?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/.test(s.replace(/,/g, ''))) out.push(Number(s.replace(/,/g, '')));
    });
    return out;
  }
  function cmp(a, b) {
    if (isBlank(a) && isBlank(b)) return 0;
    const an = typeof a === 'number' || (typeof a === 'string' && a.trim() !== '' && !isNaN(Number(a)));
    const bn = typeof b === 'number' || (typeof b === 'string' && b.trim() !== '' && !isNaN(Number(b)));
    if (an && bn) { const x = toNum(a), y = toNum(b); return x < y ? -1 : x > y ? 1 : 0; }
    const as = toStr(a).toLowerCase(), bs = toStr(b).toLowerCase();
    return as < bs ? -1 : as > bs ? 1 : 0;
  }
  function excelRound(n, digits) {
    const f = Math.pow(10, digits || 0);
    return Math.round((n + (n >= 0 ? 1e-12 : -1e-12)) * f) / f;
  }
  // 条件匹配：支持 ">5" "<>x" "abc" "*关键字*"
  function matchCond(v, cond) {
    if (typeof cond === 'number' || typeof cond === 'boolean') return cmp(v, cond) === 0;
    const c = toStr(cond).trim();
    const m = /^(<=|>=|<>|=|<|>)(.*)$/.exec(c);
    if (m) {
      const op = m[1], rhs = m[2].trim();
      const rhsVal = (rhs !== '' && !isNaN(Number(rhs.replace(/,/g, '')))) ? Number(rhs.replace(/,/g, '')) : rhs;
      const r = cmp(v, rhsVal);
      switch (op) {
        case '=': return r === 0;
        case '<>': return r !== 0;
        case '<': return r < 0;
        case '>': return r > 0;
        case '<=': return r <= 0;
        case '>=': return r >= 0;
      }
    }
    if (c.indexOf('*') >= 0 || c.indexOf('?') >= 0) {
      const re = new RegExp('^' + c.replace(/[.+^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*').replace(/\?/g, '.') + '$', 'i');
      return re.test(toStr(v));
    }
    const r = cmp(v, c);
    return r === 0;
  }

  // ---------- 函数库 ----------
  const FN = {};
  function def(names, fn) { names.split(',').forEach(n => { FN[n] = fn; }); }

  def('SUM', a => nums(a).reduce((s, v) => s + v, 0));
  def('PRODUCT', a => { const n = nums(a); return n.length ? n.reduce((s, v) => s * v, 1) : 0; });
  def('AVERAGE,AVG', a => { const n = nums(a); if (!n.length) fail('#DIV/0!'); return n.reduce((s, v) => s + v, 0) / n.length; });
  def('COUNT', a => nums(a).length);
  def('COUNTA', a => flat(a).filter(v => !isBlank(v)).length);
  def('COUNTBLANK', a => flat(a).filter(v => isBlank(v)).length);
  def('MAX', a => { const n = nums(a); return n.length ? Math.max.apply(null, n) : 0; });
  def('MIN', a => { const n = nums(a); return n.length ? Math.min.apply(null, n) : 0; });
  def('MEDIAN', a => {
    const n = nums(a).sort((x, y) => x - y);
    if (!n.length) fail('#NUM!');
    const m = Math.floor(n.length / 2);
    return n.length % 2 ? n[m] : (n[m - 1] + n[m]) / 2;
  });
  def('ABS', a => Math.abs(toNum(a[0])));
  def('SIGN', a => Math.sign(toNum(a[0])));
  def('SQRT', a => { const n = toNum(a[0]); if (n < 0) fail('#NUM!'); return Math.sqrt(n); });
  def('POWER', a => Math.pow(toNum(a[0]), toNum(a[1])));
  def('EXP', a => Math.exp(toNum(a[0])));
  def('LN', a => { const n = toNum(a[0]); if (n <= 0) fail('#NUM!'); return Math.log(n); });
  def('LOG', a => { const n = toNum(a[0]), b = a.length > 1 ? toNum(a[1]) : 10; return Math.log(n) / Math.log(b); });
  def('LOG10', a => Math.log10(toNum(a[0])));
  def('PI', () => Math.PI);
  def('ROUND', a => excelRound(toNum(a[0]), toNum(a[1] || 0)));
  def('ROUNDUP', a => { const d = toNum(a[1] || 0), f = Math.pow(10, d); return Math.sign(toNum(a[0])) * Math.ceil(Math.abs(toNum(a[0])) * f) / f; });
  def('ROUNDDOWN', a => { const d = toNum(a[1] || 0), f = Math.pow(10, d); return Math.sign(toNum(a[0])) * Math.floor(Math.abs(toNum(a[0])) * f) / f; });
  def('INT', a => Math.floor(toNum(a[0])));
  def('TRUNC', a => { const d = toNum(a[1] || 0), f = Math.pow(10, d); return Math.trunc(toNum(a[0]) * f) / f; });
  def('MOD', a => { const x = toNum(a[0]), y = toNum(a[1]); if (y === 0) fail('#DIV/0!'); const r = x - Math.floor(x / y) * y; return r; });
  def('CEILING', a => { const y = a.length > 1 ? toNum(a[1]) : 1; if (y === 0) return 0; return Math.ceil(toNum(a[0]) / y) * y; });
  def('FLOOR', a => { const y = a.length > 1 ? toNum(a[1]) : 1; if (y === 0) fail('#DIV/0!'); return Math.floor(toNum(a[0]) / y) * y; });
  def('RAND', () => Math.random());
  def('RANDBETWEEN', a => { const lo = toNum(a[0]), hi = toNum(a[1]); return lo + Math.floor(Math.random() * (hi - lo + 1)); });
  def('SUMIF', a => {
    const range = isRange(a[0]) ? a[0].matrix : [[a[0]]];
    const cond = a[1];
    const sumRange = isRange(a[2]) ? a[2].matrix : range;
    let s = 0;
    for (let r = 0; r < range.length; r++) {
      for (let c = 0; c < range[r].length; c++) {
        if (matchCond(range[r][c], cond)) {
          const sv = (sumRange[r] && sumRange[r][c] !== undefined) ? sumRange[r][c] : range[r][c];
          if (!isBlank(sv)) { const n = Number(String(sv).replace(/,/g, '')); if (!isNaN(n)) s += n; }
        }
      }
    }
    return s;
  });
  def('COUNTIF', a => {
    const range = isRange(a[0]) ? a[0].matrix : [[a[0]]];
    let n = 0;
    range.forEach(row => row.forEach(v => { if (matchCond(v, a[1])) n++; }));
    return n;
  });
  // 多条件求和：SUMIFS(sumRange, range1, cond1, [range2, cond2, ...])
  def('SUMIFS', a => {
    const sumRange = isRange(a[0]) ? a[0].matrix : [[a[0]]];
    let total = 0;
    const rows = sumRange.length, cols = (sumRange[0] || []).length;
    const conds = [];
    for (let i = 1; i + 1 < a.length; i += 2) {
      const r = isRange(a[i]) ? a[i].matrix : [[a[i]]];
      conds.push({ range: r, cond: a[i + 1] });
    }
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        let ok = true;
        for (const cd of conds) {
          const rv = (cd.range[r] && cd.range[r][c] !== undefined) ? cd.range[r][c] : '';
          if (!matchCond(rv, cd.cond)) { ok = false; break; }
        }
        if (ok) {
          const sv = sumRange[r][c];
          if (!isBlank(sv)) { const n = Number(String(sv).replace(/,/g, '')); if (!isNaN(n)) total += n; }
        }
      }
    }
    return total;
  });
  // 多条件计数：COUNTIFS(range1, cond1, [range2, cond2, ...])
  def('COUNTIFS', a => {
    const conds = [];
    for (let i = 0; i + 1 < a.length; i += 2) {
      const r = isRange(a[i]) ? a[i].matrix : [[a[i]]];
      conds.push({ range: r, cond: a[i + 1] });
    }
    if (!conds.length) return 0;
    const rows = conds[0].range.length, cols = (conds[0].range[0] || []).length;
    let n = 0;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        let ok = true;
        for (const cd of conds) {
          const rv = (cd.range[r] && cd.range[r][c] !== undefined) ? cd.range[r][c] : '';
          if (!matchCond(rv, cd.cond)) { ok = false; break; }
        }
        if (ok) n++;
      }
    }
    return n;
  });
  def('AVERAGEIF', a => {
    const range = isRange(a[0]) ? a[0].matrix : [[a[0]]];
    const cond = a[1];
    const avgRange = isRange(a[2]) ? a[2].matrix : range;
    let s = 0, n = 0;
    for (let r = 0; r < range.length; r++) {
      for (let c = 0; c < range[r].length; c++) {
        if (matchCond(range[r][c], cond)) {
          const sv = (avgRange[r] && avgRange[r][c] !== undefined) ? avgRange[r][c] : range[r][c];
          if (!isBlank(sv)) { const v = Number(String(sv).replace(/,/g, '')); if (!isNaN(v)) { s += v; n++; } }
        }
      }
    }
    if (!n) fail('#DIV/0!');
    return s / n;
  });
  // 对应元素相乘再求和
  def('SUMPRODUCT', a => {
    const mats = a.map(x => isRange(x) ? x.matrix : [[x]]);
    const rows = Math.max.apply(null, mats.map(m => m.length));
    const cols = Math.max.apply(null, mats.map(m => (m[0] || []).length));
    let total = 0;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        let p = 1;
        for (const m of mats) {
          const v = (m[r] && m[r][c] !== undefined) ? m[r][c] : 0;
          const n = typeof v === 'number' ? v : (isBlank(v) ? 0 : Number(String(v).replace(/,/g, '')));
          p *= (isNaN(n) ? 0 : n);
        }
        total += p;
      }
    }
    return total;
  });
  def('LARGE', a => { const n = nums([a[0]]).sort((x, y) => y - x); const k = toNum(a[1]); if (k < 1 || k > n.length) fail('#NUM!'); return n[k - 1]; });
  def('SMALL', a => { const n = nums([a[0]]).sort((x, y) => x - y); const k = toNum(a[1]); if (k < 1 || k > n.length) fail('#NUM!'); return n[k - 1]; });
  def('RANK', a => { const v = toNum(a[0]); const arr = nums([a[1]]).sort((x, y) => y - x); return arr.indexOf(v) + 1; });
  def('SUBTOTAL', a => { const fn = Math.floor(toNum(a[0])); const vals = nums(a.slice(1)); if (!vals.length) return 0; switch (fn) { case 1: case 101: return vals.reduce((s, v) => s + v, 0) / vals.length; case 2: case 102: return vals.length; case 4: case 104: return Math.max.apply(null, vals); case 5: case 105: return Math.min.apply(null, vals); case 9: case 109: default: return vals.reduce((s, v) => s + v, 0); } });
  def('IFERROR', a => { try { const v = a[0]; return isError(v) ? a[1] : v; } catch (e) { return a[1]; } });
  def('ISERROR', a => isError(a[0]));
  def('ISERR', a => isError(a[0]) && !/^#N\/A!?$/.test(String(a[0])));
  def('ISNA', a => typeof a[0] === 'string' && /^#N\/A!?$/.test(a[0]));
  def('N', a => { if (isError(a[0])) fail(a[0]); if (typeof a[0] === 'number') return a[0]; if (typeof a[0] === 'boolean') return a[0] ? 1 : 0; const n = Number(String(a[0]).trim()); return isNaN(n) ? 0 : n; });
  def('NA', () => fail('#N/A'));
  def('ISBLANK', a => isBlank(a[0]));
  def('ISNUMBER', a => typeof a[0] === 'number');
  def('ISTEXT', a => typeof a[0] === 'string' && !isError(a[0]) && a[0] !== '');
  def('LEN', a => toStr(a[0]).length);
  def('LEFT', a => toStr(a[0]).slice(0, a.length > 1 ? Math.max(0, toNum(a[1])) : 1));
  def('RIGHT', a => { const n = a.length > 1 ? Math.max(0, toNum(a[1])) : 1; const s = toStr(a[0]); return n === 0 ? '' : s.slice(-n); });
  def('MID', a => { const s = toStr(a[0]), start = toNum(a[1]), len = toNum(a[2]); return s.substr(Math.max(0, start - 1), Math.max(0, len)); });
  def('TRIM', a => toStr(a[0]).replace(/^\s+|\s+$/g, '').replace(/\s+/g, ' '));
  def('UPPER', a => toStr(a[0]).toUpperCase());
  def('LOWER', a => toStr(a[0]).toLowerCase());
  def('CONCAT,CONCATENATE', a => flat(a).map(toStr).join(''));
  def('REPT', a => toStr(a[0]).repeat(Math.max(0, toNum(a[1]))));
  def('SUBSTITUTE', a => {
    const s = toStr(a[0]), oldV = toStr(a[1]), newV = a.length > 2 ? toStr(a[2]) : '';
    if (a.length > 3) {
      const which = toNum(a[3]);
      let idx = -1, count = 0;
      while (count < which) { idx = s.indexOf(oldV, idx + 1); if (idx < 0) return s; count++; }
      return s.slice(0, idx) + newV + s.slice(idx + oldV.length);
    }
    return oldV === '' ? s : s.split(oldV).join(newV);
  });
  def('FIND', a => { const i = toStr(a[1]).indexOf(toStr(a[0]), a.length > 2 ? toNum(a[2]) - 1 : 0); if (i < 0) fail('#VALUE!'); return i + 1; });
  def('SEARCH', a => { const i = toStr(a[1]).toLowerCase().indexOf(toStr(a[0]).toLowerCase(), a.length > 2 ? toNum(a[2]) - 1 : 0); if (i < 0) fail('#VALUE!'); return i + 1; });
  def('REPLACE', a => { const s = toStr(a[0]); const start = Math.max(1, toNum(a[1])); const len = Math.max(0, toNum(a[2])); return s.slice(0, start - 1) + toStr(a[3]) + s.slice(start - 1 + len); });
  def('PROPER', a => toStr(a[0]).toLowerCase().replace(/(^|[^A-Za-z\u00C0-\u024F])([A-Za-z\u00C0-\u024F])/g, (m, p, c) => p + c.toUpperCase()));
  def('EXACT', a => toStr(a[0]) === toStr(a[1]));
  def('CLEAN', a => toStr(a[0]).replace(/[\x00-\x1F]/g, ''));
  def('TEXTJOIN', a => {
    const delim = toStr(a[0]), ignoreEmpty = toBool(a[1]);
    const vals = a.slice(2).map(x => isRange(x) ? x.flat : [x]);
    const parts = [];
    vals.forEach(arr => arr.forEach(v => { if (!ignoreEmpty || !isBlank(v)) parts.push(toStr(v)); }));
    return parts.join(delim);
  });
  def('VALUE', a => toNum(a[0]));
  def('TEXT', a => {
    const v = toNum(a[0]), fmt = toStr(a[1] || '');
    if (/0\.0+/.test(fmt)) return v.toFixed((fmt.split('.')[1] || '').replace(/[^0]/g, '').length);
    if (/%/.test(fmt)) return (v * 100).toFixed(0) + '%';
    if (/#,##0/.test(fmt)) return v.toLocaleString('en-US');
    if (/,/.test(fmt)) return v.toLocaleString('en-US');
    return String(v);
  });
  // 日期：用 "YYYY-MM-DD" 文本表示（不引入序列号，避免显示成一串数字）
  function pad2(n) { return String(n).padStart(2, '0'); }
  function todayStr() { const d = new Date(); return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()); }
  function parseDate(v) {
    if (v instanceof Date) return v;
    if (typeof v === 'number') { const d = new Date(Date.UTC(1899, 11, 30) + v * 86400000); return d; }
    const s = String(v).trim().replace(/[/.]/g, '-');
    const m = /^(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?/.exec(s);
    if (!m) fail('#VALUE!');
    return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]), Number(m[4] || 0), Number(m[5] || 0), Number(m[6] || 0));
  }
  def('TODAY', () => todayStr());
  def('NOW', () => { const d = new Date(); return todayStr() + ' ' + pad2(d.getHours()) + ':' + pad2(d.getMinutes()) + ':' + pad2(d.getSeconds()); });
  def('DATE', a => toNum(a[0]) + '-' + pad2(toNum(a[1])) + '-' + pad2(toNum(a[2])));
  def('YEAR', a => parseDate(a[0]).getFullYear());
  def('MONTH', a => parseDate(a[0]).getMonth() + 1);
  def('DAY', a => parseDate(a[0]).getDate());
  def('HOUR', a => parseDate(a[0]).getHours());
  def('MINUTE', a => parseDate(a[0]).getMinutes());
  def('SECOND', a => parseDate(a[0]).getSeconds());
  def('WEEKDAY', a => { const d = parseDate(a[0]); const type = a.length > 1 ? toNum(a[1]) : 1; const js = d.getDay(); return type === 2 ? (js === 0 ? 7 : js) : (js + 1); });
  def('EDATE', a => { const d = parseDate(a[0]); const m = toNum(a[1]); const r = new Date(d.getFullYear(), d.getMonth() + m, d.getDate()); return r.getFullYear() + '-' + pad2(r.getMonth() + 1) + '-' + pad2(r.getDate()); });
  def('EOMONTH', a => { const d = parseDate(a[0]); const m = toNum(a[1]); const r = new Date(d.getFullYear(), d.getMonth() + m + 1, 0); return r.getFullYear() + '-' + pad2(r.getMonth() + 1) + '-' + pad2(r.getDate()); });
  def('DATEDIF', a => {
    const d1 = parseDate(a[0]), d2 = parseDate(a[1]), unit = String(a[2] || 'D').toUpperCase();
    const diffMs = d2 - d1;
    switch (unit) {
      case 'Y': return d2.getFullYear() - d1.getFullYear() - (d2 < new Date(d2.getFullYear(), d1.getMonth(), d1.getDate()) ? 1 : 0);
      case 'M': return (d2.getFullYear() - d1.getFullYear()) * 12 + (d2.getMonth() - d1.getMonth()) - (d2.getDate() < d1.getDate() ? 1 : 0);
      case 'D': return Math.round(diffMs / 86400000);
      case 'YD': { const t = new Date(d1); t.setFullYear(d2.getFullYear()); if (t > d2) t.setFullYear(d2.getFullYear() - 1); return Math.round((d2 - t) / 86400000); }
      case 'YM': { let m = d2.getMonth() - d1.getMonth(); if (m < 0) m += 12; if (d2.getDate() < d1.getDate()) m--; return m; }
      case 'MD': return Math.round((new Date(2000, d2.getMonth(), d2.getDate()) - new Date(2000, d1.getMonth(), d1.getDate())) / 86400000);
      default: fail('#NUM!');
    }
  });
  def('DAYS', a => Math.round((parseDate(a[1]) - parseDate(a[0])) / 86400000));
  def('NETWORKDAYS', a => {
    const d1 = parseDate(a[0]), d2 = parseDate(a[1]);
    let count = 0; const cur = new Date(d1);
    while (cur <= d2) { const wd = cur.getDay(); if (wd !== 0 && wd !== 6) count++; cur.setDate(cur.getDate() + 1); }
    return count;
  });
  function lookupMatrix(m) { return isRange(m) ? m.matrix : [[m]]; }
  def('VLOOKUP', a => {
    const needle = a[0], m = lookupMatrix(a[1]), col = toNum(a[2]);
    const approx = a.length > 3 ? toBool(a[3]) : true;
    let hit = null;
    for (let r = 0; r < m.length; r++) {
      const first = m[r][0];
      const same = cmp(first, needle) === 0;
      if (same) { hit = m[r]; break; }
      if (approx && cmp(first, needle) < 0) hit = m[r];   // 近似匹配：取最后一个小于 needle 的
    }
    if (!hit) fail('#N/A');
    const v = hit[col - 1];
    if (v === undefined) fail('#REF!');
    return v;
  });
  def('INDEX', a => {
    const m = lookupMatrix(a[0]), rn = toNum(a[1]), cn = a.length > 2 ? toNum(a[2]) : 1;
    const row = m[rn - 1];
    if (!row) fail('#REF!');
    const v = row[cn - 1];
    return v === undefined ? fail('#REF!') : v;
  });
  def('MATCH', a => {
    const needle = a[0], m = lookupMatrix(a[1]);
    const line = Array.isArray(m[0]) && m.length > 1 ? m.map(r => r[0]) : m[0];  // 单行/单列都支持
    for (let i = 0; i < line.length; i++) {
      if (matchCond(line[i], needle)) return i + 1;
    }
    fail('#N/A');
  });
  // ROW / COLUMN：无参返回当前单元格行/列号（1 起）；传引用返回该引用的行/列号
  function refRowCol(addr) {
    const m = /^(\$?)([A-Za-z]{1,3})(\$?)(\d+)$/.exec(String(addr).trim());
    if (!m) fail('#REF!');
    let col = 0;
    for (const ch of m[2].toUpperCase()) col = col * 26 + (ch.charCodeAt(0) - 64);
    return { r: parseInt(m[4], 10), c: col };
  }

  function callFn(name, args, env) {
    const key = String(name).toUpperCase();
    if (key === 'IF') {
      const cond = args.length ? toBool(args[0]) : false;
      if (cond) return args.length > 1 ? args[1] : true;
      return args.length > 2 ? args[2] : false;
    }
    if (key === 'AND') return flat(args).every(v => !isBlank(v) && toBool(v));
    if (key === 'OR') return flat(args).some(v => !isBlank(v) && toBool(v));
    if (key === 'NOT') return !toBool(args[0]);
    if (key === 'TRUE') return true;
    if (key === 'FALSE') return false;
    if (key === 'ROW') {
      // 无参 → 当前单元格行号；传参且形如 "A1" 地址 → 该行号；否则按数值解析
      if (!args.length) return (env.rowIndex || 0) + 1;
      const v = args[0];
      if (typeof v === 'string' && /^\$?[A-Za-z]{1,3}\$?\d+$/.test(v.trim())) return refRowCol(v).r;
      return toNum(v);
    }
    if (key === 'COLUMN') {
      if (!args.length) return (env.colIndex || 0) + 1;
      const v = args[0];
      if (typeof v === 'string' && /^\$?[A-Za-z]{1,3}\$?\d+$/.test(v.trim())) return refRowCol(v).c;
      return toNum(v);
    }
    const fn = FN[key];
    if (!fn) throw unsupported(key);
    return fn(args, env);
  }

  // ---------- 求值 ----------
  function resolveRef(addr, sheet, env) {
    const pos = parseAddr(addr);
    return env.cellValue(sheet || env.sheetName, pos.r, pos.c);
  }
  function parseAddr(addr) {
    const m = /^(\$?)([A-Za-z]{1,3})(\$?)(\d+)$/.exec(String(addr).trim());
    if (!m) fail('#REF!');
    let col = 0;
    for (const ch of m[2].toUpperCase()) col = col * 26 + (ch.charCodeAt(0) - 64);
    return { r: parseInt(m[4], 10) - 1, c: col - 1 };
  }
  function evalNode(node, env) {
    switch (node.t) {
      case 'num': return node.v;
      case 'str': return node.v;
      case 'bool': return node.v;
      case 'ref': return resolveRef(node.addr, node.sheet, env);
      case 'range': {
        const a = parseAddr(node.a), b = parseAddr(node.b);
        const r0 = Math.min(a.r, b.r), r1 = Math.max(a.r, b.r);
        const c0 = Math.min(a.c, b.c), c1 = Math.max(a.c, b.c);
        const sheet = node.sheet || env.sheetName;
        if (env.rangeMatrix) return mkRange(env.rangeMatrix(sheet, r0, c0, r1, c1));
        const matrix = [];
        for (let r = r0; r <= r1; r++) {
          const row = [];
          for (let c = c0; c <= c1; c++) row.push(env.cellValue(sheet, r, c));
          matrix.push(row);
        }
        return mkRange(matrix);
      }
      case 'pct': return toNum(evalNode(node.a, env)) / 100;
      case 'un': {
        const v = toNum(evalNode(node.a, env));
        return node.op === '-' ? -v : v;
      }
      case 'bin': {
        const op = node.op;
        if (op === '&') return toStr(evalNode(node.a, env)) + toStr(evalNode(node.b, env));
        if (['=', '<>', '<', '>', '<=', '>='].indexOf(op) >= 0) {
          const r = cmp(evalNode(node.a, env), evalNode(node.b, env));
          switch (op) {
            case '=': return r === 0;
            case '<>': return r !== 0;
            case '<': return r < 0;
            case '>': return r > 0;
            case '<=': return r <= 0;
            case '>=': return r >= 0;
          }
        }
        const x = toNum(evalNode(node.a, env)), y = toNum(evalNode(node.b, env));
        switch (op) {
          case '+': return x + y;
          case '-': return x - y;
          case '*': return x * y;
          case '/': if (y === 0) fail('#DIV/0!'); return x / y;
          case '^': { const p = Math.pow(x, y); if (!isFinite(p)) fail('#NUM!'); return p; }
        }
        fail('#VALUE!');
      }
      case 'call': {
        const fname = String(node.name).toUpperCase();
        // IF / IFERROR / IFNA / AND / OR 需要惰性求值：否则 =IF(A1=0,"",1/A1) 这类会先算出 #DIV/0!
        if (fname === 'IF') {
          const cond = toBool(evalNode(node.args[0], env));
          if (cond) return node.args[1] ? evalNode(node.args[1], env) : true;
          return node.args[2] ? evalNode(node.args[2], env) : false;
        }
        if (fname === 'IFERROR' || fname === 'IFNA') {
          try {
            const v = evalNode(node.args[0], env);
            const bad = fname === 'IFNA' ? (v === '#N/A') : isError(v);
            if (!bad) return v;
          } catch (e) {
            if (e && e.unsupported) throw e;
            if (e && e.formulaError && fname !== 'IFERROR' && e.code !== '#N/A') throw e;
          }
          return node.args[1] ? evalNode(node.args[1], env) : '';
        }
        if (fname === 'AND' || fname === 'OR') {
          const list = [];
          node.args.forEach(a => {
            let v;
            try { v = evalNode(a, env); } catch (e) { if (e && e.unsupported) throw e; v = (e && e.code) ? e.code : '#ERROR!'; }
            if (isRange(v)) v = v.flat;
            if (Array.isArray(v)) v.forEach(x => list.push(x)); else list.push(v);
          });
          const vals = list.filter(x => !isBlank(x));
          return fname === 'AND' ? vals.every(x => toBool(x)) : vals.some(x => toBool(x));
        }
        const args = node.args.map(a => evalNode(a, env));
        return callFn(node.name, args, env);
      }
    }
    fail('#ERROR!');
  }

  function evaluate(formula, env) {
    const text = String(formula == null ? '' : formula).replace(/^=/, '');
    if (text.trim() === '') return '';
    try {
      const ast = parse(text);
      const v = evalNode(ast, env);
      if (isRange(v)) return v.flat.length ? v.flat[0] : '';
      if (typeof v === 'number' && !isFinite(v)) return '#NUM!';
      return v;
    } catch (e) {
      if (e && e.unsupported) throw e;             // 交给调用方决定（保留原值）
      if (e && e.formulaError) return e.code;
      return '#ERROR!';
    }
  }

  window.FormulaEngine = {
    evaluate,
    parse,
    isFormula(text) { return typeof text === 'string' && /^\s*=/.test(text) && text.trim().length > 1; },
    isError,
    FUNCTIONS: () => Object.keys(FN)
  };
})();

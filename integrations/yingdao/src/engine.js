// ============ RPA 引擎 ============
// 通过 IPC 调用主进程的独立浏览器窗口执行 DOM 操作

(function () {
  let excelBooks = [];     // 多标签 workbook 数组 [{ id, book, path, activeSheet }]
  let activeBookId = null; // 当前激活的 workbook id
  let excelBook = null;    // 当前激活的 workbook（快捷引用，兼容现有代码）
  let excelPath = null;    // 当前激活的路径（快捷引用）
  let bookIdSeq = 1;       // workbook id 自增
  let clipboard = null;    // 全局剪贴板 { rows, fromSheet, fromBook } 支持跨 sheet/book

  // 浏览器操作统一走 IPC
  const B = () => window.yingdao.browser;

  const ERR_STOP = 'RPA_STOP';   // 手动停止的哨兵错误（流程编排识别后显示"已手动停止"）

  // 定位元素时默认等多久（秒）：页面还没渲染完就找元素，是"识别不出来"的头号原因
  const LOCATE_WAIT_SEC = 5;

  const Engine = {
    vars: {},
    cancelRequested: false,      // 运行中断标记：点「停止」后置位，长耗时指令分段检查

    // 手动停止：置位中断标记（等待类指令会尽快退出）
    cancel() { this.cancelRequested = true; },
    resetCancel() { this.cancelRequested = false; },

    // 可被中断的等待（分段 sleep，最多 100ms 内响应停止）
    async sleepInterruptible(seconds) {
      const total = Math.max(0, Number(seconds) || 0) * 1000;
      let waited = 0;
      while (waited < total) {
        if (this.cancelRequested) throw new Error(ERR_STOP);
        const chunk = Math.min(100, total - waited);
        await new Promise(r => setTimeout(r, chunk));
        waited += chunk;
      }
      if (this.cancelRequested) throw new Error(ERR_STOP);
    },

    // ---- 变量插值 ----
    // 支持 ${变量名} 和 ${变量名[索引]}（数组元素），变量名可含中文
    expand(text) {
      if (typeof text !== 'string') return text;
      return text.replace(/\$\{([\u4e00-\u9fa5\w]+)(?:\[(\d+)\])?\}/g, (_, k, idx) => {
        const v = this.vars[k];
        if (idx !== undefined) {
          if (Array.isArray(v)) return v[Number(idx)] ?? '';
          return Number(idx) === 0 ? (v ?? '') : '';
        }
        if (Array.isArray(v)) return v.length ? v[0] : '';
        if (v && typeof v === 'object') { try { return JSON.stringify(v); } catch (e) { return String(v); } }
        return v ?? '';
      });
    },

    // 生成时间戳字符串（用于默认文件名，避免覆盖）
    timestamp() {
      const d = new Date();
      const p = (n) => String(n).padStart(2, '0');
      return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
    },

    // ---- 浏览器自动化：通过 IPC 控制独立浏览器窗口 ----
    // target：'当前标签页'（在激活窗口里打开）/ '新标签页'·'新窗口'（新建独立窗口）
    // 打开网页
    // target：'当前标签页'（在激活窗口里打开）/ '新窗口'·'新标签页'（新建独立窗口）
    // loginMode：新窗口的登录方式，决定用哪个登录会话（多账号靠它隔离）
    //   独立登录(每次全新) / 独立登录(按账号位保存) / 共用登录(沿用已有登录)
    async openUrl(url, target = '当前标签页', loginMode, engine, waitForLoad = true) {
      url = this.expand(url);
      const isNew = target === '新标签页' || target === '新窗口';
      const r = await B().loadURL(url, isNew ? '新窗口' : '当前标签页', loginMode, this.expand(engine), waitForLoad);
      return r;
    },

    // 等待页面就绪：document.readyState 到 complete + AJAX/资源网络空闲。
    // 老系统（朗坤 LiEMS 等）大量内容是 AJAX 异步加载的，readyState complete 不代表数据出来了，
    // 所以要再等网络空闲一小段时间，否则"点击不了/提取不到"十有八九是内容还没渲染。
    async waitPageReady(timeoutSec = 20) {
      const deadline = Date.now() + Math.max(1, Number(timeoutSec) || 20) * 1000;
      const code = `(async () => {
        const t0 = Date.now();
        // 第一步：等 readyState
        while (document.readyState !== 'complete') {
          if (Date.now() - t0 > 25000) break;
          await new Promise(r => setTimeout(r, 150));
        }
        return document.readyState;
      })()`;
      try { await this.execJSAny(code, 30000); } catch (e) { }
      // 第二步：等网络空闲（XHR/fetch 都不再挂起）
      const idleCode = `(async () => {
        const t0 = Date.now();
        let stable = 0;
        while (Date.now() - t0 < 20000) {
          if (window.__rpaPendingRequests === undefined) {
            // 注入计数器：拦 fetch + XHR
            window.__rpaPendingRequests = 0;
            const _f = window.fetch;
            window.fetch = function () { window.__rpaPendingRequests++; try { return _f.apply(this, arguments).finally(function(){ window.__rpaPendingRequests--; }); } catch (e) { window.__rpaPendingRequests--; throw e; } };
            const _o = XMLHttpRequest.prototype.open, _s = XMLHttpRequest.prototype.send;
            XMLHttpRequest.prototype.open = function () { this.__rpaActive = true; return _o.apply(this, arguments); };
            XMLHttpRequest.prototype.send = function () { window.__rpaPendingRequests++; this.addEventListener('loadend', function(){ window.__rpaPendingRequests--; }); return _s.apply(this, arguments); };
          }
          if (window.__rpaPendingRequests <= 0) stable++;
          else stable = 0;
          if (stable >= 3) return 'idle';
          await new Promise(r => setTimeout(r, 250));
        }
        return 'timeout';
      })()`;
      try { await this.execJSAny(idleCode, 25000); } catch (e) { }
      return true;
    },

    // 诊断：当前页面有哪些 frame、还在不在加载、候选元素（排错利器）
    async diagnosePage() {
      const code = `(function(){
        var out = { readyState: document.readyState, frames: [], hints: [] };
        try {
          var frames = document.querySelectorAll('iframe,frame');
          out.frameCount = frames.length;
          for (var i = 0; i < frames.length && i < 20; i++) {
            var f = frames[i];
            out.frames.push({
              id: f.id || '', name: f.name || '', src: (f.src || '').slice(0, 80)
            });
          }
        } catch (e) {}
        if (document.readyState !== 'complete') out.hints.push('页面还没加载完（readyState=' + document.readyState + '），元素可能还没渲染');
        var inputs = document.querySelectorAll('input,select,textarea');
        var buttons = document.querySelectorAll('button,a,input[type=button],input[type=submit],div[onclick],span[onclick],li[onclick]');
        out.inputCount = inputs.length;
        out.clickableCount = buttons.length;
        if (!buttons.length) out.hints.push('当前文档里没有明显的可点击元素（可能都在 iframe 里，或需要先点某个菜单展开）');
        return out;
      })()`;
      try { return await this.execJSAny(code); } catch (e) { return { error: e.message }; }
    },

    // 在浏览器中执行 JS 并返回结果（只跑主文档）
    async execJS(jsCode) {
      return B().execJS(jsCode);
    },

    // 在浏览器中执行 JS：优先"跨框架执行"——主文档里没有就去各个 iframe 里试，
    // 这样跨域 iframe 里的元素也能操作（单靠主文档的 document.querySelector 拿不到）
    async execJSAny(jsCode, timeoutMs) {
      const b = B();
      if (typeof b.execJSFrames === 'function') return await b.execJSFrames(jsCode, timeoutMs);
      return await b.execJS(jsCode, timeoutMs);
    },

    // ===== 元素定位（含世博自动化式「锚点定位」）=====
    // 页面内"稳健查找"工具函数：在主文档 + 同源 iframe + 开放的影子 DOM 里找元素。
    // 为什么必须有这个：内部系统大量元素在 iframe / 影子 DOM 里，
    // 老写法只用 document.querySelector 就永远找不到 —— 这是"元素识别不出来"的头号原因。
    // 返回一段 JS 源码，调用方把它塞进 (function(){ ... })() 里用（作用域自包含，不污染页面全局）。
    queryHelpersJS() {
      return `
        function __rpaRoots() {
          var out = [document], count = 0, MAX = 200;
          function walk(root, depth) {
            if (count++ > MAX || depth > 12) return;
            var frames = [];
            try { frames = Array.prototype.slice.call(root.querySelectorAll('iframe,frame')); } catch (e) { }
            for (var i = 0; i < frames.length; i++) {
              try {
                var d = frames[i].contentDocument;
                if (d) { out.push(d); walk(d, depth + 1); }
              } catch (e) { /* 跨域 iframe 拿不到 contentDocument，跳过（由主进程逐框架执行兜底） */ }
            }
            var all = [];
            try { all = Array.prototype.slice.call(root.querySelectorAll('*')); } catch (e) { }
            for (var j = 0; j < all.length; j++) {
              var sr = all[j].shadowRoot;
              if (sr) { out.push(sr); walk(sr, depth + 1); }
            }
          }
          walk(document, 0);
          return out;
        }
        function __rpaAll(sel) {
          var res = [], roots = __rpaRoots();
          for (var i = 0; i < roots.length; i++) {
            try { res = res.concat(Array.prototype.slice.call(roots[i].querySelectorAll(sel))); } catch (e) { }
          }
          return res;
        }
        function __rpaAllXPath(xp) {
          var res = [], roots = __rpaRoots();
          for (var i = 0; i < roots.length; i++) {
            try {
              var r = roots[i], doc = r.ownerDocument || document;
              var it = doc.evaluate(xp, r, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
              for (var k = 0; k < it.snapshotLength; k++) res.push(it.snapshotItem(k));
            } catch (e) { }
          }
          return res;
        }
        // 统一取值：优先按元素类型取"真正显示/保存的内容"，再逐级回退。
        // 为什么必须有：老系统里"值"可能在 value（input/textarea）、选中项（select）、
        // readonly 属性、title、placeholder，甚至 label 兄弟节点里 —— 只取 innerText 会大量漏。
        function __rpaText(e) {
          if (!e) return '';
          var tag = e.tagName;
          if (tag === 'INPUT') {
            var type = (e.type || 'text').toLowerCase();
            if (type === 'checkbox' || type === 'radio') return e.checked ? (e.value || 'true') : '';
            if (type === 'button' || type === 'submit' || type === 'reset') return (e.value || e.innerText || e.getAttribute('title') || '').trim();
            return e.value != null ? e.value : (e.getAttribute('value') || '');
          }
          if (tag === 'TEXTAREA') return e.value != null ? e.value : (e.innerText || e.textContent || '');
          if (tag === 'SELECT') {
            var o = e.options && e.options[e.selectedIndex];
            return o ? (o.text || o.value || '').trim() : (e.value || '');
          }
          if (tag === 'IMG') return (e.alt || e.title || '').trim();
          // 普通元素：优先 innerText（可视化文本，含换行），回退 textContent / title / value
          var v = (e.innerText != null && e.innerText !== '') ? e.innerText : e.textContent;
          v = (v || '').trim();
          if (v) return v;
          if (e.getAttribute && e.getAttribute('title')) return e.getAttribute('title').trim();
          if (e.value != null) return String(e.value).trim();
          // 兜底：找相邻的 label
          try {
            var lb = e.closest('label');
            if (lb) { var lv = (lb.innerText || lb.textContent || '').trim(); if (lv) return lv; }
          } catch (err) { }
          return '';
        }
        function __rpaByText(txt, fuzzy) {
          var t = String(txt == null ? '' : txt).trim();
          if (!t) return null;
          var SKIP = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, HTML: 1, HEAD: 1, META: 1, LINK: 1, TITLE: 1, BODY: 1 };
          var roots = __rpaRoots(), seen = [];
          for (var i = 0; i < roots.length; i++) {
            var all = [];
            try { all = Array.prototype.slice.call(roots[i].querySelectorAll('*')); } catch (e) { }
            for (var j = 0; j < all.length; j++) {
              var e = all[j];
              if (seen.indexOf(e) >= 0 || SKIP[e.tagName]) continue;
              seen.push(e);
              var tx = __rpaText(e);
              if (!tx) continue;
              if (tx === t) return e;
              if (fuzzy && tx.indexOf(t) >= 0) return e;
            }
          }
          return null;
        }
        function __rpaByAttr(kw) {
          var t = String(kw == null ? '' : kw).trim().toLowerCase();
          if (!t) return null;
          var ATTRS = ['name', 'id', 'placeholder', 'title', 'aria-label', 'value', 'data-id', 'data-name', 'href', 'alt'];
          var roots = __rpaRoots(), seen = [];
          for (var i = 0; i < roots.length; i++) {
            var all = [];
            try { all = Array.prototype.slice.call(roots[i].querySelectorAll('*')); } catch (e) { }
            for (var j = 0; j < all.length; j++) {
              var e = all[j];
              if (seen.indexOf(e) >= 0) continue;
              seen.push(e);
              for (var a = 0; a < ATTRS.length; a++) {
                var v = e.getAttribute && e.getAttribute(ATTRS[a]);
                if (v && String(v).toLowerCase().indexOf(t) >= 0) return e;
              }
            }
          }
          return null;
        }
        function __rpaFind(sel) {
          var t = String(sel == null ? '' : sel).trim();
          if (!t) return null;
          var a = [];
          try { a = __rpaAll(t); } catch (e) { }
          if (a.length) return a[0];
          if (t.charAt(0) === '/' || t.charAt(0) === '(') {
            var b = __rpaAllXPath(t);
            if (b.length) return b[0];
          }
          return null;
        }
      `;
    },

    // 返回一段 JS 表达式：求值得到目标元素（或在页面里找不到时返回 null）
    // by 支持 CSS选择器/XPath/文本内容/智能匹配/锚点定位
    locatorSnippet(by, esc, escAnchor, rel) {
      const H = this.queryHelpersJS();
      if (by === '锚点定位') {
        return `(function(){ ${H}
          var __anchors = String('${escAnchor}' || '').split(/[;；]/).map(function(s){ return s.trim(); }).filter(Boolean)
            .map(function(s){ return __rpaFind(s); }).filter(Boolean);
          var __anchor = __anchors[0];
          if (!__anchor) return null;
          var SEL = '${esc}';
          var REL = '${rel}';
          var aR = __anchor.getBoundingClientRect();
          var tol = 6;
          var ovV = function(r){ return Math.min(r.bottom, aR.bottom) - Math.max(r.top, aR.top) > 0; };
          var ovH = function(r){ return Math.min(r.right, aR.right) - Math.max(r.left, aR.left) > 0; };
          if (REL === '内部') { return SEL ? __anchor.querySelector(SEL) : (__anchor.children[0] || null); }
          if (REL === '相邻') { return SEL ? (__anchor.nextElementSibling && __anchor.nextElementSibling.matches(SEL) ? __anchor.nextElementSibling : null) : __anchor.nextElementSibling; }
          var cands = SEL ? __rpaAll(SEL) : __rpaAll('a,button,input,select,textarea,span,div,label,td,th');
          var best = null, bd = Infinity;
          cands.forEach(function(c){
            if (c === __anchor || __anchors.indexOf(c) >= 0 || __anchor.contains(c)) return;
            var r = c.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) return;
            var d = Infinity;
            if (REL === '下方') { if (r.top >= aR.bottom - tol && ovH(r)) d = r.top - aR.bottom; }
            else if (REL === '上方') { if (r.bottom <= aR.top + tol && ovH(r)) d = aR.top - r.bottom; }
            else if (REL === '右侧') { if (r.left >= aR.right - tol && ovV(r)) d = r.left - aR.right; }
            else if (REL === '左侧') { if (r.right <= aR.left + tol && ovV(r)) d = aR.left - r.right; }
            else { d = Math.hypot(r.left - aR.left, r.top - aR.top); }
            if (d < bd) { bd = d; best = c; }
          });
          return best;
        })()`;
      }
      if (by === 'XPath') {
        return `(function(){ ${H} var a = []; try { a = __rpaAllXPath('${esc}'); } catch(e) {} return a.length ? a[0] : null; })()`;
      }
      if (by === '文本内容') {
        return `(function(){ ${H} return __rpaByText('${esc}', true); })()`;
      }
      if (by === '智能匹配') {
        return `(function(){ ${H}
          return __rpaFind('${esc}') || __rpaByText('${esc}', false) || __rpaByText('${esc}', true) || __rpaByAttr('${esc}');
        })()`;
      }
      // 默认 CSS选择器：先严格按选择器找，找不到再按文本/属性救一把（很多时候选择器已失效，
      // 但页面上那行字还在，这时能救回来比直接报错有用得多）
      return `(function(){ ${H}
        return __rpaFind('${esc}') || __rpaByText('${esc}', true) || __rpaByAttr('${esc}');
      })()`;
    },

    // 在浏览器里探测"这个元素到底能不能找到"（给排错用），走的是同一套稳健查找
    buildLocatorJS(selector, by) {
      selector = this.expand(selector);
      const esc = selector.replace(/'/g, "\\'");
      const H = this.queryHelpersJS();
      return `(function(){ ${H}
        var by = '${by}';
        var sel = '${esc}';
        var el = null;
        if (by === 'XPath') { el = (__rpaAllXPath(sel) || [])[0]; }
        else if (by === '文本内容') { el = __rpaByText(sel, true); }
        else { el = __rpaFind(sel) || __rpaByText(sel, true) || __rpaByAttr(sel); }
        return el ? 'found' : 'notfound';
      })()`;
    },

    // 智能匹配：按优先级依次尝试所有定位方式，返回第一个找到的元素（并说明是哪招找到的）
    // 优先级：CSS选择器 > XPath > 文本完全匹配 > 文本包含 > 属性模糊
    async smartMatch(selector) {
      const esc = selector.replace(/'/g, "\\'");
      const H = this.queryHelpersJS();
      const code = `(function(){ ${H}
        var sel = '${esc}';
        function info(el, how) {
          return { by: how, el: true, tag: el.tagName, text: (el.innerText || el.value || '').slice(0, 40) };
        }
        var a = [];
        try { a = __rpaAll(sel); } catch (e) { }
        if (a.length) return info(a[0], 'CSS选择器');
        var b = __rpaAllXPath(sel);
        if (b.length) return info(b[0], 'XPath');
        var c = __rpaByText(sel, false);
        if (c) return info(c, '文本内容');
        var d = __rpaByText(sel, true);
        if (d) return info(d, '文本内容(包含)');
        var f = __rpaByAttr(sel);
        if (f) return info(f, '属性模糊匹配');
        return null;
      })()`;
      const r = await this.execJSAny(code);
      if (r) return r;
      throw new Error('所有定位方式都未找到元素：' + selector +
        '（已试过 CSS选择器 / XPath / 文本 / 属性模糊，并搜索了同源 iframe 与影子 DOM）');
    },

    // 通用定位器：等到元素出现（默认最多 LOCATE_WAIT_SEC 秒）——页面没渲染完就找元素是"识别不出来"的常见原因
    async locate(selector, by = 'CSS选择器', anchor = '', anchorRel = '下方', waitSec) {
      selector = this.expand(selector);
      anchor = this.expand(anchor);
      if (by === '锚点定位') {
        if (!anchor) throw new Error('锚点定位需要填写「锚点元素」');
      } else if (!selector) {
        throw new Error('元素定位不能为空');
      }
      const esc = selector.replace(/'/g, "\\'");
      const escA = (anchor || '').replace(/'/g, "\\'");
      const snippet = this.locatorSnippet(by, esc, escA, anchorRel);
      const secs = waitSec == null ? LOCATE_WAIT_SEC : Math.max(0, Number(waitSec) || 0);
      const limit = Math.round(secs * 1000);
      const code = `(async () => {
        const t0 = Date.now();
        while (true) {
          const el = ${snippet};
          if (el) return true;
          if (Date.now() - t0 >= ${limit}) return false;
          await new Promise(r => setTimeout(r, 200));
        }
      })()`;
      const ok = await this.execJSAny(code, limit + 5000);
      if (!ok) {
        const hint = by === '锚点定位'
          ? `锚点定位未找到元素（锚点：${anchor}｜方位：${anchorRel}${selector ? '｜目标：' + selector : ''}）`
          : `元素未找到（${by}）：${selector}`;
        // 抓一把诊断信息，帮用户在朗坤这类老系统上定位原因
        let diag = '';
        try {
          const d = await this.diagnosePage();
          if (d) {
            const parts = [];
            if (d.readyState && d.readyState !== 'complete') parts.push('页面还没加载完(readyState=' + d.readyState + ')');
            if (d.frameCount) parts.push('有 ' + d.frameCount + ' 个 iframe，目标可能在某个 iframe 里');
            if (d.clickableCount === 0) parts.push('当前文档里没找到可点击元素，可能需要先点菜单展开');
            if (parts.length) diag = ' 诊断：' + parts.join('；') + '。';
          }
        } catch (e) { }
        throw new Error(hint + `。已等待 ${secs} 秒，并搜索了同源 iframe 与影子 DOM。` +
          diag +
          `若目标在跨域 iframe 里，请用「🎯 在浏览器中选取元素」重新拾取，或把定位方式改成「智能匹配」`);
      }
      return true;
    },

    async click({ selector, clickType = '单击', by = 'CSS选择器', anchor = '', anchorRel = '下方' }) {
      selector = this.expand(selector);
      anchor = this.expand(anchor);

      // 坐标定位：直接派发到指定坐标（不查找元素）
      if (by === '坐标定位') {
        const m = selector.match(/^\s*(\d+)\s*,\s*(\d+)\s*$/);
        if (!m) throw new Error('坐标格式：x,y（如：100,200）');
        const x = parseInt(m[1], 10);
        const y = parseInt(m[2], 10);
        const code = `(() => {
          // 关键：坐标若落在 iframe 上，elementFromPoint 拿到的是 iframe 元素本身（不是里面真正要点的东西），
          // 必须从 iframe 递归钻进去找到最深的真实目标，否则点下去没反应。
          function __deepTarget(doc, x, y) {
            var el = doc.elementFromPoint(x, y);
            if (!el) return null;
            var guard = 0;
            while (el && (el.tagName === 'IFRAME' || el.tagName === 'FRAME') && guard++ < 6) {
              var d = null;
              try { d = el.contentDocument; } catch (e) { d = null; }
              if (!d) break;
              var r = el.getBoundingClientRect();
              var inner = d.elementFromPoint(x - r.left, y - r.top);
              if (!inner) break;
              el = inner;
            }
            return el;
          }
          function __fire(el, type, x, y, btn) {
            var o = { bubbles: true, cancelable: true, composed: true, clientX: x, clientY: y, button: btn, view: window };
            var ev;
            try { ev = new PointerEvent(type, Object.assign({ pointerId: 1, pointerType: 'mouse', isPrimary: true }, o)); }
            catch (e) { ev = new MouseEvent(type, o); }
            el.dispatchEvent(ev);
          }
          var el = __deepTarget(document, ${x}, ${y});
          if (!el) return '元素未找到';
          var btn = ${clickType === '右键' ? '2' : '0'};
          // 完整事件序列：老系统（EasyUI/ExtJS）的菜单要先 hover 才展开、按钮要完整按压序列才认
          __fire(el, 'mouseover', ${x}, ${y}, btn);
          __fire(el, 'mouseenter', ${x}, ${y}, btn);
          __fire(el, 'mousemove', ${x}, ${y}, btn);
          __fire(el, 'mousedown', ${x}, ${y}, btn);
          __fire(el, 'mouseup',   ${x}, ${y}, btn);
          __fire(el, '${clickType === '双击' ? 'dblclick' : (clickType === '右键' ? 'contextmenu' : 'click')}', ${x}, ${y}, btn);
          return 'clicked @ (${x}, ${y}) → ' + el.tagName;
        })()`;
        return await this.execJSAny(code);
      }

      // 普通定位
      await this.locate(selector, by, anchor, anchorRel);
      const esc = selector.replace(/'/g, "\\'");
      const escA = (anchor || '').replace(/'/g, "\\'");
      const evt = clickType === '双击' ? 'dblclick' : (clickType === '右键' ? 'contextmenu' : 'click');
      const btn = clickType === '右键' ? '2' : '0';
      const code = `(() => {
        const el = ${this.locatorSnippet(by, esc, escA, anchorRel)};
        if (!el) throw new Error('元素未找到');
        el.scrollIntoView({block:'center', inline:'center'});
        function fire(type, x, y) {
          var o = { bubbles: true, cancelable: true, composed: true, clientX: x, clientY: y, button: ${btn}, view: window };
          var ev;
          try { ev = new PointerEvent(type, Object.assign({ pointerId: 1, pointerType: 'mouse', isPrimary: true }, o)); }
          catch (e) { ev = new MouseEvent(type, o); }
          el.dispatchEvent(ev);
        }
        var r = el.getBoundingClientRect();
        var x = r.left + r.width/2, y = r.top + r.height/2;
        // 完整事件序列：先 hover 让老系统的下拉菜单/悬浮层展开，再完整按压
        fire('mouseover', x, y);
        fire('mouseenter', x, y);
        fire('mousemove', x, y);
        fire('mousedown', x, y);
        fire('mouseup', x, y);
        fire('${evt}', x, y);
        // 有的老控件把真正的"按钮"放在某个子元素上（如 EasyUI 的 <a> 在 <td> 里），
        // 点父元素没反应时，往可点击的子元素上再补一次
        if ('${clickType}' !== '右键' && !el.matches('a,button,input,select,textarea')) {
          var inner = el.querySelector('a,button,input,label');
          if (inner) {
            var ir = inner.getBoundingClientRect();
            inner.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, clientX:ir.left+ir.width/2, clientY:ir.top+ir.height/2, button:${btn}}));
            inner.dispatchEvent(new MouseEvent('mouseup',   {bubbles:true, clientX:ir.left+ir.width/2, clientY:ir.top+ir.height/2, button:${btn}}));
            inner.dispatchEvent(new MouseEvent('${evt}',    {bubbles:true, clientX:ir.left+ir.width/2, clientY:ir.top+ir.height/2, button:${btn}}));
          }
        }
        return el.tagName + (el.innerText ? ': ' + el.innerText.slice(0,20) : '');
      })()`;
      return await this.execJSAny(code);
    },

    async input({ selector, text, clear = '是', by = 'CSS选择器', anchor = '', anchorRel = '下方', pressEnter = '否' }) {
      selector = this.expand(selector);
      text = this.expand(text);
      anchor = this.expand(anchor);
      await this.locate(selector, by, anchor, anchorRel);
      const esc = selector.replace(/'/g, "\\'");
      const escA = (anchor || '').replace(/'/g, "\\'");
      const escT = text.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\r?\n/g, '\\n');
      const code = `(() => {
        const el = ${this.locatorSnippet(by, esc, escA, anchorRel)};
        if (!el) throw new Error('元素未找到');
        el.scrollIntoView({block:'center', inline:'center'});
        el.focus();
        // 触发一次完整事件链，让老 jQuery 控件（监听 keyup/keypress/blur 才认值）也能收到
        function fireAll() {
          el.dispatchEvent(new Event('input',  {bubbles:true}));
          el.dispatchEvent(new Event('change', {bubbles:true}));
          ['keydown','keypress','keyup'].forEach(function(t){
            el.dispatchEvent(new KeyboardEvent(t, {bubbles:true, cancelable:true, key:'a', code:'KeyA'}));
          });
        }
        if (el.isContentEditable) {
          // 富文本 / contenteditable 老控件：写 innerText（保留换行）
          ${clear !== '否' ? `el.innerText = '';` : ''}
          el.innerText = '${escT}';
          fireAll();
          return el.innerText;
        }
        ${clear !== '否' ? `if ('value' in el) el.value='';` : ''}
        // 按元素类型选正确的 value setter（input/textarea/select 各自的原型不同）
        const setter = el.tagName === 'TEXTAREA'
          ? Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')
          : el.tagName === 'SELECT'
            ? Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value')
            : Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
        if (setter && setter.set) setter.set.call(el, '${escT}');
        else el.value = '${escT}';
        fireAll();
        // 最后补一个 blur（有些老表单在失焦时才提交值）
        try { el.blur && el.blur(); el.focus && el.focus(); } catch (e) {}
        return el.value;
      })()`;
      const r = await this.execJSAny(code);
      // 输入后按回车（搜索框/登录框常用）
      if (pressEnter === '是') await this.pressKey({ key: '回车(Enter)', times: 1 });
      return r;
    },

    async getText({ selector, varName, by = 'CSS选择器', anchor = '', anchorRel = '下方' }) {
      selector = this.expand(selector);
      anchor = this.expand(anchor);
      await this.locate(selector, by, anchor, anchorRel);
      const esc = selector.replace(/'/g, "\\'");
      const escA = (anchor || '').replace(/'/g, "\\'");
      const H = this.queryHelpersJS();
      const code = `(() => {
        ${H}
        const el = ${this.locatorSnippet(by, esc, escA, anchorRel)};
        return el ? __rpaText(el) : '';
      })()`;
      let text = await this.execJSAny(code);
      // 值可能是空字符串（内容还没渲染出来），再等几轮
      if (!text) {
        for (let i = 0; i < 5; i++) {
          await new Promise(r => setTimeout(r, 300));
          text = await this.execJSAny(code);
          if (text) break;
        }
      }
      this.vars[varName] = text;
      return text;
    },

    // 等待元素出现：分段轮询，便于中途「停止」（每段最多 1 秒）
    // 超时后可以"点坐标兜底"：有些页面元素偶尔识别不到、但位置是固定的，
    // 这时按录制好的坐标点一下就能继续往下跑，不用整个流程报错中断。
    async waitElement({ selector, timeout = 10, by = 'CSS选择器', anchor = '', anchorRel = '下方',
                        fallbackToXY = '只报错', xyPoints = '', xyInterval = 1 }) {
      if (by !== '锚点定位' && !this.expand(selector)) throw new Error('元素定位不能为空（等待元素出现需要填写选择器）');
      if (by === '锚点定位' && !this.expand(anchor)) throw new Error('锚点定位需要填写「锚点元素」');
      const deadline = Date.now() + Math.max(0.2, Number(timeout) || 10) * 1000;
      let lastErr = null;
      let found = false;
      while (Date.now() < deadline) {
        if (this.cancelRequested) throw new Error(ERR_STOP);
        const remainSec = Math.max(0.2, (deadline - Date.now()) / 1000);
        try {
          // 注意：有的实现"没找到"是返回假值而不是抛异常，两种都要当成"还没出现"继续等，
          // 否则会把 false 当成"等到"直接放过，后面的操作再去点就全错了
          const r = await this.waitElementOnce({ selector, timeout: Math.min(1, remainSec), by, anchor, anchorRel });
          if (r) { found = true; break; }
        } catch (e) {
          lastErr = e;
          // 中途点了「停止」要立刻退出，不要傻等超时
          if (String(e && e.message || '').indexOf(ERR_STOP) >= 0) throw e;
        }
        // 兜底节流：万一某次探测瞬间返回（没找到又不抛错），别让这个循环空转到把内存打满
        if (Date.now() < deadline) await new Promise(r => setTimeout(r, 100));
      }
      if (found) return true;
      // ---- 超时了：按配置决定"点坐标兜底"还是报错 ----
      const xy = this.expand(xyPoints);
      if (fallbackToXY === '点击坐标' && String(xy || '').trim()) {
        const pts = this.parsePoints(xy);
        await this.clickXY({ points: xy, interval: xyInterval, clickType: '单击' });
        return { fallback: '点击坐标', count: pts.length };
      }
      throw new Error(lastErr && lastErr.message ? lastErr.message : '元素超时未出现');
    },

    async waitElementOnce({ selector, timeout = 1, by = 'CSS选择器', anchor = '', anchorRel = '下方' }) {
      selector = this.expand(selector);
      anchor = this.expand(anchor);
      const esc = selector.replace(/'/g, "\\'");
      const escA = (anchor || '').replace(/'/g, "\\'");
      const ms = timeout * 1000;
      const snippet = this.locatorSnippet(by, esc, escA, anchorRel);
      const code = `(async () => {
        const t0 = Date.now();
        while (Date.now() - t0 < ${ms}) {
          const el = ${snippet};
          if (el) return true;
          await new Promise(r => setTimeout(r, 200));
        }
        throw new Error('元素超时未出现');
      })()`;
      return await this.execJSAny(code);
    },

    // ---- 数据抓取（Scraping）----
    // 抓取文本
    async scrapeText({ selector, varName = '抓取结果', by = 'CSS选择器', all = '单个' }) {
      selector = this.expand(selector);
      const isAll = all === '全部匹配';
      const esc = selector.replace(/'/g, "\\'");
      const H = this.queryHelpersJS();
      // 走同一套稳健查找：主文档 + 同源 iframe + 影子 DOM，并按"选择器→XPath→文本"逐级回退
      const inline = `(function(){ ${H}
        var sel = '${esc}';
        var els = [];
        if ('${by}' === 'XPath') { els = __rpaAllXPath(sel); }
        else {
          els = __rpaAll(sel);
          if (!els.length) els = __rpaAllXPath(sel);
          if (!els.length) { var t = __rpaByText(sel, true); if (t) els = [t]; }
        }
        els = els.filter(function(e){ return e && e.nodeType === 1; });
        return els.map(function(e){ return __rpaText(e); });
      })()`;
      const result = await this.execJSAny(inline);
      const out = isAll ? result : (result[0] ?? '');
      this.vars[varName] = out;
      return out;
    },

    // 抓取属性
    async scrapeAttr({ selector, attr = 'href', varName = '抓取结果', by = 'CSS选择器', all = '全部匹配' }) {
      selector = this.expand(selector);
      const isAll = all === '全部匹配';
      const esc = selector.replace(/'/g, "\\'");
      const attrEsc = attr.replace(/'/g, "\\'");
      const H2 = this.queryHelpersJS();
      const inline = `(function(){ ${H2}
        var sel = '${esc}';
        var els = [];
        if ('${by}' === 'XPath') { els = __rpaAllXPath(sel); }
        else {
          els = __rpaAll(sel);
          if (!els.length) els = __rpaAllXPath(sel);
          if (!els.length) { var t = __rpaByText(sel, true); if (t) els = [t]; }
        }
        els = els.filter(function(e){ return e && e.nodeType === 1; });
        return els.map(function(e){ return e.getAttribute('${attrEsc}') || ''; });
      })()`;
      const result = await this.execJSAny(inline);
      const out = isAll ? result : (result[0] ?? '');
      this.vars[varName] = out;
      return out;
    },

    // 抓取列表（结构化：每条记录提取多个字段）
    async scrapeList({ selector, fields = '', varName = '抓取列表', by = 'CSS选择器' }) {
      selector = this.expand(selector);
      // 解析字段："选择器:字段名,选择器2:字段名2"
      const fieldList = fields.split(',').map(s => s.trim()).filter(Boolean).map(s => {
        const i = s.lastIndexOf(':');
        if (i === -1) return { sel: s, name: s };
        return { sel: s.slice(0, i).trim(), name: s.slice(i + 1).trim() };
      });
      const esc = selector.replace(/'/g, "\\'");
      const fieldsJson = JSON.stringify(fieldList).replace(/'/g, "\\'");
      const inline = `(() => {
        const items = [];
        ${by === 'XPath' ?
          `try { const r = document.evaluate('${esc}', document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null); for (let i = 0; i < r.snapshotLength; i++) items.push(r.snapshotItem(i)); } catch(e) {}` :
          `try { items.push(...document.querySelectorAll('${esc}')); } catch(e) {}`
        }
        const fields = JSON.parse('${fieldsJson}');
        const rows = [];
        items.forEach(item => {
          const row = {};
          fields.forEach(f => {
            let el = null;
            try { el = item.querySelector(f.sel) || item; } catch(e) { el = item; }
            if (el === item && f.sel !== item) {
              // 字段选择器未命中，尝试直接取文本
            }
            row[f.name] = el ? (el.innerText || el.textContent || '').trim() : '';
          });
          rows.push(row);
        });
        return rows;
      })()`;
      const result = await this.execJSAny(inline);
      // 转成二维数组：第一行是表头
      const headers = fieldList.map(f => f.name);
      const arr = [headers, ...result.map(r => headers.map(h => r[h] ?? ''))];
      this.vars[varName] = arr;
      return arr;
    },

    // 抓取导出到 Excel
    async scrapeExport({ varName = '抓取列表', path = '' }) {
      const data = this.vars[varName];
      if (!data || !Array.isArray(data) || data.length === 0) {
        throw new Error('变量「' + varName + '」为空或不是数组');
      }
      // 确保是二维数组
      const rows = data.map(r => Array.isArray(r) ? r : Object.values(r));
      // 新建/复用 Excel
      await this.excelNewInMemory('抓取结果');
      const ws = this.getWS();
      rows.forEach((row, ri) => {
        row.forEach((val, ci) => {
          this.setCellValue(ri, ci, val);
        });
      });
      this.refreshRef();
      // 保存
      if (!path) {
        const desktop = await window.yingdao.getDesktopPath();
        path = desktop + '\\抓取结果_' + this.timestamp() + '.xlsx';
      }
      await this.excelSaveTo(path);
      return path;
    },

    // 坐标点击（独立指令）
    // 解析坐标点列表：支持 "100,200" / "100,200; 300,400" / "100 200" / 换行分隔
    parsePoints(text) {
      const raw = String(text == null ? '' : text).trim();
      if (!raw) return [];
      return raw.split(/[;；\n\r]+/).map(s => s.trim()).filter(Boolean).map(seg => {
        const m = /^(-?\d+(?:\.\d+)?)\s*[,，\s]\s*(-?\d+(?:\.\d+)?)$/.exec(seg);
        if (!m) throw new Error(`坐标「${seg}」看不懂。正确写法：100,200；多个点用分号隔开，如 100,200; 300,400（最多 9 个点）`);
        return { x: Math.round(Number(m[1])), y: Math.round(Number(m[2])) };
      });
    },

    // 坐标点击：支持多点，每点之间按「间隔(秒)」等待（默认 1 秒），最多 9 个点
    async clickXY({ points, x, y, interval = 1, clickType = '单击' }) {
      let list = this.parsePoints(points);
      // 兼容老流程：只填了 x / y
      if (!list.length && x !== undefined && x !== '' && y !== undefined && y !== '') {
        list = [{ x: Math.round(Number(x)), y: Math.round(Number(y)) }];
      }
      if (!list.length) throw new Error('请填写点击坐标（可点「🎯 在浏览器里点选坐标」自动填入）');
      if (list.length > 9) list = list.slice(0, 9);
      const gap = Math.max(0, Number(interval) || 0);
      const evt = clickType === '双击' ? 'dblclick' : (clickType === '右键' ? 'contextmenu' : 'click');
      const btn = clickType === '右键' ? '2' : '0';
      const done = [];
      for (let i = 0; i < list.length; i++) {
        if (this.cancelRequested) throw new Error(ERR_STOP);
        const pt = list[i];
        const code = `(() => {
          // 深层取元素：坐标落在同源 iframe 上时，继续钻进 iframe 里找真正的元素
          let x = ${pt.x}, y = ${pt.y}, guard = 0;
          let el = document.elementFromPoint(x, y);
          while (el && (el.tagName === 'IFRAME' || el.tagName === 'FRAME') && guard++ < 10) {
            try {
              const r = el.getBoundingClientRect();
              const d = el.contentDocument;
              if (!d) break;
              const inner = d.elementFromPoint(x - r.left, y - r.top);
              if (!inner) break;
              el = inner; x = x - r.left; y = y - r.top;
            } catch (e) { break; }
          }
          if (!el) throw new Error('坐标 (${pt.x}, ${pt.y}) 上没找到元素');
          const W = (el.ownerDocument && el.ownerDocument.defaultView) || window;
          const mk = (t) => new W.MouseEvent(t, { bubbles: true, cancelable: true, view: W, clientX: x, clientY: y, button: ${btn} });
          el.dispatchEvent(mk('mousedown'));
          el.dispatchEvent(mk('mouseup'));
          el.dispatchEvent(mk('${evt}'));
          return el.tagName + (el.innerText ? ':' + el.innerText.slice(0, 16) : '');
        })()`;
        const on = await this.execJSAny(code);
        done.push(`${i + 1}(${pt.x},${pt.y})→${on}`);
        if (i < list.length - 1 && gap > 0) await this.sleepInterruptible(gap);   // 多点之间的间隔
      }
      return done.join(' | ');
    },

    // 浏览器内按键（回车 / Tab / ESC / 空格 / 退格 / 方向键 / 自定义）
    // 优先用主进程的 sendInputEvent 发"真实按键"——这样原生表单提交、只监听 keydown 的框架都能生效；
    // 失败再退回页面内合成 KeyboardEvent。
    // 按键规格表：名称 -> { key, code, keyCode }；带 Ctrl 的组合键见 KEY_COMBO
    keySpecMap() {
      return {
        '回车(Enter)': { key: 'Enter', code: 'Enter', keyCode: 13 },
        'Tab': { key: 'Tab', code: 'Tab', keyCode: 9 },
        'ESC(Esc)': { key: 'Escape', code: 'Escape', keyCode: 27 },
        '空格(Space)': { key: ' ', code: 'Space', keyCode: 32 },
        '退格(Backspace)': { key: 'Backspace', code: 'Backspace', keyCode: 8 },
        '删除(Delete)': { key: 'Delete', code: 'Delete', keyCode: 46 },
        '方向键↑': { key: 'ArrowUp', code: 'ArrowUp', keyCode: 38 },
        '方向键↓': { key: 'ArrowDown', code: 'ArrowDown', keyCode: 40 },
        '方向键←': { key: 'ArrowLeft', code: 'ArrowLeft', keyCode: 37 },
        '方向键→': { key: 'ArrowRight', code: 'ArrowRight', keyCode: 39 },
        'F5(刷新页面)': { key: 'F5', code: 'F5', keyCode: 116 }
      };
    },

    // 带修饰键的组合：名称 -> { key, modifiers:['control'...] }
    keyComboMap() {
      return {
        'Ctrl+A(全选)': { key: 'a', modifiers: ['control'] },
        'Ctrl+C(复制)': { key: 'c', modifiers: ['control'] },
        'Ctrl+V(粘贴)': { key: 'v', modifiers: ['control'] },
        'Ctrl+X(剪切)': { key: 'x', modifiers: ['control'] },
        'Ctrl+Z(撤销)': { key: 'z', modifiers: ['control'] },
        'Ctrl+F(查找)': { key: 'f', modifiers: ['control'] },
        'Ctrl+S(保存)': { key: 's', modifiers: ['control'] }
      };
    },

    // 把"按键名 / Ctrl+X / 自定义"统一解析成 {key, code, keyCode, modifiers}
    parseKeySpec(name, customKey) {
      const custom = String(customKey || '').trim();
      const spec = this.keySpecMap();
      const combo = this.keyComboMap();
      if (combo[name]) {
        const c = combo[name];
        const up = c.key.toUpperCase();
        return { key: c.key, code: 'Key' + up, keyCode: up.charCodeAt(0), modifiers: c.modifiers };
      }
      if (spec[name]) return Object.assign({ modifiers: [] }, spec[name]);
      // 允许手写 "Ctrl+Shift+A" 这种
      const raw = custom || name;
      if (raw && raw.indexOf('+') >= 0) {
        const parts = raw.split('+').map(s => s.trim()).filter(Boolean);
        const base = parts.pop();
        const mods = [];
        parts.forEach(p => {
          const low = p.toLowerCase();
          if (low.indexOf('ctrl') >= 0) mods.push('control');
          else if (low.indexOf('shift') >= 0) mods.push('shift');
          else if (low.indexOf('alt') >= 0) mods.push('alt');
          else if (low.indexOf('cmd') >= 0 || low.indexOf('meta') >= 0 || low.indexOf('win') >= 0) mods.push('meta');
        });
        const isSingle = base.length === 1;
        return {
          key: base,
          code: isSingle ? 'Key' + base.toUpperCase() : base,
          keyCode: isSingle ? base.toUpperCase().charCodeAt(0) : 0,
          modifiers: mods
        };
      }
      return { key: raw, code: raw, keyCode: 0, modifiers: [] };
    },

    async pressKey({ key = '回车(Enter)', customKey = '', times = 1 }) {
      const spec = this.parseKeySpec(key, customKey);
      const n = Math.max(1, Math.min(20, Number(times) || 1));
      const mods = spec.modifiers || [];

      // 主路径：真实按键（带修饰键时不补 char —— Ctrl+A 不该往输入框里插个 'a'）
      try {
        return await B().sendKey(spec.key, n, mods);
      } catch (e) {
        // 退路：页面内合成事件（老版本/接口缺失时）
        const code = `(async () => {
          const el = document.activeElement || document.body;
          const spec = ${JSON.stringify(spec)};
          for (let i = 0; i < ${n}; i++) {
            const opts = {
              key: spec.key, code: spec.code, keyCode: spec.keyCode, which: spec.keyCode,
              ctrlKey: (spec.modifiers || []).indexOf('control') >= 0,
              shiftKey: (spec.modifiers || []).indexOf('shift') >= 0,
              altKey: (spec.modifiers || []).indexOf('alt') >= 0,
              metaKey: (spec.modifiers || []).indexOf('meta') >= 0,
              bubbles: true, cancelable: true, composed: true
            };
            const ev = new KeyboardEvent('keydown', opts);
            const notPrevented = el.dispatchEvent(ev);
            el.dispatchEvent(new KeyboardEvent('keypress', opts));
            el.dispatchEvent(new KeyboardEvent('keyup', opts));
            // 合成事件触发不了浏览器的"回车提交表单"默认行为，这里补一刀；
            // 但如果页面自己已处理（调了 preventDefault），就不补，避免重复提交
            if (spec.keyCode === 13 && !opts.ctrlKey && notPrevented && el.tagName === 'INPUT' && el.form && typeof el.form.requestSubmit === 'function') {
              try { el.form.requestSubmit(); } catch (err) { }
            }
            await new Promise(r => setTimeout(r, 60));
          }
          return spec.key + ' x' + ${n};
        })()`;
        return await this.execJSAny(code);
      }
    },

    // 点击元素 -> 全选(Ctrl+A) -> 复制(Ctrl+C)
    // 常用于"点进某个只读框/表格区域，把它里面的内容整段拿走"
    async clickSelectAllCopy({ selector, anchor = '', anchorRel = '下方', clickType = '单击', by = '智能匹配' }) {
      await this.click({ selector, by, anchor, anchorRel, clickType });
      await this.sleepInterruptible(0.2);                 // 等焦点落定，不然全选可能选到别处
      await this.pressKey({ key: 'Ctrl+A(全选)' });
      await this.sleepInterruptible(0.15);
      await this.pressKey({ key: 'Ctrl+C(复制)' });
      return '已点击 → 全选 → 复制';
    },

    // 点击目标位置 -> 粘贴(Ctrl+V)
    // 目标可以是元素（按定位方式找），也可以直接给坐标（定位方式选「坐标定位」，如 100,200）
    async clickPaste({ selector, anchor = '', anchorRel = '下方', clickType = '单击', by = '智能匹配' }) {
      await this.click({ selector, by, anchor, anchorRel, clickType });
      await this.sleepInterruptible(0.2);
      await this.pressKey({ key: 'Ctrl+V(粘贴)' });
      return '已点击 → 粘贴';
    },

    // ---- 剪贴板三件套：复制到剪贴板 / 粘贴到单元格 / 粘贴到网页元素 ----
    // 复制到剪贴板：来源可以是 文本(变量)、网页里选中的内容、元素里的文本
    async clipboardCopy({ from = '文本(下面填的内容)', content = '', selector = '', by = '智能匹配' }) {
      let text = '';
      if (from === '网页里选中的内容') {
        text = await this.execJSAny('(function(){ var s = window.getSelection(); return s ? s.toString() : ""; })()');
        if (!text) {
          // 输入框/只读框里没有 DOM 选区，改看活动元素的选中区间
          text = await this.execJSAny(`(function(){
            var el = document.activeElement;
            if (!el) return '';
            if (typeof el.selectionStart === 'number') return String(el.value || '').slice(el.selectionStart, el.selectionEnd);
            return '';
          })()`);
        }
      } else if (from === '元素里的文本') {
        selector = this.expand(selector);
        if (!selector) throw new Error('来源选的是「元素里的文本」，请在下面填要提取哪个元素');
        text = await this.scrapeText({ selector, by, all: '单个', varName: '__剪贴板临时' });
      } else {
        text = this.expand(content);
      }
      text = String(text == null ? '' : text);
      if (!text) throw new Error('没取到可复制的内容（来源：' + from + '）。检查一下是不是选区为空/元素没找到');
      await window.yingdao.clipboardWrite(text);
      return { length: text.length, preview: text.slice(0, 60) };
    },

    // 读取（或新建）一个表格文件：不要求先在编辑器里打开
    async readOrCreateWorkbook(filePath, sheetName, fallbackName) {
      let book, p = filePath, name = sheetName;
      if (p && await window.yingdao.fileExists(p)) {
        try { book = XLSX.read(await window.yingdao.readFile(p), { type: 'array' }); }
        catch (e) { throw new Error('表格打不开（文件损坏或被其它程序占用）：' + p); }
        // 指定了工作表名：存在就用它，不存在就追加这个新表（不能静默降级到第一个表）
        if (name) {
          if (!book.Sheets[name]) XLSX.utils.book_append_sheet(book, XLSX.utils.aoa_to_sheet([]), name);
        } else {
          name = book.SheetNames[0];
        }
      } else {
        if (!p) {
          let dir = '';
          try { dir = await window.yingdao.getDesktopPath(); } catch (e) { dir = ''; }
          if (!dir) dir = 'C:\\Users\\Public\\Desktop';
          p = dir + '\\' + (fallbackName || '新建表格') + '_' + this.timestamp() + '.xlsx';
        }
        book = XLSX.utils.book_new();
        name = name || 'Sheet1';
        XLSX.utils.book_append_sheet(book, XLSX.utils.aoa_to_sheet([]), name);
      }
      const ws = book.Sheets[name];
      if (!ws) throw new Error('表格里没有工作表：' + name);
      return { book: book, path: p, sheetName: name, ws: ws };
    },

    // 保存表格；saveMode='另存为' 时按"原名字-1/-2…"递增，不覆盖原文件
    async saveWorkbook(book, filePath, saveMode) {
      let out = filePath;
      if (saveMode === '另存为') {
        const dir = filePath.replace(/[\\/][^\\/]*$/, '');
        const base = filePath.split(/[\\/]/).pop() || '表格.xlsx';
        const m = /^(.*?)(\.[^.]+)?$/.exec(base) || [];
        const stem = (m[1] || '表格').replace(/[-_ ](\d{1,3})$/, '');
        const ext = m[2] || '.xlsx';
        const exists = async (q) => { try { return await window.yingdao.fileExists(q); } catch (e) { return false; } };
        out = '';
        for (let n = 1; n <= 1000; n++) {
          const cand = dir + '\\' + stem + '-' + n + ext;
          if (!(await exists(cand))) { out = cand; break; }
        }
        if (!out) throw new Error('另存为找不到可用的文件名（1000 个都重名了）');
      }
      const buf = XLSX.write(book, { bookType: 'xlsx', type: 'array' });
      await window.yingdao.writeFile(out, (buf instanceof Uint8Array) ? buf : new Uint8Array(buf));
      return out;
    },

    // 粘贴到单元格：把剪贴板内容写进表格指定位置（从 Excel/WPS 复制来的多行多列会按矩阵铺开）
    async pasteToCell({ toPath = '', toSheet = '', toCell = 'A1', save = '保存' }) {
      if (typeof XLSX === 'undefined') throw new Error('Excel 组件未加载');
      const text = await window.yingdao.clipboardRead();
      if (!text) throw new Error('剪贴板是空的（先用「复制到剪贴板」或手动 Ctrl+C 复制点东西）');

      // 按行拆、行内按制表符拆 —— 这正是从 Excel/WPS 复制出来的格式
      const rows = String(text).replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
      while (rows.length && rows[rows.length - 1] === '') rows.pop();
      const matrix = rows.map(r => r.split('\t'));

      const rec = await this.readOrCreateWorkbook(this.expand(toPath), this.expand(toSheet), '粘贴结果');
      const startText = String(this.expand(toCell) || 'A1').trim() || 'A1';
      let start;
      try { start = this.parseCell(startText); }
      catch (e) { throw new Error('「' + startText + '」不是有效的起始单元格，正确示例：A1、B2'); }

      matrix.forEach((row, ri) => {
        row.forEach((v, ci) => {
          rec.ws[this.colName(start.c + ci) + (start.r + ri + 1)] = this.makeCell(v);
        });
      });
      const sc = this.scanCells(rec.ws);
      rec.ws['!ref'] = (sc.maxR >= 0 && sc.maxC >= 0) ? ('A1:' + this.colName(sc.maxC) + (sc.maxR + 1)) : 'A1:A1';
      this.recalcFormulas({ book: rec.book, activeSheet: rec.sheetName });

      const saveMode = this.expand(save);
      const out = await this.saveWorkbook(rec.book, rec.path, saveMode);
      const cols = matrix.reduce((m, r) => Math.max(m, r.length), 0);
      return {
        path: out, rows: matrix.length, cols: cols,
        msg: '已把剪贴板内容（' + matrix.length + ' 行 × ' + cols + ' 列）粘贴到「' + rec.sheetName + '」' + startText +
             ' 起，' + (saveMode === '另存为' ? '另存为 ' : '保存到 ') + out
      };
    },

    // 粘贴到网页元素内：先聚焦元素（并选中原有内容），再按选定方式把剪贴板内容放进去
    async pasteToElement({ selector, by = '智能匹配', anchor = '', anchorRel = '下方', mode = '真实粘贴(Ctrl+V)' }) {
      selector = this.expand(selector);
      if (!selector) throw new Error('请填写要粘贴到哪个元素（可点「🎯 在浏览器中选取元素」）');
      anchor = this.expand(anchor);
      await this.locate(selector, by, anchor, anchorRel);
      const esc = selector.replace(/'/g, "\\'");
      const escA = (anchor || '').replace(/'/g, "\\'");
      const snip = this.locatorSnippet(by, esc, escA, anchorRel);

      await this.execJSAny(`(function(){
        var el = ${snip};
        if (!el) throw new Error('元素未找到');
        el.scrollIntoView({block:'center'});
        if (el.focus) el.focus();
        if (typeof el.selectionStart === 'number' && el.select) { try { el.select(); } catch (e) { } }
        return true;
      })()`);

      if (mode === '直接把内容写进去') {
        const text = await window.yingdao.clipboardRead();
        const escT = String(text == null ? '' : text)
          .replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\r?\n/g, '\\n');
        await this.execJSAny(`(function(){
          var el = ${snip};
          if (!el) throw new Error('元素未找到');
          if (el.isContentEditable) { el.innerText = '${escT}'; }
          else if ('value' in el) {
            var setter = el.tagName === 'TEXTAREA'
              ? Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')
              : Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
            if (setter && setter.set) setter.set.call(el, '${escT}'); else el.value = '${escT}';
          } else { el.innerText = '${escT}'; }
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        })()`);
        return '已把剪贴板内容直接写进元素';
      }

      await this.sleepInterruptible(0.15);
      await this.pressKey({ key: 'Ctrl+V(粘贴)' });
      return '已粘贴到元素';
    },

    // ---- 提取网页文本 → 过滤 → 写进表格 ----
    // 过滤规则（按用户的原话）：
    //   纯数字(只留整数)          → 只留整数（允许千分位逗号和正负号）
    //   纯文本(不含数字)          → 只留不含数字的文字
    //   文本与数字(全都留下)      → 不过滤，只去首尾空白
    //   带小数点的数字(如 12.5)   → 留小数；若带单位（45.6元）也把数字抠出来
    //   自定义截取(如 2-3)        → 取第 2~3 个字符（也可只填一个数字 n = 取第 n 个）
    filterExtracted(text, mode) {
      const s = String(text == null ? '' : text).trim();
      if (!s) return '';
      if (!mode || mode === '文本与数字') return s;

      // 自定义截取：支持 "2-3"（第2到第3个）、"2"（第2个）、"2-"（第2个到最后）
      if (/^\d+(-\d*)?$/.test(mode)) {
        const m = /^(\d+)(?:-(\d*))?$/.exec(mode);
        const a = parseInt(m[1], 10);
        const b = m[2] === undefined ? a : (m[2] === '' ? s.length : parseInt(m[2], 10));
        const chars = Array.from(s);                      // 按"字符"切（中文占一位），不是按字节
        const start = Math.max(1, a) - 1;
        const end = Math.min(chars.length, b);
        if (start >= chars.length) return '';
        return chars.slice(start, end).join('');
      }

      const plain = s.replace(/[,\s，]/g, '');            // 去掉千分位逗号与空白
      if (mode === '纯数字') return /^[+-]?\d+$/.test(plain) ? plain : '';
      if (mode === '带小数点的数字') {
        // 先整段是纯小数；否则从文本里抠"第一个数字（可带小数点/负号/千分位）"
        if (/^[+-]?\d*\.\d+$/.test(plain)) { const n = Number(plain); return isNaN(n) ? '' : String(n); }
        const m = /[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?/.exec(s);
        if (!m) return '';
        const n = Number(m[0].replace(/,/g, ''));
        return isNaN(n) ? '' : String(n);
      }
      if (mode === '纯文本') return /\d/.test(s) ? '' : s;
      return s;
    },

    // 提取网页元素里的文本 → 按规则过滤 → 写进指定表格 → 保存（或另存为 +1 递增）
    async extractTextToTable({ selector, anchor = '', anchorRel = '下方', by = '智能匹配',
                               all = '全部匹配', filter = '文本与数字',
                               toPath = '', toSheet = '', toCell = 'A1', save = '保存' }) {
      if (typeof XLSX === 'undefined') throw new Error('Excel 组件未加载');
      selector = this.expand(selector);
      if (!selector) throw new Error('请填写要提取的元素定位（可以点「🎯 在浏览器中选取元素」）');

      // 1) 抓文本（复用抓取文本那套稳健查找：同源 iframe / 影子 DOM / 多策略回退）
      const raw = await this.scrapeText({ selector, by, all, varName: '__提取临时' });
      const list = Array.isArray(raw) ? raw : [raw];

      // 2) 按规则过滤
      const values = list.map(v => this.filterExtracted(v, filter)).filter(v => v !== '');
      if (!values.length) {
        throw new Error('提取到 ' + list.length + ' 条，但按「' + filter + '」过滤后一条都不剩（可把过滤改成「文本与数字」看看原始内容）');
      }

      // 3) 目标表格：按文件路径读写，不要求先在编辑器里打开；留空就新建到桌面
      const toPathIn = this.expand(toPath);
      let dstBook, dstPath, dstSheetName;
      if (toPathIn) {
        dstPath = toPathIn;
        if (await window.yingdao.fileExists(dstPath)) {
          try { dstBook = XLSX.read(await window.yingdao.readFile(dstPath), { type: 'array' }); }
          catch (e) { throw new Error('目标表格打不开（文件损坏或被其它程序占用）：' + dstPath); }
          // 指定了工作表名但文件里没有 → 追加这个新表；没指定才用第一个表
          if (toSheet) {
            if (dstBook.Sheets[toSheet]) dstSheetName = toSheet;
            else { dstSheetName = toSheet; XLSX.utils.book_append_sheet(dstBook, XLSX.utils.aoa_to_sheet([]), toSheet); }
          } else {
            dstSheetName = dstBook.SheetNames[0];
          }
        } else {
          dstBook = XLSX.utils.book_new();
          dstSheetName = toSheet || 'Sheet1';
          XLSX.utils.book_append_sheet(dstBook, XLSX.utils.aoa_to_sheet([]), dstSheetName);
        }
      } else {
        let desktop = '';
        try { desktop = await window.yingdao.getDesktopPath(); } catch (e) { desktop = ''; }
        if (!desktop) desktop = 'C:\\Users\\Public\\Desktop';
        dstPath = desktop + '\\提取结果_' + this.timestamp() + '.xlsx';
        dstBook = XLSX.utils.book_new();
        dstSheetName = toSheet || 'Sheet1';
        XLSX.utils.book_append_sheet(dstBook, XLSX.utils.aoa_to_sheet([]), dstSheetName);
      }
      const dstWs = dstBook.Sheets[dstSheetName];
      if (!dstWs) throw new Error('目标表格里没有工作表：' + dstSheetName);

      const startText = String(this.expand(toCell) || 'A1').trim() || 'A1';
      let start;
      try { start = this.parseCell(startText); }
      catch (e) { throw new Error('「' + startText + '」不是有效的起始单元格，正确示例：A1、B2'); }

      // 4) 一条一格，从起始单元格往下竖着写
      values.forEach((v, i) => {
        dstWs[this.colName(start.c) + (start.r + i + 1)] = this.makeCell(v);
      });
      const sc = this.scanCells(dstWs);
      dstWs['!ref'] = (sc.maxR >= 0 && sc.maxC >= 0) ? ('A1:' + this.colName(sc.maxC) + (sc.maxR + 1)) : 'A1:A1';
      this.recalcFormulas({ book: dstBook, activeSheet: dstSheetName });

      // 5) 保存 or 另存为（另存为 = 原名字后 +1 递增，不覆盖原表）
      let outPath = dstPath;
      if (save === '另存为') {
        const dir = dstPath.replace(/[\\/][^\\/]*$/, '');
        const base = dstPath.split(/[\\/]/).pop() || '表格.xlsx';
        const m = /^(.*?)(\.[^.]+)?$/.exec(base) || [];
        const stem = (m[1] || '表格').replace(/[-_ ](\d{1,3})$/, '');
        const ext = m[2] || '.xlsx';
        const exists = async (p) => { try { return await window.yingdao.fileExists(p); } catch (e) { return false; } };
        outPath = '';
        for (let n = 1; n <= 1000; n++) {
          const cand = dir + '\\' + stem + '-' + n + ext;
          if (!(await exists(cand))) { outPath = cand; break; }
        }
        if (!outPath) throw new Error('另存为找不到可用的文件名（1000 个都重名了）');
      }
      const out = XLSX.write(dstBook, { bookType: 'xlsx', type: 'array' });
      await window.yingdao.writeFile(outPath, (out instanceof Uint8Array) ? out : new Uint8Array(out));

      return {
        path: outPath,
        count: values.length,
        filtered: list.length - values.length,
        msg: '提取到 ' + values.length + ' 条（按「' + filter + '」过滤掉 ' + (list.length - values.length) + ' 条）→ ' +
             '写入「' + dstSheetName + '」' + startText + ' 起，' + (save === '另存为' ? '另存为 ' : '保存到 ') + outPath
      };
    },

    async screenshot({ selector = '', path = 'screenshot.png' }) {
      // 通过主进程截图（后续可扩展为真正保存 PNG）
      return { ok: true, note: '截图功能开发中' };
    },

    // ---- 鼠标键盘 ----
    // 鼠标点击（电脑录制回放）：在指定坐标派发鼠标事件
    async mouseClick({ x, y, button = '左键', clickType = '单击' }) {
      const ix = Number(x), iy = Number(y);
      const btn = button === '右键' ? 2 : (button === '中键' ? 1 : 0);
      const evt = clickType === '双击' ? 'dblclick' : (button === '右键' ? 'contextmenu' : 'click');
      const code = `(() => {
        const e1 = new MouseEvent('mousedown', {bubbles:true, clientX:${ix}, clientY:${iy}, button:${btn}});
        const e2 = new MouseEvent('mouseup',   {bubbles:true, clientX:${ix}, clientY:${iy}, button:${btn}});
        const e3 = new MouseEvent('${evt}',    {bubbles:true, clientX:${ix}, clientY:${iy}, button:${btn}});
        const el = document.elementFromPoint(${ix}, ${iy}) || document.body;
        el.dispatchEvent(e1); el.dispatchEvent(e2); el.dispatchEvent(e3);
        return '点击 @ (' + ${ix} + ',' + ${iy} + ')';
      })()`;
      return await this.execJSAny(code);
    },
    async typeText({ text }) {
      text = this.expand(text);
      const esc = text.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
      // 跨框架执行：这一层没有聚焦的输入框时返回空串，让执行器继续往下找 iframe 里的输入框
      await this.execJSAny(`(() => {
        const el = document.activeElement;
        const txt = '${esc}';
        if (!el || el === document.body || el === document.documentElement || !('value' in el)) return '';
        for (const ch of txt) el.dispatchEvent(new KeyboardEvent('keydown', { key: ch, bubbles: true }));
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value') ||
                       Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
        if (setter && setter.set) setter.set.call(el, txt);
        else el.value = txt;
        el.dispatchEvent(new Event('input', {bubbles:true}));
        return txt;
      })()`);
    },

    async hotkey({ keys }) {
      // 简单实现：解析为组合键后 dispatch
      keys = this.expand(keys);
      await this.execJSAny(`(() => {
        const parts = '${keys}'.split('+').map(s => s.trim());
        const key = parts.pop().toLowerCase();
        const mods = {};
        for (const p of parts) {
          const low = p.toLowerCase();
          if (low.includes('ctrl')) mods.ctrlKey = true;
          if (low.includes('shift')) mods.shiftKey = true;
          if (low.includes('alt')) mods.altKey = true;
          if (low.includes('meta')) mods.metaKey = true;
        }
        const el = document.activeElement || document.body;
        const ev = { key: key, ...mods, bubbles: true, cancelable: true };
        el.dispatchEvent(new KeyboardEvent('keydown', ev));
        el.dispatchEvent(new KeyboardEvent('keyup', ev));
        return key;
      })()`);
    },

    // ---- Excel 工具函数 ----
    // 解析单元格地址 "A1" -> { r: 0, c: 0 }（0 基）
    parseCell(addr) {
      const m = /^([A-Za-z]+)(\d+)$/.exec(addr.trim());
      if (!m) throw new Error('无效单元格地址: ' + addr);
      let col = 0;
      for (const ch of m[1].toUpperCase()) col = col * 26 + (ch.charCodeAt(0) - 64);
      return { c: col - 1, r: parseInt(m[2], 10) - 1 };
    },
    // 列号 -> 列名 (0 -> A)
    colName(c) {
      let s = '';
      c += 1;
      while (c > 0) { const m = (c - 1) % 26; s = String.fromCharCode(65 + m) + s; c = Math.floor((c - 1) / 26); }
      return s;
    },
    // 区域 "A1:C5" -> { r0, c0, r1, c1 }
    parseRange(range) {
      const parts = range.split(':');
      const a = this.parseCell(parts[0]);
      const b = parts[1] ? this.parseCell(parts[1]) : a;
      return { r0: Math.min(a.r, b.r), c0: Math.min(a.c, b.c), r1: Math.max(a.r, b.r), c1: Math.max(a.c, b.c) };
    },

    // ---- 单元格扫描 / 类型识别 / 公式引用平移（内部工具）----
    // 扫描工作表内所有单元格，返回最大行列（不依赖 !ref，!ref 可能缺失或过期）
    scanCells(ws) {
      let maxR = -1, maxC = -1;
      const list = [];
      Object.keys(ws).forEach(key => {
        if (key[0] === '!') return;         // 跳过 !ref / !cols 等元数据
        let pos;
        try { pos = this.parseCell(key); } catch (e) { return; }
        if (pos.r > maxR) maxR = pos.r;
        if (pos.c > maxC) maxC = pos.c;
        list.push({ r: pos.r, c: pos.c, addr: key, cell: ws[key] });
      });
      return { maxR, maxC, list };
    },

    // 值 → 单元格对象：数字自动识别为数值型（对齐 Excel/WPS 的输入行为）
    // "=" 开头视为公式：写入 f（公式文本）并由 recalcFormulas 立即算出 v
    // 以下情况保留文本，避免"变味"：前导零（001、电话号码）、超过 15 位的长数字（身份证/订单号）
    makeCell(v) {
      const s = String(v == null ? '' : v);
      const t = s.trim();
      if (window.FormulaEngine && window.FormulaEngine.isFormula(t)) {
        return { t: 's', f: t.replace(/^=/, ''), v: '' };   // v 由公式引擎算
      }
      const numLike = /^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/.test(t);
      const leadingZero = /^[+-]?0\d/.test(t);
      const tooLong = /^[+-]?\d{16,}$/.test(t);
      if (numLike && !leadingZero && !tooLong) return { t: 'n', v: Number(t) };
      return { t: 's', v: s };
    },

    // ---- 公式自动计算（对齐 WPS：输入即出结果，依赖变化自动重算）----
    // 构造求值环境：单元格取值 + 区域矩阵，带记忆化与循环引用检测
    _formulaEnv(rec, ws, sheetName, cache, visiting) {
      const self = this;
      function evalCell(sn, addr) {
        const key = sn + '!' + addr;
        if (cache.has(key)) return cache.get(key);
        const sheet = rec.book.Sheets[sn] || ws;
        const cell = sheet && sheet[addr];
        if (!cell || !cell.f) return cell ? (cell.v == null ? '' : cell.v) : '';
        if (visiting.has(key)) return '#CIRC!';
        visiting.add(key);
        let val = '#ERROR!';
        try {
          val = window.FormulaEngine.evaluate(cell.f, self._formulaEnv(rec, sheet, sn, cache, visiting));
        } catch (e) {
          if (e && e.unsupported) {
            // 不支持的函数：保留文件里原有的缓存值，避免把真实文件算坏
            val = (cell.v === undefined || cell.v === null || cell.v === '') ? '#NAME?' : cell.v;
          } else if (e && e.formulaError) {
            val = e.code;              // #CIRC! / #DIV/0! 等错误码原样透出（与 Excel 一致）
          } else {
            val = '#ERROR!';
          }
        }
        visiting.delete(key);
        cache.set(key, val);
        return val;
      }
      const env = {
        sheetName: sheetName,
        rowIndex: 0,
        colIndex: 0,
        cellValue: (sn, r, c) => evalCell(sn || sheetName, self.colName(c) + (r + 1)),
        rangeMatrix: (sn, r0, c0, r1, c1) => {
          const matrix = [];
          for (let r = r0; r <= r1; r++) {
            const row = [];
            for (let c = c0; c <= c1; c++) row.push(evalCell(sn || sheetName, self.colName(c) + (r + 1)));
            matrix.push(row);
          }
          return matrix;
        },
        evalCell: evalCell
      };
      return env;
    },

    // 重算指定 workbook 的全部公式，返回重算的公式个数
    recalcFormulas(rec) {
      if (!window.FormulaEngine) return 0;
      if (!rec) rec = this.getActiveBook();
      if (!rec || !rec.book) return 0;
      const jobs = [];
      rec.book.SheetNames.forEach(sn => {
        const ws = rec.book.Sheets[sn];
        if (!ws) return;
        Object.keys(ws).forEach(key => {
          if (key[0] === '!') return;
          const cell = ws[key];
          if (cell && cell.f) jobs.push({ sn, key, cell, ws });
        });
      });
      if (!jobs.length) return 0;
      const cache = new Map();
      const visiting = new Set();
      const self = this;
      jobs.forEach(job => {
        const pos = self.parseCell(job.key);
        const env = self._formulaEnv(rec, job.ws, job.sn, cache, visiting);
        env.rowIndex = pos.r; env.colIndex = pos.c;
        let val;
        try {
          val = window.FormulaEngine.evaluate(job.cell.f, env);
        } catch (e) {
          if (e && e.unsupported) {
            // 不支持的函数：文件里已有缓存值就保留（别把真实文件算坏）；
            // 用户刚输入、还没有缓存值的 → 明确显示 #NAME?
            const prev = job.cell.v;
            if (prev === undefined || prev === null || prev === '') { job.cell.v = '#NAME?'; job.cell.t = 's'; }
            return;
          }
          val = (e && e.code) ? e.code : '#ERROR!';
        }
        job.cell.v = val;
        if (typeof val === 'number') job.cell.t = 'n';
        else if (typeof val === 'boolean') job.cell.t = 'b';
        else job.cell.t = 's';
        delete job.cell.w;                     // 清掉 SheetJS 的格式化缓存
      });
      return jobs.length;
    },

    // 导出公式单元格（多窗口同步用，避免公式在快照往返中丢失）
    exportCells() {
      const rec = this.getActiveBook();
      if (!rec) return null;
      const sn = rec.activeSheet || rec.book.SheetNames[0];
      const ws = rec.book.Sheets[sn];
      if (!ws) return null;
      const out = {};
      Object.keys(ws).forEach(key => {
        if (key[0] === '!') return;
        const cell = ws[key];
        if (cell && cell.f) out[key] = { f: cell.f, v: cell.v, t: cell.t };
      });
      return Object.keys(out).length ? out : null;
    },

    // 单元格"编辑/显示用"文本：公式单元格返回 =公式，其它返回值（对齐 WPS 编辑栏）
    cellText(addr) {
      try {
        const ws = this.getWS();
        const cell = ws[String(addr).toUpperCase()];
        if (cell && cell.f) return '=' + cell.f;
        return cell ? (cell.v == null ? '' : cell.v) : '';
      } catch (e) { return ''; }
    },

    // 引用 "A1" / "$A$1" -> { col, r, cAbs, rAbs }
    parseRef(s) {
      const m = /^(\$?)([A-Za-z]{1,3})(\$?)(\d+)$/.exec(String(s).trim());
      if (!m) return null;
      let col = 0;
      for (const ch of m[2].toUpperCase()) col = col * 26 + (ch.charCodeAt(0) - 64);
      return { cAbs: m[1] === '$', col: col - 1, rAbs: m[3] === '$', r: parseInt(m[4], 10) - 1 };
    },
    fmtRef(ref, axis, idx) {
      const col = axis === 'row' ? ref.col : idx;
      const row = axis === 'row' ? idx : ref.r;
      return (ref.cAbs ? '$' : '') + this.colName(col) + (ref.rAbs ? '$' : '') + (row + 1);
    },
    // 单个下标在「插入/删除」后的新位置；-1 表示该位置已被删除
    mapIndex(idx, at, count, mode) {
      if (mode === 'insert') return idx >= at ? idx + count : idx;
      if (idx >= at + count) return idx - count;
      if (idx >= at) return -1;
      return idx;
    },
    // 公式里的单元格引用随插入/删除平移（对齐 Excel/WPS，也是插入行后公式不错位的关键）
    shiftRefsInFormula(f, axis, at, count, mode) {
      if (!f) return f;
      // 分片：奇数下标是字符串字面量，原样保留，避免误改 "A1" 这类文本
      const parts = String(f).split(/("(?:[^"]|"")*")/);
      const RE = /(?<![A-Za-z0-9_$])(\$?[A-Za-z]{1,3}\$?\d+)(?::(\$?[A-Za-z]{1,3}\$?\d+))?(?![A-Za-z0-9_(])/g;
      for (let i = 0; i < parts.length; i += 2) {
        if (!parts[i]) continue;
        parts[i] = parts[i].replace(RE, (m, s1, s2) => {
          const a = this.parseRef(s1);
          const b = s2 ? this.parseRef(s2) : null;
          if (!a || (s2 && !b)) return m;
          let i1 = this.mapIndex(axis === 'row' ? a.r : a.col, at, count, mode);
          if (!b) return i1 < 0 ? '#REF!' : this.fmtRef(a, axis, i1);
          let i2 = this.mapIndex(axis === 'row' ? b.r : b.col, at, count, mode);
          if (mode === 'delete') {
            if (i1 < 0) i1 = at;          // 起点被删 → 区间起点收缩到删除处
            if (i2 < 0) i2 = at - 1;      // 终点被删 → 区间终点收缩到删除处之前
            if (i1 > i2) return '#REF!';  // 整个区间都被删除
          }
          return this.fmtRef(a, axis, i1) + ':' + this.fmtRef(b, axis, i2);
        });
      }
      return parts.join('');
    },
    // 全表公式引用平移（插入/删除行列后引用变了 → 顺带立即重算）
    shiftFormulas(ws, axis, at, count, mode) {
      Object.keys(ws).forEach(key => {
        if (key[0] === '!') return;
        const cell = ws[key];
        if (cell && cell.f) cell.f = this.shiftRefsInFormula(cell.f, axis, at, count, mode);
      });
      this.recalcFormulas(this.getActiveBook());
    },
    // 获取当前激活 workbook 的当前 sheet
    getWS() {
      if (!excelBook) throw new Error('请先打开或新建Excel');
      const book = this.getActiveBook();
      const sheetName = book.activeSheet || excelBook.SheetNames[0];
      return excelBook.Sheets[sheetName];
    },

    // 获取当前激活 workbook 记录
    getActiveBook() {
      const found = excelBooks.find(b => b.id === activeBookId);
      return found || null;
    },

    // 切换到指定 workbook
    switchBook(id) {
      const target = excelBooks.find(b => b.id === id);
      if (!target) return null;
      activeBookId = id;
      excelBook = target.book;
      excelPath = target.path;
      return target;
    },

    // 获取所有 workbook 信息
    getBooks() {
      return excelBooks.map(b => ({
        id: b.id,
        path: b.path,
        sheetNames: b.book.SheetNames,
        activeSheet: b.activeSheet || b.book.SheetNames[0]
      }));
    },

    // 获取当前 workbook 的所有 sheet 名
    getSheetNames() {
      if (!excelBook) return [];
      return excelBook.SheetNames.slice();
    },

    // 当前激活 sheet 名
    getActiveSheetName() {
      if (!excelBook) return '';
      const book = this.getActiveBook();
      return book && book.activeSheet ? book.activeSheet : (excelBook.SheetNames[0] || '');
    },

    // 切换 sheet
    switchSheet(sheetName) {
      if (!excelBook) throw new Error('请先打开或新建Excel');
      if (!excelBook.SheetNames.includes(sheetName)) throw new Error('工作表不存在: ' + sheetName);
      const book = this.getActiveBook();
      if (book) book.activeSheet = sheetName;
      return sheetName;
    },

    // 新增 sheet
    addSheet(sheetName) {
      if (!excelBook) throw new Error('请先打开或新建Excel');
      const ws = XLSX.utils.aoa_to_sheet([]);
      XLSX.utils.book_append_sheet(excelBook, ws, sheetName);
      const book = this.getActiveBook();
      if (book) book.activeSheet = sheetName;
      return sheetName;
    },

    // 删除 sheet
    removeSheet(sheetName) {
      if (!excelBook) throw new Error('请先打开或新建Excel');
      if (excelBook.SheetNames.length <= 1) throw new Error('至少保留一个工作表');
      const idx = excelBook.SheetNames.indexOf(sheetName);
      if (idx === -1) throw new Error('工作表不存在: ' + sheetName);
      delete excelBook.Sheets[sheetName];
      excelBook.SheetNames.splice(idx, 1);
      const book = this.getActiveBook();
      if (book && book.activeSheet === sheetName) book.activeSheet = excelBook.SheetNames[0];
      return excelBook.SheetNames[0];
    },

    // 写文件（通过 IPC 到主进程写盘）
    async writeFileArray(path, buf) {
      // 主进程写二进制
      await window.yingdao.writeFile(path, buf);
    },

    // 注册一个 workbook 为当前激活标签
    registerBook(book, path, activeSheet) {
      const id = 'e' + (bookIdSeq++);
      const rec = { id, book, path, activeSheet: activeSheet || (book.SheetNames[0] || 'Sheet1') };
      excelBooks.push(rec);
      activeBookId = id;
      excelBook = book;
      excelPath = path;
      return rec;
    },

    // 关闭 workbook 标签
    closeBook(id) {
      const idx = excelBooks.findIndex(b => b.id === id);
      if (idx === -1) return 0;
      excelBooks.splice(idx, 1);
      if (activeBookId === id) {
        if (excelBooks.length) {
          const last = excelBooks[excelBooks.length - 1];
          activeBookId = last.id;
          excelBook = last.book;
          excelPath = last.path;
        } else {
          activeBookId = null;
          excelBook = null;
          excelPath = null;
        }
      }
      return excelBooks.length;
    },

    async excelOpen(path) {
      if (typeof XLSX === 'undefined') throw new Error('Excel 组件未加载');
      path = this.expand(path);
      if (!path) throw new Error('请先选择要打开的Excel文件（打开Excel指令需填写文件路径）');
      const buf = await window.yingdao.readFile(path);
      const book = XLSX.read(buf, { type: 'array' });
      this.registerBook(book, path, book.SheetNames[0]);
    },

    async excelNew(path, sheetName = 'Sheet1') {
      if (typeof XLSX === 'undefined') throw new Error('Excel 组件未加载');
      path = this.expand(path);
      // 未指定路径时，默认保存到桌面文件夹下
      if (!path) {
        let desktop = '';
        try { desktop = await window.yingdao.getDesktopPath(); } catch (e) { desktop = ''; }
        if (!desktop) desktop = 'C:\\Users\\Public\\Desktop';
        const stamp = this.timestamp();
        path = `${desktop}\\新建Excel_${stamp}.xlsx`;
      }
      const book = XLSX.utils.book_new();
      const ws = XLSX.utils.aoa_to_sheet([]);
      XLSX.utils.book_append_sheet(book, ws, sheetName);
      this.registerBook(book, path, sheetName);
      await this.excelSaveTo(path);
    },

    // 仅内存新建（不写盘），供 Excel 编辑器用
    excelNewInMemory(sheetName = 'Sheet1') {
      if (typeof XLSX === 'undefined') throw new Error('Excel 组件未加载');
      const book = XLSX.utils.book_new();
      const ws = XLSX.utils.aoa_to_sheet([]);
      XLSX.utils.book_append_sheet(book, ws, sheetName);
      this.registerBook(book, null, sheetName);  // 尚未保存
    },

    // 从快照加载 Excel 数据（独立窗口回传时用，含公式单元格）
    loadSnapshot(snap) {
      if (typeof XLSX === 'undefined') throw new Error('Excel 组件未加载');
      if (!snap) return;
      const rows = snap.rows || [];
      const book = XLSX.utils.book_new();
      const ws = XLSX.utils.aoa_to_sheet(rows);
      XLSX.utils.book_append_sheet(book, ws, snap.sheetName || 'Sheet1');
      const rec = this.registerBook(book, snap.path || null, snap.sheetName || 'Sheet1');
      this.applyCellsTo(ws, snap.cells);
      this.recalcFormulas(rec);
      this.refreshRef();
    },

    excelRead(cell) {
      const ws = this.getWS();
      return ws[cell] ? ws[cell].v : '';
    },

    excelWrite(cell, value) {
      const ws = this.getWS();
      ws[cell] = this.makeCell(this.expand(value));
      this.recalcFormulas(this.getActiveBook());
      this.refreshRef();
    },

    // 读取区域 -> 二维数组
    excelReadRange(range) {
      const ws = this.getWS();
      const { r0, c0, r1, c1 } = this.parseRange(range);
      const result = [];
      for (let r = r0; r <= r1; r++) {
        const row = [];
        for (let c = c0; c <= c1; c++) {
          const addr = this.colName(c) + (r + 1);
          row.push(ws[addr] ? ws[addr].v : '');
        }
        result.push(row);
      }
      return result;
    },

    // 写入区域（二维数组）
    excelWriteRange(startCell, data) {
      const ws = this.getWS();
      const { r, c } = this.parseCell(startCell);
      if (!Array.isArray(data)) throw new Error('写入区域需要二维数组变量');
      data.forEach((row, ri) => {
        if (!Array.isArray(row)) { ws[this.colName(c) + (r + ri + 1)] = this.makeCell(row); return; }
        row.forEach((val, ci) => {
          ws[this.colName(c + ci) + (r + ri + 1)] = this.makeCell(val);
        });
      });
      this.recalcFormulas(this.getActiveBook());
      this.refreshRef();
    },

    // 复制粘贴：选择性粘贴（对齐 Excel 的"选择性粘贴"语义）
    excelCopyPaste(from, to, mode = '全部粘贴') {
      const ws = this.getWS();
      const src = this.parseRange(from);
      const dst = this.parseCell(to);
      // 目标区域大小等于源区域（选择性粘贴区域对齐）
      const dstR0 = dst.r;
      const dstC0 = dst.c;
      const srcR0 = src.r0;
      const srcC0 = src.c0;
      const dr = src.r1 - src.r0;
      const dc = src.c1 - src.c0;

      // 取目标区域已有值（用于"值与数字格式"、"公式与数字格式"等判断）
      const dstOld = {};
      for (let r = dstR0; r <= dstR0 + dr; r++) {
        for (let c = dstC0; c <= dstC0 + dc; c++) {
          dstOld[this.colName(c) + (r + 1)] = ws[this.colName(c) + (r + 1)];
        }
      }

      for (let r = srcR0; r <= src.r1; r++) {
        for (let c = srcC0; c <= src.c1; c++) {
          const srcAddr = this.colName(c) + (r + 1);
          const dstAddr = this.colName(dstC0 + (c - srcC0)) + (dstR0 + (r - srcR0) + 1);
          const cell = ws[srcAddr];
          const oldDst = dstOld[dstAddr];

          switch (mode) {
            case '只粘贴值':
              // 只取计算值
              ws[dstAddr] = this.makeCell(cell ? (cell.v ?? '') : '');
              break;
            case '只粘贴公式':
              // 只保留公式
              if (cell && cell.f) ws[dstAddr] = { t: 'n', f: cell.f, v: cell.v };
              else delete ws[dstAddr];
              break;
            case '只粘贴格式':
              // 仅复制样式（XLSX 用 s 属性表示样式）——SheetJS 部分支持
              if (cell && cell.s) {
                if (!ws[dstAddr]) ws[dstAddr] = { t: 's', v: '' };
                ws[dstAddr].s = cell.s;
              }
              break;
            case '保留公式':
              if (cell && cell.f) ws[dstAddr] = { t: 'n', f: cell.f, v: cell.v };
              else if (cell) ws[dstAddr] = this.makeCell(cell.v ?? '');
              else delete ws[dstAddr];
              break;
            case '值与数字格式':
              ws[dstAddr] = this.makeCell(cell ? (cell.v ?? '') : '');
              if (cell && cell.s) ws[dstAddr].s = cell.s;
              break;
            case '公式与数字格式':
              if (cell && cell.f) {
                ws[dstAddr] = { t: 'n', f: cell.f, v: cell.v };
                if (cell.s) ws[dstAddr].s = cell.s;
              }
              break;
            case '不覆盖原有内容':
              // 目标已有内容则跳过
              if (oldDst) continue;
              if (cell) ws[dstAddr] = this.makeCell(cell.v ?? '');
              break;
            case '全部粘贴':
            default:
              // 完整复制（含公式、样式、值）
              if (cell) {
                ws[dstAddr] = { ...cell };
              } else {
                delete ws[dstAddr];
              }
              break;
          }
        }
      }
    },

    // 按 id / 完整路径 / 文件名定位一个 workbook 记录（留空或"当前"返回激活项）
    findBook(ref) {
      const s = String(ref == null ? '' : ref).trim();
      if (s === '' || s === '当前' || s === '当前表格') return this.getActiveBook();
      const byId = excelBooks.find(b => b.id === s);
      if (byId) return byId;
      const byPath = excelBooks.find(b => b.path && b.path === s);
      if (byPath) return byPath;
      const byName = excelBooks.find(b => {
        if (!b.path) return false;
        const base = b.path.split(/[\\/]/).pop();
        return base === s || base.replace(/\.[^.]+$/, '') === s;
      });
      return byName || null;
    },

    // 定位指定 workbook 里的工作表（不存在时抛错）
    getSheetOf(rec, sheetName) {
      const rec2 = rec || this.getActiveBook();
      if (!rec2) throw new Error('请先打开或新建Excel');
      const name = sheetName || rec2.activeSheet || rec2.book.SheetNames[0];
      if (!rec2.book.Sheets[name]) throw new Error('工作表不存在: ' + name);
      return { rec: rec2, name, ws: rec2.book.Sheets[name] };
    },

    // 跨表/跨文件复制粘贴：源区域（某表格某工作表）→ 目标（某表格某工作表）
    // fromBook/toBook 留空=当前；可用 id / 路径 / 文件名 定位
    excelSheetCopyPaste(fromBook, fromSheet, fromRange, toBook, toSheet, toRange, mode = '全部粘贴') {
      const src = this.getSheetOf(this.findBook(fromBook) || this.getActiveBook(), fromSheet);
      const dst = this.getSheetOf(this.findBook(toBook) || this.getActiveBook(), toSheet);
      const s = this.parseRange(fromRange);
      const d = this.parseCell(toRange);
      const dr = s.r1 - s.r0, dc = s.c1 - s.c0;

      // 目标区域已有值（用于"不覆盖原有内容"）
      const dstOld = {};
      for (let r = d.r; r <= d.r + dr; r++) {
        for (let c = d.c; c <= d.c + dc; c++) {
          dstOld[this.colName(c) + (r + 1)] = dst.ws[this.colName(c) + (r + 1)];
        }
      }

      for (let r = s.r0; r <= s.r1; r++) {
        for (let c = s.c0; c <= s.c1; c++) {
          const srcAddr = this.colName(c) + (r + 1);
          const dstAddr = this.colName(d.c + (c - s.c0)) + (d.r + (r - s.r0) + 1);
          const cell = src.ws[srcAddr];
          const oldDst = dstOld[dstAddr];
          switch (mode) {
            case '只粘贴值':
              dst.ws[dstAddr] = this.makeCell(cell ? (cell.v ?? '') : '');
              break;
            case '只粘贴公式':
              if (cell && cell.f) dst.ws[dstAddr] = { t: 'n', f: cell.f, v: cell.v };
              else delete dst.ws[dstAddr];
              break;
            case '只粘贴格式':
              if (cell && cell.s) {
                if (!dst.ws[dstAddr]) dst.ws[dstAddr] = { t: 's', v: '' };
                dst.ws[dstAddr].s = cell.s;
              }
              break;
            case '保留公式':
              if (cell && cell.f) dst.ws[dstAddr] = { t: 'n', f: cell.f, v: cell.v };
              else if (cell) dst.ws[dstAddr] = this.makeCell(cell.v ?? '');
              else delete dst.ws[dstAddr];
              break;
            case '值与数字格式':
              dst.ws[dstAddr] = this.makeCell(cell ? (cell.v ?? '') : '');
              if (cell && cell.s) dst.ws[dstAddr].s = cell.s;
              break;
            case '公式与数字格式':
              if (cell && cell.f) {
                dst.ws[dstAddr] = { t: 'n', f: cell.f, v: cell.v };
                if (cell.s) dst.ws[dstAddr].s = cell.s;
              }
              break;
            case '不覆盖原有内容':
              if (oldDst) continue;
              if (cell) dst.ws[dstAddr] = this.makeCell(cell.v ?? '');
              break;
            case '全部粘贴':
            default:
              if (cell) dst.ws[dstAddr] = { ...cell };
              else delete dst.ws[dstAddr];
              break;
          }
        }
      }
      // 刷新目标工作表的 !ref 并重算目标表格公式
      const { maxR, maxC } = this.scanCells(dst.ws);
      dst.ws['!ref'] = (maxR >= 0 && maxC >= 0) ? ('A1:' + this.colName(maxC) + (maxR + 1)) : 'A1:A1';
      this.recalcFormulas(dst.rec);
      return true;
    },

    // 指定列范围内最后一个有数据的行（0 基；无数据返回 -1）
    // 用「整列」写法（A、A:C）时靠它定位到该列有数据的部分，避免写一堆空单元格
    lastRowOf(ws, c0, c1) {
      let last = -1;
      Object.keys(ws).forEach(key => {
        if (key[0] === '!') return;
        let pos;
        try { pos = this.parseCell(key); } catch (e) { return; }
        if (pos.c >= c0 && pos.c <= c1 && pos.r > last) last = pos.r;
      });
      return last;
    },

    // ===== 白话「表格复制粘贴」：两张表之间按文件路径来，不需要先打开表格 =====
    // 解析「复制哪几列/区域」，支持这些写法（多个用 , ， ; ； 或空格分隔）：
    //   A1-A9 / A1:A9   区域（- 和 : 都认）
    //   A1              单个单元格
    //   A               整列（该列有数据的部分）
    //   A:C / A-C       连续多整列
    //   留空            = 整个表格已用区域
    // 返回每个段的区域（0 基行列）
    parsePickSegments(rangesText, ws) {
      const scan = this.scanCells(ws);
      if (scan.maxR < 0 || scan.maxC < 0) throw new Error('源表格是空的，没有内容可以复制');
      const whole = { r0: 0, c0: 0, r1: scan.maxR, c1: scan.maxC };
      const raw = String(rangesText == null ? '' : rangesText).trim();
      if (!raw) return [whole];
      const parts = raw.split(/[,，;；\s]+/).map(s => s.trim()).filter(Boolean);
      const out = [];
      for (const part of parts) {
        // 各种连字符/破折号统一成半角 -（用户可能从别处粘贴过来）
        const t = part.replace(/[\u2010-\u2015\u2212\uFF0D]/g, '-');
        let m;
        try {
          if ((m = /^([A-Za-z]{1,3})(?:列)?$/.exec(t))) {
            // 整列 A / A列：只取该列有数据的部分
            const c = this.parseCell(m[1] + '1').c;
            out.push({ r0: 0, c0: c, r1: Math.max(0, this.lastRowOf(ws, c, c)), c1: c });
          } else if ((m = /^([A-Za-z]{1,3})[-:]([A-Za-z]{1,3})$/.exec(t))) {
            // 连续多整列 A:C：同样只取这些列有数据的部分
            const c1 = this.parseCell(m[1] + '1').c;
            const c2 = this.parseCell(m[2] + '1').c;
            const lo = Math.min(c1, c2), hi = Math.max(c1, c2);
            out.push({ r0: 0, c0: lo, r1: Math.max(0, this.lastRowOf(ws, lo, hi)), c1: hi });
          } else {
            // 区域 / 单元格（- 和 : 都当作区间分隔符，白话里用户更常写 A1-A9）
            const segs = t.replace(/-/g, ':').split(':');
            const a = this.parseCell(segs[0]);
            const b = segs[1] ? this.parseCell(segs[1]) : a;
            out.push({ r0: Math.min(a.r, b.r), c0: Math.min(a.c, b.c), r1: Math.max(a.r, b.r), c1: Math.max(a.c, b.c) });
          }
        } catch (e) {
          throw new Error(`看不懂「${part}」这种写法。正确示例：A1-A9,B2-B4（也支持 A1:A9、A、A:C）`);
        }
      }
      return out.length ? out : [whole];
    },

    // 空格子判断：没有单元格对象、或值是空串/空值
    isEmptyCell(cell) {
      return !cell || cell.v === undefined || cell.v === null || cell.v === '';
    },

    // 把 srcWs 的 seg 区域按 mode 写到 dstWs 的（startR, startC）处
    pasteSegment(srcWs, seg, dstWs, startR, startC, mode) {
      const h = seg.r1 - seg.r0 + 1, w = seg.c1 - seg.c0 + 1;
      for (let r = 0; r < h; r++) {
        for (let c = 0; c < w; c++) {
          const srcAddr = this.colName(seg.c0 + c) + (seg.r0 + r + 1);
          const dstAddr = this.colName(startC + c) + (startR + r + 1);
          const cell = srcWs[srcAddr];
          switch (mode) {
            case '只粘贴文本':
              // 一律落成文本：公式、数字都变成屏幕上看见的字，不会被 Excel 重新计算
              if (this.isEmptyCell(cell)) delete dstWs[dstAddr];
              else dstWs[dstAddr] = { t: 's', v: String(cell.v) };
              break;
            case '只粘贴值':
              if (this.isEmptyCell(cell)) delete dstWs[dstAddr];
              else dstWs[dstAddr] = this.makeCell(cell.v);
              break;
            case '只粘贴公式':
              if (cell && cell.f) dstWs[dstAddr] = { t: 'n', f: cell.f, v: cell.v };
              else delete dstWs[dstAddr];
              break;
            case '只粘贴格式':
              if (cell && cell.s) {
                if (!dstWs[dstAddr]) dstWs[dstAddr] = { t: 's', v: '' };
                dstWs[dstAddr].s = cell.s;
              }
              break;
            case '保留公式':
              if (cell && cell.f) dstWs[dstAddr] = { t: 'n', f: cell.f, v: cell.v };
              else if (cell) dstWs[dstAddr] = this.makeCell(cell.v ?? '');
              else delete dstWs[dstAddr];
              break;
            case '值与数字格式':
              if (this.isEmptyCell(cell)) { delete dstWs[dstAddr]; break; }
              dstWs[dstAddr] = this.makeCell(cell.v);
              if (cell.s) dstWs[dstAddr].s = cell.s;
              break;
            case '公式与数字格式':
              if (cell && cell.f) {
                dstWs[dstAddr] = { t: 'n', f: cell.f, v: cell.v };
                if (cell.s) dstWs[dstAddr].s = cell.s;
              }
              break;
            case '不覆盖原有内容':
              if (dstWs[dstAddr]) break;
              if (cell) dstWs[dstAddr] = this.makeCell(cell.v ?? '');
              break;
            case '全部粘贴':
            default:
              if (cell) dstWs[dstAddr] = { ...cell };
              else delete dstWs[dstAddr];
              break;
          }
        }
      }
    },

    // 白话：从「源表格」按区域复制，粘到「目标表格」的指定起始单元格，可选保存
    // 多段区域会依次横排：第 1 段从起始列开始，第 2 段接在第 1 段右边，以此类推
    async excelTableCopyPaste(p) {
      if (typeof XLSX === 'undefined') throw new Error('Excel 组件未加载');
      p = p || {};

      // ---- 源表 ----
      const fromPath = this.expand(p.fromPath);
      if (!fromPath) throw new Error('请填写①源表格路径（可以把 Excel 文件直接拖到输入框里）');
      if (!(await window.yingdao.fileExists(fromPath))) throw new Error('①源表格不存在：' + fromPath);
      let srcBook;
      try {
        srcBook = XLSX.read(await window.yingdao.readFile(fromPath), { type: 'array' });
      } catch (e) {
        throw new Error('①源表格打不开（文件损坏或被其它程序占用）：' + fromPath);
      }
      const srcSheetName = (p.fromSheet && srcBook.Sheets[p.fromSheet]) ? p.fromSheet : srcBook.SheetNames[0];
      const srcWs = srcBook.Sheets[srcSheetName];
      if (!srcWs) throw new Error('①源表格里没有工作表');

      const segments = this.parsePickSegments(p.fromRanges, srcWs);

      // ---- 目标表（留空 = 新建一个，存到桌面）----
      const toPathIn = this.expand(p.toPath);
      let dstBook, dstPath, dstSheetName;
      if (toPathIn) {
        dstPath = toPathIn;
        if (await window.yingdao.fileExists(dstPath)) {
          try {
            dstBook = XLSX.read(await window.yingdao.readFile(dstPath), { type: 'array' });
          } catch (e) {
            throw new Error('④目标表格打不开（文件损坏或被其它程序占用）：' + dstPath);
          }
          dstSheetName = (p.toSheet && dstBook.Sheets[p.toSheet]) ? p.toSheet : dstBook.SheetNames[0];
        } else {
          dstBook = XLSX.utils.book_new();
          dstSheetName = p.toSheet || 'Sheet1';
          XLSX.utils.book_append_sheet(dstBook, XLSX.utils.aoa_to_sheet([]), dstSheetName);
        }
      } else {
        let desktop = '';
        try { desktop = await window.yingdao.getDesktopPath(); } catch (e) { desktop = ''; }
        if (!desktop) desktop = 'C:\\Users\\Public\\Desktop';
        dstPath = `${desktop}\\表格复制粘贴_${this.timestamp()}.xlsx`;
        dstBook = XLSX.utils.book_new();
        dstSheetName = p.toSheet || 'Sheet1';
        XLSX.utils.book_append_sheet(dstBook, XLSX.utils.aoa_to_sheet([]), dstSheetName);
      }
      const dstWs = dstBook.Sheets[dstSheetName];
      if (!dstWs) throw new Error('④目标表格里没有工作表：' + dstSheetName);

      // ---- 起始单元格 ----
      const startText = String(this.expand(p.toCell) || 'A1').trim() || 'A1';
      let start;
      try {
        start = this.parseCell(startText);
      } catch (e) {
        throw new Error(`⑥「${startText}」不是有效的起始单元格，正确示例：A1、B1、D2`);
      }

      const mode = p.mode || '只粘贴文本';

      // ---- 逐段粘贴（横排）----
      let colOffset = 0, maxH = 0;
      segments.forEach(seg => {
        const h = seg.r1 - seg.r0 + 1;
        if (h > maxH) maxH = h;
        this.pasteSegment(srcWs, seg, dstWs, start.r, start.c + colOffset, mode);
        colOffset += Math.max(1, seg.c1 - seg.c0 + 1);
      });

      // ---- 刷新 !ref 并重算目标表公式 ----
      const sc = this.scanCells(dstWs);
      dstWs['!ref'] = (sc.maxR >= 0 && sc.maxC >= 0) ? ('A1:' + this.colName(sc.maxC) + (sc.maxR + 1)) : 'A1:A1';
      this.recalcFormulas({ book: dstBook, activeSheet: dstSheetName });

      // ---- 保存 ----
      const wantSave = p.save !== '不保存';
      if (wantSave) {
        const out = XLSX.write(dstBook, { bookType: 'xlsx', type: 'array' });
        await window.yingdao.writeFile(dstPath, (out instanceof Uint8Array) ? out : new Uint8Array(out));
      }

      // 粘贴区域的右下角（用于日志，写清楚到底贴到哪）
      const endAddr = this.colName(start.c + Math.max(0, colOffset - 1)) + (start.r + Math.max(1, maxH));
      return {
        path: dstPath,
        saved: wantSave,
        msg: `表格复制粘贴：源「${srcSheetName}」${segments.length} 段 → 目标「${dstSheetName}」` +
             `${startText}:${endAddr}（${mode}）${wantSave ? '，已保存到 ' + dstPath : '，未保存（仅内存）'}`
      };
    },

    // 插入行（在 row 行前插入 count 行，row 从 1 开始）
    excelInsertRow(row, count) {
      const ws = this.getWS();
      count = Math.max(1, Number(count) || 1);
      const ref = this.getWSRange(ws);
      const maxR = ref.r1;
      // 从下往上搬移
      for (let r = maxR; r >= row - 1; r--) {
        for (let c = 0; c <= ref.c1; c++) {
          const src = this.colName(c) + (r + 1);
          const dst = this.colName(c) + (r + 1 + count);
          if (ws[src]) { ws[dst] = ws[src]; delete ws[src]; }
        }
      }
      this.shiftFormulas(ws, 'row', row - 1, count, 'insert');
      this.refreshRef();
    },

    excelInsertCol(col, count) {
      const ws = this.getWS();
      count = Math.max(1, Number(count) || 1);
      const ref = this.getWSRange(ws);
      for (let c = ref.c1; c >= col - 1; c--) {
        for (let r = 0; r <= ref.r1; r++) {
          const src = this.colName(c) + (r + 1);
          const dst = this.colName(c + count) + (r + 1);
          if (ws[src]) { ws[dst] = ws[src]; delete ws[src]; }
        }
      }
      this.shiftFormulas(ws, 'col', col - 1, count, 'insert');
      this.refreshRef();
    },

    excelDeleteRow(row, count) {
      const ws = this.getWS();
      count = Math.max(1, Number(count) || 1);
      const ref = this.getWSRange(ws);
      for (let r = row - 1; r <= ref.r1; r++) {
        for (let c = 0; c <= ref.c1; c++) {
          const src = this.colName(c) + (r + 1 + count);
          const dst = this.colName(c) + (r + 1);
          if (ws[src]) { ws[dst] = ws[src]; delete ws[src]; }
        }
      }
      this.shiftFormulas(ws, 'row', row - 1, count, 'delete');
      this.refreshRef();
    },

    excelDeleteCol(col, count) {
      const ws = this.getWS();
      count = Math.max(1, Number(count) || 1);
      const ref = this.getWSRange(ws);
      for (let c = col - 1; c <= ref.c1; c++) {
        for (let r = 0; r <= ref.r1; r++) {
          const src = this.colName(c + count) + (r + 1);
          const dst = this.colName(c) + (r + 1);
          if (ws[src]) { ws[dst] = ws[src]; delete ws[src]; }
        }
      }
      this.shiftFormulas(ws, 'col', col - 1, count, 'delete');
      this.refreshRef();
    },

    getWSRange(ws) {
      const { maxR, maxC } = this.scanCells(ws);
      if (maxR < 0 || maxC < 0) return { r0: 0, c0: 0, r1: 0, c1: 0 };
      return { r0: 0, c0: 0, r1: maxR, c1: maxC };
    },

    excelGetRows() {
      const ws = this.getWS();
      return this.getWSRange(ws).r1 + 1;
    },

    // 导出原始内容（公式单元格返回 "=公式"），供界面复制/编辑公式使用
    excelRawArray() {
      const ws = this.getWS();
      const { maxR, maxC, list } = this.scanCells(ws);
      if (maxR < 0 || maxC < 0) return [];
      const grid = Array.from({ length: maxR + 1 }, () => Array(maxC + 1).fill(''));
      list.forEach(({ r, c, cell }) => {
        grid[r][c] = cell ? (cell.f ? ('=' + cell.f) : (cell.v ?? '')) : '';
      });
      return grid;
    },

    // 导出为数组供数据表格显示（手动扫描，不依赖 !ref）
    excelToArray() {
      const ws = this.getWS();
      const { maxR, maxC, list } = this.scanCells(ws);
      if (maxR < 0 || maxC < 0) return [];
      const grid = Array.from({ length: maxR + 1 }, () => Array(maxC + 1).fill(''));
      list.forEach(({ r, c, cell }) => { grid[r][c] = cell ? (cell.v ?? '') : ''; });
      return grid;
    },

    // 更新工作表的 !ref（保证保存时数据完整）
    refreshRef() {
      const ws = this.getWS();
      const { maxR, maxC } = this.scanCells(ws);
      if (maxR >= 0 && maxC >= 0) {
        ws['!ref'] = 'A1:' + this.colName(maxC) + (maxR + 1);
      } else {
        // 全部清空后也要重置，否则残留的旧 !ref 会把幽灵区域写进文件
        ws['!ref'] = 'A1:A1';
      }
    },

    // 内部：把二维数组写进指定工作表
    // 空值删除、值未变动的单元格保留原有公式与样式（撤销/填充柄/多窗口回写共用）
    applyRowsTo(ws, rows) {
      const data = Array.isArray(rows) ? rows : [];
      Object.keys(ws).forEach(key => {
        if (key[0] === '!') return;
        let pos;
        try { pos = this.parseCell(key); } catch (e) { return; }
        const v = (data[pos.r] && data[pos.r][pos.c] != null) ? String(data[pos.r][pos.c]) : '';
        if (v === '') delete ws[key];
      });
      data.forEach((row, r) => {
        if (!Array.isArray(row)) return;
        row.forEach((val, c) => {
          const v = val == null ? '' : String(val);
          if (v === '') return;
          const addr = this.colName(c) + (r + 1);
          const cell = ws[addr];
          if (cell && String(cell.v ?? '') === v) return;   // 值未变 → 保留公式/样式
          ws[addr] = this.makeCell(v);
        });
      });
      const { maxR, maxC } = this.scanCells(ws);
      ws['!ref'] = (maxR >= 0 && maxC >= 0) ? ('A1:' + this.colName(maxC) + (maxR + 1)) : 'A1:A1';
    },

    // 整表回写当前工作表（撤销 / 填充柄 / 内置结构操作后由界面调用）
    setSheetValues(rows) {
      this.applyRowsTo(this.getWS(), rows);
      this.recalcFormulas(this.getActiveBook());
    },

    // 当前激活 workbook 的 id（弹出独立窗口时带上，便于回写时定位到同一张表格）
    getActiveBookId() {
      return activeBookId;
    },

    // 按「表格+工作表」就地更新内容（拖出的单 sheet 窗口回写用，不新建标签）
    updateSheet(bookId, sheetName, rows, cells) {
      const rec = excelBooks.find(b => b.id === bookId) || this.getActiveBook();
      if (!rec) return false;
      const name = sheetName || rec.activeSheet || rec.book.SheetNames[0] || 'Sheet1';
      if (!rec.book.Sheets[name]) {
        XLSX.utils.book_append_sheet(rec.book, XLSX.utils.aoa_to_sheet([]), name);
      }
      this.applyRowsTo(rec.book.Sheets[name], rows || []);
      this.applyCellsTo(rec.book.Sheets[name], cells);
      this.recalcFormulas(rec);
      rec.activeSheet = name;
      if (rec.id === activeBookId) excelBook = rec.book;
      return true;
    },

    // 按 id 更新已有 workbook 的内容（独立 Excel 窗口回写用，不新建标签）
    updateBook(id, snap) {
      const rec = excelBooks.find(b => b.id === id);
      if (!rec) return false;
      const sheetName = snap.sheetName || rec.book.SheetNames[0] || 'Sheet1';
      if (!rec.book.Sheets[sheetName]) {
        XLSX.utils.book_append_sheet(rec.book, XLSX.utils.aoa_to_sheet([]), sheetName);
      }
      this.applyRowsTo(rec.book.Sheets[sheetName], snap.rows || []);
      this.applyCellsTo(rec.book.Sheets[sheetName], snap.cells);
      this.recalcFormulas(rec);
      rec.activeSheet = sheetName;
      if (snap.path) rec.path = snap.path;
      // 同步快捷引用（当前激活的就是这张表时）
      if (rec.id === activeBookId) { excelBook = rec.book; excelPath = rec.path; }
      return true;
    },

    // 把公式单元格（{addr:{f,v,t}}）合并进工作表
    applyCellsTo(ws, cells) {
      if (!ws || !cells) return;
      Object.keys(cells).forEach(addr => {
        const c = cells[addr];
        if (!c) return;
        if (c.f) ws[addr] = { t: c.t || 'n', v: c.v, f: c.f };
      });
    },

    // 清空区域内容（保留格式）
    clearRange(range) {
      const ws = this.getWS();
      const { r0, c0, r1, c1 } = this.parseRange(range);
      for (let r = r0; r <= r1; r++) {
        for (let c = c0; c <= c1; c++) delete ws[this.colName(c) + (r + 1)];
      }
      this.refreshRef();
    },

    // 直接写单元格（r/c 为 0 起始索引，供界面编辑用；数字自动识别为数值型，= 开头按公式计算）
    // 返回本次重算的公式数量（>0 表示有依赖单元格跟着变了，界面据此刷新显示）
    setCellValue(r, c, value) {
      const ws = this.getWS();
      const addr = this.colName(c) + (r + 1);
      if (value === '' || value === null || value === undefined) {
        delete ws[addr];
      } else {
        ws[addr] = this.makeCell(value);
      }
      const n = this.recalcFormulas(this.getActiveBook());   // 公式与依赖立即出结果
      this.refreshRef();
      return n;
    },

    // 获取当前 Excel 路径与工作表名（供界面显示）
    getExcelPath() { return excelPath; },
    getExcelSheetName() {
      if (!excelBook) return '';
      return this.getActiveSheetName();
    },

    // 全局剪贴板：复制（跨 sheet / 跨 workbook）
    copyToClipboard(range) {
      const { r0, c0, r1, c1 } = this.parseRange(range);
      const ws = this.getWS();
      const rows = [];
      for (let r = r0; r <= r1; r++) {
        const row = [];
        for (let c = c0; c <= c1; c++) {
          const addr = this.colName(c) + (r + 1);
          const cell = ws[addr];
          row.push(cell ? { v: cell.v, f: cell.f, s: cell.s, t: cell.t } : null);
        }
        rows.push(row);
      }
      clipboard = { rows, fromSheet: this.getActiveSheetName(), fromBook: activeBookId };
      return rows;
    },

    // 全局剪贴板：粘贴（可跨 sheet / 跨 workbook，粘贴到当前 sheet）
    pasteFromClipboard(to, mode = '全部粘贴') {
      if (!clipboard || !clipboard.rows) throw new Error('剪贴板为空，请先复制');
      const dst = this.parseCell(to);
      const ws = this.getWS();
      clipboard.rows.forEach((row, ri) => {
        row.forEach((cell, ci) => {
          const addr = this.colName(dst.c + ci) + (dst.r + ri + 1);
          if (!cell) { if (mode === '全部粘贴') delete ws[addr]; return; }
          switch (mode) {
            case '只粘贴值': ws[addr] = this.makeCell(cell.v ?? ''); break;
            case '只粘贴公式': if (cell.f) ws[addr] = { t: 'n', f: cell.f, v: cell.v }; break;
            case '只粘贴格式': if (cell.s) { if (!ws[addr]) ws[addr] = { t: 's', v: '' }; ws[addr].s = cell.s; } break;
            case '保留公式': if (cell.f) ws[addr] = { t: 'n', f: cell.f, v: cell.v }; else ws[addr] = this.makeCell(cell.v ?? ''); break;
            case '值与数字格式': ws[addr] = this.makeCell(cell.v ?? ''); if (cell.s) ws[addr].s = cell.s; break;
            case '公式与数字格式': if (cell.f) { ws[addr] = { t: 'n', f: cell.f, v: cell.v }; if (cell.s) ws[addr].s = cell.s; } break;
            case '不覆盖原有内容': if (ws[addr]) return; ws[addr] = this.makeCell(cell.v ?? ''); break;
            case '全部粘贴':
            default: ws[addr] = { t: cell.t || 's', v: cell.v, f: cell.f, s: cell.s }; break;
          }
        });
      });
      this.refreshRef();
      return true;
    },

    // 保存到指定路径（通过 IPC 写二进制）
    async excelSaveTo(path) {
      if (!excelBook) throw new Error('请先打开Excel');
      const wbout = XLSX.write(excelBook, { bookType: 'xlsx', type: 'array' });
      await window.yingdao.writeFile(path, (wbout instanceof Uint8Array) ? wbout : new Uint8Array(wbout));
      // 更新当前激活 book 的路径
      const book = this.getActiveBook();
      if (book) book.path = path;
      excelPath = path;
    },

    // ---- 多格式保存（xlsx/xls/csv/txt/ods/html/json，默认只勾 xlsx）----
    EXPORT_FORMATS: [
      { key: 'xlsx', label: 'Excel 工作簿', ext: '.xlsx', def: true, note: '推荐，支持多工作表' },
      { key: 'xls', label: 'Excel 97-2003', ext: '.xls', note: '老版本兼容' },
      { key: 'csv', label: 'CSV 逗号分隔', ext: '.csv', note: '仅当前工作表，带 BOM 防乱码' },
      { key: 'txt', label: '文本（制表符）', ext: '.txt', note: '仅当前工作表' },
      { key: 'ods', label: 'OpenDocument', ext: '.ods', note: 'WPS/LibreOffice 通用' },
      { key: 'html', label: '网页表格', ext: '.html', note: '可直接用浏览器打开' },
      { key: 'json', label: 'JSON 数据', ext: '.json', note: '仅当前工作表，便于程序读取' }
    ],
    getExportFormats() { return this.EXPORT_FORMATS.map(f => Object.assign({}, f)); },
    defaultFormats() {
      const d = this.EXPORT_FORMATS.filter(f => f.def).map(f => f.key);
      return d.length ? d : ['xlsx'];
    },
    isValidFormat(key) { return this.EXPORT_FORMATS.some(f => f.key === key); },
    // 替换扩展名（无扩展名也能处理）
    swapExt(path, ext) {
      const s = String(path || '');
      return /\.[^./\\]+$/.test(s) ? s.replace(/\.[^./\\]+$/, ext) : s + ext;
    },
    // 按格式生成可写文件的内容（Uint8Array）
    exportBook(format) {
      if (!excelBook) throw new Error('请先打开Excel');
      const fmt = this.isValidFormat(format) ? format : 'xlsx';
      if (fmt === 'json') {
        const aoa = XLSX.utils.sheet_to_json(this.getWS(), { header: 1, defval: '' });
        const text = JSON.stringify({ sheet: this.getActiveSheetName(), rows: aoa }, null, 2);
        return new TextEncoder().encode(text);
      }
      if (fmt === 'csv' || fmt === 'txt') {
        // 只导出当前工作表；加 BOM，避免 Excel 打开中文乱码
        const text = XLSX.write(excelBook, { bookType: fmt, type: 'string', sheet: this.getActiveSheetName() });
        return new TextEncoder().encode('\ufeff' + text);
      }
      const out = XLSX.write(excelBook, { bookType: fmt, type: 'array' });
      // type:'array' 在不同环境可能返回 ArrayBuffer 或 Uint8Array，统一成 Uint8Array
      return (out instanceof Uint8Array) ? out : new Uint8Array(out);
    },
    // 按勾选的多种格式保存到同一基名，返回写出的文件路径列表
    async excelSaveFormats(path, formats) {
      if (!excelBook) throw new Error('请先打开Excel');
      let list = (Array.isArray(formats) ? formats : []).filter(f => this.isValidFormat(f));
      if (!list.length) list = this.defaultFormats();
      let base = path ? this.expand(path) : excelPath;
      if (!base) {
        let desktop = '';
        try { desktop = await window.yingdao.getDesktopPath(); } catch (e) { }
        if (!desktop) desktop = 'C:\\Users\\Public\\Desktop';
        base = `${desktop}\\新建Excel_${this.timestamp()}.xlsx`;
      }
      const written = [];
      for (const fmt of list) {
        const meta = this.EXPORT_FORMATS.find(f => f.key === fmt);
        const target = this.swapExt(base, meta.ext);
        const buf = this.exportBook(fmt);
        await window.yingdao.writeFile(target, buf);
        written.push(target);
      }
      // 以第一个格式的文件作为当前路径（xlsx 优先）
      const mainPath = written[0];
      const book = this.getActiveBook();
      if (book) book.path = mainPath;
      excelPath = mainPath;
      return written;
    },

    async excelSave(path, formats) {
      const list = (Array.isArray(formats) && formats.length) ? formats
        : (Array.isArray(this.saveFormats) && this.saveFormats.length ? this.saveFormats : this.defaultFormats());
      return await this.excelSaveFormats(path, list);
    },

    // ---- 另存为（命名方式可选）----
    // 目录默认取原表格所在目录（没有就用桌面）；文件名默认"原名-1、原名-2…"递增，绝不覆盖原文件。
    // naming: 后缀递增（默认）| 加前缀 | 覆盖
    // startIndex: 后缀从几开始（默认 1）
    async resolveSaveAsPath({ naming = '后缀递增', prefix = '', startIndex = 1 } = {}) {
      const book = this.getActiveBook();
      const cur = (book && book.path) || this.excelPath || '';
      let dir = '', stem = '未命名表格', ext = '.xlsx';
      if (cur) {
        const base = String(cur).split(/[\\/]/).pop() || '未命名表格';
        const m = /^(.*?)(\.[^.]+)?$/.exec(base) || [];
        stem = m[1] || '未命名表格';
        ext = m[2] || '.xlsx';
        dir = String(cur).replace(/[\\/][^\\/]*$/, '');
      } else {
        try { dir = await window.yingdao.getDesktopPath(); } catch (e) { dir = ''; }
        if (!dir) dir = 'C:\\Users\\Public\\Desktop';
      }
      // 名字末尾如果已经带了递增序号（报表-3），先剥掉再算新号，
      // 否则连续另存为会变成 报表-3-1、报表-3-1-1… 越滚越长。
      // 只剥 1~999 的小序号，像 报表-2026 这种年份不会被误剥。
      stem = stem.replace(/[-_ ](\d{1,3})$/, '');
      if (naming === '覆盖' && cur) return cur;      // 直接覆盖原文件

      const exists = async (p) => { try { return await window.yingdao.fileExists(p); } catch (e) { return false; } };
      const join = (name) => dir.replace(/[\\/]+$/, '') + '\\' + name;
      const pre = String(prefix == null ? '' : prefix);
      const start = Math.max(0, Number(startIndex));

      if (naming === '加前缀') {
        const first = join(pre + stem + ext);
        if (pre && !(await exists(first))) return first;      // 前缀不重名就直接用
        for (let n = start; n <= start + 999; n++) {          // 重名就往后再加序号
          const c = join(pre + stem + '-' + n + ext);
          if (!(await exists(c))) return c;
        }
      } else {
        for (let n = start; n <= start + 999; n++) {
          const c = join(stem + '-' + n + ext);
          if (!(await exists(c))) return c;
        }
      }
      throw new Error('找了 1000 个文件名都重名了，请换个前缀或起始序号');
    },

    // 另存为：算好路径 -> 按当前保存格式写出 -> 当前表格切到这个新文件
    async excelSaveAs({ naming = '后缀递增', prefix = '', startIndex = 1 } = {}) {
      const base = await this.resolveSaveAsPath({ naming, prefix, startIndex });
      const formats = (Array.isArray(this.saveFormats) && this.saveFormats.length) ? this.saveFormats : this.defaultFormats();
      const written = await this.excelSaveFormats(base, formats);
      return { path: base, written: written || [], naming };
    },

    // ---- 文件操作（通过 IPC 到主进程执行） ----
    // 对目录条目排序：sortBy 支持 '字符'/'文件名' | '修改时间' | '大小'/'文件大小'
    // order 支持 '顺序'/'从小到大'/'从早到晚'(=升序) 与 '逆序'/'从大到小'/'从晚到早'(=降序)
    sortFileEntries(list, sortBy, order) {
      const arr = (Array.isArray(list) ? list : []).slice();
      const key = (sortBy === '修改时间') ? 'mtime' : ((sortBy === '大小' || sortBy === '文件大小') ? 'size' : 'name');
      const o = String(order || '');
      const desc = /逆序|从大到小|从晚到早/.test(o);
      const dir = desc ? -1 : 1;
      arr.sort((a, b) => {
        let x = a[key], y = b[key];
        if (key === 'name') { x = String(x == null ? '' : x).toLowerCase(); y = String(y == null ? '' : y).toLowerCase(); return dir * (x < y ? -1 : x > y ? 1 : 0); }
        x = Number(x) || 0; y = Number(y) || 0;
        return dir * (x - y);
      });
      return arr;
    },
    // 列出目录并按需排序，返回文件名列表（目录项带 [目录] 前缀，便于数据表格展示）
    async fileListDir(path, sortBy, order) {
      const p = this.expand(path);
      if (!p) throw new Error('请填写目录路径');
      const list = await window.yingdao.listDir(p);
      const sorted = this.sortFileEntries(list, sortBy || '字符', order || '顺序');
      return sorted.map(f => f.isDir ? '[目录] ' + f.name : f.name);
    },
    // 从文件夹取排序后的第 index 个文件（index 从 1 开始，负数=倒数第N个，如 -1=最后一个）；不是目录则返回 null
    async pickFileFromDir(src, sortBy, order, index) {
      const s = this.expand(src);
      if (!s) throw new Error('请填写源路径');
      const idx = Number(index) || 0;
      if (idx === 0) return null;   // 未启用"取第N个"
      let list;
      try { list = await window.yingdao.listDir(s); } catch (e) { return null; }  // 不是目录 → 当作文件
      const sorted = this.sortFileEntries(list.filter(f => f.isFile), sortBy || '字符', order || '顺序');
      if (!sorted.length) throw new Error('文件夹里没有文件');
      const abs = Math.abs(idx);
      if (abs > sorted.length) throw new Error(`文件夹里只有 ${sorted.length} 个文件，无法取第 ${idx} 个`);
      const target = idx > 0 ? sorted[idx - 1] : sorted[sorted.length + idx];   // 负数从末尾数
      return target.path;
    },

    // 解析「第几个文件」表达式：支持 "1,3,5,7"、"1-3"、"1-3,5,-1"（负数=倒数），返回索引数组
    parseIndexList(expr) {
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
          if (a === 0 || b === 0 || (a < 0 && b > 0) || b-a > 10000) throw new Error('文件序号范围无效');
          for (let n = a; n <= b; n++) out.push(n);
        } else {
          const n = parseInt(part, 10);
          if (!/^-?\d+$/.test(part) || !Number.isSafeInteger(n) || n === 0) throw new Error('文件序号无效：' + part);
          out.push(n);
        }
      });
      return out;
    },

    // 从文件夹按表达式取多个文件（支持 "1,3,5"、"1-3"、"1-3,5,-1"），返回文件路径数组
    async pickFilesFromDir(src, sortBy, order, expr) {
      const s = this.expand(src);
      if (!s) throw new Error('请填写源路径');
      const idxs = this.parseIndexList(expr);
      if (!idxs.length) throw new Error('请填写有效的文件序号，例如 1、1-3、-1');
      let list;
      try { list = await window.yingdao.listDir(s); } catch (e) { return null; }
      const sorted = this.sortFileEntries(list.filter(f => f.isFile), sortBy || '字符', order || '顺序');
      if (!sorted.length) throw new Error('文件夹里没有文件');
      const paths = [];
      idxs.forEach(idx => {
        const abs = Math.abs(idx);
        if (abs > sorted.length) throw new Error(`文件夹里只有 ${sorted.length} 个文件，无法取第 ${idx} 个`);
        const t = idx > 0 ? sorted[idx - 1] : sorted[sorted.length + idx];
        paths.push(t.path);
      });
      return [...new Set(paths)];
    },
    async fileReadText(path) {
      const p = this.expand(path);
      if (!p) throw new Error('请填写文件路径');
      return await window.yingdao.readText(p);
    },
    async fileWriteText(path, content, append) {
      const p = this.expand(path);
      if (!p) throw new Error('请填写文件路径');
      let text = this.expand(content);
      if (append === '追加') {
        let old = '';
        try { old = await window.yingdao.readText(p); } catch (e) { }
        text = old + text;
      }
      await window.yingdao.writeText(p, text);
      return true;
    },
    // 判断路径是否为已存在的目录（能列出内容即目录）
    async isDir(p) {
      if (!p) return false;
      try { await window.yingdao.listDir(p); return true; } catch (e) { return false; }
    },
    // 复制目标解析：若 dst 是已存在目录，则自动拼接源文件名（复制到文件夹里）
    async resolveCopyDst(srcFile, dst) {
      if (await this.isDir(dst)) {
        const base = srcFile.split(/[\\/]/).pop();
        return dst.replace(/[\\/]$/, '') + '\\' + base;
      }
      return dst;
    },
    async fileCopy(src, dst, sortBy, order, index) {
      let s = this.expand(src), d = this.expand(dst);
      if (!s || !d) throw new Error('请填写源路径和目标路径');
      // 源是文件夹且设置了"取第N个" → 取排序后的第 index 个文件
      const picked = await this.pickFileFromDir(src, sortBy, order, index);
      if (picked) s = picked;
      d = await this.resolveCopyDst(s, d);
      await window.yingdao.copyFile(s, d);
      return true;
    },
    async fileMove(src, dst) {
      const s = this.expand(src), d = this.expand(dst);
      if (!s || !d) throw new Error('请填写源文件和目标路径');
      await window.yingdao.moveFile(s, d);
      return true;
    },
    async fileDelete(path, sortBy, order, index) {
      let p = this.expand(path);
      if (!p) throw new Error('请填写文件路径');
      // 源是文件夹且设置了"删除第N个" → 取排序后的第 index 个文件删除
      const picked = await this.pickFileFromDir(path, sortBy, order, index);
      if (picked) p = picked;
      await window.yingdao.deleteFile(p);
      return true;
    },
    async fileExists(path) {
      const p = this.expand(path);
      if (!p) throw new Error('请填写文件路径');
      return await window.yingdao.fileExists(p);
    },
    // 生成不重名的路径：若 target 已存在，在名字后加递增数字（文件加在扩展名前），如 名字1.txt、名字2.txt
    async uniquePath(target) {
      let p = target;
      let i = 1;
      // 拆出扩展名
      const dir = p.replace(/[\\/][^\\/]*$/, '');
      const base = p.split(/[\\/]/).pop();
      const dot = base.lastIndexOf('.');
      const stem = dot > 0 ? base.slice(0, dot) : base;
      const ext = dot > 0 ? base.slice(dot) : '';
      while (await window.yingdao.fileExists(p)) {
        p = dir + '\\' + stem + i + ext;
        i++;
      }
      return p;
    },

    async fileMkdir(folder, name, content) {
      const f = this.expand(folder);
      const n = this.expand(name);
      if (!f) throw new Error('请填写「在哪个文件夹里新建」');
      // 支持多个名字，逗号分隔（中英文逗号都行），一次新建多个文件/文件夹
      const names = String(n || '').split(/[,，]/).map(s => s.trim()).filter(Boolean);
      if (!names.length) throw new Error('请填写「叫什么名字」');
      const results = [];
      for (const oneName of names) {
        const looksLikeFile = /\.[A-Za-z0-9]+$/.test(oneName);
        // 重名自动加递增数字（新建文件夹1、新建文件夹2 ...）
        const target = await this.uniquePath(f + '\\' + oneName);
        if (looksLikeFile) {
          const c = this.expand(content) || '';
          await window.yingdao.writeText(target, c);
        } else {
          await window.yingdao.mkdir(target);
        }
        results.push(target);
      }
      return results.length === 1 ? results[0] : results;
    },

    // 白话指令：一句大白话搞定文件操作（删除/复制/移动/列出），尽量少用变量
    // index 支持 "1"、"1,3,5,7"、"1-3"、"1-3,5,-1"（负数=倒数）；dst 用于复制/移动的目标
    async fileOp(action, folder, sortBy, order, index, dst) {
      const f = this.expand(folder);
      if (!f) throw new Error('请填写「哪个文件夹」');
      const sortKey = sortBy === '文件名' ? '字符' : sortBy;   // 归一化到 sortFileEntries 认识的 key
      // 列出文件名
      if (action === '列出文件名') {
        const list = await window.yingdao.listDir(f);
        const sorted = this.sortFileEntries(list, sortKey, order);
        return sorted.map(e => e.isDir ? '[目录] ' + e.name : e.name);
      }
      // 其余动作：解析多个文件（支持 1,3,5 / 1-3 / 1-3,5,-1）
      let files = await this.pickFilesFromDir(folder, sortKey, order, index);
      if (!files || !files.length) {
        // 没有索引表达式 → 当作单个文件路径直接用
        files = [f];
      }
      const results = [];
      for (const filePath of files) {
        if (action === '删除') {
          await window.yingdao.deleteFile(filePath);
          results.push(filePath);
        } else if (action === '复制') {
          const d = this.expand(dst);
          if (!d) throw new Error('请填写「复制到哪」');
          const realDst = await this.resolveCopyDst(filePath, d);
          await window.yingdao.copyFile(filePath, realDst);
          results.push(realDst);
        } else if (action === '移动') {
          const d = this.expand(dst);
          if (!d) throw new Error('请填写「移动到哪」');
          const realDst = await this.resolveCopyDst(filePath, d);
          await window.yingdao.moveFile(filePath, realDst);
          results.push(realDst);
        } else {
          throw new Error('未知操作：' + action);
        }
      }
      return results.length === 1 ? results[0] : results;
    },

    // 生成自动标识：数字序号/字母序号/日期
    makeTag(type, idx) {
      if (type === '数字序号') return String(idx);
      if (type === '字母序号') { let s = ''; let n = idx; while (n > 0) { const m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = Math.floor((n - 1) / 26); } return s || 'A'; }
      if (type === '日期') { const d = new Date(); const p = (x) => String(x).padStart(2, '0'); return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`; }
      return '';
    },

    // 白话重命名：加前缀/加后缀/替换文字/删除文字/按分隔符重组，支持多文件（index 可 1,3,5 / 1-3）
    async fileRename(folder, sortBy, order, index, mode, text, type, sep, parts, replacement = '') {
      const sortKey = sortBy === '文件名' ? '字符' : sortBy;
      const doRename = async (filePath, seq) => {
        const dir = filePath.replace(/[\\/][^\\/]*$/, '');
        const base = filePath.split(/[\\/]/).pop();          // 含扩展名的文件名
        const dot = base.lastIndexOf('.');
        const stem = dot > 0 ? base.slice(0, dot) : base;    // 去掉扩展名的主体
        const ext = dot > 0 ? base.slice(dot) : '';          // 扩展名（含点）

        // 标识内容：优先用自动类型（序号用 seq，支持批量连续编号），否则用 text
        let tag = this.expand(text) || '';
        if (type && type !== '自定义文字') tag = this.makeTag(type, seq >= 1 ? seq : 1);

        let newStem = stem;
        if (mode === '加前缀') newStem = tag + stem;
        else if (mode === '删前缀') {
          const t = this.expand(text) || '';
          newStem = t ? (stem.startsWith(t) ? stem.slice(t.length) : stem) : stem;
        }
        else if (mode === '加后缀') newStem = stem + tag;
        else if (mode === '删后缀') {
          const t = this.expand(text) || '';
          newStem = t ? (stem.endsWith(t) ? stem.slice(0, stem.length - t.length) : stem) : stem;
        }
        else if (mode === '替换文字') {
          const t = this.expand(text) || '';
          if (!t) throw new Error('请填写要替换的文字');
          newStem = stem.replaceAll(t, this.expand(replacement));
        }
        else if (mode === '删除文字') {
          const t = this.expand(text) || '';
          newStem = stem.split(t).join('');
        }
        else if (mode === '按分隔符重组') {
          const sp = this.expand(sep) || '_';
          const segs = stem.split(sp);
          const ps = String(parts || '').trim();
          if (ps) {
            const order = ps.split(/[,，\s]+/).map(x => parseInt(x, 10)).filter(n => !isNaN(n));
            const re = [];
            order.forEach(n => { if (n >= 1 && n <= segs.length) re.push(segs[n - 1]); });
            newStem = re.join(sp);
          }
        }
        const newName = newStem + ext;
        const newPath = dir + '\\' + newName;
        if (newPath === filePath) return filePath;   // 名字没变，跳过
        await window.yingdao.moveFile(filePath, newPath);
        return newPath;
      };

      // 解析多个文件（支持 1,3,5 / 1-3 / 1-3,5,-1）
      let files = await this.pickFilesFromDir(folder, sortKey, order, index);
      if (!files || !files.length) {
        files = [this.expand(folder)];   // 单个文件路径直接用
      }
      const results = [];
      for (let i = 0; i < files.length; i++) {
        // 序号：按在原排序里的真实位置（用 index 表达式的第 i 个值），单文件时用 index 本身
        let seq = i + 1;
        const idxs = this.parseIndexList(index);
        if (idxs.length && idxs[i] !== undefined) seq = idxs[i] >= 1 ? idxs[i] : seq;
        results.push(await doRename(files[i], seq));
      }
      return results.length === 1 ? results[0] : results;
    },

    // 白话查找：按文件名关键字 + 扩展名过滤，返回匹配的文件名列表
    async fileFind(folder, keyword, ext) {
      const f = this.expand(folder);
      if (!f) throw new Error('请填写「在哪个文件夹找」');
      const list = await window.yingdao.listDir(f);
      const kw = this.expand(keyword) || '';
      const ex = this.expand(ext) || '';
      let files = list.filter(e => e.isFile);
      if (kw) files = files.filter(e => e.name.toLowerCase().includes(kw.toLowerCase()));
      if (ex) files = files.filter(e => e.name.toLowerCase().endsWith('.' + ex.toLowerCase().replace(/^\./, '')));
      return files.map(e => e.name);
    },

    // 白话统计：统计文件夹文件个数和总大小（字节）
    async fileCount(folder, ext) {
      const f = this.expand(folder);
      if (!f) throw new Error('请填写「统计哪个文件夹」');
      const list = await window.yingdao.listDir(f);
      const ex = this.expand(ext) || '';
      let files = list.filter(e => e.isFile);
      if (ex) files = files.filter(e => e.name.toLowerCase().endsWith('.' + ex.toLowerCase().replace(/^\./, '')));
      const total = files.reduce((s, e) => s + (Number(e.size) || 0), 0);
      return { 文件个数: files.length, 总大小字节: total };
    },

    // ---- 指令执行器 ----
    async runCommand(cmd, ui) {
      // 每条指令开始前检查中断标记（点「停止」后不再执行后续指令）
      if (this.cancelRequested) throw new Error(ERR_STOP);
      const p = cmd.params || {};
      switch (cmd.id) {
        case 'openUrl': {
          const r = await this.openUrl(p.url, p.target, p.loginMode, p.engine, p.waitType !== '立即返回');
          if (p.waitType !== '立即返回') await this.waitPageReady();
          return r;
        }
        case 'click': return await this.click(p);
        case 'input': return await this.input(p);
        case 'getText': return await this.getText(p);
        case 'waitElement': return await this.waitElement(p);
        case 'waitPageReady': return await this.waitPageReady(p.timeout);
        case 'diagnosePage': {
          const d = await this.diagnosePage();
          if (d && ui && ui.log) {
            ui.log('页面诊断：readyState=' + (d.readyState || '?') +
              '｜iframe 数=' + (d.frameCount || 0) +
              '｜可点击元素=' + (d.clickableCount || 0) +
              '｜输入框=' + (d.inputCount || 0));
            if (d.frames && d.frames.length) ui.log('  子框架：' + d.frames.slice(0, 8).map(f => (f.id || f.name || '(无名字)') + ' → ' + f.src).join('；'));
            if (d.hints && d.hints.length) d.hints.forEach(h => ui.log('  提示：' + h, 'error'));
          }
          return d;
        }
        case 'clickXY': return await this.clickXY(p);
        case 'pickElement': return await B().pickElement();
        case 'scrapeText': return await this.scrapeText(p);
        case 'scrapeAttr': return await this.scrapeAttr(p);
        case 'scrapeList': return await this.scrapeList(p);
        case 'scrapeExport': return await this.scrapeExport(p);
        case 'sleep': return await this.sleepInterruptible(p.seconds || 1);
        case 'browserWait': return await this.sleepInterruptible(p.seconds || 1);
        case 'pressKey': return await this.pressKey(p);
        case 'clickSelectCopy': return await this.clickSelectAllCopy(p);
        case 'clickPaste': return await this.clickPaste(p);
        case 'extractTextToTable': {
          const r = await this.extractTextToTable(p);
          ui.log(r.msg);
          this.vars['提取结果路径'] = r.path;
          return { path: r.path, count: r.count };
        }
        case 'clipboardCopy': {
          const r = await this.clipboardCopy(p);
          ui.log('已复制到剪贴板：' + r.length + ' 个字符' + (r.preview ? '（' + r.preview.replace(/\s+/g, ' ') + '…）' : ''));
          return r;
        }
        case 'pasteToCell': {
          const r = await this.pasteToCell(p);
          ui.log(r.msg);
          this.vars['粘贴结果路径'] = r.path;
          return r;
        }
        case 'pasteToElement': {
          const r = await this.pasteToElement(p);
          ui.log(r);
          return r;
        }
        case 'setVar': this.vars[p.name] = this.expand(p.value); return;
        case 'printLog': ui.log(this.expand(p.text)); return;
        case 'typeText': return await this.typeText(p);
        case 'hotkey': return await this.hotkey(p);
        case 'mouseClick': return await this.mouseClick(p);
        case 'excelOpen': return await this.excelOpen(p.path);
        case 'excelNew': return await this.excelNew(p.path, p.sheetName);
        case 'excelRead': this.vars[p.varName] = this.excelRead(p.cell); return;
        case 'excelWrite': this.excelWrite(p.cell, p.value); return;
        case 'excelReadRange': this.vars[p.varName] = this.excelReadRange(p.range); return;
        case 'excelWriteRange': this.excelWriteRange(p.range, this.vars[p.data]); return;
        case 'excelCopyPaste': this.excelCopyPaste(p.from, p.to, p.mode); return;
        case 'excelSheetCopyPaste': this.excelSheetCopyPaste(p.fromBook, p.fromSheet, p.fromRange, p.toBook, p.toSheet, p.toRange, p.mode); return;
        case 'excelTableCopyPaste': {
          const r = await this.excelTableCopyPaste(p);
          this.vars['表格复制粘贴结果'] = r.path;
          ui.log(r.msg);
          return;
        }
        case 'excelInsertRow': this.excelInsertRow(p.row, p.count); return;
        case 'excelInsertCol': this.excelInsertCol(p.col, p.count); return;
        case 'excelDeleteRow': this.excelDeleteRow(p.row, p.count); return;
        case 'excelDeleteCol': this.excelDeleteCol(p.col, p.count); return;
        case 'excelGetRows': this.vars[p.varName] = this.excelGetRows(); return;
        case 'excelSave': return await this.excelSave(p.path);
        case 'excelSaveAs': {
          const r = await this.excelSaveAs({ naming: p.naming, prefix: this.expand(p.prefix), startIndex: p.startIndex });
          ui.log('已另存为：' + (r.written || []).map(x => x.split(/[\\/]/).pop()).join('、') + '（' + r.naming + '）');
          return r;
        }
        // ===== 文件操作 =====
        case 'fileReadText': this.vars[p.varName] = await this.fileReadText(p.path); return;
        case 'fileWriteText': await this.fileWriteText(p.path, p.content, p.append); return;
        case 'fileCopy': await this.fileCopy(p.src, p.dst, p.sortBy, p.order, p.index); return;
        case 'fileMove': await this.fileMove(p.src, p.dst); return;
        case 'fileDelete': await this.fileDelete(p.path, p.sortBy, p.order, p.index); return;
        case 'fileExists': this.vars[p.varName] = await this.fileExists(p.path); return;
        case 'fileMkdir': await this.fileMkdir(p.folder, p.name, p.content); return;
        case 'fileListDir': this.vars[p.varName] = await this.fileListDir(p.path, p.sortBy, p.order); return;
        case 'fileOp': this.vars[p.varName || '白话结果'] = await this.fileOp(p.action, p.folder, p.sortBy, p.order, p.index, p.dst); return;
        case 'fileRename': this.vars['重命名结果'] = await this.fileRename(p.folder, p.sortBy, p.order, p.index, p.mode, p.text, p.type, p.sep, p.parts, p.replacement); return;
        case 'fileFind': this.vars['查找结果'] = await this.fileFind(p.folder, p.keyword, p.ext); return;
        case 'fileCount': this.vars['统计结果'] = await this.fileCount(p.folder, p.ext); return;
        default:
          throw new Error(`未知指令「${cmd.name}」`);
      }
    }
  };

  window.Engine = Engine;
})();
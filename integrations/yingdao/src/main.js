const acRecorder = require('./ac-recorder');
const { app, BrowserWindow, ipcMain, dialog, screen, shell, session, clipboard } = require('electron');
const extBrowser = require('./ext-browser');   // 外部浏览器驱动（Edge / 便携版 Chrome，走 CDP）
const path = require('path');
const fs = require('fs');

app.setName('AnClickerRPA');
app.setPath('userData', process.env.ANCLICKER_RPA_DATA || path.join(app.getPath('appData'), 'AnClicker', 'rpa'));
const bridge = require('./ac-bridge-main');


let mainWindow = null;
let browserWindows = [];    // 独立浏览器窗口数组 [{ id, win }]
let activeBrowserId = null; // 当前激活的浏览器窗口 id
let excelEditors = [];       // 多个独立 Excel 编辑器窗口 [{ id, win, snapshot, embedded }]
let excelEditorSeq = 1;      // 编辑器窗口 id 自增
let excelWindows = [];       // 拖出的单个 sheet 独立窗口数组 [{ id, sheetId, win, sheetName }]
let excelSnapshot = null;    // Excel 数据快照 { path, sheetName, rows }
let browserIdSeq = 1;        // 浏览器窗口 id 自增
let excelWinSeq = 1;         // sheet 独立窗口 id 自增
const sheetDataStore = {};   // sheet 独立窗口数据存储（按 id 索引）

// ============ 主窗口尺寸记忆（打开时恢复上次最终大小/位置） ============
// 存到 userData 下的 JSON，主进程直接读写（界面那个分区持久化的是 localStorage，主进程够不着）
function settingsFile() {
  return path.join(app.getPath('userData'), 'window-state.json');
}
function loadWindowState() {
  try {
    const raw = fs.readFileSync(settingsFile(), 'utf-8');
    const o = JSON.parse(raw);
    if (o && Number.isFinite(o.width) && Number.isFinite(o.height)) return o;
  } catch (e) { }
  return null;
}
function saveWindowState(b) {
  try {
    const o = {
      x: b.x, y: b.y,
      width: b.width, height: b.height,
      maximized: b.maximized || false
    };
    fs.writeFileSync(settingsFile(), JSON.stringify(o), 'utf-8');
  } catch (e) { }
}
// 取一个"在屏幕内、不小于最小尺寸"的窗口尺寸（用户可能换过显示器/分辨率）
function safeWindowBounds(saved) {
  const minW = 1100, minH = 700;
  const dflt = { width: 1440, height: 900 };
  if (!saved) return dflt;
  let { x, y, width, height } = saved;
  width = Math.max(minW, Math.round(width));
  height = Math.max(minH, Math.round(height));
  // 校验是否落在某个显示器可见范围内（屏幕可能变少/分辨率变低）
  try {
    const displays = screen.getAllDisplays();
    const visible = displays.some(d => {
      const a = d.workArea;
      return x >= a.x - 200 && y >= a.y - 200 && x < a.x + a.width && y < a.y + a.height;
    });
    if (!visible) {
      const a = screen.getPrimaryDisplay().workArea;
      x = a.x + Math.round((a.width - width) / 2);
      y = a.y + Math.round((a.height - height) / 2);
    }
  } catch (e) { }
  return { x, y, width, height };
}

// ============ 页面内「生成稳健选择器」的 JS 片段（元素拾取 / 操作录制共用） ============
// 老版本只会生成 tag.class（取第一个 class），遇到动态类名、自动生成的 id 就永久失效，
// 或者生成 'div' 这种匹配到第一个 div 的假选择器 —— 这是"元素识别不出来"的另一半原因。
// 现在按「稳定 id → data-* → name/aria-label/placeholder → 稳定 class 组合 → nth-of-type 全路径」
// 依次尝试，并且每一步都用"在整页（含同源 iframe / 影子 DOM）里是否唯一"来校验。
const ROBUST_SELECTOR_JS = `
  function __qAll(sel) {
    var res = [], roots = [document], count = 0;
    (function walk(r, depth) {
      if (count++ > 40 || depth > 4) return;
      var fr = [];
      try { fr = Array.prototype.slice.call(r.querySelectorAll('iframe,frame')); } catch (e) { }
      for (var i = 0; i < fr.length; i++) {
        try { var d = fr[i].contentDocument; if (d) { roots.push(d); walk(d, depth + 1); } } catch (e) { }
      }
      var all = [];
      try { all = Array.prototype.slice.call(r.querySelectorAll('*')); } catch (e) { }
      for (var j = 0; j < all.length; j++) { if (all[j].shadowRoot) { roots.push(all[j].shadowRoot); walk(all[j].shadowRoot, depth + 1); } }
    })(document, 0);
    for (var k = 0; k < roots.length; k++) {
      try { res = res.concat(Array.prototype.slice.call(roots[k].querySelectorAll(sel))); } catch (e) { }
    }
    return res;
  }
  function __unique(sel) { try { return __qAll(sel).length === 1; } catch (e) { return false; } }
  function __esc(s) { return String(s).replace(/[^a-zA-Z0-9_-]/g, function (c) { return '\\\\' + c; }); }
  function __aq(v) { return String(v).replace(/\\\\/g, '\\\\\\\\').replace(/"/g, '\\\\"'); }
  // 框架自动生成的类名/id：带长串数字或哈希，用来定位迟早失效
  function __stable(s) {
    if (!s) return false;
    if (/^[0-9]/.test(s)) return false;
    if (/[0-9a-f]{6,}/i.test(s)) return false;
    if ((String(s).match(/[0-9]/g) || []).length >= 4) return false;
    return true;
  }
  function buildSelector(el) {
    if (!el || el.nodeType !== 1) return '';
    var tag = el.tagName.toLowerCase();
    if (el.id && __stable(el.id) && __unique('#' + __esc(el.id))) return '#' + __esc(el.id);
    var attrs = el.attributes || [];
    var i, n;
    for (i = 0; i < attrs.length; i++) {
      n = attrs[i].name;
      if (/^data-(id|name|key|test|role|type|code|value|index)$/i.test(n) && __stable(attrs[i].value)) {
        var s1 = tag + '[' + n + '="' + __aq(attrs[i].value) + '"]';
        if (__unique(s1)) return s1;
      }
    }
    var ATS = ['name', 'aria-label', 'placeholder', 'title', 'alt'];
    for (i = 0; i < ATS.length; i++) {
      var v = el.getAttribute && el.getAttribute(ATS[i]);
      if (v && __stable(v)) {
        var s2 = tag + '[' + ATS[i] + '="' + __aq(v) + '"]';
        if (__unique(s2)) return s2;
      }
    }
    var cls = (typeof el.className === 'string' ? el.className : '').trim().split(/\\s+/)
      .filter(function (c) { return c && __stable(c); });
    for (var len = 1; len <= Math.min(3, cls.length); len++) {
      for (var st = 0; st + len <= cls.length; st++) {
        var seg = cls.slice(st, st + len).map(function (c) { return '.' + __esc(c); }).join('');
        var s3 = tag + seg;
        if (__unique(s3)) return s3;
      }
    }
    // 兜底：从元素往上拼带 :nth-of-type 的全路径，保证唯一
    var parts = [], cur = el, guard = 0;
    while (cur && cur.nodeType === 1 && cur !== document.documentElement && guard++ < 12) {
      var t = cur.tagName.toLowerCase();
      var par = cur.parentElement;
      if (par) {
        var same = Array.prototype.slice.call(par.children).filter(function (c) { return c.tagName === cur.tagName; });
        if (same.length > 1) t += ':nth-of-type(' + (same.indexOf(cur) + 1) + ')';
      }
      parts.unshift(t);
      if (cur.id && __stable(cur.id)) { parts.unshift('#' + __esc(cur.id)); break; }
      cur = par;
    }
    return parts.join(' > ');
  }
`;

// 规范化 URL：空地址/纯 https:// 返回 about:blank，避免 ERR_INVALID_URL
function normalizeUrl(url) {
  if (!url || typeof url !== 'string') return 'about:blank';
  url = url.trim();
  if (!url || ['https://', 'http://', 'https://www.', 'about:blank'].includes(url)) return 'about:blank';
  if (!url.includes('://')) url = 'https://' + url;
  const parsed = new URL(url);
  if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('请输入 http 或 https 网页地址');
  if (['hao123', 'www.hao123'].includes(parsed.hostname.toLowerCase())) parsed.hostname = 'www.hao123.com';
  return parsed.href;
}

function createWindow() {
  const saved = safeWindowBounds(loadWindowState());
  mainWindow = new BrowserWindow({
    show: false,
    width: saved.width,
    height: saved.height,
    x: saved.x,
    y: saved.y,
    minWidth: 1100,
    minHeight: 700,
    title: '世博自动化',
    icon: path.join(__dirname, '..', 'icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      // 程序自身界面单独一个分区：这样"清空浏览器登录数据"永远不会碰到程序自己的设置
      partition: APP_PARTITION,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // 记住上次最终大小/位置：关闭/移动/缩放时都存
  const persistBounds = () => {
    try {
      if (mainWindow && !mainWindow.isDestroyed()) {
        saveWindowState({ ...mainWindow.getBounds(), maximized: mainWindow.isMaximized() });
      }
    } catch (e) { }
  };
  mainWindow.on('close', persistBounds);
  mainWindow.on('resize', () => { if (mainWindow && !mainWindow.isMaximized()) persistBounds(); });
  mainWindow.on('move', () => { if (mainWindow && !mainWindow.isMaximized()) persistBounds(); });

  mainWindow.loadFile(path.join(__dirname, 'ac-bridge.html'));
  bridge.attach(mainWindow);
  mainWindow.setMenuBarVisibility(false);
}

// ============ 浏览器多账号：会话隔离 ============
// 每个浏览器窗口 = 一个独立的登录会话，互不串号，这样同一个网站可以同时登多个账号。
//
//   独立登录(每次全新)      → 全新内存会话（关窗即清空，绝不残留）  ← 默认
//   独立登录(按账号位保存)  → 依次占用账号位 1、2、3…，各自把登录数据存到磁盘，
//                            适合"固定几个账号天天复用"；关掉窗口后账号位会被释放，
//                            下次开窗仍从账号位1开始
//   共用登录(沿用已有登录)  → 所有窗口共享一份登录（旧行为，单账号场景用）
const LOGIN_MODE = {
  CLEAN: '独立登录(每次全新)',
  SLOT: '独立登录(按账号位保存)',
  SHARED: '共用登录(沿用已有登录)'
};
const LOGIN_MODE_LIST = [LOGIN_MODE.CLEAN, LOGIN_MODE.SLOT, LOGIN_MODE.SHARED];
const ACCOUNT_SLOT_MAX = 20;        // 账号位上限
const APP_PARTITION = 'persist:yd-app';   // 程序自身界面用的分区（与浏览器完全隔离）

let browserSessionSeq = 0;          // 全新会话自增（进程内唯一）

// ============ 浏览器引擎：内置(自带内核) / Edge / 内置Chrome ============
// 选外部引擎时，所有浏览器操作改由 CDP 驱动一个真实浏览器完成（Edge 与 Chrome 同协议）
let browserEngine = '内置';
let extLaunchInfo = null;

function exeDirPath() {
  try { return path.dirname(app.getPath('exe')); } catch (e) { return ''; }
}
// 当前是否在用外部浏览器
function extOn() {
  return browserEngine !== '内置' && extBrowser.isRunning();
}

// 引擎别名归一化：用户说「Chrome」= 内置 Chromium 内核；「Edge」= 外部 Edge。
// 内置Chrome 是便携版 Chrome（供无 Edge 的老系统机器当备用内核），三者都映射到统一 key。
function normalizeEngineKey(k) {
  const s = String(k || '');
  if (!s || s === '跟随' || s === '自动' || s === '默认' || s === '跟随当前') return '';
  if (/^chrome/i.test(s) || s === '内置' || s === 'Chrome') return '内置';
  if (/^edge/i.test(s) || s === 'Edge') return 'Edge';
  if (s === '内置Chrome') return '内置Chrome';
  return s;
}

// 把引擎切到指定 key（内部用，setEngine / loadURL 都走这里）
async function switchEngineTo(key) {
  const want = normalizeEngineKey(key);
  if (!want) return { ok: true, engine: browserEngine, note: '保持当前引擎' };
  if (want === browserEngine) return { ok: true, engine: browserEngine, note: '已是该引擎' };
  if (want === '内置') {
    if (extBrowser.isRunning()) await extBrowser.close();
    extLaunchInfo = null;
    browserEngine = '内置';
    return { ok: true, engine: browserEngine, note: '已切回 Chrome 内核（内置 Chromium）' };
  }
  const found = extBrowser.findBrowsers({ appDir: exeDirPath() });
  const target = found.find(b => b.kind === want);
  if (!target) {
    return {
      ok: false, engine: browserEngine,
      err: want === 'Edge'
        ? '这台电脑没找到 Edge（msedge.exe）。朗坤 6.5 这类老系统需要 Edge 内核，请先安装 Edge。'
        : '包里没找到便携版 Chrome（应在 浏览器备用版\\<版本>\\chrome-win64\\chrome.exe）'
    };
  }
  if (extBrowser.isRunning()) await extBrowser.close();
  try {
    extLaunchInfo = await extBrowser.launch({ exePath: target.path, kind: want, url: 'about:blank' });
    browserEngine = want;
    return { ok: true, engine: browserEngine, info: extLaunchInfo };
  } catch (e) {
    extLaunchInfo = null;
    browserEngine = '内置';
    return { ok: false, engine: browserEngine, err: e.message };
  }
}

// 当前被占用的账号位
function usedAccountSlots() {
  const s = new Set();
  browserWindows.forEach(b => { if (b.slot) s.add(b.slot); });
  return s;
}

// 取最小空闲账号位（用满则返回 null）
function nextFreeAccountSlot() {
  const used = usedAccountSlots();
  for (let i = 1; i <= ACCOUNT_SLOT_MAX; i++) if (!used.has(i)) return i;
  return null;
}

// 按登录方式算出一个窗口的会话信息
function makeSession(mode) {
  if (mode === LOGIN_MODE.SHARED) {
    // partition 传 null = 用默认会话（所有"共用登录"窗口共享同一份登录）
    return { partition: null, slot: null, badge: '共用' };
  }
  if (mode === LOGIN_MODE.SLOT) {
    const slot = nextFreeAccountSlot();
    if (slot) return { partition: 'persist:yd-acc-' + slot, slot, badge: '账号位' + slot };
    // 账号位用满 → 退化成全新会话，至少保证不串号
  }
  browserSessionSeq++;
  return { partition: 'yd-tmp-' + Date.now() + '-' + browserSessionSeq, slot: null, badge: '新会话#' + browserSessionSeq };
}

// 创建新的独立浏览器窗口
// 多个浏览器窗口彼此错开摆放：否则新窗口完全盖住旧窗口，看起来像"只开了一个"
function createBrowserWindow(url, loginMode) {
  const id = 'b' + (browserIdSeq++);
  const mode = LOGIN_MODE_LIST.includes(loginMode) ? loginMode : LOGIN_MODE.CLEAN;
  const ses = makeSession(mode);
  const W = 1180, H = 760;
  const webPreferences = {
    nodeIntegration: false,
    contextIsolation: true,
    preload: path.join(__dirname, 'browser-preload.js')
  };
  // 不设 partition = 跟默认会话共用；设了就是独立会话
  if (ses.partition) webPreferences.partition = ses.partition;
  const win = new BrowserWindow({
    width: W,
    height: H,
    title: '极速网页AC',
    icon: path.join(__dirname, '..', 'icon.ico'),
    webPreferences
  });
  win.setMenuBarVisibility(false);

  // 错开定位（以主窗口右上角为基准向右下阶梯排列，并保证不超出屏幕）
  try {
    const wa = screen.getPrimaryDisplay().workAreaSize;
    let bx = 120, by = 60;
    if (mainWindow && !mainWindow.isDestroyed()) {
      const mb = mainWindow.getBounds();
      bx = mb.x + 80; by = mb.y + 60;
    }
    const n = browserWindows.length % 6;          // 阶梯步进
    let x = bx + n * 32, y = by + n * 32;
    x = Math.max(0, Math.min(x, Math.max(0, wa.width - W - 8)));
    y = Math.max(0, Math.min(y, Math.max(0, wa.height - H - 8)));
    win.setBounds({ x: Math.round(x), y: Math.round(y), width: W, height: H });
  } catch (e) { }

  const wc = win.webContents;
  // Use Chromium's desktop identity; Electron's app token makes some sites
  // redirect a desktop window to a mobile/offline landing page.
  wc.setUserAgent(wc.getUserAgent().replace(/\s(?:Electron|anclicker-rpa-runtime|AnClickerRPA)\/[^\s]+/gi, ''));
  acRecorder.attach(wc);
  // 转发导航事件给主应用渲染进程（带窗口 id）
  wc.on('did-navigate', (_e, url) => {
    if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('browser:navigated', { id, url });
  });
  wc.on('did-fail-load', (_e, code, desc, url) => {
    if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('browser:loadFailed', { id, code, desc, url });
  });
  wc.on('page-title-updated', (e, title) => {
    // 不让页面标题直接覆盖窗口标题：把会话标记保留在标题里，方便区分多个窗口
    e.preventDefault();
    try { win.setTitle('极速网页AC'); } catch (err) { }
    if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('browser:titleUpdated', { id, title });
  });
  // 注入录制脚本 + 悬浮工具栏（工具栏上显示会话标记）
  wc.on('did-finish-load', () => {
    // Recording is opt-in via the isolated preload and ac-recorder.
    injectFloatingToolbar(wc, id, ses.badge);
  });

  // 窗口获得焦点时，标记为激活
  win.on('focus', () => { activeBrowserId = id; });
  // 窗口关闭时，从数组移除
  win.on('closed', () => {
    const idx = browserWindows.findIndex(b => b.id === id);
    if (idx !== -1) browserWindows.splice(idx, 1);
    if (activeBrowserId === id) {
      activeBrowserId = browserWindows.length ? browserWindows[browserWindows.length - 1].id : null;
    }
    // 通知主应用刷新任务栏
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('browser:windowClosed', { id });
    }
  });

  browserWindows.push({ id, win, slot: ses.slot, badge: ses.badge, mode, partition: ses.partition });
  activeBrowserId = id;
  // 新窗口立刻通知主应用刷新任务栏（不等页面加载，加载失败也能出现在任务栏里）
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('browser:navigated', { id, url: normalizeUrl(url), badge: ses.badge });
  }

  // 加载目标网址（无效/空地址用 about:blank）
  const targetUrl = normalizeUrl(url);
  if (targetUrl !== 'about:blank') {
    wc.loadURL(targetUrl).catch(() => {});
  }

  return { id, win, badge: ses.badge };
}

// 获取当前激活的浏览器窗口
function getActiveBrowser() {
  if (!browserWindows.length) return null;
  const found = browserWindows.find(b => b.id === activeBrowserId);
  return found || browserWindows[browserWindows.length - 1];
}

// 切换激活窗口（聚焦对应窗口）
function activateBrowserWindow(id) {
  const target = browserWindows.find(b => b.id === id);
  if (!target) return null;
  activeBrowserId = id;
  if (target.win && !target.win.isDestroyed()) {
    if (target.win.isMinimized()) target.win.restore();
    target.win.focus();
  }
  return target;
}

// 关闭窗口
function closeBrowserWindow(id) {
  const idx = browserWindows.findIndex(b => b.id === id);
  if (idx === -1) return null;
  const { win } = browserWindows[idx];
  if (win && !win.isDestroyed()) win.close();
  browserWindows.splice(idx, 1);
  if (activeBrowserId === id) {
    activeBrowserId = browserWindows.length ? browserWindows[browserWindows.length - 1].id : null;
  }
  return browserWindows.length;
}

// 兼容旧的 ensureBrowserView（返回激活窗口，或新建一个独立窗口）
function ensureBrowserWindow() {
  if (getActiveBrowser()) return getActiveBrowser().win;
  return createBrowserWindow('about:blank', LOGIN_MODE.CLEAN).win;
}

// 向浏览器视图注入录制脚本（监听 click / input 事件，存入全局数组）
function injectRecordScript(wc) {
  const script = `
    (function () {
      if (window.__rpaRecordInjected) return;
      window.__rpaRecordInjected = true;
      window.__rpaEvents = window.__rpaEvents || [];

      ${ROBUST_SELECTOR_JS}

      document.addEventListener('click', function (e) {
        const el = e.target.closest('a,button,input,select,textarea,[role=button],[onclick]') || e.target;
        const selector = buildSelector(el);
        const text = (el.innerText || el.value || el.tagName || '').trim().slice(0, 40);
        window.__rpaEvents.push({ type: 'click', selector: selector, text: text });
      }, true);

      document.addEventListener('input', function (e) {
        const el = e.target;
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
          const selector = buildSelector(el);
          window.__rpaEvents.push({ type: 'input', selector: selector, text: el.value });
        }
      }, true);

      // 键盘输入录制：组合键 → hotkey；普通键 → typeText
      document.addEventListener('keydown', function (e) {
        // 忽略修饰键本身
        if (['Control','Shift','Alt','Meta'].includes(e.key)) return;
        const mods = [];
        if (e.ctrlKey) mods.push('Ctrl');
        if (e.shiftKey) mods.push('Shift');
        if (e.altKey) mods.push('Alt');
        if (e.metaKey) mods.push('Meta');
        if (mods.length > 0) {
          // 组合键 → 快捷键
          const key = e.key.length === 1 ? e.key.toUpperCase() : e.key;
          const keys = mods.concat([key]).join('+');
          window.__rpaEvents.push({ type: 'hotkey', keys: keys });
        } else if (e.key.length === 1 && !e.target.closest('input,textarea,select,[contenteditable=true]')) {
          // 非输入框的普通按键 → 模拟按键
          window.__rpaEvents.push({ type: 'typeText', text: e.key });
        }
      }, true);

      // 页面跳转/加载标记：用于录制"等待"
      window.__rpaPageLoading = false;
      document.addEventListener('beforeunload', function () {
        window.__rpaEvents.push({ type: 'pageLoad', note: '页面跳转' });
      }, true);
    })();
  `;
  wc.executeJavaScript(script, true).catch(() => {});
}

// 向独立浏览器窗口注入悬浮工具栏（后退/前进/刷新/地址栏/缩放）
// badge：会话标记（账号位1 / 新会话#2 / 共用），显示在工具栏最左边，方便一眼区分多个窗口
function injectFloatingToolbar(wc, id, badge) {
  const install = require('./ac-toolbar');
  wc.executeJavaScript('(' + install.toString() + ')(' + wc.getZoomLevel() + ')', true).catch(() => {});
}

// 元素拾取：注入选择模式脚本，返回 Promise<{ selector, by, text }>
let pickResolve = null;

// 拾取脚本源码（注入到主文档 + 所有子框架，这样 iframe 里的元素也能拾取）
function pickScriptSource() {
  return `
    (function () {
      // 清掉旧状态
      window.__rpaPicked = undefined;
      window.__rpaPickActive = true;

      // 移除旧遮罩（如果还在）
      const old = document.getElementById('__rpa_pick_overlay');
      if (old) old.remove();
      // 移除旧高亮
      const all = document.querySelectorAll('[style*="outline"]');
      all.forEach(el => { el.style.outline = ''; el.style.outlineOffset = ''; });

      // 创建遮罩 + 提示
      const overlay = document.createElement('div');
      overlay.id = '__rpa_pick_overlay';
      overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;padding:10px 14px;background:#4a6cf7;color:#fff;font:14px/1.4 system-ui;z-index:2147483647;box-shadow:0 2px 10px rgba(0,0,0,.3);text-align:center;';
      overlay.innerHTML = '🎯 <b>元素拾取模式</b>：点击目标元素  |  按 ESC 取消';
      document.body.appendChild(overlay);

      // hover 高亮
      let lastHover = null;
      function highlight(el) {
        if (lastHover === el) return;
        if (lastHover) lastHover.style.outline = '';
        lastHover = el;
        if (el) {
          el.style.outline = '2px dashed #4a6cf7';
          el.style.outlineOffset = '-2px';
        }
      }

      ${ROBUST_SELECTOR_JS}
      function buildXPath(el) {
        if (!el || el === document.body) return '';
        if (el.id) return '//*[@id="' + el.id + '"]';
        const parts = [];
        let cur = el;
        while (cur && cur.nodeType === 1 && cur !== document.body) {
          let part = cur.tagName.toLowerCase();
          const parent = cur.parentElement;
          if (parent) {
            const sameTag = [...parent.children].filter(c => c.tagName === cur.tagName);
            if (sameTag.length > 1) part += '[' + (sameTag.indexOf(cur) + 1) + ']';
          }
          parts.unshift(part);
          cur = parent;
        }
        return '//' + parts.join('/');
      }

      // 阻止真实点击
      function block(e) { e.preventDefault(); e.stopPropagation(); }

      document.addEventListener('mousemove', function (e) {
        highlight(e.target);
      }, true);

      document.addEventListener('click', function (e) {
        const el = e.target;
        block(e);
        const css = buildSelector(el);
        const xp = buildXPath(el);
        const text = (el.innerText || el.value || '').trim().slice(0, 60);
        // 清理
        if (lastHover) lastHover.style.outline = '';
        overlay.remove();
        window.__rpaPickActive = false;
        window.__rpaPicked = { css, xpath: xp, text };
      }, true);

      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          if (lastHover) lastHover.style.outline = '';
          overlay.remove();
          window.__rpaPickActive = false;
          window.__rpaPicked = null;
        }
      }, true);
    })();
  `;
}

// 兼容旧调用：往当前激活窗口（含所有子框架）注入拾取脚本
function injectPickScript() {
  const win = ensureBrowserWindow();
  injectAllFrames(win.webContents, pickScriptSource());
}

// 把一段脚本注入到「主文档 + 所有子框架」（framesInSubtree 连跨域 iframe 也拿得到），
// 这样用户在 iframe 里点元素也能被拾取到 —— 只注入主文档的话 iframe 内部完全无感。
async function injectAllFrames(wc, script) {
  let frames = [];
  try { frames = (wc.mainFrame && wc.mainFrame.framesInSubtree) || []; } catch (e) { frames = []; }
  if (!frames.length) { try { await wc.executeJavaScript(script, true); } catch (e) { } return; }
  await Promise.all(frames.map(f => f.executeJavaScript(script, true).catch(() => { })));
}

// 在「主文档 + 所有子框架」里求值，返回第一个有意义的结果；
// 全都没值时返回最后一次的 null（用于区分"取消了"）
async function readAllFrames(wc, expr) {
  let frames = [];
  try { frames = (wc.mainFrame && wc.mainFrame.framesInSubtree) || []; } catch (e) { frames = []; }
  if (!frames.length) return await wc.executeJavaScript(expr, true).catch(() => undefined);
  let fallback;
  for (const f of frames) {
    const r = await f.executeJavaScript(expr, true).catch(() => undefined);
    if (r !== undefined && r !== null) return r;
    if (r !== undefined) fallback = r;
  }
  return fallback;
}

// 拾取元素：注入脚本 + 轮询检测用户操作（支持在 iframe 里点选）
async function pickElement() {
  // 外部浏览器（Edge / 便携Chrome）：注入到所有框架，再逐框架读结果
  if (extOn()) {
    await extBrowser.injectAll('(() => { window.__rpaPicked = undefined; return true; })()');
    await extBrowser.injectAll(pickScriptSource());
    for (let i = 0; i < 100; i++) {
      await new Promise(r => setTimeout(r, 500));
      if (!extBrowser.isRunning()) return { canceled: true };
      const picked = await extBrowser.readAllFrames('window.__rpaPicked').catch(() => undefined);
      if (picked === null) return { canceled: true };
      if (picked) return { canceled: false, css: picked.css, xpath: picked.xpath, text: picked.text };
    }
    return { canceled: true };
  }
  const win = ensureBrowserWindow();
  const wc = win.webContents;
  // 清空之前的状态
  await injectAllFrames(wc, '(() => { window.__rpaPicked = undefined; return true; })()');
  await injectAllFrames(wc, pickScriptSource());

  // 轮询直到用户点击或取消
  for (let i = 0; i < 100; i++) { // 最多等 50 秒
    await new Promise(r => setTimeout(r, 500));
    if (win.isDestroyed()) return { canceled: true };
    const picked = await readAllFrames(wc, 'window.__rpaPicked');
    if (picked === null) return { canceled: true };
    if (picked) return { canceled: false, css: picked.css, xpath: picked.xpath, text: picked.text };
  }
  return { canceled: true };
}

// 抓取拾取：进入拾取模式，用户点选元素后自动抓取文本（单个 + 同类全部），回传结果
async function pickForScrape() {
  const win = ensureBrowserWindow();
  const wc = win.webContents;
  // 进入拾取模式（注入到所有子框架，iframe 里的元素也能点选）
  await injectAllFrames(wc, '(() => { window.__rpaPicked = undefined; return true; })()');
  await injectAllFrames(wc, pickScriptSource());

  // 轮询等待用户点选
  let picked = null;
  for (let i = 0; i < 100; i++) {
    await new Promise(r => setTimeout(r, 500));
    if (win.isDestroyed()) return { canceled: true };
    picked = await readAllFrames(wc, 'window.__rpaPicked');
    if (picked === null) return { canceled: true };
    if (picked) break;
  }
  if (!picked) return { canceled: true };

  // 根据拾取的选择器，抓取单个文本 + 同类全部文本（在所有框架里找，取第一个有结果的）
  const css = picked.css;
  const esc = css.replace(/'/g, "\\'");
  const scrapeScript = `(() => {
    const sel = '${esc}';
    const one = document.querySelector(sel);
    const all = document.querySelectorAll(sel);
    if (!all.length) return null;
    return {
      text: one ? (one.innerText || one.value || one.textContent || '').trim().slice(0, 200) : '',
      count: all.length,
      samples: Array.from(all).slice(0, 20).map(e => (e.innerText || e.value || e.textContent || '').trim().slice(0, 100))
    };
  })()`;
  const data = await readAllFrames(wc, scrapeScript);
  if (!data) return { canceled: true };
  return {
    canceled: false,
    css: picked.css,
    xpath: picked.xpath,
    text: data.text,
    count: data.count,
    samples: data.samples || []
  };
}

// ============ 坐标拾取（多点，最多 9 个）============
// 在浏览器窗口叠一层拾取层：鼠标移动实时显示坐标、点击记一个点并在页面上标序号，
// 已标的点还能拖着微调；Backspace 撤销一个，ESC 或点「完成」结束。
function pointPickScriptSource(maxPoints) {
  return `
    (function () {
      const MAX = ${maxPoints};
      const oldOv = document.getElementById('__rpa_pointpick');
      if (oldOv) oldOv.remove();
      window.__rpaPoints = window.__rpaPoints || [];
      window.__rpaPointsDone = false;

      const bar = document.getElementById('__rpa_toolbar');
      if (bar) bar.style.display = 'none';

      const ov = document.createElement('div');
      ov.id = '__rpa_pointpick';
      ov.style.cssText = 'position:fixed;left:0;top:0;right:0;bottom:0;z-index:2147483647;cursor:crosshair;background:transparent;';
      document.documentElement.appendChild(ov);

      // 十字准线（跟随鼠标，方便精确定位）
      const vline = document.createElement('div');
      vline.style.cssText = 'position:fixed;top:0;bottom:0;width:1px;background:#e74c3c;opacity:.7;pointer-events:none;';
      const hline = document.createElement('div');
      hline.style.cssText = 'position:fixed;left:0;right:0;height:1px;background:#e74c3c;opacity:.7;pointer-events:none;';
      ov.appendChild(vline); ov.appendChild(hline);

      const panel = document.createElement('div');
      panel.style.cssText = 'position:absolute;left:12px;top:12px;font:13px/1.7 system-ui;background:#fff;border:1px solid #d0d8e8;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.2);padding:10px 12px;min-width:280px;cursor:default;';
      panel.innerHTML = '<div style="font-weight:600;color:#4a6cf7;margin-bottom:4px">🎯 坐标拾取（最多 ' + MAX + ' 个点）</div>'
        + '<div>当前坐标：<b id="__pp_xy" style="color:#e74c3c">-</b></div>'
        + '<div>已选：<b id="__pp_n">0</b> 个<span id="__pp_list" style="color:#666"></span></div>'
        + '<div style="color:#888;font-size:12px;margin-top:4px">点击页面记点 · 已标的点可拖动微调 · Backspace 撤销 · ESC 结束</div>'
        + '<div style="margin-top:8px;display:flex;gap:6px">'
        + '<button id="__pp_done" style="flex:1;padding:5px 10px;border:1px solid #4a6cf7;background:#eef2ff;color:#4a6cf7;border-radius:5px;cursor:pointer;font-weight:600">完成</button>'
        + '<button id="__pp_clear" style="padding:5px 10px;border:1px solid #d0d8e8;background:#fff;border-radius:5px;cursor:pointer">清空</button>'
        + '</div>';
      ov.appendChild(panel);
      panel.addEventListener('click', function (e) { e.stopPropagation(); });
      panel.addEventListener('mousedown', function (e) { e.stopPropagation(); });

      function sync() {
        var pts = window.__rpaPoints;
        panel.querySelector('#__pp_n').textContent = pts.length;
        panel.querySelector('#__pp_list').textContent = pts.length
          ? '：' + pts.map(function (p, i) { return (i + 1) + '(' + p.x + ',' + p.y + ')'; }).join(' ')
          : '';
      }
      function renderMarks() {
        Array.prototype.slice.call(ov.querySelectorAll('[data-mark]')).forEach(function (c) { c.remove(); });
        window.__rpaPoints.forEach(function (p, i) {
          var m = document.createElement('div');
          m.setAttribute('data-mark', '1');
          m.setAttribute('data-idx', String(i));
          // 记录点时的滚动位置也存了，这里按滚动量补偿，标注就"粘"在页面内容上
          var dx = window.scrollX - (p.sx || 0), dy = window.scrollY - (p.sy || 0);
          m.style.cssText = 'position:fixed;width:24px;height:24px;margin:-12px 0 0 -12px;border-radius:50%;'
            + 'background:#e74c3c;color:#fff;font:600 12px/24px system-ui;text-align:center;'
            + 'box-shadow:0 1px 6px rgba(0,0,0,.4);cursor:move;user-select:none;'
            + 'left:' + (p.x - dx) + 'px;top:' + (p.y - dy) + 'px;';
          m.textContent = String(i + 1);
          m.title = '拖动可微调，当前 ' + p.x + ',' + p.y;
          ov.appendChild(m);
        });
      }
      function setXY(x, y) {
        panel.querySelector('#__pp_xy').textContent = Math.round(x) + ', ' + Math.round(y);
        vline.style.left = Math.round(x) + 'px';
        hline.style.top = Math.round(y) + 'px';
      }
      function addPoint(x, y) {
        if (window.__rpaPoints.length >= MAX) return;
        window.__rpaPoints.push({ x: Math.round(x), y: Math.round(y), sx: window.scrollX, sy: window.scrollY });
        renderMarks(); sync();
      }
      function finish() {
        window.__rpaPointsDone = true;
        ov.remove();
        if (bar) bar.style.display = '';
      }

      var dragIdx = -1;
      ov.addEventListener('mousemove', function (e) {
        if (dragIdx >= 0) {
          var p = window.__rpaPoints[dragIdx];
          if (p) {
            p.x = Math.round(e.clientX); p.y = Math.round(e.clientY);
            p.sx = window.scrollX; p.sy = window.scrollY;
            renderMarks(); sync();
          }
        }
        setXY(e.clientX, e.clientY);
      });
      ov.addEventListener('mousedown', function (e) {
        var t = e.target;
        e.preventDefault(); e.stopPropagation();
        if (t && t.getAttribute && t.getAttribute('data-idx') !== null) dragIdx = Number(t.getAttribute('data-idx'));
      }, true);
      ov.addEventListener('mouseup', function (e) { e.preventDefault(); e.stopPropagation(); dragIdx = -1; }, true);
      ov.addEventListener('click', function (e) {
        e.preventDefault(); e.stopPropagation();
        if (dragIdx >= 0) return;
        var t = e.target;
        if (t && t.getAttribute && t.getAttribute('data-idx') !== null) return;   // 点的是标注本身，不算新点
        addPoint(e.clientX, e.clientY);
      }, true);
      ov.addEventListener('contextmenu', function (e) { e.preventDefault(); e.stopPropagation(); }, true);
      ov.addEventListener('wheel', function (e) { e.stopPropagation(); }, true);

      panel.querySelector('#__pp_done').addEventListener('click', finish);
      panel.querySelector('#__pp_clear').addEventListener('click', function () {
        window.__rpaPoints = []; renderMarks(); sync();
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') { e.preventDefault(); finish(); }
        else if (e.key === 'Backspace') { e.preventDefault(); window.__rpaPoints.pop(); renderMarks(); sync(); }
      }, true);
      window.addEventListener('scroll', renderMarks, true);

      setXY(0, 0); sync();
    })();
  `;
}

// 往内置窗口注入坐标拾取层（外部浏览器走 injectAll）
function injectPointPickScript(wc, maxPoints) {
  wc.executeJavaScript(pointPickScriptSource(maxPoints), true).catch(() => { });
}

// 进入坐标拾取模式，等用户点完返回点列表（最多 5 分钟）
async function pickPoints(maxPoints = 9) {
  // 外部浏览器（Edge / 便携Chrome）：注入拾取层脚本 + 逐框架轮询结果
  if (extOn()) {
    await extBrowser.injectAll('(() => { window.__rpaPoints = []; window.__rpaPointsDone = false; return true; })()');
    await extBrowser.injectAll(pointPickScriptSource(maxPoints));
    for (let i = 0; i < 600; i++) {
      await new Promise(r => setTimeout(r, 500));
      if (!extBrowser.isRunning()) return { canceled: true };
      const st = await extBrowser.readAllFrames('({ done: !!window.__rpaPointsDone, points: (window.__rpaPoints || []).map(function(p){ return { x: p.x, y: p.y }; }) })').catch(() => null);
      if (st && st.done) {
        const pts = st.points || [];
        if (!pts.length) return { canceled: true };
        return { canceled: false, points: pts, count: pts.length };
      }
    }
    return { canceled: true };
  }
  const win = ensureBrowserWindow();
  const wc = win.webContents;
  await wc.executeJavaScript('(() => { window.__rpaPoints = []; window.__rpaPointsDone = false; return true; })()', true).catch(() => { });
  injectPointPickScript(wc, maxPoints);
  for (let i = 0; i < 600; i++) {
    await new Promise(r => setTimeout(r, 500));
    if (win.isDestroyed()) return { canceled: true };
    const st = await wc.executeJavaScript(
      '({ done: !!window.__rpaPointsDone, points: (window.__rpaPoints || []).map(function(p){ return { x: p.x, y: p.y }; }) })',
      true).catch(() => null);
    if (st && st.done) {
      const pts = st.points || [];
      if (!pts.length) return { canceled: true };
      return { canceled: false, points: pts, count: pts.length };
    }
  }
  return { canceled: true };
}

// ============ 把流程 json 拖到 exe 上直接打开 ============
// 两种情形都要管：
//   1) 程序没在跑：把 json 拖到 exe 图标上 → 文件路径会作为启动参数传进来
//   2) 程序已经在跑：拖上去会再启动一个进程，靠单实例锁交给第一个实例处理（second-instance）
let pendingFlowPath = null;

// 从命令行参数里挑出 .json 文件（跳过 -- 开头的开关和 exe 自身路径）
function findFlowJsonArg(argv) {
  const list = Array.isArray(argv) ? argv : [];
  for (const a of list) {
    if (!a || typeof a !== 'string') continue;
    if (a.startsWith('--') || a.startsWith('-')) continue;
    if (!/\.json$/i.test(a)) continue;
    try { if (fs.existsSync(a) && fs.statSync(a).isFile()) return a; } catch (e) { }
  }
  return null;
}

function readTextSafe(p) {
  try { return fs.readFileSync(p, 'utf-8'); } catch (e) { return ''; }
}

// 把 json 交给界面打开；界面还没就绪就先记下来，等它来取
function pushFlowToRenderer(file) {
  if (!file) return;
  const payload = { path: file, content: readTextSafe(file) };
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('flow:open', payload);
    try {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    } catch (e) { }
  } else {
    pendingFlowPath = file;
  }
}

// 界面就绪后来取"启动时拖进来的那个 json"
ipcMain.handle('flow:getPending', () => {
  const p = pendingFlowPath;
  pendingFlowPath = null;
  if (!p) return null;
  return { path: p, content: readTextSafe(p) };
});

// 单实例锁：把 json 拖到 exe 上时会再起一个进程，交给已经在跑的那个实例来打开文件
const singleInstanceLock = true;
if (!singleInstanceLock) {
  app.quit();
} else {
  app.on('second-instance', (_e, argv) => {
    const file = findFlowJsonArg(argv);
    if (file) { pushFlowToRenderer(file); return; }        // 拖进来的 json → 当前实例打开它
    if (mainWindow && !mainWindow.isDestroyed()) {          // 只是重复启动 → 把已有窗口叫到前面
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  // 首次启动就带着 json（把文件拖到 exe 图标上）→ 先记下，界面就绪后来取
  pendingFlowPath = findFlowJsonArg(process.argv);

  app.whenReady().then(() => {
    createWindow();
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
  });
}

// ============ 系统剪贴板 ============
// 给"复制到剪贴板 / 粘贴到单元格 / 粘贴到网页元素"这套组合用
ipcMain.handle('clipboard:write', (_e, text) => {
  clipboard.writeText(String(text == null ? '' : text));
  return true;
});
ipcMain.handle('clipboard:read', () => {
  try { return clipboard.readText(); } catch (e) { return ''; }
});

// ============ 文件对话框 ============
ipcMain.handle('dialog:openFile', async () => {
  const res = await dialog.showOpenDialog(mainWindow, {
    title: '选择文件',
    properties: ['openFile'],
    filters: [
      { name: 'Excel 文件', extensions: ['xlsx', 'xls', 'csv'] },
      { name: '所有文件', extensions: ['*'] }
    ]
  });
  if (res.canceled) return null;
  return res.filePaths[0];
});

ipcMain.handle('dialog:saveFile', async (_e, defaultName) => {
  const name = String(defaultName || '');
  const spreadsheetLike = /\.(xlsx|xls|csv|txt|ods|html|json)$/i.test(name);
  const res = await dialog.showSaveDialog(mainWindow, {
    title: '保存文件',
    defaultPath: name || '流程.json',
    filters: spreadsheetLike
      ? [
          { name: 'Excel 工作簿 (*.xlsx)', extensions: ['xlsx'] },
          { name: 'Excel 97-2003 (*.xls)', extensions: ['xls'] },
          { name: 'CSV 逗号分隔 (*.csv)', extensions: ['csv'] },
          { name: '文本 - 制表符 (*.txt)', extensions: ['txt'] },
          { name: 'OpenDocument (*.ods)', extensions: ['ods'] },
          { name: '网页表格 (*.html)', extensions: ['html'] },
          { name: 'JSON 数据 (*.json)', extensions: ['json'] },
          { name: '所有文件', extensions: ['*'] }
        ]
      : [
          { name: '流程文件', extensions: ['json'] },
          { name: '所有文件', extensions: ['*'] }
        ]
  });
  if (res.canceled) return null;
  return res.filePath;
});

// 选择文件夹（通用：目录路径参数 / 导出可运行程序都用）
ipcMain.handle('dialog:openDir', async (_e, title) => {
  const res = await dialog.showOpenDialog(mainWindow, {
    title: String(title || '选择文件夹'),
    properties: ['openDirectory', 'createDirectory']
  });
  if (res.canceled) return null;
  return res.filePaths[0];
});

// 定位便携 node.exe（纯离线，不依赖目标机预装 Node）
// 查找顺序：exe 同级 -> resources/node -> 开发树 23332 -> 环境变量 PATH
// 说明：不能直接用 process.execPath（那是 Electron 外壳，不是纯 node）
function resolvePortableNode() {
  const cands = [];
  const push = (p) => { if (p) cands.push(p); };
  let exeDir = '';
  try { exeDir = path.dirname(app.getPath('exe')); } catch (e) { }
  const res = process.resourcesPath || '';

  // 1) 程序自带：exe 同级 / resources\node / resources
  try { push(path.join(exeDir, 'node.exe')); } catch (e) { }
  // 2) 成品包与"程序"目录两种常见摆法
  push(path.join(res, 'node', 'node.exe'));
  push(path.join(res, 'node.exe'));
  push(path.join(exeDir, 'resources', 'node', 'node.exe'));
  push(path.join(exeDir, 'resources', 'node.exe'));
  // 3) 被放进便携包时：<包根>\程序\世博自动化.exe 旁边就是 <包根>\浏览器备用版 等同级目录，
  //    也兼容 <包根>\resources\node\node.exe
  if (exeDir) {
    push(path.join(exeDir, '..', 'resources', 'node', 'node.exe'));
    push(path.join(exeDir, '..', '..', 'resources', 'node', 'node.exe'));
  }
  // 4) 开发树：<项目根>/../23332/4_Node环境/node.exe（app.getAppPath() 打包后指向 app.asar）
  try { push(path.join(app.getAppPath(), '..', '..', '23332', '4_Node环境', 'node.exe')); } catch (e) { }
  push(path.join(__dirname, '..', '..', '23332', '4_Node环境', 'node.exe'));
  // 5) 系统装了 Node 也能用
  if (process.env.ProgramFiles) push(path.join(process.env.ProgramFiles, 'nodejs', 'node.exe'));
  if (process.env['ProgramFiles(x86)']) push(path.join(process.env['ProgramFiles(x86)'], 'nodejs', 'node.exe'));
  if (process.env.LOCALAPPDATA) push(path.join(process.env.LOCALAPPDATA, 'Programs', 'nodejs', 'node.exe'));
  if (process.env.APPDATA) push(path.join(process.env.APPDATA, 'npm', 'node.exe'));

  for (const p of cands) {
    try { if (p && fs.existsSync(p)) return p; } catch (e) { }
  }
  // 兜底：PATH 上的 node
  try {
    const r = require('child_process').spawnSync('where', ['node'], { encoding: 'utf-8', windowsHide: true });
    if (r && r.status === 0) {
      const first = String(r.stdout || '').split(/\r?\n/).map(s => s.trim()).filter(Boolean)[0];
      if (first && fs.existsSync(first)) return first;
    }
  } catch (e) { }
  return null;
}

// ============ 浏览器引擎切换（内置 / Edge / 内置Chrome）============
// Edge 和 Chrome 是同一套 Chromium 内核 + 同一套 CDP 协议，所以换 Edge 后
// 所有元素操作、点击、输入、按键、抓取都是同一套代码在跑，行为一致。
ipcMain.handle('browser:listEngines', async () => {
  const found = extBrowser.findBrowsers({ appDir: exeDirPath() });
  const edge = found.find(b => b.kind === 'Edge');
  const chrome = found.find(b => b.kind === '内置Chrome');
  return {
    current: browserEngine,
    running: extBrowser.isRunning(),
    info: extLaunchInfo,
    engines: [
      { key: '内置', label: 'Chrome（程序自带内核）', available: true, path: '' },
      { key: 'Edge', label: 'Edge' + (edge ? '' : '（这台电脑没装）'), available: !!edge, path: edge ? edge.path : '' },
      { key: '内置Chrome', label: 'Chrome便携版' + (chrome ? '' : '（包里没有）'), available: !!chrome, path: chrome ? chrome.path : '' }
    ]
  };
});

ipcMain.handle('browser:setEngine', async (_e, key) => {
  return await switchEngineTo(key);
});

// 导出流程为双击可运行程序：生成 运行流程.bat + runner.js + flow.json + 便携 node + xlsx
ipcMain.handle('export:flowRunner', async (_e, payload) => {
  const flow = (payload && payload.flow) || [];
  const flowName = String((payload && payload.name) || '流程').replace(/[\\/:*?"<>|]/g, '_');
  const baseDir = (payload && payload.dir) || app.getPath('desktop');
  const outDir = path.join(baseDir, flowName);
  fs.mkdirSync(outDir, { recursive: true });

  // 1. 写 flow.json
  fs.writeFileSync(path.join(outDir, 'flow.json'), JSON.stringify(flow, null, 2), 'utf-8');

  // 2. 复制 runner.js（源码里已写好）
  const srcRunner = path.join(__dirname, 'flow-runner.js');
  fs.copyFileSync(srcRunner, path.join(outDir, 'runner.js'));

  // 3. 复制便携 node.exe（多路径探测；找不到时由 bat 给出明确中文提示，不再静默生成坏脚本）
  const nodeSrc = resolvePortableNode();
  let nodeCopied = false;
  if (nodeSrc) {
    try { fs.copyFileSync(nodeSrc, path.join(outDir, 'node.exe')); nodeCopied = true; } catch (e) { }
  }

  // 4. 复制 xlsx 依赖：直接把程序内置的 xlsx.full.min.js 写到导出目录（930KB 左右）
  //    为什么不用 node_modules/xlsx：asar 内 cpSync 整目录不可靠，且 npm 包还带 8 个二级
  //    依赖（adler-32/cfb/codepage/...），漏一个就 require 失败。浏览器版单文件更稳，
  //    配合 runner 里的 "读Buffer/写Buffer" 适配，读写行为与 Node 版一致。
  let hasXlsx = false;
  try {
    fs.writeFileSync(path.join(outDir, 'xlsx.full.min.js'),
                     fs.readFileSync(path.join(__dirname, 'lib', 'xlsx.full.min.js')));
    hasXlsx = true;
  } catch (e) { }

  // 5. 写运行流程.bat
  //    有便携 node 就直接用（目标机零依赖）；没有的话先找同目录的 node.exe，
  //    再找"程序\resources\node\node.exe"，再看系统 PATH，最后才报错并给出可操作指引。
  //    这样即使导出时本机没找到 node，用户把 exe 扔进目录里也能直接跑起来。
  const nodeCmd = nodeCopied
    ? '"%~dp0node.exe" runner.js\r\n'
    : [
        'set "YD_NODE=%~dp0node.exe"',
        'if exist "%YD_NODE%" goto yd_run',
        'set "YD_NODE=%~dp0..\\..\\程序\\resources\\node\\node.exe"',
        'if exist "%YD_NODE%" goto yd_run',
        'set "YD_NODE=%~dp0..\\resources\\node\\node.exe"',
        'if exist "%YD_NODE%" goto yd_run',
        'where node >nul 2>nul',
        'if not errorlevel 1 (',
        '  echo [提示] 本文件夹没有 node.exe，改用系统已装的 Node 运行。',
        '  echo.',
        '  node runner.js',
        '  goto yd_done',
        ')',
        'echo.',
        'echo [!] 这个流程需要 node.exe 才能运行，但没找到。',
        'echo.',
        'echo     三种解决办法（任选一种）：',
        'echo     1) 把主程序目录里的  resources\\node\\node.exe  复制到本文件夹',
        'echo        （与"运行流程.bat"放在一起），再重新双击本文件；',
        'echo     2) 把本文件夹放到便携包里形如  程序\\xx流程\\  的位置，会自动找到；',
        'echo     3) 装上 Node.js（https://nodejs.org）后重新双击本文件（需联网）。',
        'echo.',
        'pause',
        'exit /b 1',
        ':yd_run',
        '"%YD_NODE%" runner.js',
        ':yd_done',
        ''
      ].join('\r\n');
  const bat = `@echo off\r\nchcp 65001 >nul\r\ntitle ${flowName}\r\ncd /d "%~dp0"\r\n${nodeCmd}echo.\r\necho 流程已结束，按任意键关闭...\r\npause >nul\r\n`;
  fs.writeFileSync(path.join(outDir, '运行流程.bat'), bat, 'utf-8');

  return {
    dir: outDir,
    hasNode: nodeCopied,
    nodeFrom: nodeSrc || '',
    nodeHint: nodeCopied ? '' : (nodeSrc ? '找到了 node 但复制失败（目标目录可能无写入权限）'
      : '本机没找到 node.exe：已生成手动放置说明，导出的流程仍可在目标机补上 node.exe 后运行'),
    hasXlsx: hasXlsx
  };
});

// ============ 系统路径 ============
ipcMain.handle('app:getDesktopPath', () => {
  return app.getPath('desktop');
});

// 打开文件/文件夹（日志右键用）
ipcMain.handle('shell:openPath', async (_e, p) => {
  const err = await shell.openPath(p);
  return { ok: !err, err: err || '' };
});
ipcMain.handle('shell:showInFolder', (_e, p) => {
  shell.showItemInFolder(p);
  return true;
});

// ============ 文件读写 ============
ipcMain.handle('fs:readFile', async (_e, filePath) => {
  const buf = await fs.promises.readFile(filePath);
  return buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
});

ipcMain.handle('fs:readText', async (_e, filePath) => {
  return await fs.promises.readFile(filePath, 'utf-8');
});

ipcMain.handle('fs:writeText', async (_e, filePath, content) => {
  await fs.promises.writeFile(filePath, content, 'utf-8');
  return true;
});

ipcMain.handle('fs:writeFile', async (_e, filePath, arrayBuffer) => {
  const buf = Buffer.from(arrayBuffer);
  await fs.promises.writeFile(filePath, buf);
  return true;
});

// ============ 文件操作（复制/移动/删除/重命名/存在判断/新建文件夹/列出目录） ============
ipcMain.handle('fs:copy', async (_e, src, dst) => {
  await fs.promises.copyFile(src, dst);
  return true;
});
ipcMain.handle('fs:move', async (_e, src, dst) => {
  await fs.promises.rename(src, dst);
  return true;
});
ipcMain.handle('fs:delete', async (_e, filePath) => {
  await fs.promises.unlink(filePath);
  return true;
});
ipcMain.handle('fs:exists', async (_e, filePath) => {
  try { await fs.promises.access(filePath); return true; } catch (e) { return false; }
});
ipcMain.handle('fs:mkdir', async (_e, dirPath) => {
  await fs.promises.mkdir(dirPath, { recursive: true });
  return true;
});
ipcMain.handle('fs:listDir', async (_e, dirPath) => {
  const entries = await fs.promises.readdir(dirPath, { withFileTypes: true });
  const out = [];
  for (const e of entries) {
    const full = path.join(dirPath, e.name);
    let size = 0, mtime = 0, birthtime = 0;
    try {
      const st = await fs.promises.stat(full);
      size = st.size; mtime = st.mtimeMs; birthtime = st.birthtimeMs;
    } catch (err) { }
    out.push({ name: e.name, isDir: e.isDirectory(), isFile: e.isFile(), size, mtime, birthtime, path: full });
  }
  return out;
});

// ============ 独立浏览器窗口控制 ============

// 打开网址：target='新窗口'/'新标签页' 时新建独立窗口，否则在激活窗口中打开
// loginMode：新窗口的登录方式（独立登录/共用登录），决定该窗口用哪个会话
// engine：可选，指定用哪个内核（Chrome / Edge / 跟随当前）。朗坤 6.5 等老系统需要 Edge。
ipcMain.handle('browser:loadURL', async (_e, url, target, loginMode, engine, waitForLoad = true) => {
  const norm = normalizeUrl(url);
  if (norm === 'about:blank') throw new Error('请填写完整网页地址');
  // 指定了内核就先切过去（没指定就保持当前引擎）
  const ek = normalizeEngineKey(engine);
  if (ek && ek !== browserEngine) {
    const sw = await switchEngineTo(ek);
    if (!sw.ok) throw new Error(sw.err || '浏览器内核启动失败');
  }
  if (extOn()) {
    const r = await extBrowser.navigate(norm, target);
    return { id: r.id, url: r.url, badge: browserEngine };
  }
  const wantNew = target === '新窗口' || target === '新标签页' || target === 'new';
  let targetWin = wantNew ? createBrowserWindow('about:blank', loginMode) : getActiveBrowser();
  if (!targetWin) targetWin = createBrowserWindow('about:blank', loginMode);
  // Await the actual navigation, not the initial blank document.
  const navigation = targetWin.win.webContents.loadURL(norm);
  if (waitForLoad) await navigation;
  else navigation.catch(() => {});
  return { id: targetWin.id, url: waitForLoad ? targetWin.win.webContents.getURL() : norm, badge: targetWin.badge };
});

// 新建独立窗口并打开网址（每个网页 = 一个独立窗口、独立登录会话）
ipcMain.handle('browser:newTab', async (_e, url, loginMode) => {
  if (extOn()) {
    const r = await extBrowser.createTarget(normalizeUrl(url));
    return { id: r.id, url: r.url, badge: browserEngine };
  }
  const tab = createBrowserWindow(url, loginMode);
  return { id: tab.id, url: tab.win.webContents.getURL(), badge: tab.badge };
});

// 切换/聚焦窗口
ipcMain.handle('browser:switchTab', async (_e, id) => {
  if (extOn()) { const r = await extBrowser.switchTarget(id); return { id: r.id }; }
  const target = activateBrowserWindow(id);
  return { id: target ? target.id : null };
});

// 关闭窗口
ipcMain.handle('browser:closeTab', async (_e, id) => {
  if (extOn()) { const n = await extBrowser.closeTarget(id); return { remaining: n }; }
  const remaining = closeBrowserWindow(id);
  return { remaining: remaining };
});

// 获取所有窗口信息（含登录会话标记，便于区分多个账号窗口）
ipcMain.handle('browser:getTabs', async () => {
  if (extOn()) {
    const pages = await extBrowser.listPages();
    return pages.map(p => ({ id: p.id, url: p.url, title: p.title, badge: browserEngine, mode: browserEngine, slot: null }));
  }
  return browserWindows.map(b => {
    let url = '', title = '';
    try { url = b.win.webContents.getURL(); title = b.win.webContents.getTitle(); } catch (e) {}
    return { id: b.id, url, title, badge: b.badge || '', mode: b.mode || '', slot: b.slot || null };
  });
});

// ============ 清空浏览器登录数据（多账号切换前清理残留） ============
// 会清掉：共用会话的历史登录数据 + 全部账号位的登录数据 + 当前已打开的独立窗口的会话数据。
// 注意：程序自身界面用的是 persist:yd-app 分区，不受影响。
ipcMain.handle('browser:clearData', async () => {
  // 外部浏览器：直接删掉它的数据目录再重建（最彻底）
  if (extOn() || browserEngine !== '内置') {
    const r = await extBrowser.clearData({ restart: browserEngine !== '内置' });
    if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('browser:dataCleared', { cleared: [browserEngine + '（' + r.note + '）'] });
    return { ok: true, cleared: [browserEngine], count: 1, note: r.note };
  }
  const storages = ['cookies', 'localstorage', 'indexdb', 'websql',
                    'cachestorage', 'serviceworkers', 'shadercache', 'filesystem'];
  const cleared = [];
  const done = new Set();

  const clearOne = async (ses, name) => {
    if (!ses || done.has(ses)) return;
    done.add(ses);
    try {
      await ses.clearStorageData({ storages });
      await ses.clearCache();
      if (ses.clearAuthCache) await ses.clearAuthCache();
      if (ses.clearHostResolverCache) ses.clearHostResolverCache();
      cleared.push(name);
    } catch (e) { }
  };

  // 1) 共用会话：以前所有窗口共用一份登录，登录残留基本都在这
  await clearOne(session.defaultSession, '共用会话');
  // 2) 账号位 1..N（磁盘上的持久会话）
  for (let i = 1; i <= ACCOUNT_SLOT_MAX; i++) {
    await clearOne(session.fromPartition('persist:yd-acc-' + i), '账号位' + i);
  }
  // 3) 当前已打开的独立窗口（内存会话，清完这些窗口就退出登录了）
  for (const b of browserWindows) {
    try { await clearOne(b.win.webContents.session, '窗口' + (b.badge || b.id)); } catch (e) { }
  }

  // 通知主界面刷新任务栏
  if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('browser:dataCleared', { cleared });
  return { ok: true, cleared, count: cleared.length };
});

// 当前登录方式选项（给界面下拉用）
ipcMain.handle('browser:getLoginModes', () => LOGIN_MODE_LIST.slice());

// 后退/前进/刷新（作用于激活窗口）
ipcMain.handle('browser:back', async () => {
  if (extOn()) return await extBrowser.back();
  const active = getActiveBrowser();
  if (active && active.win.webContents.canGoBack()) active.win.webContents.goBack();
  return true;
});
ipcMain.handle('browser:forward', async () => {
  if (extOn()) return await extBrowser.forward();
  const active = getActiveBrowser();
  if (active && active.win.webContents.canGoForward()) active.win.webContents.goForward();
  return true;
});
ipcMain.handle('browser:reload', async () => {
  if (extOn()) return await extBrowser.reload();
  const active = getActiveBrowser();
  if (active) active.win.webContents.reload();
  return true;
});

// 在浏览器窗口里执行 JS（核心：DOM 自动化）
// 加超时保护：页面加载失败/卡死时 executeJavaScript 可能永不返回，导致流程假死
ipcMain.handle('browser:execJS', async (_e, jsCode, timeoutMs) => {
  if (extOn()) return await extBrowser.execJS(jsCode, timeoutMs);
  const active = getActiveBrowser() || createBrowserWindow('about:blank', LOGIN_MODE.CLEAN);
  const limit = Math.max(1000, Number(timeoutMs) || 30000);
  return await Promise.race([
    active.win.webContents.executeJavaScript(jsCode, true),
    new Promise((_res, rej) => setTimeout(() => rej(new Error('页面脚本执行超时（可能是页面未加载成功）')), limit))
  ]);
});

// 把一段 JS 依次丢进「主文档 + 所有子框架」执行，直到某个框架给出"有意义"的结果。
// 为什么需要：跨域 iframe 里的元素，主文档的 document.querySelector 永远找不到，
// 必须把同一段脚本丢进那个 iframe 自己执行。判断规则：抛异常 / 返回假值 / 返回空数组 = 这个框架里没有目标。
// 注意：只适合"找不到就抛错或返回假值"的脚本（元素定位、点击、输入这类），不要塞有副作用的脚本。
ipcMain.handle('browser:execJSFrames', async (_e, jsCode, timeoutMs) => {
  if (extOn()) return await extBrowser.execJSFrames(jsCode, timeoutMs);
  const active = getActiveBrowser() || createBrowserWindow('about:blank', LOGIN_MODE.CLEAN);
  const wc = active.win.webContents;
  const limit = Math.max(1000, Number(timeoutMs) || 30000);
  let frames = [];
  try { frames = (wc.mainFrame && wc.mainFrame.framesInSubtree) || []; } catch (e) { frames = []; }
  if (!frames.length) {
    return await Promise.race([
      wc.executeJavaScript(jsCode, true),
      new Promise((_res, rej) => setTimeout(() => rej(new Error('页面脚本执行超时（可能是页面未加载成功）')), limit))
    ]);
  }
  const meaningful = (r) => {
    if (r === false || r === null || r === undefined || r === '' || r === 0) return false;
    if (Array.isArray(r) && r.length === 0) return false;
    return true;
  };
  let lastErr = null;
  for (const f of frames) {
    try {
      const r = await Promise.race([
        f.executeJavaScript(jsCode, true),
        new Promise((_res, rej) => setTimeout(() => rej(new Error('页面脚本执行超时（可能是页面未加载成功）')), limit))
      ]);
      if (meaningful(r)) return r;
    } catch (e) { lastErr = e; }
  }
  if (lastErr) throw lastErr;
  return false;
});

// 在浏览器里发"真实按键"（回车等）。
// 为什么不用页面内合成 KeyboardEvent：合成事件 isTrusted=false，不会触发浏览器的默认行为，
// 例如"在输入框里按回车提交表单"就永远不会发生。sendInputEvent 发的是真实输入，兼容性最好。
//
// 三个必须处理的坑（都是实测踩出来的）：
//   1) 窗口没显示 / 没聚焦时按键会丢 → 先 show + focus
//   2) 窗口重新获得焦点时 Chromium 会把页面里的焦点重置成 body → 按键打到 body 上，
//      "输入框里按回车"会失效 → 聚焦窗口前记住焦点元素，聚焦后还回去
//   3) 回车/Tab/空格这类"字符类按键"的默认行为挂在 char 事件上，只发 keyDown/keyUp 不触发
//      → 要补一个 char 事件（实测：不补 char 时回车提交表单不生效）
async function sendKeyToActiveWindow(key, times, modifiers) {
  const KEY_CHAR = { 'Enter': '\r', 'Tab': '\t', 'Space': ' ' };
  const mods = (Array.isArray(modifiers) ? modifiers : []).filter(Boolean);
  const active = getActiveBrowser();
  if (!active) throw new Error('没有打开的浏览器窗口');
  const win = active.win;
  const wc = win.webContents;
  const n = Math.max(1, Math.min(20, Number(times) || 1));

  await wc.executeJavaScript('(() => { window.__rpaFocusKeeper = document.activeElement; return true; })()', true).catch(() => { });
  try {
    if (!win.isVisible()) win.show();
    if (win.isMinimized()) win.restore();
    win.focus();
  } catch (e) { }
  try { wc.focus(); } catch (e) { }
  await new Promise(r => setTimeout(r, 150));
  // 把焦点还给刚才那个元素（不然回车会打到 body 上）
  await wc.executeJavaScript(`(() => {
    const el = window.__rpaFocusKeeper;
    if (el && el.focus && document.activeElement !== el) { try { el.focus(); } catch (e) { } }
    return (document.activeElement && (document.activeElement.id || document.activeElement.tagName)) || '';
  })()`, true).catch(() => { });

  for (let i = 0; i < n; i++) {
    const down = { type: 'keyDown', keyCode: key };
    const up = { type: 'keyUp', keyCode: key };
    if (mods.length) { down.modifiers = mods; up.modifiers = mods; }
    wc.sendInputEvent(down);
    // 带修饰键时不补 char —— Ctrl+A 不该往输入框里插一个 'a'
    if (!mods.length && (key.length === 1 || key === 'Space')) await wc.insertText(key === 'Space' ? ' ' : key);
    else if (!mods.length && KEY_CHAR[key]) wc.sendInputEvent({ type: 'char', keyCode: KEY_CHAR[key] });
    wc.sendInputEvent(up);
    await new Promise(r => setTimeout(r, 80));
  }
  return (mods.length ? mods.join('+') + '+' : '') + key + ' x' + n;
}

ipcMain.handle('browser:sendKey', async (_e, key, times, modifiers) => {
  if (extOn()) return await extBrowser.sendKey(key, times, modifiers);
  return await sendKeyToActiveWindow(key, times, modifiers);
});

// 获取当前 URL / 标题
ipcMain.handle('browser:getURL', async () => {
  if (extOn()) return await extBrowser.currentUrl();
  const active = getActiveBrowser();
  return active ? active.win.webContents.getURL() : '';
});
ipcMain.handle('browser:getTitle', async () => {
  if (extOn()) return await extBrowser.currentTitle();
  const active = getActiveBrowser();
  return active ? active.win.webContents.getTitle() : '';
});

// 缩放相关
let browserZoomLevel = 0; // 0 = 100%

// Ctrl+滚轮缩放（由 browser-preload 通过 ipcRenderer.send 触发）
ipcMain.on('browser:zoomBy', (_e, delta) => {
  const active = browserWindows.find(b=>b.win.webContents===_e.sender);
  const wc = active ? active.win.webContents : null;
  if (!wc) return;
  browserZoomLevel = Math.min(4, Math.max(-3, wc.getZoomLevel() + delta));
  wc.setZoomLevel(browserZoomLevel);
  wc.send('ac:zoomLevel',browserZoomLevel);
  // 回传缩放百分比给主应用渲染进程
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('browser:zoomChanged', Math.round(wc.getZoomFactor() * 100));
  }
});

// 直接设置缩放级别（渲染进程调用）
ipcMain.handle('browser:setZoomLevel', (_e, level) => {
  const active = getActiveBrowser();
  const wc = active ? active.win.webContents : null;
  if (!wc) return browserZoomLevel;
  browserZoomLevel = Math.min(4, Math.max(-3, level));
  wc.setZoomLevel(browserZoomLevel);
  return browserZoomLevel;
});

// 重置缩放为 100%
ipcMain.handle('browser:resetZoom', () => {
  browserZoomLevel = 0;
  const active = getActiveBrowser();
  const wc = active ? active.win.webContents : null;
  if (wc) wc.setZoomLevel(0);
  return 0;
});

// ============ 浏览器窗口操作（悬浮工具栏动作 / 全屏 / 最大化） ============

// 悬浮工具栏动作（来自独立窗口的 ipcRenderer.send）
ipcMain.on('browser:toolbarAction', (e, action) => {
  // 找到发送动作的窗口
  const sender = e.sender;
  const item = browserWindows.find(b => b.win.webContents === sender);
  if (!item) return;
  const wc = item.win.webContents;
  if (['back','forward','reload'].includes(action) || action.startsWith('navigate:')) acRecorder.markNavigation(wc);
  if(action.startsWith('navigate:')) { const url=normalizeUrl(action.slice(9));if(/^https?:/.test(url))wc.loadURL(url).catch(()=>{}); }
  else if (action === 'back') { if (wc.canGoBack()) wc.goBack(); }
  else if (action === 'forward') { if (wc.canGoForward()) wc.goForward(); }
  else if (action === 'reload') { wc.reload(); }
  else if (action === 'close') { item.win.close(); }
  else if (action === 'scrape') {
    // 摘取元素：进入拾取模式，点选后抓取文本并回传主应用
    activeBrowserId = item.id;
    pickForScrape().then(r => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('browser:scrapePicked', r);
      }
    });
  }
  else if (action.startsWith('zoom:')) {
    const lvl = parseFloat(action.split(':')[1]);
    if (!isNaN(lvl)) { wc.setZoomLevel(lvl); wc.send('ac:zoomLevel',lvl); }
  }
});

// 抓取拾取（供主应用主动调用）
ipcMain.handle('browser:pickForScrape', async () => {
  return await pickForScrape();
});

// 全屏切换（作用于激活窗口）
ipcMain.handle('browser:toggleFullscreen', () => {
  const active = getActiveBrowser();
  if (active && !active.win.isDestroyed()) {
    active.win.setFullScreen(!active.win.isFullScreen());
    return active.win.isFullScreen();
  }
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.setFullScreen(!mainWindow.isFullScreen());
    return mainWindow.isFullScreen();
  }
  return false;
});

// 最大化切换（作用于激活窗口）
ipcMain.handle('browser:maximize', () => {
  const active = getActiveBrowser();
  if (active && !active.win.isDestroyed()) {
    if (active.win.isMaximized()) active.win.unmaximize();
    else active.win.maximize();
    return true;
  }
  return false;
});

// 读取并清空浏览器录制的操作事件（作用于激活窗口）
ipcMain.handle('browser:consumeEvents', async () => {
  const win = ensureBrowserWindow();
  const events = await win.webContents.executeJavaScript(
    '(() => { const e = window.__rpaEvents || []; window.__rpaEvents = []; return e; })()',
    true
  );
  return events || [];
});

// 兼容：popout/embed/isPoppedOut 现在都是独立窗口，直接返回成功
ipcMain.handle('browser:popout', () => {
  const active = getActiveBrowser();
  if (active) { active.win.focus(); }
  return { poppedOut: true };
});
ipcMain.handle('browser:embed', () => ({ poppedOut: false }));
ipcMain.handle('browser:togglePopout', () => ({ poppedOut: true }));
ipcMain.handle('browser:isPoppedOut', () => true);

// 元素拾取：用户在浏览器里点击目标元素，自动返回选择器
ipcMain.handle('browser:pickElement', async () => {
  return await pickElement();
});

// 坐标拾取（多点）：在浏览器里点几个点，返回这些点的坐标
ipcMain.handle('browser:pickPoints', async (_e, maxPoints) => {
  return await pickPoints(Number(maxPoints) || 9);
});

// ============ Excel 编辑器弹出为独立窗口 ============

// 弹出 Excel 编辑器为独立窗口（可同时打开多个：每个表格各自一个窗口）
function popoutExcel(snapshot) {
  const snap = Object.assign({}, snapshot || {});
  const id = 'x' + (excelEditorSeq++);
  const W = 560, H = 720;
  const fileName = snap.path ? path.basename(snap.path) : '未命名表格';
  const win = new BrowserWindow({
    width: W,
    height: H,
    title: '世博自动化 Excel - ' + fileName,
    icon: path.join(__dirname, '..', 'icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });
  win.setMenuBarVisibility(false);
  excelSnapshot = snap;                       // 兼容无 sender 场景的兜底快照

  const rec = { id, win, snapshot: snap, embedded: false };
  excelEditors.push(rec);

  // 位置：完全独立窗口，不跟随主窗口。
  // 首次摆放在主窗口右侧，之后记住用户拖到的位置，新窗口在此基础上阶梯错开
  {
    const n = excelEditors.length - 1;
    const saved = loadExcelPos();
    let x = 140, y = 80;
    if (saved && Number.isFinite(saved.x) && Number.isFinite(saved.y)) {
      x = saved.x + n * 34; y = saved.y + n * 34;
    } else if (mainWindow && !mainWindow.isDestroyed()) {
      const b = mainWindow.getBounds();
      x = b.x + b.width + 6; y = b.y;
    }
    const pos = clampToWorkArea(x, y, W, H);
    try { win.setBounds({ x: pos.x, y: pos.y, width: W, height: H }); } catch (e) { }
  }

  // 用户拖动/缩放后记住位置（下次打开沿用）
  const remember = () => {
    if (win.isDestroyed() || win.isMinimized()) return;
    try { saveExcelPos(win.getBounds()); } catch (e) { }
  };
  win.on('moved', remember);
  win.on('resized', remember);
  win.on('close', remember);      // 兜底：关闭前也记住位置（不依赖 moved 事件平台差异）

  win.on('closed', () => {
    const i = excelEditors.findIndex(e => e.id === id);
    if (i !== -1) excelEditors.splice(i, 1);
    // 通知主应用：哪个编辑器关了、是否点了「嵌入回去」
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('excel:standaloneClosed', {
        editorId: id,
        bookId: rec.snapshot ? rec.snapshot.bookId : null,
        embedded: !!rec.embedded
      });
    }
  });

  win.loadFile(path.join(__dirname, 'excel-standalone.html'));
  return { ok: true, id: id };
}

// 按发起请求的窗口反查编辑器记录
function findExcelEditor(sender) {
  return excelEditors.find(e => e.win && !e.win.isDestroyed() && e.win.webContents === sender) || null;
}

// ---- Excel 编辑器窗口的位置记忆（窗口完全独立：不跟随主窗口，位置由用户决定）----
function excelPosFile() { return path.join(app.getPath('userData'), 'excel-window.json'); }
function loadExcelPos() {
  try { return JSON.parse(fs.readFileSync(excelPosFile(), 'utf8')); } catch (e) { return null; }
}
function saveExcelPos(bounds) {
  try { fs.writeFileSync(excelPosFile(), JSON.stringify(bounds)); } catch (e) { }
}
// 单 sheet 窗口的位置记忆（独立文件，避免与编辑器窗口互相覆盖）
function sheetPosFile() { return path.join(app.getPath('userData'), 'sheet-window.json'); }
function loadSheetPos() {
  try { return JSON.parse(fs.readFileSync(sheetPosFile(), 'utf8')); } catch (e) { return null; }
}
function saveSheetPos(bounds) {
  try { fs.writeFileSync(sheetPosFile(), JSON.stringify(bounds)); } catch (e) { }
}
function clampToWorkArea(x, y, w, h) {
  try {
    const wa = screen.getPrimaryDisplay().workAreaSize;
    return {
      x: Math.round(Math.max(0, Math.min(x, Math.max(0, wa.width - w - 8)))),
      y: Math.round(Math.max(0, Math.min(y, Math.max(0, wa.height - h - 8))))
    };
  } catch (e) { return { x: Math.round(x), y: Math.round(y) }; }
}

ipcMain.handle('excel:popout', (_e, snapshot) => {
  return popoutExcel(snapshot);
});

// 获取 Excel 数据快照（按窗口返回各自的数据，支持多窗口）
ipcMain.handle('excel:getSnapshot', (e) => {
  const rec = findExcelEditor(e.sender);
  return rec ? rec.snapshot : excelSnapshot;
});

// 更新 Excel 数据快照（独立窗口编辑后回写）
ipcMain.on('excel:setSnapshot', (e, snapshot) => {
  const rec = findExcelEditor(e.sender);
  if (rec) rec.snapshot = Object.assign({}, rec.snapshot, snapshot);
  else excelSnapshot = snapshot;
  // 带上 bookId，主应用才能把改动写回同一张表格（否则每改一次就多出一个标签、原表格不更新）
  const payload = Object.assign({}, rec ? rec.snapshot : snapshot, { editorId: rec ? rec.id : null });
  // 回传给主应用渲染进程：按 bookId 更新对应表格
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('excel:snapshotUpdated', payload);
  }
});

// 关闭独立 Excel 窗口（点「嵌入回去」）——关闭后由主应用把该表格嵌入回主窗口
ipcMain.handle('excel:embed', (e) => {
  const rec = findExcelEditor(e.sender);
  if (rec) {
    rec.embedded = true;
    rec.win.close();
  }
  return { ok: true };
});

// 聚焦指定编辑器窗口（底部任务栏点击）
ipcMain.handle('excel:focusEditor', (_e, id) => {
  const rec = excelEditors.find(e => e.id === id);
  if (!rec || rec.win.isDestroyed()) return { ok: false };
  if (rec.win.isMinimized()) rec.win.restore();
  rec.win.focus();
  return { ok: true };
});

// 关闭指定编辑器窗口（主应用关闭对应表格标签时）
ipcMain.handle('excel:closeEditor', (_e, id) => {
  const rec = excelEditors.find(e => e.id === id);
  if (rec && !rec.win.isDestroyed()) rec.win.close();
  return { ok: true };
});

// 当前已弹出的编辑器窗口列表
ipcMain.handle('excel:getEditors', () => {
  return excelEditors.map(e => ({
    id: e.id,
    bookId: e.snapshot ? e.snapshot.bookId : null,
    path: e.snapshot ? e.snapshot.path : ''
  }));
});

// 拖出单个 sheet 为独立窗口（多个 sheet 各自独立、互不影响）
ipcMain.handle('excel:popoutSheet', (_e, sheetData) => {
  // sheetData: { sheetName, path, rows, allSheets } — rows 是该 sheet 的数据
  const { sheetName, path: filePath, rows } = sheetData || {};
  const id = 's' + (excelWinSeq++);
  const W = 620, H = 680;

  const win = new BrowserWindow({
    width: W,
    height: H,
    title: `世博自动化 - ${sheetName || 'Sheet'}`,
    icon: path.join(__dirname, '..', 'icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });
  win.setMenuBarVisibility(false);

  // 位置：独立窗口，记住上次位置，新窗口阶梯错开
  {
    const n = excelWindows.length;
    const saved = loadSheetPos();
    let x = 220, y = 120;
    if (saved && Number.isFinite(saved.x) && Number.isFinite(saved.y)) {
      x = saved.x + n * 28; y = saved.y + n * 28;
    }
    const pos = clampToWorkArea(x, y, W, H);
    try { win.setBounds({ x: pos.x, y: pos.y, width: W, height: H }); } catch (e) { }
  }
  const rememberSheet = () => {
    if (win.isDestroyed() || win.isMinimized()) return;
    try { saveSheetPos(win.getBounds()); } catch (e) { }
  };
  win.on('moved', rememberSheet);
  win.on('resized', rememberSheet);
  win.on('close', rememberSheet);

  // 给这个窗口设置独立的 sheet 快照（通过全局变量 + 查询参数传递）
  excelWindows.push({ id, sheetName, path: filePath, win });

  // 注意：file:// 下带 query 的地址在部分环境下会 ERR_FAILED(-2)，因此不再用查询参数，
  // 改由页面通过 IPC(excel:mySheetId) 按窗口反查自己的 sheetId
  win.loadFile(path.join(__dirname, 'excel-sheet-window.html'));

  win.on('closed', () => {
    const idx = excelWindows.findIndex(w => w.id === id);
    if (idx !== -1) excelWindows.splice(idx, 1);
  });

  // 保存这个 sheet 的数据，供独立窗口加载
  sheetDataStore[id] = { sheetName: sheetName || 'Sheet1', path: filePath || '', rows: rows || [] };
  return { ok: true, id };
});

// 获取指定 sheet 窗口的数据
ipcMain.handle('excel:getSheetData', (_e, sheetId) => {
  return sheetDataStore[sheetId] || null;
});

// 单 sheet 窗口反查自己的 sheetId（按发起请求的窗口匹配，替代 URL 查询参数）
ipcMain.handle('excel:mySheetId', (e) => {
  const rec = excelWindows.find(w => w.win && !w.win.isDestroyed() && w.win.webContents === e.sender);
  return rec ? rec.id : null;
});

// 更新指定 sheet 窗口的数据（独立窗口编辑后回写）
ipcMain.on('excel:setSheetData', (_e, sheetId, data) => {
  sheetDataStore[sheetId] = data;
  // 通知主应用刷新（合并回原 Excel）
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('excel:sheetUpdated', { sheetId, ...data });
  }
});

// Host transport closes its owned windows when AnClicker exits.
app.on('before-quit', () => { extBrowser.close().catch(() => {}); });
ipcMain.handle('ac:browserScreenshot', async (_e, selector, target) => {
  if (!mainWindow || _e.sender !== mainWindow.webContents) throw new Error('无效调用');
  if (extOn()) {
    fs.writeFileSync(target, await extBrowser.screenshot(selector));
    return target;
  }
  const active = getActiveBrowser();
  if (!active) throw new Error('请先打开网页');
  let rect;
  if (selector) {
    rect = await active.win.webContents.executeJavaScript('(function(){const e=document.querySelector(' + JSON.stringify(selector) + ');if(!e)throw new Error("未找到截图元素");e.scrollIntoView({block:"center"});const r=e.getBoundingClientRect();if(r.width<=0||r.height<=0)throw new Error("截图元素不可见");return {x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height)};})()');
  }
  const picture = await active.win.webContents.capturePage(rect);
  fs.writeFileSync(target, picture.toPNG());
  return target;
});

ipcMain.handle('ac:windowTitles', e => {
  if (!mainWindow || e.sender !== mainWindow.webContents) throw new Error('无效调用');
  return browserWindows.map(b => b.win.getTitle());
});

ipcMain.handle('ac:recordControl', (e,action) => {
  if(!mainWindow||e.sender!==mainWindow.webContents)throw new Error('无效调用');
  if(action==='start'){if(extOn())throw new Error('网页录制请使用内置浏览器');const active=getActiveBrowser();return acRecorder.start(active&&active.win.webContents);}
  if(action==='stop')return acRecorder.stop();
  if(action==='status')return acRecorder.status();
  throw new Error('未知录制操作');
});

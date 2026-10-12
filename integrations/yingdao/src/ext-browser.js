// ============ 外部浏览器驱动（Edge / 便携版 Chrome）============
// 为什么能"换 Edge 也能干同样的活"：Edge 和 Chrome 是同一套 Chromium 内核 + 同一套 CDP 协议，
// 而本程序所有元素操作都是"往页面里丢一段 JS"，所以只要把 JS 丢进 Edge 就行。
//
// 传输用 --remote-debugging-pipe（子进程的 fd3 读 / fd4 写，JSON + \0 分隔）：
// 不需要 WebSocket，零第三方依赖，目标机也不需要装任何东西。
//
// 用法（主进程）：
//   const ext = require('./ext-browser');
//   await ext.launch({ exePath, headless, url });
//   await ext.execJS('document.title');
//   await ext.execJSFrames('...');     // 主框架 + 所有子框架（含跨域）
//   await ext.sendKey('a', 1, ['control']);
//   await ext.close();
const { spawn, spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

// 按键规格：和内置引擎那套保持一致（key/code/虚拟键码/是否字符键）
const KEY_SPEC = {
  'Enter': { key: 'Enter', code: 'Enter', vk: 13, text: '\r' },
  'Tab': { key: 'Tab', code: 'Tab', vk: 9, text: '\t' },
  'Escape': { key: 'Escape', code: 'Escape', vk: 27 },
  ' ': { key: ' ', code: 'Space', vk: 32, text: ' ' },
  'Backspace': { key: 'Backspace', code: 'Backspace', vk: 8 },
  'Delete': { key: 'Delete', code: 'Delete', vk: 46 },
  'ArrowUp': { key: 'ArrowUp', code: 'ArrowUp', vk: 38 },
  'ArrowDown': { key: 'ArrowDown', code: 'ArrowDown', vk: 40 },
  'ArrowLeft': { key: 'ArrowLeft', code: 'ArrowLeft', vk: 37 },
  'ArrowRight': { key: 'ArrowRight', code: 'ArrowRight', vk: 39 },
  'F5': { key: 'F5', code: 'F5', vk: 116 }
};
const MOD_BITS = { alt: 1, control: 2, meta: 4, shift: 8 };

function keySpec(key) {
  if (KEY_SPEC[key]) return KEY_SPEC[key];
  const s = String(key || '');
  if (s.length === 1) {
    const up = s.toUpperCase();
    return { key: s, code: 'Key' + up, vk: up.charCodeAt(0), text: s };
  }
  return { key: s, code: s, vk: 0 };
}

function meaningful(r) {
  if (r === false || r === null || r === undefined || r === '' || r === 0) return false;
  if (Array.isArray(r) && r.length === 0) return false;
  return true;
}

// ---------------------------------------------------------------- 找浏览器可执行文件
// 优先系统 Edge（Win10/11 基本都自带），其次包内便携版 Chrome。
// 注意：不要用 reg.exe 查注册表 —— 有些受管控环境把它列进黑名单，一调就被拦。
function findBrowsers(opts) {
  opts = opts || {};
  const out = [];
  const add = (kind, p) => {
    if (!p) return;
    try { if (fs.existsSync(p) && !out.some(x => x.path === p)) out.push({ kind, path: p }); } catch (e) { }
  };
  const pf = process.env.ProgramFiles || 'C:\\Program Files';
  const pf86 = process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)';
  const local = process.env.LOCALAPPDATA || '';

  // 1) 系统 Edge 的常见位置
  add('Edge', path.join(pf86, 'Microsoft', 'Edge', 'Application', 'msedge.exe'));
  add('Edge', path.join(pf, 'Microsoft', 'Edge', 'Application', 'msedge.exe'));
  if (local) add('Edge', path.join(local, 'Microsoft', 'Edge', 'Application', 'msedge.exe'));
  // 装在别处但有进 PATH 的话，where 也能找到（Edge 安装时一般会写 PATH）
  try {
    const r = spawnSync('where', ['msedge'], { encoding: 'utf-8', windowsHide: true, timeout: 5000 });
    if (r && r.status === 0) {
      String(r.stdout || '').split(/\r?\n/).map(s => s.trim()).filter(Boolean).forEach(p => add('Edge', p));
    }
  } catch (e) { }

  // 2) 包内便携版 Chrome（成品包\浏览器备用版\<版本>\chrome-win64\chrome.exe）
  //    appDir = 程序所在目录；便携包里它在 <包根>\程序\，于是浏览器备用版在它的上一级
  const roots = [];
  const pushRoot = (base) => { if (base) roots.push(path.join(base, '浏览器备用版')); };
  if (opts.appDir) { pushRoot(path.join(opts.appDir, '..')); pushRoot(opts.appDir); }
  if (process.resourcesPath) { pushRoot(path.join(process.resourcesPath, '..')); pushRoot(process.resourcesPath); }
  if (opts.searchDir) pushRoot(opts.searchDir);
  for (const root of roots) {
    try {
      if (!root || !fs.existsSync(root)) continue;
      for (const ver of fs.readdirSync(root)) {
        add('内置Chrome', path.join(root, ver, 'chrome-win64', 'chrome.exe'));
      }
    } catch (e) { }
  }

  return out;
}

// ---------------------------------------------------------------- 驱动
let child = null;
let readPipe = null;
let writePipe = null;
let buf = Buffer.alloc(0);
let seq = 0;
const waiters = new Map();
let sessionId = null;
let targetId = null;
let browserVersion = '';
let userDataDir = '';
let launchedPath = '';
let launchedKind = '';
let lastChild = null;      // 记住刚关掉的进程，方便等它真正退出（Windows 上文件还占着就删不掉目录）

function isRunning() { return !!child && !child.killed && !!writePipe; }

function send(method, params, sid) {
  if (!isRunning()) return Promise.reject(new Error('外部浏览器没在运行'));
  const id = ++seq;
  const payload = { id, method, params: params || {} };
  if (sid) payload.sessionId = sid;
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => {
      waiters.delete(id);
      reject(new Error('外部浏览器没响应：' + method + '（可能已关闭）'));
    }, 30000);
    waiters.set(id, (m) => {
      clearTimeout(t);
      if (m.error) reject(new Error(method + ' → ' + m.error.message));
      else resolve(m.result);
    });
    try { writePipe.write(JSON.stringify(payload) + '\0'); }
    catch (e) { clearTimeout(t); waiters.delete(id); reject(new Error('写入外部浏览器失败：' + e.message)); }
  });
}

function onPipeData(chunk) {
  buf = Buffer.concat([buf, chunk]);
  let i;
  while ((i = buf.indexOf(0)) >= 0) {
    const raw = buf.slice(0, i).toString('utf-8');
    buf = buf.slice(i + 1);
    if (!raw.trim()) continue;
    let m;
    try { m = JSON.parse(raw); } catch (e) { continue; }
    if (m.id && waiters.has(m.id)) { waiters.get(m.id)(m); waiters.delete(m.id); }
  }
}

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function launch(opts) {
  opts = opts || {};
  if (isRunning()) return info();
  const exePath = opts.exePath;
  if (!exePath || !fs.existsSync(exePath)) throw new Error('找不到浏览器可执行文件：' + (exePath || '(空)'));

  userDataDir = opts.userDataDir || fs.mkdtempSync(path.join(os.tmpdir(), 'yd-ext-'));
  const args = [
    '--remote-debugging-pipe',
    '--user-data-dir=' + userDataDir,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-networking',
    '--disable-component-update',
    '--disable-sync',
    '--disable-default-apps',
    '--no-service-autorun',
    '--disable-features=OptimizationHints,MediaRouter,Translate'
  ];
  if (opts.headless) args.unshift('--headless=new');
  args.push('--new-window', opts.url || 'about:blank');

  child = spawn(exePath, args, { stdio: ['ignore', 'ignore', 'pipe', 'pipe', 'pipe'], windowsHide: !!opts.headless });
  writePipe = child.stdio[3];
  readPipe = child.stdio[4];
  buf = Buffer.alloc(0);
  seq = 0;
  waiters.clear();
  sessionId = null;
  targetId = null;
  launchedPath = exePath;
  launchedKind = opts.kind || '';

  readPipe.on('data', onPipeData);
  child.on('exit', () => { child = null; writePipe = null; readPipe = null; sessionId = null; targetId = null; });
  child.stderr.on('data', () => { });

  // 等浏览器起来（刚启动时可能还没有页面 target）
  let lastErr = null;
  for (let i = 0; i < 60; i++) {
    await sleep(250);
    if (!isRunning()) break;
    try {
      const v = await send('Browser.getVersion');
      browserVersion = v.product || '';
      const pages = await listPages();
      if (pages.length) { await attach(pages[0].id); return info(); }
    } catch (e) { lastErr = e; }
  }
  const detail = lastErr ? '（' + lastErr.message + '）' : '';
  await close();
  throw new Error('外部浏览器启动失败' + detail + '。若选的是 Edge，请确认这台电脑装了 Edge；也可改用「内置Chrome」');
}

async function close() {
  const c = child;
  lastChild = c;
  child = null; writePipe = null; readPipe = null; sessionId = null; targetId = null;
  if (c) { try { c.kill(); } catch (e) { } }
  const dir = userDataDir;
  userDataDir = '';
  for (const [, fn] of waiters) fn({ id: 0, error: { message: '已关闭' } });
  waiters.clear();
  // 顺手清掉临时数据目录（删不掉也不影响，下次启动会换新的）
  if (dir) { await waitExit(3000); await rmDirWithRetry(dir); }
}

// 等刚才那个进程真正退出（最多 ms 毫秒）
async function waitExit(ms) {
  const c = lastChild;
  if (!c || c.exitCode !== null || c.signalCode) return true;
  return await new Promise((resolve) => {
    let done = false;
    const t = setTimeout(() => { if (!done) { done = true; resolve(false); } }, ms);
    c.once('exit', () => { if (!done) { done = true; clearTimeout(t); resolve(true); } });
  });
}

// Windows 上进程刚退出时文件可能还被占着，删目录要重试几次
async function rmDirWithRetry(dir) {
  for (let i = 0; i < 6; i++) {
    try {
      if (fs.existsSync(dir)) fs.rmSync(dir, { recursive: true, force: true });
      if (!fs.existsSync(dir)) return true;
    } catch (e) { }
    await sleep(400);
  }
  return false;
}

function info() {
  return { running: isRunning(), version: browserVersion, exe: launchedPath, kind: launchedKind, pid: child ? child.pid : 0 };
}

async function listPages() {
  const r = await send('Target.getTargets');
  return (r.targetInfos || [])
    .filter(t => t.type === 'page')
    .map(t => ({ id: t.targetId, url: t.url, title: t.title }));
}

// 附加到某个页面 target（要执行 JS / 发按键必须先进 session）
async function attach(tid) {
  const r = await send('Target.attachToTarget', { targetId: tid, flatten: true });
  sessionId = r.sessionId;
  targetId = tid;
  resetFrameCtx();                                  // 换页面了，框架上下文作废
  try { await send('Runtime.enable', {}, sessionId); } catch (e) { }
  try { await send('Page.enable', {}, sessionId); } catch (e) { }
  return sessionId;
}

async function ensureSession() {
  if (sessionId) return sessionId;
  const pages = await listPages();
  if (!pages.length) throw new Error('外部浏览器里没有可用页面');
  return await attach(pages[0].id);
}

// 每个子框架复用一个"隔离执行上下文"：createIsolatedWorld 每次都新建世界，
// 状态不共享，所以必须缓存 frameId -> contextId（导航后失效，要清）
let frameCtx = new Map();
function resetFrameCtx() { frameCtx = new Map(); }

async function frameContext(frameId) {
  if (frameCtx.has(frameId)) return frameCtx.get(frameId);
  const sid = await ensureSession();
  const w = await send('Page.createIsolatedWorld', { frameId: frameId }, sid);
  frameCtx.set(frameId, w.executionContextId);
  return w.executionContextId;
}

// 在指定框架里求值；frameId 为空则用主框架（主世界）
async function evalInFrame(code, frameId, timeoutMs) {
  const sid = await ensureSession();
  let contextId;
  if (frameId) contextId = await frameContext(frameId);
  const params = { expression: code, returnByValue: true, awaitPromise: true, userGesture: true };
  if (contextId) params.contextId = contextId;
  const r = await Promise.race([
    send('Runtime.evaluate', params, sid),
    new Promise((_res, rej) => setTimeout(() => rej(new Error('页面脚本执行超时（可能是页面没加载成功）')), Math.max(2000, Number(timeoutMs) || 30000)))
  ]);
  if (r.exceptionDetails) {
    const d = r.exceptionDetails;
    // 上下文失效（页面导航过）→ 清缓存，下次重建
    if (/Cannot find context|Execution context was destroyed|Inspected target navigated/i.test(String(d.text || ''))) {
      resetFrameCtx();
    }
    throw new Error('页面脚本报错：' + ((d.exception && (d.exception.description || d.exception.value)) || d.text || '未知'));
  }
  return r.result ? r.result.value : undefined;
}

// 只跑主框架（和内置引擎的 execJS 对应）
async function execJS(code, timeoutMs) {
  return await evalInFrame(code, null, timeoutMs);
}

// 主框架 + 所有子框架（含跨域，用隔离执行上下文）逐个跑，返回 [{frameId, value, err}]
async function evalAllFrames(code, timeoutMs, parallel = false) {
  const sid = await ensureSession();
  const tree = await send('Page.getFrameTree', {}, sid);
  const ids = [];
  (function walk(node) {
    if (!node) return;
    if (node.frame && node.frame.id) ids.push(node.frame.id);
    (node.childFrames || []).forEach(walk);
  })(tree.frameTree);

  const evaluate = async (id, index) => {
    try {
      const value = await evalInFrame(code, index === 0 ? null : id, timeoutMs);
      return {frameId:id, value, err:false};
    } catch (error) {
      return {frameId:id, err:true, message:error.message};
    }
  };
  if (parallel) return await Promise.all(ids.map(evaluate));
  const results = [];
  for (let index = 0; index < ids.length; index++) results.push(await evaluate(ids[index], index));
  return results;
}

// 和主进程 execJSFrames 语义一致：抛错/假值 = 这个框架没目标，继续下一个
async function execJSFrames(code, timeoutMs) {
  const res = await evalAllFrames(code, timeoutMs);
  for (const r of res) {
    if (r.err) continue;
    if (meaningful(r.value)) return r.value;
  }
  if (res.length && res.every(r => r.err)) throw new Error(res[0].message || '页面脚本在所有框架里都失败');
  return false;
}

// 读取某个全局值在哪个框架里出现了（给元素拾取用）
async function readAllFrames(expr) {
  const sid = await ensureSession();
  const tree = await send('Page.getFrameTree', {}, sid);
  const ids = [];
  (function walk(node) {
    if (!node) return;
    if (node.frame) ids.push(node.frame.id);
    (node.childFrames || []).forEach(walk);
  })(tree.frameTree);
  return await new Promise((resolve, reject) => {
    let remaining = ids.length, fallback, successful = 0, lastError;
    if (!remaining) return reject(new Error('没有可用的网页框架'));
    ids.forEach((id, index) => {
      evalInFrame(expr, index === 0 ? null : id, 2000).then(value => {
        successful++;
        if (value !== undefined && value !== null) resolve(value);
        else if (value === null) fallback = null;
      }).catch(error => { lastError = error; }).finally(() => {
        if (!--remaining) {
          if (!successful) reject(lastError || new Error('网页框架读取失败'));
          else resolve(fallback);
        }
      });
    });
  });
}

async function sendKey(key, times, modifiers) {
  const sid = await ensureSession();
  const spec = keySpec(key);
  const bits = (Array.isArray(modifiers) ? modifiers : []).reduce((a, m) => a | (MOD_BITS[m] || 0), 0);
  const n = Math.max(1, Math.min(20, Number(times) || 1));
  for (let i = 0; i < n; i++) {
    const base = {
      key: spec.key, code: spec.code,
      windowsVirtualKeyCode: spec.vk, nativeVirtualKeyCode: spec.vk,
      modifiers: bits
    };
    await send('Input.dispatchKeyEvent', Object.assign({ type: 'keyDown' }, base), sid);
    // 带修饰键时不补 char（Ctrl+A 不该往输入框里插个 a）
    if (!bits && spec.text) {
      await send('Input.dispatchKeyEvent', Object.assign({ type: 'char', text: spec.text }, base), sid);
    }
    await send('Input.dispatchKeyEvent', Object.assign({ type: 'keyUp' }, base), sid);
    await sleep(60);
  }
  return (bits ? modifiers.join('+') + '+' : '') + key + ' x' + n;
}

// 打开网址：target='新窗口' 时新建标签页，否则在当前页导航
async function navigate(url, target) {
  const wantNew = target === '新窗口' || target === '新标签页' || target === 'new';
  if (wantNew) return await createTarget(url);
  const sid = await ensureSession();
  resetFrameCtx();
  await send('Page.navigate', { url: url }, sid);
  return { id: targetId, url: url };
}

async function createTarget(url) {
  const r = await send('Target.createTarget', { url: url || 'about:blank' });
  await attach(r.targetId);
  await sleep(300);
  return { id: r.targetId, url: url || 'about:blank' };
}

async function closeTarget(tid) {
  await send('Target.closeTarget', { targetId: tid });
  if (tid === targetId) { sessionId = null; targetId = null; }
  return (await listPages()).length;
}

async function switchTarget(tid) {
  await attach(tid);
  try { await send('Target.activateTarget', { targetId: tid }); } catch (e) { }
  return { id: tid };
}

async function focusCurrent() {
  if (!isRunning() || !targetId) throw new Error('没有可定位的上一步网页，请先打开网页');
  const sid = await ensureSession();
  await send('Target.activateTarget', {targetId});
  await send('Page.bringToFront', {}, sid);
  return {id:targetId};
}

async function currentUrl() { try { return await execJS('location.href'); } catch (e) { return ''; } }
async function currentTitle() { try { return await execJS('document.title'); } catch (e) { return ''; } }

async function back() {
  // 注意：Runtime.evaluate 只吃"表达式"，history.back(); true 这种多语句会直接语法报错 —— 必须包成 IIFE
  try { await execJS('(function(){ history.back(); return true; })()'); return true; } catch (e) { return false; }
}
async function forward() {
  try { await execJS('(function(){ history.forward(); return true; })()'); return true; } catch (e) { return false; }
}
async function reload() {
  try { await execJS('(function(){ location.reload(); return true; })()'); return true; } catch (e) { return false; }
}

// 清空登录数据：对"专用 user-data-dir"启动的浏览器来说，最彻底也最可靠的做法是
// 关掉它 -> 删掉数据目录 -> 再按原样启动（CDP 那几个 clear* 命令在部分版本上并不生效）。
async function clearData(opts) {
  opts = opts || {};
  const wasRunning = isRunning();
  const exe = launchedPath;
  const kind = launchedKind;
  const dir = userDataDir;
  if (!wasRunning) return { cleared: 0, restarted: false, note: '外部浏览器没在运行' };

  await close();
  const removed = dir ? (fs.existsSync(dir) ? await rmDirWithRetry(dir) : true) : false;

  let restarted = false, launchErr = '';
  if (opts.restart !== false && exe) {
    try { await launch({ exePath: exe, kind: kind, url: opts.url || 'about:blank' }); restarted = true; }
    catch (e) { launchErr = e.message; }
  }
  return {
    cleared: removed ? 1 : 0,
    restarted: restarted,
    note: (removed ? '已删除浏览器数据目录' : '数据目录删除失败') + (restarted ? '并重新启动' : (launchErr ? '，重启失败：' + launchErr : ''))
  };
}

// 往"主框架 + 所有子框架"都注入一段脚本（不关心返回值，给拾取用）
async function injectAll(code) {
  const results = await evalAllFrames(code, 2000, true);
  if (!results.some(r => !r.err)) throw new Error(results[0]?.message || '无法在当前网页启用拾取');
  return true;
}

async function screenshot(selector) {
  const sid = await ensureSession();
  let clip;
  if (selector) {
    clip = await execJS('(function(){const e=document.querySelector(' + JSON.stringify(selector) + ');if(!e)throw new Error("未找到截图元素");e.scrollIntoView({block:"center"});const r=e.getBoundingClientRect();return {x:r.x+scrollX,y:r.y+scrollY,width:r.width,height:r.height,scale:1};})()');
    if (clip.width <= 0 || clip.height <= 0) throw new Error('截图元素不可见');
  }
  const result = await send('Page.captureScreenshot', {format:'png', ...(clip ? {clip} : {})}, sid);
  return Buffer.from(result.data, 'base64');
}

module.exports = {
  screenshot,
  findBrowsers,
  launch,
  close,
  info,
  isRunning,
  listPages,
  attach,
  createTarget,
  closeTarget,
  switchTarget,
  focusCurrent,
  execJS,
  execJSFrames,
  evalAllFrames,
  readAllFrames,
  injectAll,
  sendKey,
  navigate,
  currentUrl,
  currentTitle,
  back,
  forward,
  reload,
  clearData,
  KEY_SPEC
};

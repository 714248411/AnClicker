// ============ 「另存为」命名方式（三个 Excel 界面共用）============
// 需求：另存为时目录默认取原表格所在目录；文件名默认"原名-1、原名-2…"递增（不覆盖原文件）；
//       也可以选"加前缀"或"直接覆盖原文件"；位置还能临时改成别处。
// 用法：
//   const c = await window.ExcelSaveAs.pick(Engine, btnEl)   // 取消返回 null
//   if (c.path)  -> 用户选了"其它位置"，直接按这个路径存
//   else         -> 交给 Engine.excelSaveAs({naming, prefix, startIndex}) 自动算名字
(function () {
  const LS_KEY = 'rpa.excel.saveas';

  function lastChoice() {
    try {
      const o = JSON.parse(localStorage.getItem(LS_KEY) || 'null');
      if (o && o.naming) return o;
    } catch (e) { }
    return { naming: '后缀递增', prefix: todayPrefix(), startIndex: 1 };
  }
  function remember(o) {
    try { localStorage.setItem(LS_KEY, JSON.stringify({ naming: o.naming, prefix: o.prefix, startIndex: o.startIndex })); } catch (e) { }
  }
  function todayPrefix() {
    const d = new Date();
    const p = (n) => String(n).padStart(2, '0');
    return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + '_';
  }
  const baseName = (p) => String(p || '').split(/[\\/]/).pop() || '';
  const dirName = (p) => String(p || '').replace(/[\\/][^\\/]*$/, '');

  // 弹层：选命名方式 + 实时预览最终文件名；返回 {naming,prefix,startIndex} / {path} / null
  function pick(Engine, anchor) {
    return new Promise((resolve) => {
      const last = lastChoice();
      const panel = document.createElement('div');
      panel.className = 'xsa-panel';
      panel.innerHTML = `
        <div class="xsa-title">另存为</div>
        <div class="xsa-row"><label>保存到</label><div class="xsa-path" data-el="dir">读取中…</div></div>
        <div class="xsa-row"><label>命名方式</label>
          <select data-el="naming">
            <option value="后缀递增">后缀递增（原名-1、原名-2…）</option>
            <option value="加前缀">加前缀（前缀 + 原名）</option>
            <option value="覆盖">覆盖原文件</option>
          </select>
        </div>
        <div class="xsa-row" data-row="prefix"><label>前缀</label>
          <input data-el="prefix" type="text" placeholder="如 20260922_" value="${String(last.prefix || '').replace(/"/g, '&quot;')}">
        </div>
        <div class="xsa-row" data-row="start"><label>起始序号</label>
          <input data-el="start" type="number" min="0" step="1" value="${Number(last.startIndex) || 1}">
        </div>
        <div class="xsa-preview">将保存为：<b data-el="preview">…</b></div>
        <div class="xsa-actions">
          <button data-a="ok" class="primary">确定</button>
          <button data-a="browse">换到其它位置…</button>
          <button data-a="cancel">取消</button>
        </div>`;

      const r = anchor && anchor.getBoundingClientRect ? anchor.getBoundingClientRect() : { left: 300, bottom: 140 };
      panel.style.visibility = 'hidden';
      document.body.appendChild(panel);
      const pw = panel.offsetWidth, ph = panel.offsetHeight;
      const left = Math.max(8, Math.min(r.left, window.innerWidth - pw - 8));
      let top = Math.max(8, Math.min(r.bottom + 6, window.innerHeight - ph - 8));
      panel.style.left = left + 'px';
      panel.style.top = top + 'px';
      panel.style.visibility = 'visible';

      const q = (n) => panel.querySelector('[data-el="' + n + '"]');
      const selNaming = q('naming'), inpPrefix = q('prefix'), inpStart = q('start'), elPreview = q('preview');

      // 默认值
      selNaming.value = last.naming || '后缀递增';

      let basePath = '';
      const syncRows = () => {
        const n = selNaming.value;
        panel.querySelector('[data-row="prefix"]').style.display = (n === '加前缀') ? '' : 'none';
        panel.querySelector('[data-row="start"]').style.display = (n === '覆盖') ? 'none' : '';
      };

      // 实时预览：直接问引擎"按当前选择会存成什么名字"
      let previewSeq = 0;
      const refresh = async () => {
        const my = ++previewSeq;
        const opt = { naming: selNaming.value, prefix: inpPrefix.value, startIndex: inpStart.value };
        try {
          const p = await Engine.resolveSaveAsPath(opt);
          if (my !== previewSeq) return;
          basePath = p;
          q('dir').textContent = dirName(p) || '(桌面)';
          q('dir').title = dirName(p);
          elPreview.textContent = baseName(p);
        } catch (e) {
          if (my === previewSeq) elPreview.textContent = '（' + e.message + '）';
        }
      };

      const done = (val) => {
        document.removeEventListener('mousedown', onOutside, true);
        document.removeEventListener('keydown', onKey, true);
        panel.remove();
        resolve(val);
      };
      const onOutside = (e) => { if (!panel.contains(e.target) && e.target !== anchor) done(null); };
      const onKey = (e) => { if (e.key === 'Escape') done(null); };
      setTimeout(() => {
        document.addEventListener('mousedown', onOutside, true);
        document.addEventListener('keydown', onKey, true);
      }, 0);

      panel.addEventListener('click', (e) => e.stopPropagation());
      selNaming.addEventListener('change', () => { syncRows(); refresh(); });
      inpPrefix.addEventListener('input', refresh);
      inpStart.addEventListener('change', refresh);

      panel.querySelectorAll('button').forEach(b => {
        b.addEventListener('click', async (e) => {
          e.stopPropagation();
          const a = b.dataset.a;
          if (a === 'cancel') return done(null);
          if (a === 'browse') {
            const def = baseName(basePath) || '新建表格.xlsx';
            const picked = await window.yingdao.saveFile(def);
            if (!picked) return;
            remember({ naming: selNaming.value, prefix: inpPrefix.value, startIndex: inpStart.value });
            return done({ path: picked });
          }
          const opt = { naming: selNaming.value, prefix: inpPrefix.value, startIndex: Number(inpStart.value) || 1 };
          remember(opt);
          done(opt);
        });
      });

      syncRows();
      refresh();
    });
  }

  // 一次性注入样式
  if (!document.getElementById('__xsa_style')) {
    const st = document.createElement('style');
    st.id = '__xsa_style';
    st.textContent = `
.xsa-panel { position: fixed; z-index: 20000; width: 320px; background: #fff; border: 1px solid #d0d5dd;
  border-radius: 8px; box-shadow: 0 8px 26px rgba(0,0,0,.18); padding: 10px 12px;
  font-family: "Segoe UI","Microsoft YaHei",sans-serif; font-size: 12px; color: #333; }
.xsa-title { font-weight: 700; margin-bottom: 8px; color: #16a085; }
.xsa-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.xsa-row label { flex: 0 0 56px; color: #667085; }
.xsa-row select, .xsa-row input[type=text], .xsa-row input[type=number] {
  flex: 1; min-width: 0; padding: 4px 6px; font-size: 12px; border: 1px solid #d0d8e8; border-radius: 5px; }
.xsa-path { flex: 1; min-width: 0; color: #475467; font-size: 11px; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; }
.xsa-preview { margin: 8px 0; padding: 6px 8px; background: #f4f7ff; border-radius: 5px;
  color: #475467; word-break: break-all; }
.xsa-preview b { color: #16a085; }
.xsa-actions { display: flex; gap: 6px; justify-content: flex-end; }
.xsa-actions button { padding: 4px 10px; font-size: 12px; border: 1px solid #d0d8e8; background: #fff;
  border-radius: 5px; cursor: pointer; }
.xsa-actions button.primary { background: #16a085; border-color: #16a085; color: #fff; }
`;
    document.head.appendChild(st);
  }

  window.ExcelSaveAs = { pick, todayPrefix, lastChoice };
})();

// ============ 保存格式选择（三个 Excel 界面共用）============
// 需求：保存时可以保存多种格式，默认勾选一种（xlsx）
// 用法：
//   window.ExcelSaveFormat.applyToEngine(Engine)      // 把上次选择写进 Engine.saveFormats
//   const fmt = await window.ExcelSaveFormat.pick(Engine, btnEl)   // 弹勾选面板，返回格式数组（取消返回 null）
//   window.ExcelSaveFormat.label(Engine, fmt)         // 按钮上显示的简写，如 "xlsx" / "3 种格式"
(function () {
  const LS_KEY = 'rpa.excel.saveFormats';

  function defaults() { return ['xlsx']; }

  function getFormats() {
    try {
      const raw = localStorage.getItem(LS_KEY);
      const arr = raw ? JSON.parse(raw) : null;
      if (Array.isArray(arr) && arr.length) return arr.filter(Boolean);
    } catch (e) { }
    return defaults();
  }

  function setFormats(list) {
    const arr = (Array.isArray(list) && list.length) ? list.slice() : defaults();
    try { localStorage.setItem(LS_KEY, JSON.stringify(arr)); } catch (e) { }
    return arr;
  }

  // 把选择同步给引擎（保存时 engine 会读 Engine.saveFormats）
  function applyToEngine(Engine) {
    const list = getFormats();
    try { Engine.saveFormats = list; } catch (e) { }
    return list;
  }

  function label(Engine, list) {
    const arr = list || getFormats();
    if (!arr.length) return 'xlsx';
    if (arr.length === 1) return arr[0];
    return arr.length + ' 种格式';
  }

  // 弹层：勾选要保存的格式（默认只勾一种）；返回 Promise<string[]|null>
  function pick(Engine, anchor) {
    return new Promise((resolve) => {
      const metas = (Engine && Engine.getExportFormats) ? Engine.getExportFormats() : [{ key: 'xlsx', label: 'Excel 工作簿', ext: '.xlsx', note: '' }];
      const current = getFormats();
      const panel = document.createElement('div');
      panel.className = 'xfmt-panel';
      let html = '<div class="xfmt-title">保存格式（可多选，一次保存多个文件）</div>';
      metas.forEach(m => {
        const checked = current.indexOf(m.key) >= 0 ? ' checked' : '';
        html += `<label class="xfmt-row"><input type="checkbox" value="${m.key}"${checked}>
          <span class="xfmt-name">${m.label}<em>${m.ext}</em></span>
          <span class="xfmt-note">${m.note || ''}</span></label>`;
      });
      html += `<div class="xfmt-tip">提示：CSV / 文本 / JSON 只导出当前工作表</div>
        <div class="xfmt-actions"><button data-a="ok" class="primary">确定</button>
        <button data-a="def">恢复默认</button><button data-a="cancel">取消</button></div>`;
      panel.innerHTML = html;

      const r = anchor && anchor.getBoundingClientRect ? anchor.getBoundingClientRect() : { left: 200, bottom: 120 };
      panel.style.visibility = 'hidden';
      document.body.appendChild(panel);
      const pw = panel.offsetWidth, ph = panel.offsetHeight;
      let left = Math.min(r.left, window.innerWidth - pw - 8);
      let top = r.bottom + 6;
      if (top + ph > window.innerHeight - 8) top = Math.max(8, r.top - ph - 6);
      panel.style.left = Math.max(8, left) + 'px';
      panel.style.top = top + 'px';
      panel.style.visibility = 'visible';

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

      panel.querySelectorAll('button').forEach(b => {
        b.addEventListener('click', (e) => {
          e.stopPropagation();
          const a = b.dataset.a;
          if (a === 'cancel') return done(null);
          if (a === 'def') {
            panel.querySelectorAll('input[type=checkbox]').forEach(cb => { cb.checked = cb.value === 'xlsx'; });
            return;
          }
          const picked = [...panel.querySelectorAll('input[type=checkbox]:checked')].map(cb => cb.value);
          if (!picked.length) {
            panel.querySelector('.xfmt-title').textContent = '至少勾选一种格式';
            return;
          }
          setFormats(picked);
          applyToEngine(Engine);
          done(picked);
        });
      });
    });
  }

  // 一次性注入样式
  if (!document.getElementById('__xfmt_style')) {
    const st = document.createElement('style');
    st.id = '__xfmt_style';
    st.textContent = `
.xfmt-panel { position: fixed; z-index: 20000; width: 268px; background: #fff; border: 1px solid #d0d5dd;
  border-radius: 8px; box-shadow: 0 8px 26px rgba(0,0,0,.18); padding: 10px 12px;
  font-family: "Segoe UI","Microsoft YaHei",sans-serif; font-size: 12px; color: #333; }
.xfmt-title { font-weight: 700; margin-bottom: 8px; color: #16a085; }
.xfmt-row { display: flex; align-items: center; gap: 6px; padding: 4px 2px; border-radius: 4px; cursor: pointer; }
.xfmt-row:hover { background: #f4f7ff; }
.xfmt-row input { margin: 0; }
.xfmt-name { font-weight: 600; min-width: 96px; }
.xfmt-name em { font-style: normal; color: #98a2b3; font-weight: 400; margin-left: 4px; }
.xfmt-note { color: #98a2b3; font-size: 11px; }
.xfmt-tip { color: #98a2b3; font-size: 11px; margin: 6px 0 8px; }
.xfmt-actions { display: flex; gap: 6px; justify-content: flex-end; }
.xfmt-actions button { padding: 4px 10px; font-size: 12px; border: 1px solid #d0d8e8; background: #fff;
  border-radius: 5px; cursor: pointer; }
.xfmt-actions button.primary { background: #16a085; border-color: #16a085; color: #fff; }
`;
    document.head.appendChild(st);
  }

  window.ExcelSaveFormat = { defaults, getFormats, setFormats, applyToEngine, label, pick };
})();

// 独立 Excel 编辑器（挂件窗口）：复用 engine.js 的 Engine 完整能力
// 表格交互统一使用共享的 WPS 风格组件 ExcelGrid
// （点击选中/双击编辑/键盘导航/拖拽选区/撤销重做/填充柄/查找替换/列宽拖拽/右键菜单）
(function () {
  const $ = (s) => document.querySelector(s);
  const Engine = window.Engine;
  const state = { zoom: 1 };

  function escapeHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // 结构操作 / 整表回写接到引擎（共享接线，避免各宿主重复实现）
  const hooks = window.ExcelGrid.engineHooks(Engine, () => { syncToMain(); updateStatus(); });

  // ===== WPS 风格网格 =====
  const gridApi = window.ExcelGrid($('#grid'), {
    getRows: () => {
      try { return Engine.excelToArray(); } catch (e) { return []; }
    },
    getRawRows: () => {
      try { return Engine.excelRawArray(); } catch (e) { return []; }
    },
    setCell: (r, c, v) => Engine.setCellValue(r, c, v),
    onEdit: () => { syncToMain(); updateStatus(); syncFormulaBar(); },
    onSelectChange: (r, c) => { syncFormulaBar(); },
    onStats: renderStats,
    onStructure: hooks.onStructure,
    onRestore: hooks.onRestore,
    colName: (c) => Engine.colName(c),
    minRows: 30,
    minCols: 12
  });

  // ===== 编辑栏（名称框 + 内容框，对齐 WPS）=====
  function syncFormulaBar() {
    try {
      const range = gridApi.getSelRange();
      $('#namebox').textContent = range;
      const sel = gridApi.getSel();
      const addr = Engine.colName(sel.c) + (sel.r + 1);
      // 公式单元格显示公式（WPS 行为），普通单元格显示值
      $('#formula').value = Engine.cellText ? Engine.cellText(addr) : (Engine.excelRead(addr) ?? '');
      $('#cellinfo').textContent = range;
    } catch (e) { }
  }
  // 编辑栏回车 → 写入当前单元格
  $('#formula').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const sel = gridApi.getSel();
      try {
        Engine.setCellValue(sel.r, sel.c, $('#formula').value);
        gridApi.reload();
        gridApi.setSel(sel.r, sel.c);
        syncToMain(); updateStatus();
      } catch (err) { alert(err.message); }
    } else if (e.key === 'Escape') {
      syncFormulaBar();
      gridApi.focus();
    }
    e.stopPropagation();
  });
  $('#formula').addEventListener('blur', () => syncFormulaBar());

  // ===== 状态栏：选区统计（WPS 行为）=====
  function renderStats(st) {
    if (!st) { $('#stat').textContent = ''; return; }
    const parts = ['计数: ' + st.count];
    if (st.numCount) {
      parts.push('求和: ' + fmt(st.sum));
      parts.push('平均值: ' + fmt(st.avg));
      if (st.numCount > 1) parts.push('最小: ' + fmt(st.min), '最大: ' + fmt(st.max));
    }
    $('#stat').textContent = parts.join('   ');
  }
  function fmt(n) {
    const r = Math.round(n * 1e6) / 1e6;
    return String(r);
  }

  // ===== 工作表标签 =====
  function renderSheets() {
    const bar = $('#sheets');
    let names = [];
    try { names = Engine.getSheetNames ? Engine.getSheetNames() : []; } catch (e) { }
    const active = Engine.getActiveSheetName ? Engine.getActiveSheetName() : (names[0] || '');
    let html = '';
    names.forEach(n => {
      const cls = n === active ? 'sheet-tab active' : 'sheet-tab';
      html += `<span class="${cls}" data-sheet="${escapeHtml(n)}">${escapeHtml(n)}</span>`;
    });
    html += `<span class="sheet-add" id="sheet-add" title="新增工作表">＋</span>`;
    bar.innerHTML = html;
    bar.querySelectorAll('.sheet-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        try { Engine.switchSheet(tab.dataset.sheet); } catch (e) { }
        renderSheets(); gridApi.reload(); updateStatus(); syncFormulaBar();
      });
    });
    const add = bar.querySelector('#sheet-add');
    if (add) add.addEventListener('click', () => {
      const name = 'Sheet' + (names.length + 1);
      try { Engine.addSheet(name); } catch (e) { }
      renderSheets(); gridApi.reload(); updateStatus(); syncFormulaBar();
    });
  }

  function updateStatus() {
    try {
      const arr = Engine.excelToArray();
      const cols = arr.reduce((m, r) => Math.max(m, r.length), 0);
      const dim = arr.length + ' 行 × ' + cols + ' 列';
      $('#dim').textContent = dim;
      const p = Engine.getExcelPath() || '未保存的新文件';
      $('#path').textContent = p;
      $('#excel-path').textContent = p;
    } catch (e) { }
  }

  // 同步当前数据快照回主进程（带公式单元格，避免公式在多窗口往返中丢失）
  function syncToMain() {
    try {
      const snap = {
        path: Engine.getExcelPath ? Engine.getExcelPath() : '',
        sheetName: Engine.getActiveSheetName ? Engine.getActiveSheetName() : 'Sheet1',
        rows: Engine.excelToArray(),
        cells: Engine.exportCells ? Engine.exportCells() : null
      };
      window.yingdao.excel.setSnapshot(snap);
    } catch (e) { }
  }

  // 保存（支持多格式：按勾选的格式各存一个文件，默认只存 xlsx）
  async function save(as = false) {
    try {
      const SF = window.ExcelSaveFormat;
      const formats = SF ? SF.getFormats() : ['xlsx'];
      let path = '';
      if (as || !Engine.getExcelPath()) {
        path = await window.yingdao.saveFile('新建Excel.xlsx');
        if (!path) return;
      }
      const written = await Engine.excelSave(path, formats);
      syncToMain();
      updateStatus();
      const names = (written || []).map(p => p.split(/[\\/]/).pop()).join('、');
      flash('已保存 ' + (written ? written.length : 1) + ' 个文件：' + names);
    } catch (e) {
      alert('保存失败：' + e.message);
    }
  }

  // 保存格式按钮：弹勾选面板（默认只勾 xlsx）
  function refreshFmtBtn() {
    const SF = window.ExcelSaveFormat;
    const el = $('#fmt');
    if (!el || !SF) return;
    el.textContent = '格式：' + SF.label(Engine);
    el.title = '已选：' + SF.getFormats().join('、') + '\n可多选，一次保存多个文件';
  }

  // 打开
  async function openFile() {
    const p = await window.yingdao.openFile();
    if (!p) return;
    try {
      await Engine.excelOpen(p);
      renderSheets(); gridApi.reload(); updateStatus(); syncFormulaBar();
      syncToMain();
    } catch (e) {
      alert('打开失败：' + e.message);
    }
  }

  // 初始化：从主进程快照加载
  async function init() {
    if (window.ExcelSaveFormat) window.ExcelSaveFormat.applyToEngine(Engine);
    refreshFmtBtn();
    try {
      const snap = await window.yingdao.excel.getSnapshot();
      if (snap && snap.rows) {
        Engine.loadSnapshot(snap);  // 直接重建 workbook（含 path/sheetName/rows）
      } else {
        Engine.excelNewInMemory('Sheet1');
      }
    } catch (e) {
      try { Engine.excelNewInMemory('Sheet1'); } catch (e2) { }
    }
    renderSheets(); gridApi.reload(); updateStatus(); syncFormulaBar();
  }

  // 绑定工具栏
  $('#open').addEventListener('click', openFile);
  $('#save').addEventListener('click', () => save(false));
  $('#saveas').addEventListener('click', () => save(true));
  $('#fmt').addEventListener('click', async (e) => {
    e.stopPropagation();
    const SF = window.ExcelSaveFormat;
    if (!SF) return;
    const picked = await SF.pick(Engine, $('#fmt'));
    if (picked) {
      refreshFmtBtn();
      flash('保存格式：' + picked.join('、'));
    }
  });
  $('#undo').addEventListener('click', () => { if (!gridApi.undo()) flash('没有可撤销的操作'); });
  $('#redo').addEventListener('click', () => { if (!gridApi.redo()) flash('没有可重做的操作'); });
  $('#find').addEventListener('click', () => gridApi.find());
  $('#copy').addEventListener('click', () => {
    try { Engine.copyToClipboard(gridApi.getSelRange()); } catch (e) { alert(e.message); }
    gridApi.copy();
    syncToMain();
  });
  $('#paste').addEventListener('click', () => {
    const sel = gridApi.getSel();
    const to = Engine.colName(sel.c) + (sel.r + 1);
    try {
      Engine.pasteFromClipboard(to, '全部粘贴');
      gridApi.reload(); syncToMain(); updateStatus(); syncFormulaBar();
    } catch (e) { alert(e.message); }
  });
  $('#insrow').addEventListener('click', () => { const s = gridApi.getSel(); Engine.excelInsertRow(s.r + 1, 1); gridApi.reload(); syncToMain(); updateStatus(); });
  $('#inscol').addEventListener('click', () => { const s = gridApi.getSel(); Engine.excelInsertCol(s.c + 1, 1); gridApi.reload(); syncToMain(); updateStatus(); });
  $('#delrow').addEventListener('click', () => { const s = gridApi.getSel(); Engine.excelDeleteRow(s.r + 1, 1); gridApi.reload(); syncToMain(); updateStatus(); });
  $('#delcol').addEventListener('click', () => { const s = gridApi.getSel(); Engine.excelDeleteCol(s.c + 1, 1); gridApi.reload(); syncToMain(); updateStatus(); });
  $('#readrange').addEventListener('click', () => {
    const range = gridApi.getSelRange();
    const data = Engine.excelReadRange(range);
    Engine.vars['变量1'] = data;
    alert('已读取区域 ' + range + ' 到变量「变量1」\n' + JSON.stringify(data).slice(0, 200));
  });
  $('#getrows').addEventListener('click', () => {
    const rows = Engine.excelGetRows();
    Engine.vars['行数'] = rows;
    alert('当前工作表共 ' + rows + ' 行');
  });
  // 嵌入回去：先同步快照，再关闭独立窗口（主应用会自动嵌入显示）
  $('#embed').addEventListener('click', () => {
    syncToMain();
    // 等快照写入完成后再关闭
    setTimeout(() => window.yingdao.excel.embed(), 150);
  });
  // 拖出当前工作表为独立窗口
  $('#popout-sheet').addEventListener('click', async () => {
    const sheetName = Engine.getActiveSheetName();
    if (!sheetName) { alert('请先打开 Excel'); return; }
    const rows = Engine.excelToArray();
    const path = Engine.getExcelPath ? Engine.getExcelPath() : '';
    await window.yingdao.excel.popoutSheet({ sheetName, path, rows });
    // 拖出后，从当前工作簿移除该 sheet（仅剩一个则保留）
    try {
      const names = Engine.getSheetNames();
      if (names.length > 1) Engine.removeSheet(sheetName);
    } catch (e) { }
    renderSheets(); gridApi.reload(); updateStatus(); syncToMain();
  });

  // 浮动提示（不打断操作的轻提示）
  let flashTimer = null;
  function flash(msg) {
    const el = $('#toast');
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(flashTimer);
    flashTimer = setTimeout(() => el.classList.remove('show'), 1400);
  }

  // Ctrl+滚轮缩放
  const grid = $('#grid');
  grid.addEventListener('wheel', (e) => {
    if (!e.ctrlKey) return;
    e.preventDefault();
    state.zoom = Math.min(3, Math.max(0.5, state.zoom + (e.deltaY < 0 ? 0.1 : -0.1)));
    grid.style.zoom = state.zoom;
    $('#zoom').textContent = Math.round(state.zoom * 100) + '%';
  }, { passive: false });
  $('#zoom-out').addEventListener('click', () => setZoom(-0.1));
  $('#zoom-in').addEventListener('click', () => setZoom(0.1));
  $('#zoom').addEventListener('dblclick', () => setZoom(1, true));
  function setZoom(delta, absolute) {
    state.zoom = absolute ? 1 : Math.min(3, Math.max(0.5, state.zoom + delta));
    grid.style.zoom = state.zoom;
    $('#zoom').textContent = Math.round(state.zoom * 100) + '%';
  }

  init();
})();

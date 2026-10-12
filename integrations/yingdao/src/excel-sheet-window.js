// 单个 sheet 独立窗口逻辑：复用 Engine，加载指定 sheet 数据，独立编辑
// 表格交互统一使用共享的 WPS 风格组件 ExcelGrid
(function () {
  const $ = (s) => document.querySelector(s);
  const Engine = window.Engine;
  const params = new URLSearchParams(location.search);
  // sheetId / sheetName：优先取 URL 参数；没有则通过 IPC 按窗口反查
  // （file:// 带 query 在部分环境加载失败，主进程已改为 IPC 传参）
  let sheetId = params.get('sheetId');
  let sheetName = params.get('sheetName') || 'Sheet1';
  const state = { zoom: 1 };

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
    onSelectChange: () => syncFormulaBar(),
    onStats: renderStats,
    onStructure: hooks.onStructure,
    onRestore: hooks.onRestore,
    colName: (c) => Engine.colName(c),
    minRows: 30,
    minCols: 12
  });

  // 编辑栏（名称框 + 内容框）：公式单元格显示公式
  function syncFormulaBar() {
    try {
      const range = gridApi.getSelRange();
      $('#namebox').textContent = range;
      $('#cellinfo').textContent = range;
      const sel = gridApi.getSel();
      const addr = Engine.colName(sel.c) + (sel.r + 1);
      $('#formula').value = Engine.cellText ? Engine.cellText(addr) : (Engine.excelRead(addr) ?? '');
    } catch (e) { }
  }
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
    } else if (e.key === 'Escape') { syncFormulaBar(); gridApi.focus(); }
    e.stopPropagation();
  });
  $('#formula').addEventListener('blur', () => syncFormulaBar());

  // 状态栏统计
  function renderStats(st) {
    if (!st) { $('#stat').textContent = ''; return; }
    const parts = ['计数: ' + st.count];
    if (st.numCount) {
      const r6 = (n) => Math.round(n * 1e6) / 1e6;
      parts.push('求和: ' + r6(st.sum), '平均值: ' + r6(st.avg));
      if (st.numCount > 1) parts.push('最小: ' + r6(st.min), '最大: ' + r6(st.max));
    }
    $('#stat').textContent = parts.join('   ');
  }

  function updateStatus() {
    $('#sheet-name').textContent = sheetName;
    try {
      const arr = Engine.excelToArray();
      const cols = arr.reduce((m, r) => Math.max(m, r.length), 0);
      $('#dim').textContent = arr.length + ' 行 × ' + cols + ' 列';
    } catch (e) { }
  }

  // 同步数据回主进程（按 sheetId，带公式单元格）
  function syncToMain() {
    try {
      const data = {
        sheetName,
        rows: Engine.excelToArray(),
        cells: Engine.exportCells ? Engine.exportCells() : null
      };
      window.yingdao.excel.setSheetData(sheetId, data);
    } catch (e) { }
  }

  // 保存此工作表（支持多格式：xlsx/xls/csv/txt/ods/html/json）
  async function save() {
    if (!window.XLSX) { alert('Excel 组件未加载'); return; }
    const SF = window.ExcelSaveFormat;
    const formats = SF ? SF.getFormats() : ['xlsx'];
    const p = await window.yingdao.saveFile(sheetName + '.xlsx');
    if (!p) return;
    try {
      const written = await Engine.excelSaveFormats(p, formats);
      alert('已保存 ' + (written || []).length + ' 个文件：\n' + (written || []).join('\n'));
    } catch (e) {
      alert('保存失败：' + e.message);
    }
  }

  function refreshFmtBtn() {
    const SF = window.ExcelSaveFormat;
    const el = $('#fmt');
    if (!el || !SF) return;
    el.textContent = '格式：' + SF.label(Engine);
    el.title = '已选：' + SF.getFormats().join('、') + '\n可多选，一次保存多个文件';
  }

  // 初始化：从主进程加载该 sheet 的数据
  async function init() {
    if (window.ExcelSaveFormat) window.ExcelSaveFormat.applyToEngine(Engine);
    refreshFmtBtn();
    // 补全 sheetId / sheetName（IPC 反查）
    try {
      if (!sheetId && window.yingdao.excel.mySheetId) sheetId = await window.yingdao.excel.mySheetId();
    } catch (e) { }
    try {
      const data = await window.yingdao.excel.getSheetData(sheetId);
      if (data && data.rows) {
        if (data.sheetName) sheetName = data.sheetName;
        Engine.loadSnapshot({ path: data.path || '', sheetName: data.sheetName || sheetName, rows: data.rows });
      } else {
        Engine.excelNewInMemory(sheetName);
      }
    } catch (e) {
      try { Engine.excelNewInMemory(sheetName); } catch (e2) { }
    }
    gridApi.reload(); updateStatus(); syncFormulaBar();
  }

  // 绑定工具栏
  $('#save').addEventListener('click', save);
  $('#fmt').addEventListener('click', async (e) => {
    e.stopPropagation();
    const SF = window.ExcelSaveFormat;
    if (!SF) return;
    const picked = await SF.pick(Engine, $('#fmt'));
    if (picked) refreshFmtBtn();
  });
  $('#undo').addEventListener('click', () => gridApi.undo());
  $('#redo').addEventListener('click', () => gridApi.redo());
  $('#find').addEventListener('click', () => gridApi.find());
  $('#insrow').addEventListener('click', () => { const s = gridApi.getSel(); Engine.excelInsertRow(s.r + 1, 1); gridApi.reload(); syncToMain(); updateStatus(); });
  $('#inscol').addEventListener('click', () => { const s = gridApi.getSel(); Engine.excelInsertCol(s.c + 1, 1); gridApi.reload(); syncToMain(); updateStatus(); });
  $('#delrow').addEventListener('click', () => { const s = gridApi.getSel(); Engine.excelDeleteRow(s.r + 1, 1); gridApi.reload(); syncToMain(); updateStatus(); });
  $('#delcol').addEventListener('click', () => { const s = gridApi.getSel(); Engine.excelDeleteCol(s.c + 1, 1); gridApi.reload(); syncToMain(); updateStatus(); });

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

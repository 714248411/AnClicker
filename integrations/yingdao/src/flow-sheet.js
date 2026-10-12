// ============ 流程编排 ↔ 表格 的序列化（纯函数，方便单独测试）============
// 表格列：序号 | 指令 | 层级 | 说明 | <各参数列…> | 指令ID
//   序号   = 第几步（只给人看，回写按行顺序走）
//   层级   = 缩进层级（0 最外层；1 表示在「循环 / 条件判断」里面）
//   说明   = 备注（只是记录，不影响执行）
//   指令ID = 回写时用来认指令；认不出就按「指令」名字反查
// 删掉整行 = 删掉这一步；把「指令」单元格清空也不参与回写。
(function () {
  const SHEET_NAME = '流程编排';
  const FIXED_COLS = ['序号', '指令', '层级', '说明', '指令ID'];

  // 步骤数组 -> 二维数组（含表头）
  function toRows(steps, commands) {
    const list = Array.isArray(steps) ? steps : [];
    const cmds = Array.isArray(commands) ? commands : [];
    const keys = [];
    list.forEach(s => Object.keys((s && s.params) || {}).forEach(k => {
      if (keys.indexOf(k) < 0) keys.push(k);
    }));
    const rows = [FIXED_COLS.slice(0, 4).concat(keys).concat(['指令ID'])];
    list.forEach((s, i) => {
      const def = cmds.find(c => c.id === s.id);
      const row = [i + 1, s.name || (def ? def.name : s.id), Number(s.level) || 0, s.note || ''];
      keys.forEach(k => {
        const v = (s.params || {})[k];
        row.push(v === undefined || v === null ? '' : String(v));
      });
      row.push(s.id);
      rows.push(row);
    });
    return rows;
  }

  // 二维数组 -> 步骤数组
  // 返回 { steps, skipped, error }：error 有值表示表头不对，调用方别改动流程
  function fromRows(aoa, commands) {
    const rows = Array.isArray(aoa) ? aoa : [];
    const cmds = Array.isArray(commands) ? commands : [];
    if (!rows.length) return { steps: [], skipped: [], error: '表格是空的' };

    const header = (rows[0] || []).map(x => String(x == null ? '' : x).trim());
    const idxOf = (n) => header.indexOf(n);
    const cName = idxOf('指令'), cLevel = idxOf('层级'), cId = idxOf('指令ID');
    if (cName < 0 && cId < 0) {
      return { steps: [], skipped: [], error: '第 1 行得是表头（至少要有「指令」列）。请先用「流程→表格」生成，不要改表头' };
    }
    const paramCols = [];
    header.forEach((h, i) => { if (h && FIXED_COLS.indexOf(h) < 0) paramCols.push({ key: h, idx: i }); });

    const steps = [], skipped = [];
    for (let r = 1; r < rows.length; r++) {
      const row = rows[r] || [];
      const rawName = cName >= 0 ? String(row[cName] == null ? '' : row[cName]).trim() : '';
      const rawId = cId >= 0 ? String(row[cId] == null ? '' : row[cId]).trim() : '';
      if (!rawName && !rawId) continue;                       // 空行 → 跳过（等于删掉这一步）
      let def = rawId ? cmds.find(c => c.id === rawId) : null;
      if (!def && rawName) def = cmds.find(c => c.name === rawName);
      if (!def) { skipped.push('第' + (r + 1) + '行「' + (rawName || rawId) + '」'); continue; }

      const params = {};
      paramCols.forEach(pc => {
        const cell = row[pc.idx];
        const pdef = (def.params || []).find(x => x.key === pc.key);
        if (pdef && pdef.type === 'number') params[pc.key] = Number(cell) || 0;
        else params[pc.key] = cell == null ? '' : String(cell);
      });
      steps.push({
        id: def.id,
        name: def.name,
        params: params,
        level: cLevel >= 0 ? (Number(row[cLevel]) || 0) : 0
      });
    }
    if (!steps.length) return { steps: [], skipped: skipped, error: '表格里没有解析出任何步骤，流程没有改动' };
    return { steps: steps, skipped: skipped, error: '' };
  }

  const api = { SHEET_NAME, FIXED_COLS, toRows, fromRows };
  if (typeof window !== 'undefined') window.FlowSheet = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})();

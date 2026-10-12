// ============ 主应用逻辑 ============
(function () {
  const state = {
    flows: { '主流程': [] },  // 流程名 -> 步骤数组（主流程 + 子流程）
    activeFlow: '主流程',     // 当前编辑/查看的流程名
    flowName: '未命名流程',   // 整体流程的名称（双击顶栏「未命名流程」可改名，用于保存/导出）
    selectedIdx: -1,
    selUids: new Set(),   // 多选：选中步骤的 _uid 集合（按 uid 记，插入/排序后不会错位）
    anchorUid: null,      // 主选（属性面板、插入位置以它为准）
    runningIdx: -1,       // 运行中高亮（与选中态分离，避免运行流程冲掉用户的选择）
    excelEditors: {},     // bookId -> 已弹出的独立 Excel 窗口 id（支持多表格多窗口）
    running: false,
    stopped: false,       // 本次运行是否被手动停止（用于日志提示）
    recording: false,
    recordMode: 'web',  // 'web' 录制网页 | 'win' 录制电脑操作 | 'table' 录制表格
    recordTableSrc: null, // 录制表格：已复制的源 { bookId, bookName, sheetName, range }
    lastOpTime: 0,      // 上次操作时间戳（用于自动记录等待时间）
    clipboardStep: null, // 复制的步骤（单条，兼容旧逻辑）
    clipboardSteps: null, // 复制的步骤组（支持多选复制）
    collapsedSteps: new Set(), // 折叠的步骤 _uid 集合（默认新加步骤折叠）
    logCount: 0
  };
  // steps 动态映射到当前活动流程（子流程切换后，所有读/写 state.steps 都自动指向当前流程）
  Object.defineProperty(state, 'steps', {
    get() { return state.flows[state.activeFlow] || (state.flows[state.activeFlow] = []); },
    set(v) { state.flows[state.activeFlow] = v; }
  });
  let stepUidSeq = 1; // 步骤唯一 id 自增（用于折叠状态跟踪）
  let varsGrid = null; // 底部数据表格使用的网格实例（每次重渲染前先销毁，避免监听器泄漏）

  const $ = (sel) => document.querySelector(sel);
  const flowCanvas = $('#flow-canvas');
  const flowEmpty = $('#flow-empty');
  const cmdList = $('#cmd-list');
  const propBody = $('#prop-body');

  // ===== 渲染指令库 =====
  // 分类折叠状态（Set 存已折叠的分类名）
  const collapsedCats = new Set();

  function renderCommands(filter = '') {
    cmdList.innerHTML = '';
    CATEGORIES.forEach(cat => {
      const items = COMMANDS.filter(c => c.category === cat && (!filter || c.name.includes(filter)));
      if (items.length === 0) return;

      // 分类标题（可点击折叠/展开）
      const catDiv = document.createElement('div');
      catDiv.className = 'cmd-category' + (collapsedCats.has(cat) ? ' collapsed' : '');
      const isCollapsed = collapsedCats.has(cat);
      catDiv.innerHTML = `<span class="cat-toggle">${isCollapsed ? '▸' : '▾'}</span><span class="cat-name">${cat}</span>`;
      catDiv.addEventListener('click', () => {
        if (collapsedCats.has(cat)) collapsedCats.delete(cat);
        else collapsedCats.add(cat);
        renderCommands(filter); // 重渲染
      });
      cmdList.appendChild(catDiv);

      // 折叠时不渲染指令项
      if (collapsedCats.has(cat)) return;

      items.forEach(cmd => {
        const item = document.createElement('div');
        item.className = 'cmd-item';
        item.draggable = true;
        item.dataset.cmdId = cmd.id;
        // 白话指令（大白话操作，多属性）前面用「-」标记，单功能指令用彩色圆点「·」区分
        const isMulti = cmd.category === '白话指令';
        if (isMulti) {
          item.innerHTML = `<span class="cmd-dash" title="白话指令">-</span>${cmd.name}`;
        } else {
          item.innerHTML = `<span class="cmd-dot" style="background:${cmd.color}"></span>${cmd.name}`;
        }
        item.addEventListener('dragstart', (e) => {
          e.dataTransfer.setData('cmdId', cmd.id);
        });
        item.addEventListener('dblclick', () => addStep(cmd.id));
        cmdList.appendChild(item);
      });
    });
  }

  // ===== 流程 Tab（主流程 + 子流程） =====
  function renderFlowTabs() {
    const tabsWrap = document.querySelector('.flow-tabs');
    if (!tabsWrap) return;
    const names = Object.keys(state.flows);
    // 保留「+ 子流程」按钮
    tabsWrap.querySelectorAll('.flow-tab-item').forEach(el => el.remove());
    const addBtn = $('#btn-add-flow');
    names.forEach(name => {
      const tab = document.createElement('span');
      tab.className = 'tab flow-tab-item' + (name === state.activeFlow ? ' active' : '');
      tab.textContent = name;
      tab.title = name === '主流程' ? '右键：新建子流程' : '右键：重命名 / 删除';
      tab.addEventListener('click', () => switchFlow(name));
      // 右键弹出菜单：重命名 / 删除（主流程：只给新建子流程）
      tab.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        e.stopPropagation();
        showFlowTabMenu(e.clientX, e.clientY, name);
      });
      tabsWrap.insertBefore(tab, addBtn);
    });
  }

  // 流程 tab 右键菜单：重命名 / 删除
  function showFlowTabMenu(x, y, name) {
    let menu = document.getElementById('flow-tab-menu');
    if (!menu) {
      menu = document.createElement('div');
      menu.id = 'flow-tab-menu';
      menu.style.cssText = 'position:fixed;z-index:99999;background:#fff;border:1px solid #d0d8e8;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.15);padding:4px;min-width:150px;font-size:13px;display:none';
      document.body.appendChild(menu);
    }
    menu.innerHTML = '';
    const mk = (label, fn) => {
      const it = document.createElement('div');
      it.textContent = label;
      it.style.cssText = 'padding:8px 12px;cursor:pointer;border-radius:5px;color:#333;white-space:nowrap';
      it.addEventListener('mouseenter', () => it.style.background = '#f0f4ff');
      it.addEventListener('mouseleave', () => it.style.background = 'transparent');
      it.addEventListener('click', () => { menu.style.display = 'none'; fn(); });
      menu.appendChild(it);
    };
    if (name === '主流程') {
      mk('＋ 新建子流程', addFlow);
    } else {
      mk('✏️ 重命名', () => renameFlow(name));
      mk('🗑️ 删除', () => deleteFlow(name));
    }
    menu.style.display = 'block';
    menu.style.left = Math.min(x, window.innerWidth - 170) + 'px';
    menu.style.top = y + 'px';
    const close = () => { menu.style.display = 'none'; document.removeEventListener('click', close); };
    setTimeout(() => document.addEventListener('click', close), 0);
  }

  function renameFlow(name) {
    if (!state.flows[name]) return;
    const newName = prompt('重命名流程：', name);
    if (newName === null) return;
    const nn = newName.trim();
    if (!nn || nn === name) return;
    if (state.flows[nn]) { log('已存在同名流程：' + nn, 'error'); return; }
    // 保持顺序重建 flows
    const rebuilt = {};
    Object.keys(state.flows).forEach(k => {
      if (k === name) rebuilt[nn] = state.flows[name];
      else rebuilt[k] = state.flows[k];
    });
    state.flows = rebuilt;
    if (state.activeFlow === name) state.activeFlow = nn;
    renderFlowTabs();
    renderFlow();
    renderProps();
    log(`流程已重命名为：${nn}`, 'success');
  }

  function deleteFlow(name) {
    if (name === '主流程' || !state.flows[name]) return;
    if (!confirm(`删除流程「${name}」及其所有步骤？`)) return;
    delete state.flows[name];
    if (state.activeFlow === name) state.activeFlow = '主流程';
    clearSel();
    renderFlowTabs();
    renderFlow();
    renderProps();
    log(`已删除流程：${name}`, 'success');
  }

  function switchFlow(name) {
    if (!state.flows[name]) return;
    state.activeFlow = name;
    clearSel();
    renderFlowTabs();
    renderFlow();
    renderProps();
    log(`已切换到流程：${name}`, 'success');
  }

  function addFlow() {
    let name = '子流程' + (Object.keys(state.flows).length);
    // 自动去重
    while (state.flows[name]) name = '子流程' + (Math.floor(Math.random() * 1000));
    state.flows[name] = [];
    state.activeFlow = name;
    clearSel();
    renderFlowTabs();
    renderFlow();
    renderProps();
    log(`已新建子流程：${name}（双击 tab 可重命名）`, 'success');
  }

  // ===== 添加步骤（插入到当前选中步骤之后，默认折叠） =====
  function addStep(cmdId) {
    const cmd = COMMANDS.find(c => c.id === cmdId);
    if (!cmd) return;
    const params = {};
    cmd.params.forEach(p => { params[p.key] = p.default; });
    const newStep = { id: cmd.id, name: cmd.name, category: cmd.category, color: cmd.color, params, level: 0, _uid: 'u' + (stepUidSeq++) };
    const insertAt = (state.selectedIdx >= 0) ? state.selectedIdx + 1 : state.steps.length;
    state.steps.splice(insertAt, 0, newStep);
    // 新步骤默认折叠
    state.collapsedSteps.add(newStep._uid);
    selectOnly(insertAt);
    renderFlow();
    renderProps();
  }

  // 录制时添加步骤（插入到当前选中步骤之后，默认折叠）
  function addRecordedStep(cmdId, params) {
    const cmd = COMMANDS.find(c => c.id === cmdId);
    if (!cmd) { log(`录制：未知指令 ${cmdId}`, 'error'); return; }
    const fullParams = {};
    cmd.params.forEach(p => { fullParams[p.key] = (params && params[p.key] !== undefined) ? params[p.key] : p.default; });
    const newStep = { id: cmd.id, name: cmd.name, category: cmd.category, color: cmd.color, params: fullParams, level: 0, _uid: 'u' + (stepUidSeq++) };
    const insertAt = (state.selectedIdx >= 0) ? state.selectedIdx + 1 : state.steps.length;
    state.steps.splice(insertAt, 0, newStep);
    // 新步骤默认折叠
    state.collapsedSteps.add(newStep._uid);
    selectOnly(insertAt);
    renderFlow();
    renderProps();
    // 录制中：更新按钮上的实时步数 + 滚动到新步骤（给出明确反馈）
    if (state.recording) {
      state.recordCount = (state.recordCount || 0) + 1;
      const btn = $('#btn-record');
      if (btn) {
        const modeName = state.recordMode === 'win' ? '电脑' : (state.recordMode === 'table' ? '表格' : '网页');
        btn.textContent = `⏹ 停止${modeName}录制 (${state.recordCount})`;
      }
      try {
        const el = flowCanvas.querySelector(`.flow-step[data-idx="${insertAt}"]`);
        if (el && el.scrollIntoView) el.scrollIntoView({ block: 'nearest' });
      } catch (e) { }
    }
  }

  // 记录操作（含自动等待时间）：电脑录制模式下，自动插入与上次操作之间的等待
  function recordOpWithWait(cmdId, params, label) {
    const now = Date.now();
    const idle = Math.round((now - state.lastOpTime) / 1000);
    if (idle >= 1 && state.lastOpTime > 0) {
      addRecordedStep('sleep', { seconds: idle });
      log(`已录制：等待 ${idle} 秒`, 'time');
    }
    state.lastOpTime = now;
    addRecordedStep(cmdId, params);
    if (label) log(label);
  }

  // ===== 流程步骤选中 / 多选 =====
  // 说明：选中状态用 _uid 记录（而不是下标），这样插入、删除、拖拽排序后不会错位
  let dragGroup = null;   // 正在拖拽的步骤 _uid 数组（多选时整组移动）
  function uidAt(idx) { const s = state.steps[idx]; return s ? s._uid : null; }
  function idxOfUid(uid) { return state.steps.findIndex(s => s._uid === uid); }
  function isSelected(uid) { return state.selUids.has(uid); }
  // 选中的步骤下标（升序）
  function selIdxList() {
    const out = [];
    state.steps.forEach((s, i) => { if (state.selUids.has(s._uid)) out.push(i); });
    return out;
  }
  // 由 anchorUid 反推 selectedIdx，并清理已不存在的选中项（增删改后调用）
  function syncSelectedIdx() {
    const alive = new Set(state.steps.map(s => s._uid));
    for (const u of Array.from(state.selUids)) if (!alive.has(u)) state.selUids.delete(u);
    if (state.anchorUid && !alive.has(state.anchorUid)) state.anchorUid = null;
    if (!state.anchorUid) {
      const list = selIdxList();
      if (list.length) state.anchorUid = uidAt(list[list.length - 1]);
    }
    state.selectedIdx = state.anchorUid ? idxOfUid(state.anchorUid) : -1;
  }
  function selectOnly(idx) {
    const uid = uidAt(idx);
    state.selUids = uid ? new Set([uid]) : new Set();
    state.anchorUid = uid;
    state.selectedIdx = uid ? idx : -1;
  }
  function toggleSelect(idx) {
    const uid = uidAt(idx);
    if (!uid) return;
    if (state.selUids.has(uid)) {
      state.selUids.delete(uid);
      if (state.anchorUid === uid) {
        const list = selIdxList();
        state.anchorUid = list.length ? uidAt(list[list.length - 1]) : null;
      }
    } else {
      state.selUids.add(uid);
      state.anchorUid = uid;
    }
    syncSelectedIdx();
  }
  // Shift+点击：以主选为锚点选择连续区间
  function extendSelectTo(idx) {
    let a = state.selectedIdx;
    if (a < 0) { selectOnly(idx); return; }
    const r0 = Math.min(a, idx), r1 = Math.max(a, idx);
    const set = new Set();
    for (let i = r0; i <= r1; i++) { const s = state.steps[i]; if (s) set.add(s._uid); }
    state.selUids = set;
    state.anchorUid = uidAt(a);
    syncSelectedIdx();
  }
  function selectAllSteps() {
    state.selUids = new Set(state.steps.map(s => s._uid));
    if (!state.anchorUid) state.anchorUid = uidAt(0);
    syncSelectedIdx();
  }
  function clearSel() {
    state.selUids = new Set();
    state.anchorUid = null;
    state.selectedIdx = -1;
  }
  // 查找 idx 上方最近的「循环」指令（loop/loopForever），返回其缩进层级；找不到返回 null
  function findLoopLevelAbove(idx) {
    for (let i = idx - 1; i >= 0; i--) {
      const s = state.steps[i];
      if (!s) continue;
      // 遇到 level 更浅或同级的普通指令会中断查找（循环体边界），但简单起见：
      // 直接找最近的 loop/loopForever（不跨过更浅的循环边界）
      if (s.id === 'loop' || s.id === 'loopForever') return s.level || 0;
    }
    return null;
  }

  // 批量删除选中步骤
  function deleteSelected() {
    if (!state.selUids.size) return 0;
    const keep = state.steps.filter(s => !state.selUids.has(s._uid));
    const n = state.steps.length - keep.length;
    state.steps = keep;
    clearSel();
    return n;
  }
  // 把一组步骤移动到 targetIdx 位置（before=true 插到前面）；选中的整组一起移动
  function moveSteps(uids, targetIdx, before) {
    const set = new Set(uids);
    const moving = state.steps.filter(s => set.has(s._uid));
    if (!moving.length) return;
    const rest = state.steps.filter(s => !set.has(s._uid));
    const targetStep = state.steps[targetIdx];
    let insertAt;
    if (targetStep && !set.has(targetStep._uid)) {
      insertAt = rest.indexOf(targetStep) + (before ? 0 : 1);
    } else {
      // 落点本身在选中集合里：找一个未选中的参照元素
      let ref = null, refBefore = true;
      for (let i = targetIdx; i < state.steps.length; i++) {
        const s = state.steps[i];
        if (!set.has(s._uid)) { ref = s; refBefore = true; break; }
      }
      if (!ref) {
        for (let i = targetIdx - 1; i >= 0; i--) {
          const s = state.steps[i];
          if (!set.has(s._uid)) { ref = s; refBefore = false; break; }
        }
      }
      if (!ref) return;                     // 全部被选中，位置不变
      insertAt = rest.indexOf(ref) + (refBefore ? 0 : 1);
    }
    rest.splice(Math.max(0, Math.min(insertAt, rest.length)), 0, ...moving);
    state.steps = rest;
    syncSelectedIdx();
  }

  // ===== 渲染流程 =====
  function renderFlow() {
    flowCanvas.innerHTML = '';
    if (state.steps.length === 0) {
      flowCanvas.appendChild(flowEmpty);
      return;
    }
    let skipUntilLevel = -1;   // 折叠的循环/条件体：跳过 level 大于该值的子步骤
    for (let idx = 0; idx < state.steps.length; idx++) {
      const step = state.steps[idx];
      // 折叠的循环体子步骤：跳过渲染
      if (skipUntilLevel >= 0 && (step.level || 0) >= skipUntilLevel) continue;
      skipUntilLevel = -1;
      const div = document.createElement('div');
      const isCollapsed = state.collapsedSteps.has(step._uid);
      const selected = state.selUids.has(step._uid);
      const isAnchor = selected && step._uid === state.anchorUid;
      const level = step.level || 0;
      // 循环/条件指令折叠时，隐藏其子步骤（level 更大的连续步骤）
      if (isCollapsed && (step.id === 'loop' || step.id === 'loopForever' || step.id === 'if')) {
        skipUntilLevel = level + 1;
      }
      div.className = 'flow-step'
        + (selected ? ' selected' : '')
        + (isAnchor ? ' sel-anchor' : '')
        + (idx === state.runningIdx ? ' running' : '')
        + (isCollapsed ? ' collapsed' : '');
      div.dataset.idx = String(idx);
      // 缩进层级：循环体子步骤向右缩进（一级 22px），并加左侧竖线标记归属
      if (level > 0) div.style.marginLeft = (level * 22) + 'px';
      const desc = Object.entries(step.params).map(([k, v]) => `${k}=${v}`).join(', ');
      // 循环/条件指令：折叠按钮放最前（⋮⋮ 旁），标识下三角；普通步骤放最后
      const foldHtml = (step.id === 'loop' || step.id === 'loopForever' || step.id === 'if')
        ? `<button class="step-fold step-fold-front" title="${isCollapsed ? '展开循环体' : '折叠循环体'}">${isCollapsed ? '▸' : '▾'}</button>`
        : '';
      const foldHtmlEnd = (step.id === 'loop' || step.id === 'loopForever' || step.id === 'if')
        ? ''
        : `<button class="step-fold" title="${isCollapsed ? '展开' : '折叠'}">${isCollapsed ? '▸' : '▾'}</button>`;
      div.innerHTML = `
        <span class="step-drag-handle" title="拖拽排序">⋮⋮</span>
        ${foldHtml}
        <span class="step-idx">${idx + 1}</span>
        <span class="step-name">${step.name}</span>
        <span class="step-desc">${isCollapsed ? '' : desc}</span>
        ${foldHtmlEnd}
        <button class="step-del" title="删除">✕</button>
      `;
      // 点击卡片：普通=单选，Ctrl/Cmd+点击=加选/取消，Shift+点击=范围选择
      div.addEventListener('click', (e) => {
        if (e.shiftKey) extendSelectTo(idx);
        else if (e.ctrlKey || e.metaKey) toggleSelect(idx);
        else selectOnly(idx);
        renderFlow();
        renderProps();
      });
      // 折叠/展开按钮
      div.querySelector('.step-fold').addEventListener('click', (e) => {
        e.stopPropagation();
        if (state.collapsedSteps.has(step._uid)) state.collapsedSteps.delete(step._uid);
        else state.collapsedSteps.add(step._uid);
        renderFlow();
      });
      // 删除按钮：删掉这一条（多选时其余选中项保留）
      div.querySelector('.step-del').addEventListener('click', (e) => {
        e.stopPropagation();
        state.collapsedSteps.delete(step._uid);
        state.selUids.delete(step._uid);
        if (state.anchorUid === step._uid) state.anchorUid = null;
        state.steps.splice(idx, 1);
        syncSelectedIdx();
        renderFlow();
        renderProps();
      });

      // 整个卡片直接可拖拽排序（无需抓把手）；多选时整组一起移动
      div.draggable = true;
      div.addEventListener('dragstart', (e) => {
        // 拖的这张卡在多选集合里 → 整组移动；否则只移动这一张
        const group = (selected && state.selUids.size > 1)
          ? state.steps.filter(s => state.selUids.has(s._uid)).map(s => s._uid)
          : [step._uid];
        dragGroup = group;
        e.dataTransfer.setData('srcIdx', String(idx));
        e.dataTransfer.effectAllowed = 'move';
        // 视觉反馈：拖动源变半透明（整组一起标记）
        setTimeout(() => {
          flowCanvas.querySelectorAll('.flow-step').forEach(el => {
            const i = +el.dataset.idx;
            if (group.indexOf(uidAt(i)) >= 0) el.classList.add('dragging');
          });
        }, 0);
      });
      div.addEventListener('dragend', () => {
        dragGroup = null;
        flowCanvas.querySelectorAll('.flow-step.dragging, .flow-step.drag-over-top, .flow-step.drag-over-bottom')
          .forEach(el => el.classList.remove('dragging', 'drag-over-top', 'drag-over-bottom'));
      });
      // 拖拽经过：显示插入位置指示
      div.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        const srcIdx = parseInt(e.dataTransfer.getData('srcIdx'), 10);
        if (isNaN(srcIdx) || srcIdx === idx) return;
        // 判断鼠标在上半区还是下半区
        const rect = div.getBoundingClientRect();
        const isTop = (e.clientY - rect.top) < rect.height / 2;
        // 清除其它指示线
        document.querySelectorAll('.flow-step').forEach(el => {
          el.classList.remove('drag-over-top', 'drag-over-bottom');
        });
        div.classList.add(isTop ? 'drag-over-top' : 'drag-over-bottom');
      });
      div.addEventListener('dragleave', (e) => {
        // 只在真正离开时清除
        if (!div.contains(e.relatedTarget)) {
          div.classList.remove('drag-over-top', 'drag-over-bottom');
        }
      });
      div.addEventListener('drop', (e) => {
        e.preventDefault();
        const src = parseInt(e.dataTransfer.getData('srcIdx'), 10);
        const cmdId = e.dataTransfer.getData('cmdId');
        const isTop = div.classList.contains('drag-over-top');
        if (cmdId) {
          // 从指令库拖入新步骤
          const target = COMMANDS.find(c => c.id === cmdId);
          if (!target) return;
          const params = {};
          target.params.forEach(p => { params[p.key] = p.default; });
          const newStep = { id: target.id, name: target.name, category: target.category, color: target.color, params, level: 0, _uid: 'u' + (stepUidSeq++) };
          const at = isTop ? idx : idx + 1;
          state.steps.splice(at, 0, newStep);
          state.collapsedSteps.add(newStep._uid); // 默认折叠
          selectOnly(at);
        } else if (dragGroup && dragGroup.length) {
          // 排序：多选时整组移动（拖到上半区=插到前面，下半区=插到后面）
          moveSteps(dragGroup, idx, isTop);
          dragGroup = null;
        } else if (!isNaN(src) && src !== idx) {
          const srcUid = uidAt(src);
          if (srcUid) moveSteps([srcUid], idx, isTop);
        }
        renderFlow();
        renderProps();
      });
      flowCanvas.appendChild(div);
    }
  }

  // ===== 渲染属性面板 =====
  function renderProps() {
    propBody.innerHTML = '';
    const selList = selIdxList();

    // 多选：显示批量操作面板
    if (selList.length > 1) {
      const wrap = document.createElement('div');
      wrap.innerHTML = `
        <div style="font-weight:700;font-size:15px;color:var(--primary);margin-bottom:6px">已选中 ${selList.length} 条指令</div>
        <div style="color:#8a94a6;font-size:12px;line-height:1.9;margin-bottom:12px">
          第 ${selList[0] + 1} ~ ${selList[selList.length - 1] + 1} 条（共 ${state.steps.length} 条）<br>
          拖动任意一条可整组移动；Shift+点击=范围选择，Ctrl+点击=加选
        </div>`;
      const row = document.createElement('div');
      row.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px';
      const mkBtn = (label, title, fn, danger) => {
        const b = document.createElement('button');
        b.textContent = label;
        b.title = title;
        b.style.cssText = 'padding:5px 10px;font-size:12px;border:1px solid ' + (danger ? '#f0b7b7' : '#d0d8e8') +
          ';background:#fff;border-radius:5px;cursor:pointer;color:' + (danger ? '#e74c3c' : '#333');
        b.addEventListener('click', fn);
        return b;
      };
      row.appendChild(mkBtn('📋 复制选中', 'Ctrl+C', () => {
        state.clipboardSteps = selList.map(i => {
          const s = state.steps[i];
          return { id: s.id, name: s.name, category: s.category, color: s.color, params: JSON.parse(JSON.stringify(s.params)), level: s.level || 0 };
        });
        state.clipboardStep = null;
        log(`已复制 ${state.clipboardSteps.length} 条指令`, 'success');
      }));
      row.appendChild(mkBtn('粘贴到其后', 'Ctrl+V', () => {
        const group = (state.clipboardSteps && state.clipboardSteps.length) ? state.clipboardSteps : null;
        if (!group) { log('剪贴板为空，先复制再粘贴', 'error'); return; }
        const at = selList[selList.length - 1] + 1;
        const added = group.map(clip => {
          const ns = {
            id: clip.id, name: clip.name, category: clip.category, color: clip.color,
            params: JSON.parse(JSON.stringify(clip.params)), level: clip.level || 0, _uid: 'u' + (stepUidSeq++)
          };
          state.collapsedSteps.add(ns._uid);
          return ns;
        });
        state.steps.splice(at, 0, ...added);
        state.selUids = new Set(added.map(s => s._uid));
        state.anchorUid = added[added.length - 1]._uid;
        syncSelectedIdx();
        renderFlow(); renderProps();
        log(`已粘贴 ${added.length} 条指令`, 'success');
      }));
      row.appendChild(mkBtn('🗑 删除选中', 'Delete', () => {
        const n = deleteSelected();
        renderFlow(); renderProps();
        log(`已删除选中 ${n} 条指令`, 'success');
      }, true));
      row.appendChild(mkBtn('取消选择', 'Esc', () => {
        clearSel(); renderFlow(); renderProps();
      }));
      wrap.appendChild(row);
      propBody.appendChild(wrap);
      return;
    }

    const idx = state.selectedIdx;
    if (idx < 0 || !state.steps[idx]) {
      propBody.innerHTML = '<div class="prop-empty">选中一条指令查看属性</div>';
      return;
    }
    const step = state.steps[idx];
    const cmd = COMMANDS.find(c => c.id === step.id);
    if (!cmd || cmd.params.length === 0) {
      propBody.innerHTML = '<div class="prop-empty">该指令无参数</div>';
      return;
    }
    const title = document.createElement('div');
    title.style.cssText = 'font-weight:700;margin-bottom:12px;font-size:15px;color:' + step.color;
    title.textContent = step.name;
    propBody.appendChild(title);

    // 参数顺序：支持拖拽调整，按指令 id 持久化到 localStorage
    const paramOrderKey = 'rpa.paramOrder.' + step.id;
    let paramOrder = [];
    try { paramOrder = JSON.parse(localStorage.getItem(paramOrderKey) || '[]'); } catch (e) { paramOrder = []; }
    let orderedParams = cmd.params.slice();
    if (Array.isArray(paramOrder) && paramOrder.length) {
      orderedParams.sort((a, b) => {
        const ia = paramOrder.indexOf(a.key), ib = paramOrder.indexOf(b.key);
        if (ia === -1) return 1; if (ib === -1) return -1;
        return ia - ib;
      });
    }

    orderedParams.forEach(p => {
      const group = document.createElement('div');
      group.className = 'prop-group';
      // 拖拽排序手柄（⋮⋮），拖动调整参数顺序
      const handle = document.createElement('span');
      handle.className = 'prop-drag-handle';
      handle.title = '拖拽调整参数顺序';
      handle.textContent = '⋮⋮';
      handle.draggable = true;
      handle.addEventListener('dragstart', (e) => { e.dataTransfer.setData('paramKey', p.key); });
      handle.addEventListener('dragover', (e) => { e.preventDefault(); group.classList.add('param-drag-over'); });
      handle.addEventListener('dragleave', () => group.classList.remove('param-drag-over'));
      handle.addEventListener('drop', (e) => {
        e.preventDefault();
        group.classList.remove('param-drag-over');
        const fromKey = e.dataTransfer.getData('paramKey');
        if (!fromKey || fromKey === p.key) return;
        const keys = orderedParams.map(x => x.key);
        const fromIdx = keys.indexOf(fromKey), toIdx = keys.indexOf(p.key);
        if (fromIdx < 0 || toIdx < 0) return;
        const moved = keys.splice(fromIdx, 1)[0];
        keys.splice(toIdx, 0, moved);
        try { localStorage.setItem(paramOrderKey, JSON.stringify(keys)); } catch (err) { }
        renderProps();
      });
      group.appendChild(handle);
      const label = document.createElement('label');
      label.textContent = p.label;
      group.appendChild(label);

      let input;
      if (p.type === 'select') {
        input = document.createElement('select');
        p.options.forEach(o => {
          const opt = document.createElement('option');
          opt.value = o; opt.textContent = o;
          if (o === step.params[p.key]) opt.selected = true;
          input.appendChild(opt);
        });
        // 标记"定位方式" select（拾取按钮要用）
        if (p.options.includes('CSS选择器') && p.options.includes('XPath')) {
          input.dataset.bySelect = '1';
        }
      } else if (p.type === 'order') {
        // 排序方向动态下拉：按「修改时间」→ 从早到晚/从晚到早；否则 → 从小到大/从大到小
        input = document.createElement('select');
        const isTime = step.params.sortBy === '修改时间';
        const orderOpts = isTime ? ['从早到晚', '从晚到早'] : ['从小到大', '从大到小'];
        orderOpts.forEach(o => {
          const opt = document.createElement('option');
          opt.value = o; opt.textContent = o;
          if (o === step.params[p.key]) opt.selected = true;
          input.appendChild(opt);
        });
        // 若当前值不在新选项里（比如从时间切回文件名），重置为第一个
        if (!orderOpts.includes(step.params[p.key])) {
          step.params[p.key] = orderOpts[0];
          input.value = orderOpts[0];
        }
      } else if (p.type === 'number') {
        input = document.createElement('input');
        input.type = 'number';
        input.value = step.params[p.key];
      } else if (p.type === 'targetlist') {
        // 跳转目标：可输入 + 下拉选择（流程名 / 第几步 / 标记名）
        input = document.createElement('input');
        input.type = 'text';
        input.value = step.params[p.key] ?? '';
        input.setAttribute('list', 'goto-target-list');
        input.setAttribute('placeholder', '如 3、第5步、流程:子流程1、标记名');
        const dl = document.createElement('datalist');
        dl.id = 'goto-target-list';
        // 流程名
        Object.keys(state.flows).forEach(name => {
          const opt = document.createElement('option');
          opt.value = '流程:' + name; opt.textContent = '流程：' + name;
          dl.appendChild(opt);
        });
        // 当前流程的步骤序号
        const curSteps = state.steps || [];
        curSteps.forEach((s, i) => {
          const opt = document.createElement('option');
          opt.value = String(i + 1); opt.textContent = '第' + (i + 1) + '步 · ' + s.name;
          dl.appendChild(opt);
        });
        // 标记名
        curSteps.forEach(s => {
          if (s.id === 'mark' && s.params && s.params.name) {
            const opt = document.createElement('option');
            opt.value = s.params.name; opt.textContent = '标记：' + s.params.name;
            dl.appendChild(opt);
          }
        });
        group.appendChild(dl);
      } else if (p.type === 'sheet') {
        // 工作表下拉：从已打开的 workbook 里取 sheet 名（多个表格时带「表格名:」前缀区分）
        input = document.createElement('select');
        const sheetOpts = collectSheetOptions();
        sheetOpts.forEach(o => {
          const opt = document.createElement('option');
          opt.value = o.value; opt.textContent = o.label;
          if (o.value === step.params[p.key]) opt.selected = true;
          input.appendChild(opt);
        });
        // 已保存值不在选项里（如尚未打开对应表格）→ 补一个当前值选项
        const cur = step.params[p.key];
        if (cur && !sheetOpts.some(o => o.value === cur)) {
          const opt = document.createElement('option');
          opt.value = cur; opt.textContent = cur;
          opt.selected = true;
          input.appendChild(opt);
        }
      } else {
        input = document.createElement('input');
        input.type = 'text';
        input.value = step.params[p.key] ?? '';
      }
      input.addEventListener('input', () => {
        step.params[p.key] = p.type === 'number' ? Number(input.value) : input.value;
        renderFlow();
        // select 变化可能联动其它参数（如「按什么排序」改变「排序方向」的选项）→ 重渲染属性面板
        if (p.type === 'select' || p.type === 'order') renderProps();
      });
      group.appendChild(input);

      // 路径类参数：只对文本输入框加"选择"按钮（目录类选文件夹、文件类选文件）+ 拖拽支持
      const isTextType = p.type === 'text' || p.type === undefined;
      if (isTextType && (p.label.includes('路径') || p.label.includes('文件') || p.label.includes('目录') || p.label.includes('文件夹'))) {
        // 「目录」「文件夹」→ 选文件夹；其余（文件/路径）→ 选文件
        const isDir = p.label.includes('目录') || p.label.includes('文件夹');
        const btn = document.createElement('button');
        btn.textContent = isDir ? '选择文件夹...' : '选择文件...';
        btn.style.cssText = 'margin-top:6px;padding:5px 10px;font-size:12px;border:1px solid #d0d8e8;background:#f5f7fa;border-radius:5px;cursor:pointer';
        btn.addEventListener('click', async () => {
          const path = isDir
            ? await window.yingdao.openDir('选择文件夹')
            : await window.yingdao.openFile();
          if (path) {
            input.value = path;
            step.params[p.key] = path;
            renderFlow();
          }
        });
        group.appendChild(btn);

        // 拖拽文件到输入框：显示虚线框提示 + 拖放填入路径
        group.classList.add('drop-target');
        group.addEventListener('dragover', (e) => {
          e.preventDefault();
          e.stopPropagation();
          group.classList.add('dragging');
        });
        group.addEventListener('dragleave', (e) => {
          e.preventDefault();
          e.stopPropagation();
          group.classList.remove('dragging');
        });
        group.addEventListener('drop', (e) => {
          e.preventDefault();
          e.stopPropagation();
          group.classList.remove('dragging');
          const file = e.dataTransfer.files && e.dataTransfer.files[0];
          const filePath = file && (file.path || '');
          if (filePath) {
            input.value = filePath;
            step.params[p.key] = filePath;
            renderFlow();
            log(`已拖入文件：${filePath}`, 'success');
          } else {
            log('未识别到文件路径，请用「选择文件」按钮', 'error');
          }
        });
      }

      // 元素定位类参数：加"🎯 选取"按钮（在浏览器里点选）
      if (p.label.includes('元素定位') || p.label.includes('锚点元素')) {
        const isAnchor = p.label.includes('锚点元素');
        const row = document.createElement('div');
        row.style.cssText = 'display:flex;gap:6px;margin-top:6px;align-items:center';

        const pickBtn = document.createElement('button');
        pickBtn.innerHTML = isAnchor ? '🎯 在浏览器中选取锚点元素' : '🎯 在浏览器中选取元素';
        pickBtn.style.cssText = 'flex:1;padding:6px 10px;font-size:12px;border:1px solid #4a6cf7;background:#eef2ff;color:#4a6cf7;border-radius:5px;cursor:pointer;font-weight:600';
        pickBtn.addEventListener('click', async () => {
          // 先确保浏览器可见
          if (window.__showBrowser) await window.__showBrowser();
          pickBtn.disabled = true;
          pickBtn.textContent = '⏳ 等待选取...';
          try {
            const r = await window.yingdao.browser.pickElement();
            if (r && !r.canceled) {
              const picked = r.css || r.xpath || '';
              if (isAnchor) {
                // 锚点元素：可拾取多个（; 分隔追加），并自动把定位方式切到「锚点定位」
                const cur = String(step.params[p.key] || '').trim();
                const list = cur ? cur.split(/[;；]/).map(s => s.trim()).filter(Boolean) : [];
                if (picked && !list.includes(picked)) list.push(picked);
                input.value = list.join('; ');
                step.params[p.key] = input.value;
                const byInput2 = propBody.querySelector('[data-by-select="1"]');
                if (byInput2) { byInput2.value = '锚点定位'; step.params.by = '锚点定位'; }
              } else {
                input.value = picked;
                step.params[p.key] = input.value;
                // 如果指令有"定位方式"参数，尝试智能推荐
                const byInput = propBody.querySelector('[data-by-select="1"]');
                if (byInput && r.xpath && r.css) {
                  byInput.value = 'CSS选择器'; // 默认 CSS（更通用）
                }
              }
              log(`🎯 已拾取${isAnchor ? '锚点' : ''}元素：${r.text || picked}`, 'success');
              renderFlow();
            } else {
              log('元素拾取已取消', 'error');
            }
          } catch (e) {
            log('元素拾取失败：' + e.message, 'error');
          } finally {
            pickBtn.disabled = false;
            pickBtn.innerHTML = isAnchor ? '🎯 在浏览器中选取锚点元素' : '🎯 在浏览器中选取元素';
          }
        });

        row.appendChild(pickBtn);
        group.appendChild(row);
      }

      // 坐标类参数：加「🎯 在浏览器里点选坐标」按钮
      // 点选时鼠标移动会实时显示坐标，点一下记一个点并在页面上标注 1、2、3…，
      // 已标的点还能拖动微调，最多 9 个点；完成后坐标自动回填到输入框（也可手工改）
      if (p.label.includes('点击坐标')) {
        const row = document.createElement('div');
        row.style.cssText = 'display:flex;gap:6px;margin-top:6px;align-items:center';

        const btn = document.createElement('button');
        const idleText = '🎯 在浏览器里点选坐标（可点多个点）';
        btn.innerHTML = idleText;
        btn.style.cssText = 'flex:1;padding:6px 10px;font-size:12px;border:1px solid #e67e22;background:#fff7ef;color:#e67e22;border-radius:5px;cursor:pointer;font-weight:600';
        btn.addEventListener('click', async () => {
          if (window.__showBrowser) await window.__showBrowser();
          btn.disabled = true;
          btn.textContent = '⏳ 请在浏览器里点选（ESC 结束）...';
          try {
            const r = await window.yingdao.browser.pickPoints(9);
            if (r && !r.canceled && r.points && r.points.length) {
              const txt = r.points.map(pt => pt.x + ',' + pt.y).join('; ');
              input.value = txt;
              step.params[p.key] = txt;
              log(`🎯 已拾取 ${r.points.length} 个坐标：${txt}`, 'success');
              renderFlow();
            } else {
              log('坐标拾取已取消', 'error');
            }
          } catch (e) {
            log('坐标拾取失败：' + (e && e.message ? e.message : e), 'error');
          } finally {
            btn.disabled = false;
            btn.innerHTML = idleText;
          }
        });
        row.appendChild(btn);
        group.appendChild(row);
      }

      // 元素定位类参数：额外说明一下现在支持 iframe
      if (p.label.includes('元素定位')) {
        const tip = document.createElement('div');
        tip.style.cssText = 'margin-top:4px;font-size:11px;color:#8a94a6';
        tip.textContent = '提示：定位会自动搜索同源 iframe / 影子 DOM，并默认等 5 秒等页面渲染完；跨域 iframe 会自动逐框架重试。';
        group.appendChild(tip);
      }

      propBody.appendChild(group);
    });
  }

  // ===== 日志 =====
  // 从日志文本里提取可能的文件/文件夹路径（Windows 盘符绝对路径，或反斜杠路径）
  function extractPath(text) {
    const m = String(text).match(/[A-Za-z]:[\\/][^\s"'，。;；]+/);
    return m ? m[0] : null;
  }

  function log(text, type = '') {
    const logView = $('#log-view');
    const line = document.createElement('div');
    line.className = 'log-line ' + type;
    const time = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    line.textContent = `[${time}] ${text}`;
    // 含路径的日志行：右键可打开文件/所在文件夹
    const p = extractPath(text);
    if (p && window.yingdao.openPath) {
      line.style.cursor = 'context-menu';
      line.title = p;
      line.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        showLogCtxMenu(e.clientX, e.clientY, p);
      });
    }
    logView.appendChild(line);
    logView.scrollTop = logView.scrollHeight;
    state.logCount++;
  }

  // 浏览器引擎切换菜单（右键「浏览器」按钮呼出）
  async function showEngineMenu(x, y) {
    let menu = document.getElementById('engine-menu');
    if (!menu) {
      menu = document.createElement('div');
      menu.id = 'engine-menu';
      menu.style.cssText = 'position:fixed;z-index:99999;background:#fff;border:1px solid #d0d8e8;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.15);padding:4px;min-width:260px;font-size:13px;display:none';
      document.body.appendChild(menu);
    }
    menu.innerHTML = '<div style="padding:6px 12px;color:#98a2b3;font-size:12px">浏览器内核（右键「浏览器」按钮切换）：</div>';
    let list;
    try { list = await window.yingdao.browser.listEngines(); } catch (e) { list = null; }
    if (!list) { log('读不到浏览器引擎信息', 'error'); return; }

    const mk = (key, label, avail, note) => {
      const it = document.createElement('div');
      const cur = list.current === key;
      it.innerHTML = '<span style="color:#333">' + label + '</span>' +
        (cur ? '<span style="color:#16a085;margin-left:6px;font-weight:600">当前</span>' : '') +
        (avail ? '' : '<span style="color:#98a2b3;margin-left:6px;font-size:12px">' + (note || '不可用') + '</span>');
      it.style.cssText = 'padding:8px 12px;cursor:' + (avail ? 'pointer' : 'default') + ';border-radius:5px;display:flex;align-items:center;gap:4px';
      it.addEventListener('mouseenter', () => it.style.background = avail ? '#f0f4ff' : 'transparent');
      it.addEventListener('mouseleave', () => it.style.background = 'transparent');
      it.addEventListener('click', async () => {
        menu.style.display = 'none';
        if (!avail) { log(label + ' 当前不可用', 'error'); return; }
        log('正在切换到 ' + label + ' …');
        const r = await window.yingdao.browser.setEngine(key);
        if (r.ok) log('浏览器内核已切换为：' + label + (r.info && r.info.version ? '（' + r.info.version + '）' : ''), 'success');
        else log('切换失败：' + (r.err || '未知原因'), 'error');
      });
      menu.appendChild(it);
    };
    list.engines.forEach(en => {
      mk(en.key, en.label, en.available, en.key === 'Edge' ? '未安装' : '未找到');
    });
    menu.style.display = 'block';
    menu.style.left = x + 'px';
    menu.style.top = y + 'px';
    const close = () => { menu.style.display = 'none'; document.removeEventListener('click', close); };
    setTimeout(() => document.addEventListener('click', close), 0);
  }

  // 日志右键菜单：打开文件 / 打开所在文件夹 / 复制路径
  function showLogCtxMenu(x, y, p) {
    let menu = document.getElementById('log-ctx-menu');
    if (!menu) {
      menu = document.createElement('div');
      menu.id = 'log-ctx-menu';
      menu.style.cssText = 'position:fixed;z-index:99999;background:#fff;border:1px solid #d0d8e8;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.15);padding:4px;min-width:160px;font-size:13px;display:none';
      document.body.appendChild(menu);
    }
    menu.innerHTML = '';
    const mk = (label, fn) => {
      const it = document.createElement('div');
      it.textContent = label;
      it.style.cssText = 'padding:8px 12px;cursor:pointer;border-radius:5px;color:#333';
      it.addEventListener('mouseenter', () => it.style.background = '#f0f4ff');
      it.addEventListener('mouseleave', () => it.style.background = 'transparent');
      it.addEventListener('click', () => { menu.style.display = 'none'; fn(); });
      menu.appendChild(it);
    };
    mk('📂 打开所在文件夹', async () => { await window.yingdao.showInFolder(p); });
    mk('📄 打开文件', async () => { await window.yingdao.openPath(p); });
    mk('📋 复制路径', async () => { try { await navigator.clipboard.writeText(p); log('已复制路径：' + p, 'success'); } catch (e) { } });
    menu.style.display = 'block';
    menu.style.left = x + 'px';
    menu.style.top = y + 'px';
    // 点击别处关闭
    const close = () => { menu.style.display = 'none'; document.removeEventListener('click', close); };
    setTimeout(() => document.addEventListener('click', close), 0);
  }

  // ===== 渲染数据表格（变量 + 可编辑 Excel 内容） =====
  function renderVars() {
    const view = $('#vars-view');
    const keys = Object.keys(Engine.vars);
    let html = '';

    // 如果有 Excel 打开，显示可编辑的 Excel 数据表格（WPS 风格网格组件）
    try {
      const arr = Engine.excelToArray ? Engine.excelToArray() : null;
      if (arr && arr.length > 0) {
        const excelPath = Engine.getExcelPath ? Engine.getExcelPath() : '';
        const sheetName = Engine.getExcelSheetName ? Engine.getExcelSheetName() : '';
        const displayPath = excelPath || '（未保存的新文件）';
        html += `<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
          <div style="font-weight:600;color:#16a085">📊 Excel：${sheetName} <span style="color:#999;font-weight:400;font-size:11px">${displayPath}</span></div>
          <button id="btn-save-excel" style="padding:4px 12px;font-size:12px;border:1px solid #16a085;background:#16a085;color:#fff;border-radius:5px;cursor:pointer">💾 保存</button>
        </div>`;
        html += '<div id="vars-grid-holder" style="overflow:auto;max-height:320px"></div>';
        if (arr.length > 200) html += `<div style="color:#999;margin-top:4px">仅显示前 200 行，共 ${arr.length} 行</div>`;
        html += '<div style="color:#999;font-size:11px;margin-top:6px">💡 单击选中，双击/回车/直接输入编辑，方向键导航，支持拖拽选区与 Ctrl+C/V/X</div>';
      }
    } catch (e) { /* 无 Excel 打开 */ }

    // 变量表
    if (keys.length > 0) {
      html += '<div style="font-weight:600;margin:12px 0 6px;color:#4a6cf7">🔤 变量</div>';
      html += '<table><tr><th>变量名</th><th>值</th></tr>';
      keys.forEach(k => {
        let val = Engine.vars[k];
        if (Array.isArray(val)) val = JSON.stringify(val);
        html += `<tr><td>${k}</td><td>${val}</td></tr>`;
      });
      html += '</table>';
    }

    if (html === '') {
      view.innerHTML = '<div style="color:#999;padding:10px">暂无数据（打开Excel或运行含变量的流程后显示）</div>';
      return;
    }
    view.innerHTML = html;

    // 用 WPS 风格网格组件渲染 Excel 数据（点击选中/双击编辑/键盘导航/拖拽选区）
    const holder = view.querySelector('#vars-grid-holder');
    if (holder) {
      // 旧实例先销毁：节点每次都是新建的，不销毁会残留 document 级监听器
      if (varsGrid && varsGrid.destroy) { try { varsGrid.destroy(); } catch (e) { } varsGrid = null; }
      let arr = [];
      try { arr = Engine.excelToArray(); } catch (e) { }
      const shown = arr.slice(0, 200);
      varsGrid = window.ExcelGrid(holder, {
        getRows: () => shown,
        getRawRows: () => { try { return (Engine.excelRawArray ? Engine.excelRawArray() : []).slice(0, 200); } catch (e) { return []; } },
        setCell: (r, c, v) => { if (Engine.setCellValue) Engine.setCellValue(r, c, v); },
        onEdit: (r, c, v) => log(`已编辑单元格 ${Engine.colName(c)}${r + 1} = ${v}`, 'success'),
        colName: (c) => Engine.colName(c),
        minRows: Math.max(shown.length, 8),
        minCols: 8
      });
    }

    // 绑定保存按钮
    const btnSave = view.querySelector('#btn-save-excel');
    if (btnSave) {
      btnSave.addEventListener('click', async () => {
        try {
          if (Engine.excelSave) {
            await Engine.excelSave('');
            log('Excel 已保存', 'success');
          }
        } catch (e) {
          log('保存失败：' + e.message, 'error');
        }
      });
    }
  }

  // HTML 转义（防止单元格内容破坏表格）
  function escapeHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // ===== 执行流程 =====
  // 执行一段步骤（支持循环体嵌套），返回控制流信号：
  //   { breakLoop: true } 表示遇到「跳出循环」
  //   { endFlow: true } 表示遇到「结束流程」
  async function runSteps(fromIdx, baseLevel, flowName = '主流程') {
    // 运行时执行指定流程（默认主流程，子流程通过「调用子流程」进入）
    const steps = state.flows[flowName] || [];
    let i = fromIdx;
    while (i < steps.length) {
      if (!state.running) return { endFlow: true };   // 被手动停止
      const step = steps[i];
      const level = step.level || 0;
      if (level < baseLevel) return {};   // 已退出当前块（比基准更浅）

      // 循环指令：收集循环体（level > 当前 level 的连续子步骤）并重复执行
      if (step.id === 'loop' || step.id === 'loopForever') {
        state.runningIdx = i;
        renderFlow();
        const isTimeMode = step.id === 'loop' && step.params.mode === '按时间';
        const count = step.id === 'loop' ? (isTimeMode ? Infinity : Math.max(0, Number(step.params.count) || 0)) : Infinity;
        const secs = isTimeMode ? (Math.max(0, Number(step.params.seconds) || 0)) : 0;
        const logDesc = step.id === 'loopForever' ? '无限循环'
          : (isTimeMode ? '按时间循环 ' + secs + ' 秒' : '循环 ' + count + ' 次');
        log(`▶ 执行：${step.name}（${logDesc}）`);
        const bodyLevel = level + 1;
        // 找循环体结束位置
        let bodyEnd = i + 1;
        while (bodyEnd < steps.length && (steps[bodyEnd].level || 0) >= bodyLevel) bodyEnd++;
        let iter = 0;
        let broke = false;
        const startTime = Date.now();
        while (true) {
          if (!state.running) break;
          // 按时间模式：超时则停止
          if (isTimeMode && (Date.now() - startTime) >= secs * 1000) break;
          const r = await runSteps(i + 1, bodyLevel, flowName);
          if (r && r.endFlow) return r;
          if (r && r.breakLoop) { broke = true; break; }
          iter++;
          if (!isTimeMode && iter >= count) break;
        }
        i = bodyEnd;   // 跳到循环体之后继续
        continue;
      }
      if (step.id === 'breakLoop') {
        log('▶ 执行：跳出循环');
        return { breakLoop: true };
      }
      if (step.id === 'end') {
        log('▶ 执行：结束流程');
        return { endFlow: true };
      }
      // 标记：仅作为跳转目标，无实际操作
      if (step.id === 'mark') {
        log(`🔖 标记：${step.params.name || ''}`);
        i++;
        continue;
      }
      // 跳转：支持「第N步」/「N」/「流程:名」/「标记名」
      if (step.id === 'goto') {
        const target = String(step.params.target || '').trim();
        // 「流程:X」→ 切换到指定流程并从第 1 步执行
        if (target.startsWith('流程:')) {
          const fn = target.slice(3).trim();
          if (!fn || !state.flows[fn]) {
            log(`✘ 跳转流程不存在：${fn || '(空)'}`, 'error');
            i++;
            continue;
          }
          log(`⤵ 跳转到流程：${fn}`);
          const r = await runSteps(0, 0, fn);
          if (r && r.endFlow) return r;
          if (r && r.breakLoop) return r;
          // 流程执行完，返回当前流程继续
          i++;
          continue;
        }
        // 「第N步」或纯数字 → 序号
        let m = /^第?\s*(\d+)\s*步?$/.exec(target);
        let targetIdx = -1;
        if (m) {
          targetIdx = Number(m[1]) - 1;
        } else if (target) {
          // 标记名：查找对应 mark 指令
          targetIdx = steps.findIndex(s => s.id === 'mark' && s.params && s.params.name === target);
        }
        if (targetIdx < 0 || targetIdx >= steps.length) {
          log(`✘ 跳转目标不存在：${target}`, 'error');
          i++;
          continue;
        }
        log(`⤵ 跳转到第 ${targetIdx + 1} 步（${steps[targetIdx].name}）`);
        i = targetIdx;
        continue;
      }
      // 调用子流程：执行指定子流程的步骤，执行完返回主流程继续
      if (step.id === 'callFlow') {
        const flowName = String(step.params.flowName || '').trim();
        if (!flowName || !state.flows[flowName]) {
          log(`✘ 子流程不存在：${flowName || '(空)'}`, 'error');
          i++;
          continue;
        }
        log(`📦 调用子流程：${flowName}`);
        const r = await runSteps(0, 0, flowName);
        if (r && r.endFlow) return r;
        if (r && r.breakLoop) return r;
        log(`↩ 子流程 ${flowName} 执行完毕，返回主流程`);
        i++;
        continue;
      }

      state.runningIdx = i;      // 运行高亮单独记，不动用户的选中态
      renderFlow();
      log(`▶ 执行：${step.name}`);
      // 网页相关指令执行前，自动显示内嵌浏览器
      if (['openUrl', 'click', 'input', 'getText', 'waitElement'].includes(step.id)) {
        if (window.__showBrowser) await window.__showBrowser();
      }
      await Engine.runCommand(step, { log });
      // Excel 相关指令执行后刷新内嵌 Excel 网格 + 底部数据表格
      if (step.id.startsWith('excel')) {
        renderExcelGrid();
        renderVars();
        // 打开/新建 Excel 后自动切到「数据表格」标签，让用户立即看到内容
        if (step.id === 'excelOpen' || step.id === 'excelNew') {
          switchTab('vars');
        }
      }
      i++;
    }
    return {};
  }

  async function runFlow(fromIdx = 0) {
    if (state.running) return;
    state.running = true;
    state.stopped = false;
    if (Engine.resetCancel) Engine.resetCancel();
    $('#btn-run').disabled = true;
    $('#btn-stop').disabled = false;
    log(fromIdx > 0 ? `===== 从第 ${fromIdx + 1} 步开始运行 =====` : '===== 开始运行流程 =====', 'time');
    try {
      const r = await runSteps(fromIdx, 0);
      if (r && r.endFlow && state.running) log('===== 流程已结束 =====', 'time');
      if (state.stopped) log('===== 已手动停止 =====', 'error');
      else log('===== 流程运行完成 =====', 'success');
    } catch (err) {
      // 手动停止：等待类指令会抛哨兵错误，提示友好信息
      if (err && err.message === 'RPA_STOP') log('===== 已手动停止 =====', 'error');
      else log(`✘ 运行出错：${err.message}`, 'error');
    } finally {
      state.running = false;
      state.stopped = false;
      state.runningIdx = -1;
      $('#btn-run').disabled = false;
      $('#btn-stop').disabled = true;
      renderFlow();
      renderVars();
    }
  }

  // 手动停止：立即置位中断标记 + 立刻恢复按钮状态（不等当前长指令结束）
  function stopFlow() {
    if (!state.running) {
      log('当前没有正在运行的流程', 'error');
      return;
    }
    state.running = false;
    state.stopped = true;
    if (Engine.cancel) Engine.cancel();
    state.runningIdx = -1;
    $('#btn-run').disabled = false;
    $('#btn-stop').disabled = true;
    renderFlow();
    log('正在停止…（等待中的指令会立即中断）', 'error');
  }

  // ===== 录制 =====
  // 开始录制（mode: 'web' 录制网页 | 'win' 录制电脑操作 | 'table' 录制表格）
  function startRecord(mode) {
    state.recording = true;
    state.recordMode = mode;
    state.lastOpTime = Date.now();
    state.recordCount = 0;
    const btn = $('#btn-record');
    btn.classList.add('recording');
    btn.textContent = mode === 'web' ? '⏹ 停止网页录制'
      : mode === 'win' ? '⏹ 停止电脑录制'
      : '⏹ 停止表格录制';
    if (mode === 'web') {
      log('开始录制网页… 请在浏览器窗口中操作', 'success');
      if (window.__showBrowser) window.__showBrowser();
    } else if (mode === 'win') {
      log('开始录制电脑操作… 请在【本软件窗口内】或内置浏览器里操作，每一步都会实时加入右侧/中间的流程编排', 'success');
      // 电脑录制也显示内置浏览器，方便录制网页操作
      if (window.__showBrowser) window.__showBrowser();
    } else {
      log('开始录制表格… 请在 Excel 编辑器里复制、粘贴（自动记录源表格→目标表格）', 'success');
      // 确保 Excel 编辑器打开
      openExcelEditor('embed');
    }
    // 两种模式都启动浏览器事件轮询（电脑模式额外记录等待时间 + 主应用内鼠标键盘）
    if (window.__startRecordPolling) window.__startRecordPolling();
    if (mode === 'win') {
      if (window.__startWinRecord) window.__startWinRecord();
      else log('⚠ 录制监听未就绪（初始化异常），请重启软件后再试', 'error');
    }
  }

  function stopRecord() {
    state.recording = false;
    const btn = $('#btn-record');
    btn.classList.remove('recording');
    btn.textContent = '⏺ 录制 ▾';
    // 停浏览器事件轮询（两种模式都启用了）
    if (window.__stopRecordPolling) window.__stopRecordPolling();
    // 电脑模式额外停主应用内鼠标键盘监听
    if (state.recordMode === 'win' && window.__stopWinRecord) window.__stopWinRecord();
    log('录制结束');
    renderRecordMenuState();
  }

  // 录制下拉菜单显示/隐藏
  function toggleRecordMenu(show) {
    const menu = $('#record-menu');
    if (menu) menu.classList.toggle('show', show);
  }

  function renderRecordMenuState() {
    const web = $('#record-web');
    const win = $('#record-win');
    const table = $('#record-table');
    if (web) web.classList.toggle('active', state.recording && state.recordMode === 'web');
    if (win) win.classList.toggle('active', state.recording && state.recordMode === 'win');
    if (table) table.classList.toggle('active', state.recording && state.recordMode === 'table');
  }

  // ===== 浏览器窗口（独立 BrowserWindow） =====
  function setupBrowser() {
    const B = window.yingdao.browser;

    // 手动新建窗口时用的登录方式：默认「独立登录(每次全新)」——
    // 每个窗口一份全新会话、互不串号，这样同一个网站可以同时登不同账号。
    // （指令「打开网页」里可以单独选登录方式，这里是界面上按钮的默认值）
    const DEFAULT_LOGIN_MODE = '独立登录(每次全新)';

    // 打开浏览器窗口（已有则聚焦最后一个，没有才新建）——给"运行流程/录制"用，避免每次多开窗口
    async function showBrowser() {
      const tabs = await B.getTabs();
      if (tabs && tabs.length > 0) {
        await B.switchTab(tabs[tabs.length - 1].id);
      } else {
        await B.newTab('about:blank', DEFAULT_LOGIN_MODE);
      }
      renderTaskbar();
    }
    window.__showBrowser = showBrowser;

    // 新建浏览器窗口（点顶栏「🌐 浏览器」时用：每次都是新窗口 + 独立登录会话）
    async function newBrowserWindow() {
      const r = await B.newTab('about:blank', DEFAULT_LOGIN_MODE);
      log(`已新建浏览器窗口${r && r.badge ? ' [' + r.badge + ']' : ''}（独立登录，可同时登不同账号）`, 'success');
      renderTaskbar();
    }
    window.__newBrowserWindow = newBrowserWindow;

    // 导航事件（传 { id, url }）
    B.onNavigated((payload) => {
      renderTaskbar();
    });
    B.onTitleUpdated((payload) => {
      renderTaskbar();
    });
    B.onWindowClosed(() => {
      renderTaskbar();
    });
    if (B.onDataCleared) B.onDataCleared(() => renderTaskbar());
    // 加载失败也要刷新任务栏（否则新开的窗口不会出现在任务栏里）
    B.onLoadFailed((info) => {
      renderTaskbar();
      if (info && info.url) log(`网页加载失败：${info.desc || info.code} — ${info.url}`, 'error');
    });
    // 摘取元素结果：自动生成抓取指令
    B.onScrapePicked((r) => {
      if (!r || r.canceled) {
        log('摘取已取消', 'error');
        return;
      }
      if (r.count > 1) {
        // 同类元素有多个：生成"抓取文本（全部匹配）"指令
        addRecordedStep('scrapeText', { selector: r.css, varName: '抓取结果', by: '智能匹配', all: '全部匹配' });
        log(`🎯 已摘取：${r.css} 共 ${r.count} 个匹配项，已生成抓取指令（全部匹配）`, 'success');
        // 预览样本
        if (r.samples && r.samples.length) {
          log(`   样本预览：${r.samples.slice(0, 5).join(' | ')}`, 'time');
        }
      } else {
        // 单个元素：生成"抓取文本（单个）"指令
        addRecordedStep('scrapeText', { selector: r.css, varName: '抓取结果', by: '智能匹配', all: '单个' });
        log(`🎯 已摘取文本：${r.text || r.css}`, 'success');
      }
    });
    B.onLoadFailed((info) => {
      if (info.code !== -3) log(`网页加载失败：${info.desc}`, 'error');
    });

    // 缩放百分比显示（浏览器窗口内有悬浮工具栏，此处仅做状态同步）
    B.onZoomChanged((pct) => { /* 缩放状态已在独立窗口内显示 */ });

    // 录制事件轮询：录制状态下，定时读取浏览器内用户操作，转为流程步骤
    let recordPollTimer = null;
    function startRecordPolling() {
      if (recordPollTimer) return;
      recordPollTimer = setInterval(async () => {
        if (!state.recording) return;
        try {
          const events = await B.consumeEvents();
          if (events && events.length > 0) {
            events.forEach(ev => {
              // 电脑录制模式：用 recordOpWithWait 自动插入等待时间
              if (state.recordMode === 'win') {
                if (ev.type === 'click') {
                  recordOpWithWait('click', { selector: ev.selector, clickType: '单击', by: '智能匹配' }, `已录制：点击元素 ${ev.text || ev.selector}`);
                } else if (ev.type === 'input') {
                  recordOpWithWait('input', { selector: ev.selector, text: ev.text, clear: '是', by: '智能匹配' }, `已录制：输入文本 ${ev.text}`);
                } else if (ev.type === 'hotkey') {
                  recordOpWithWait('hotkey', { keys: ev.keys }, `已录制：快捷键 ${ev.keys}`);
                } else if (ev.type === 'typeText') {
                  recordOpWithWait('typeText', { text: ev.text }, `已录制：模拟按键 ${ev.text}`);
                } else if (ev.type === 'pageLoad') {
                  recordOpWithWait('sleep', { seconds: 2 }, '已录制：等待（页面加载）2 秒');
                }
                return;
              }
              // 网页录制模式：直接记录
              if (ev.type === 'click') {
                addRecordedStep('click', { selector: ev.selector, clickType: '单击', by: '智能匹配' });
                log(`已录制：点击元素 ${ev.text || ev.selector}`);
              } else if (ev.type === 'input') {
                addRecordedStep('input', { selector: ev.selector, text: ev.text, clear: '是', by: '智能匹配' });
                log(`已录制：输入文本 ${ev.text}`);
              } else if (ev.type === 'hotkey') {
                addRecordedStep('hotkey', { keys: ev.keys });
                log(`已录制：快捷键 ${ev.keys}`);
              } else if (ev.type === 'typeText') {
                addRecordedStep('typeText', { text: ev.text });
                log(`已录制：模拟按键 ${ev.text}`);
              } else if (ev.type === 'pageLoad') {
                addRecordedStep('sleep', { seconds: 2 });
                log('已录制：等待（页面加载）2 秒');
              }
            });
          }
        } catch (e) { /* 忽略轮询错误 */ }
      }, 800);
    }
    function stopRecordPolling() {
      if (recordPollTimer) { clearInterval(recordPollTimer); recordPollTimer = null; }
    }
    window.__startRecordPolling = startRecordPolling;
    window.__stopRecordPolling = stopRecordPolling;
  }

  // ===== 录制电脑操作（Windows 操作 + 自动等待时间） =====
  function setupWinRecord() {
    let keyBuf = '';   // 连续普通按键缓存（合并成一段文本）
    let keyBufTimer = null;

    // 鼠标点击（记录坐标）
    function onMouseDown(e) {
      if (!state.recording || state.recordMode !== 'win') return;
      // 忽略录制按钮/菜单自身的点击
      if (e.target.closest('#record-menu-wrap')) return;
      recordOpWithWait('mouseClick', { x: e.clientX, y: e.clientY, button: e.button === 2 ? '右键' : '左键' },
        `已录制：鼠标${e.button === 2 ? '右键' : '左键'}点击 (${e.clientX}, ${e.clientY})`);
    }

    // 键盘（组合键 → hotkey，普通键 → typeText）
    function onKeyDown(e) {
      if (!state.recording || state.recordMode !== 'win') return;
      if (['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) return;
      const mods = [];
      if (e.ctrlKey) mods.push('Ctrl');
      if (e.shiftKey) mods.push('Shift');
      if (e.altKey) mods.push('Alt');
      if (e.metaKey) mods.push('Meta');
      if (mods.length > 0) {
        const key = e.key.length === 1 ? e.key.toUpperCase() : e.key;
        const keys = mods.concat([key]).join('+');
        recordOpWithWait('hotkey', { keys }, `已录制：快捷键 ${keys}`);
      } else if (e.key.length === 1) {
        // 普通字符按键：合并成文本（等待输入停顿后一起记录）
        keyBuf += e.key;
        if (keyBufTimer) clearTimeout(keyBufTimer);
        keyBufTimer = setTimeout(() => {
          if (keyBuf) {
            const txt = keyBuf;
            keyBuf = '';
            recordOpWithWait('typeText', { text: txt }, `已录制：输入文本 ${txt}`);
          }
        }, 600);
      }
    }

    function startWinRecord() {
      document.addEventListener('mousedown', onMouseDown, true);
      document.addEventListener('keydown', onKeyDown, true);
    }
    function stopWinRecord() {
      document.removeEventListener('mousedown', onMouseDown, true);
      document.removeEventListener('keydown', onKeyDown, true);
      // 残留按键缓存也记录
      if (keyBuf) {
        const txt = keyBuf; keyBuf = '';
        recordOpWithWait('typeText', { text: txt }, `已录制：输入文本 ${txt}`);
      }
    }

    window.__startWinRecord = startWinRecord;
    window.__stopWinRecord = stopWinRecord;
  }

  // ===== 保存/打开流程 =====
  async function saveFlow() {
    const path = await window.yingdao.saveFile((state.flowName || '流程') + '.json');
    if (!path) return;
    // 保存时去掉 _uid（运行时字段），多流程存 { flows: {...} }，并记录流程名
    const flows = {};
    Object.keys(state.flows).forEach(name => {
      flows[name] = state.flows[name].map(({ _uid, ...rest }) => rest);
    });
    const data = JSON.stringify({ name: state.flowName, flows }, null, 2);
    await window.yingdao.writeText(path, data);
    log('流程已保存到：' + path, 'success');
  }

  // 从指定文件加载流程（「打开」按钮、以及把 json 拖到 exe 上打开，都走这里）
  async function loadFlowFromPath(path) {
    if (!path) return false;
    let text = '';
    try { text = await window.yingdao.readText(path); } catch (e) { }
    try {
      const loaded = JSON.parse(text);
      // 恢复流程名
      if (loaded && loaded.name) {
        state.flowName = loaded.name;
        const appNameEl = $('.app-name');
        if (appNameEl) appNameEl.textContent = state.flowName;
      }
      // 兼容旧格式（纯步骤数组）与新格式（{ flows: {...} }）
      const patchUid = (arr) => arr.map(s => ({ ...s, level: s.level || 0, _uid: 'u' + (stepUidSeq++) }));
      if (loaded && loaded.flows && typeof loaded.flows === 'object') {
        state.flows = {};
        Object.keys(loaded.flows).forEach(name => {
          state.flows[name] = patchUid(loaded.flows[name] || []);
        });
        if (!state.flows['主流程']) state.flows['主流程'] = [];
        state.activeFlow = '主流程';
      } else if (Array.isArray(loaded)) {
        state.flows = { '主流程': patchUid(loaded) };
        state.activeFlow = '主流程';
      } else {
        throw new Error('格式错误');
      }
      state.collapsedSteps.clear();
      clearSel();
      renderFlowTabs();
      renderFlow();
      renderProps();
      log('流程已加载：' + path, 'success');
      return true;
    } catch (e) {
      log('流程文件格式错误：' + path, 'error');
      return false;
    }
  }

  async function openFlow() {
    const path = await window.yingdao.openFile();
    if (!path) return;
    await loadFlowFromPath(path);
  }

  // ===== 流程编排 ↔ 表格（把流程当表格改，改完再应用回流程）=====
  // 序列化在 flow-sheet.js 里（纯函数，方便单独测），这里只负责"建表 / 读表 / 调界面"
  const FLOW_SHEET_NAME = (window.FlowSheet && window.FlowSheet.SHEET_NAME) || '流程编排';

  // 流程 → 表格
  function flowToSheet() {
    if (typeof XLSX === 'undefined' || !window.FlowSheet) { log('组件未加载', 'error'); return; }
    const flowName = state.activeFlow || '主流程';
    const steps = state.flows[flowName] || [];
    if (!steps.length) { log('「' + flowName + '」还是空的，先加几步再导', 'error'); return; }

    const rows = window.FlowSheet.toRows(steps, window.COMMANDS || []);
    // 用一张新表承载，不动用户已经打开的表格
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(rows), FLOW_SHEET_NAME);
    Engine.registerBook(wb, null, FLOW_SHEET_NAME);
    renderTaskbar();
    openExcelEditor();
    log('已把「' + flowName + '」的 ' + steps.length + ' 步写进表格「' + FLOW_SHEET_NAME + '」，改完点「表格→流程」应用回去', 'success');
    log('表格说明：序号=第几步；层级=缩进（0 最外层，1 在循环/判断里）；删掉整行=删掉这一步；「指令ID」列别改', '');
  }

  // 表格 → 流程
  function sheetToFlow() {
    if (typeof XLSX === 'undefined' || !window.FlowSheet) { log('组件未加载', 'error'); return; }
    const cur = Engine.getActiveBook && Engine.getActiveBook();
    if (!cur || !cur.book) { log('没有打开任何表格，请先点「流程→表格」', 'error'); return; }

    let ws = cur.book.Sheets[FLOW_SHEET_NAME];
    let sheetName = FLOW_SHEET_NAME;
    if (!ws) {
      sheetName = Engine.getActiveSheetName ? Engine.getActiveSheetName() : '';
      ws = cur.book.Sheets[sheetName];
    }
    if (!ws) { log('没找到「' + FLOW_SHEET_NAME + '」表，请先点「流程→表格」生成', 'error'); return; }

    const aoa = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
    const r = window.FlowSheet.fromRows(aoa, window.COMMANDS || []);
    if (r.error) { log(r.error, 'error'); return; }

    const target = state.activeFlow || '主流程';
    state.flows[target] = r.steps.map(s => Object.assign({}, s, { _uid: 'u' + (stepUidSeq++) }));
    state.collapsedSteps.clear();
    clearSel();
    renderFlowTabs();
    renderFlow();
    renderProps();
    log('已用表格「' + sheetName + '」更新流程「' + target + '」：' + r.steps.length + ' 步', 'success');
    if (r.skipped.length) {
      log('有 ' + r.skipped.length + ' 行没认出来，已跳过：' + r.skipped.slice(0, 5).join('、') +
          (r.skipped.length > 5 ? ' …' : ''), 'error');
    }
  }

  // 导出为双击即可运行的程序（生成文件夹：运行流程.bat + runner.js + flow.json + 便携 node + xlsx）
  async function exportRunable() {
    const mainSteps = state.flows['主流程'] || [];
    if (!mainSteps.length) { log('主流程为空，无法导出', 'error'); return; }
    if (!window.yingdao.exportFlowRunner) { log('当前版本不支持导出', 'error'); return; }
    const dir = await window.yingdao.openDir('选择导出目录（将创建「流程名」子文件夹）');
    if (!dir) return;
    // 去掉 _uid 运行时字段
    const clean = mainSteps.map(({ _uid, ...rest }) => rest);
    const name = state.flowName || '未命名流程';
    try {
      const r = await window.yingdao.exportFlowRunner({ flow: clean, dir: dir, name: name });
      log('已导出到：' + r.dir, 'success');
      if (r.hasNode) {
        log('已内置 Node 运行环境，目标电脑不用装任何东西就能跑', 'success');
      } else {
        // 这里必须说清楚"怎么办"，否则用户换台电脑只会看到"没有环境"却无从下手
        log('⚠ 这次没能带上 Node 运行环境：' + (r.nodeHint || '未在本机找到 node.exe'), 'error');
        log('⚠ 补救办法：把主程序目录里的 resources\\node\\node.exe 复制到导出文件夹（与「运行流程.bat」放一起），再双击即可', 'error');
      }
      if (!r.hasXlsx) log('⚠ 未找到 xlsx 依赖，Excel 指令将无法运行', 'error');
      log('双击该文件夹里的「运行流程.bat」即可运行', 'success');
    } catch (e) {
      log('导出失败：' + e.message, 'error');
    }
  }

  // ===== 切换底部标签页 =====
  function switchTab(tabName) {
    document.querySelectorAll('.btab').forEach(t => {
      t.classList.toggle('active', t.dataset.tab === tabName);
    });
    document.querySelectorAll('.bottom-view').forEach(v => {
      v.classList.toggle('active', v.id === tabName + '-view');
    });
    // 切到数据表格时刷新
    if (tabName === 'vars') renderVars();
  }

  // ===== 底部任务栏（多标签切换） =====
  async function renderTaskbar() {
    const items = $('#taskbar-items');
    if (!items) return;
    let html = '';

    // 浏览器标签（带登录会话标记：共用 / 账号位1 / 新会话#2 —— 一眼看出哪个窗口是哪个账号）
    try {
      const tabs = await window.yingdao.browser.getTabs();
      tabs.forEach(t => {
        const label = t.title || t.url || '新窗口';
        const badge = t.badge
          ? ` <span style="color:#4a6cf7;font-weight:600">[${escapeHtml(t.badge)}]</span>`
          : '';
        const tip = t.badge ? `登录会话：${escapeHtml(t.badge)}（各窗口互相独立，可同时登不同账号）` : '';
        html += `<div class="taskbar-item browser" data-type="browser" data-id="${t.id}" title="${tip}">
          <span class="t-label">🌐 ${escapeHtml(label)}${badge}</span>
          <span class="t-close" data-close="${t.id}">✕</span>
        </div>`;
      });
    } catch (e) {}

    // Excel 标签（每个表格可作为独立窗口打开，可同时开多个）
    try {
      const books = Engine.getBooks ? Engine.getBooks() : [];
      books.forEach(b => {
        const name = b.path ? b.path.split(/[\\/]/).pop() : '未命名表格';
        const sheet = b.activeSheet || (b.sheetNames && b.sheetNames[0]) || '';
        const isPopped = !!state.excelEditors[b.id];
        html += `<div class="taskbar-item excel${isPopped ? ' popped' : ''}" data-type="excel" data-id="${b.id}" title="${isPopped ? '已在独立窗口打开，点击聚焦' : '点击打开 Excel 编辑器'}">
          <span class="t-label">📊 ${escapeHtml(name)} [${escapeHtml(sheet)}]${isPopped ? ' ⧉' : ''}</span>
          <span class="t-close" data-close="${b.id}">✕</span>
        </div>`;
      });
    } catch (e) {}

    items.innerHTML = html;

    // 高亮当前激活标签
    try {
      const activeB = await window.yingdao.browser.getTabs();
      // 浏览器激活态：默认高亮最后一个（主进程 activeBrowserId 管理的）
    } catch (e) {}

    // 绑定点击切换 + 关闭
    items.querySelectorAll('.taskbar-item').forEach(item => {
      item.addEventListener('click', (e) => {
        if (e.target.dataset.close) return; // 点关闭按钮
        const type = item.dataset.type;
        const id = item.dataset.id;
        if (type === 'browser') {
          // 聚焦对应独立窗口
          window.yingdao.browser.switchTab(id).then(() => {
            renderTaskbar();
          });
        } else if (type === 'excel') {
          Engine.switchBook(id);
          // 已弹出独立窗口 → 聚焦；否则打开编辑器（默认也是独立窗口）
          const editorId = state.excelEditors[id];
          if (editorId) {
            window.yingdao.excel.focusEditor(editorId).then((r) => {
              if (!r || !r.ok) {
                delete state.excelEditors[id];
                openExcelEditor();
              } else {
                renderTaskbar();
              }
            });
          } else {
            openExcelEditor();
            renderTaskbar();
          }
        }
      });
    });
    // 绑定关闭按钮
    items.querySelectorAll('.t-close').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = btn.dataset.close;
        const type = btn.closest('.taskbar-item').dataset.type;
        if (type === 'browser') {
          await window.yingdao.browser.closeTab(id);
        } else if (type === 'excel') {
          // 该表格若已弹出独立窗口，一并关闭
          const editorId = state.excelEditors[id];
          if (editorId) {
            await window.yingdao.excel.closeEditor(editorId);
            delete state.excelEditors[id];
          }
          Engine.closeBook(id);
        }
        renderTaskbar();
      });
    });
  }

  function setupTaskbar() {
    $('#taskbar-add-browser').addEventListener('click', async () => {
      // 新窗口默认「独立登录(每次全新)」：每次都是干净会话，方便登不同账号
      const r = await window.yingdao.browser.newTab('about:blank', '独立登录(每次全新)');
      log(`已新建浏览器窗口${r && r.badge ? ' [' + r.badge + ']' : ''}（独立登录，互不串号）`, 'success');
      renderTaskbar();
    });

    // 清空浏览器登录数据：多账号切换前把之前残留的登录状态清干净
    const clearBtn = $('#taskbar-clear-browser');
    if (clearBtn) {
      clearBtn.addEventListener('click', async () => {
        const yes = confirm(
          '确定要清空所有浏览器的登录数据吗？\n\n' +
          '会清掉：\n' +
          '  · 以前“共用登录”残留的登录状态\n' +
          '  · 各账号位保存的登录状态\n' +
          '  · 当前已打开浏览器窗口的登录状态（清完需重新登录）\n\n' +
          '程序自身的设置不受影响。\n（想直接换账号，也可以关掉窗口重新开一个，新窗口本来就是全新会话）'
        );
        if (!yes) return;
        try {
          const r = await window.yingdao.browser.clearData();
          const names = (r && r.cleared) || [];
          const shown = names.slice(0, 6).join('、') + (names.length > 6 ? ' 等' : '');
          log(`🧹 已清空浏览器登录数据：共 ${names.length} 份会话${shown ? '（' + shown + '）' : ''}`, 'success');
        } catch (e) {
          log('清空登录数据失败：' + (e && e.message ? e.message : e), 'error');
        }
        renderTaskbar();
      });
    }

    $('#taskbar-add-excel').addEventListener('click', () => {
      Engine.excelNewInMemory('Sheet1');
      openExcelEditor();
      log('已新建 Excel 标签', 'success');
      renderTaskbar();
    });
  }

  // ===== 分栏面板：拖动分隔条调整大小（指令/属性左右宽度、日志上下高度）=====
  // 尺寸存 localStorage，下次打开沿用；双击分隔条恢复默认。
  function makeSplitResizable(splitEl, opts) {
    if (!splitEl || splitEl.dataset.splitReady === '1') return;
    splitEl.dataset.splitReady = '1';
    const {
      target,        // 要改变尺寸的元素选择器
      dir,           // 'h' 水平拖（改宽度）| 'v' 垂直拖（改高度）
      lsKey,         // localStorage 键
      min = 120,     // 最小尺寸
      max = 1200,    // 最大尺寸
      dflt           // 默认尺寸（双击恢复）
    } = opts;

    const apply = (v) => {
      if (dir === 'v') target.style.height = v + 'px';
      else target.style.width = v + 'px';
    };
    const save = () => {
      try {
        localStorage.setItem(lsKey, String(dir === 'v' ? target.offsetHeight : target.offsetWidth));
      } catch (e) { }
    };

    // 恢复上次尺寸
    try {
      const v = parseInt(localStorage.getItem(lsKey), 10);
      if (Number.isFinite(v) && v >= min && v <= max) apply(v);
    } catch (e) { }

    splitEl.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return;
      e.preventDefault();
      splitEl.classList.add('dragging');
      const startX = e.clientX, startY = e.clientY;
      const startSize = dir === 'v' ? target.offsetHeight : target.offsetWidth;
      const move = (ev) => {
        const delta = dir === 'v' ? (startY - ev.clientY) : (ev.clientX - startX);
        // 右侧/底部面板：向左/向上拖 = 变大；这里按 dir 决定符号
        const sign = (dir === 'v' || splitEl.id === 'split-right') ? 1 : 1;
        // split-left 在左面板右侧，向右拖 = 变宽（delta 为正）；split-right 在右面板左侧，向左拖 = 变宽
        let size;
        if (splitEl.id === 'split-right') size = startSize - delta;
        else size = startSize + delta;
        size = Math.max(min, Math.min(max, size));
        apply(size);
      };
      const up = () => {
        splitEl.classList.remove('dragging');
        document.removeEventListener('mousemove', move);
        document.removeEventListener('mouseup', up);
        document.body.style.userSelect = '';
        document.body.style.cursor = '';
        save();
      };
      document.body.style.userSelect = 'none';
      document.body.style.cursor = dir === 'v' ? 'row-resize' : 'col-resize';
      document.addEventListener('mousemove', move);
      document.addEventListener('mouseup', up);
    });

    // 双击恢复默认
    splitEl.addEventListener('dblclick', () => {
      apply(dflt);
      try { localStorage.removeItem(lsKey); } catch (e) { }
    });
  }

  // 初始化三个分隔条：指令面板宽 / 属性面板宽 / 底部日志高
  function setupPanelSplitters() {
    const left = document.querySelector('.panel-left');
    const right = document.querySelector('.panel-right');
    const bottom = document.querySelector('.bottombar');
    if (left && $('#split-left')) {
      makeSplitResizable($('#split-left'), { target: left, dir: 'h', lsKey: 'rpa.panel.leftW', min: 160, max: 500, dflt: 240 });
    }
    if (right && $('#split-right')) {
      makeSplitResizable($('#split-right'), { target: right, dir: 'h', lsKey: 'rpa.panel.rightW', min: 200, max: 600, dflt: 280 });
    }
    if (bottom && $('#split-bottom')) {
      makeSplitResizable($('#split-bottom'), { target: bottom, dir: 'v', lsKey: 'rpa.panel.bottomH', min: 100, max: 600, dflt: 180 });
    }
  }

  // ===== 界面内窗口：拖拽移动 + 右下角缩放（位置尺寸记住，下次沿用）=====
  // 用于内嵌的 Excel 编辑器这类"贴边停靠"的面板：拖标题栏就从停靠变自由摆放，
  // 拖右下角三角可以缩放；双击标题栏恢复默认停靠。
  function makePanelDraggable(el, lsKey) {
    if (!el || el.dataset.draggableReady === '1') return;
    const header = el.querySelector('.excel-modal-header') || el.firstElementChild;
    if (!header) return;
    el.dataset.draggableReady = '1';

    const applyGeom = (g) => {
      el.style.left = g.left + 'px';
      el.style.top = g.top + 'px';
      el.style.width = g.width + 'px';
      el.style.height = g.height + 'px';
      el.style.right = 'auto';
      el.style.bottom = 'auto';
    };
    const saveGeom = () => {
      const r = el.getBoundingClientRect();
      try {
        localStorage.setItem(lsKey, JSON.stringify({
          left: Math.round(r.left), top: Math.round(r.top),
          width: Math.round(r.width), height: Math.round(r.height)
        }));
      } catch (e) { }
    };
    // 从"贴边停靠"切成"自由摆放"（不切的话把 left/top 拖动不了）
    const pinDown = () => {
      const r = el.getBoundingClientRect();
      applyGeom({ left: Math.round(r.left), top: Math.round(r.top), width: Math.round(r.width), height: Math.round(r.height) });
    };
    // 恢复上次的位置尺寸
    try {
      const saved = JSON.parse(localStorage.getItem(lsKey) || 'null');
      if (saved && Number.isFinite(saved.width) && Number.isFinite(saved.height)) {
        applyGeom({
          left: Math.min(Math.max(0, saved.left), Math.max(0, window.innerWidth - 200)),
          top: Math.min(Math.max(0, saved.top), Math.max(0, window.innerHeight - 80)),
          width: Math.max(320, saved.width),
          height: Math.max(220, saved.height)
        });
      }
    } catch (e) { }

    const dragLoop = (e, onMove) => {
      e.preventDefault();
      const sx = e.clientX, sy = e.clientY;
      const r = el.getBoundingClientRect();
      const move = (ev) => onMove(r, ev.clientX - sx, ev.clientY - sy);
      const up = () => {
        document.removeEventListener('mousemove', move);
        document.removeEventListener('mouseup', up);
        document.body.style.userSelect = '';
        saveGeom();
      };
      document.body.style.userSelect = 'none';
      document.addEventListener('mousemove', move);
      document.addEventListener('mouseup', up);
    };

    header.title = (header.title ? header.title + ' · ' : '') + '拖动可移动窗口，双击恢复默认位置';
    header.addEventListener('mousedown', (e) => {
      if (e.target.closest('button, input, select, a, textarea')) return;   // 点按钮/输入框不算拖动
      if (e.button !== 0) return;
      pinDown();
      dragLoop(e, (r, dx, dy) => {
        const left = Math.max(-r.width + 90, Math.min(window.innerWidth - 90, r.left + dx));
        const top = Math.max(0, Math.min(window.innerHeight - 40, r.top + dy));
        el.style.left = Math.round(left) + 'px';
        el.style.top = Math.round(top) + 'px';
      });
    });
    header.addEventListener('dblclick', (e) => {
      if (e.target.closest('button, input, select, a, textarea')) return;
      el.style.left = ''; el.style.top = ''; el.style.right = ''; el.style.bottom = '';
      el.style.width = ''; el.style.height = '';
      try { localStorage.removeItem(lsKey); } catch (err) { }
      log('窗口已恢复默认位置', 'success');
    });

    const grip = document.createElement('div');
    grip.className = 'win-resize-grip';
    grip.title = '拖动可缩放窗口大小';
    el.appendChild(grip);
    grip.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return;
      e.stopPropagation();
      pinDown();
      dragLoop(e, (r, dx, dy) => {
        el.style.width = Math.max(320, Math.round(r.width + dx)) + 'px';
        el.style.height = Math.max(200, Math.round(r.height + dy)) + 'px';
      });
    });
  }

  // ===== Excel 编辑器（独立挂件窗口 / 内嵌模态窗口） =====
  const excelState = { zoom: 1 };
  let excelGrid = null;   // 内嵌编辑器使用的共享 WPS 风格网格实例

  // 结构操作：工具栏按钮与网格右键菜单共用；录制模式下自动记录为流程步骤
  function excelStructure(action, index, count, label) {
    count = count || 1;
    const rowActs = { insertRowBefore: index, insertRowAfter: index + 1, deleteRow: index };
    const colActs = { insertColBefore: index, insertColAfter: index + 1, deleteCol: index };
    try {
      if (rowActs[action] !== undefined) {
        if (action === 'deleteRow') Engine.excelDeleteRow(rowActs[action], count);
        else Engine.excelInsertRow(rowActs[action], count);
      } else if (colActs[action] !== undefined) {
        if (action === 'deleteCol') Engine.excelDeleteCol(colActs[action], count);
        else Engine.excelInsertCol(colActs[action], count);
      } else {
        return false;   // clearRow / clearCol 由网格自行在内容层处理
      }
    } catch (e) {
      log(e.message, 'error');
      return false;
    }
    if (label) log(label, 'success');
    // 录制：与工具栏按钮行为保持一致
    if (state.recording) {
      const cmdMap = {
        insertRowBefore: ['excelInsertRow', 'row'], insertRowAfter: ['excelInsertRow', 'row'],
        deleteRow: ['excelDeleteRow', 'row'],
        insertColBefore: ['excelInsertCol', 'col'], insertColAfter: ['excelInsertCol', 'col'],
        deleteCol: ['excelDeleteCol', 'col']
      };
      const m = cmdMap[action];
      if (m) {
        const p = m[1] === 'row' ? { row: rowActs[action], count } : { col: colActs[action], count };
        addRecordedStep(m[0], p);
        log('已录制：' + (label || action));
      }
    }
    return true;
  }

  // 创建（或复用）内嵌编辑器网格：WPS 风格交互 + 撤销重做 + 填充柄 + 右键菜单
  let varsRefreshTimer = null;
  // 编辑后延迟刷新底部「数据表格」，让改动即时可见（防抖，避免连续编辑反复重建网格）
  function scheduleVarsRefresh() {
    if (varsRefreshTimer) return;
    varsRefreshTimer = setTimeout(() => {
      varsRefreshTimer = null;
      try { renderVars(); } catch (e) { }
    }, 200);
  }

  // 当前激活表格的显示名（文件名，未命名返回「未命名表格」），供录制表格/日志用
  function currentBookName() {
    try {
      const path = Engine.getExcelPath ? Engine.getExcelPath() : '';
      if (path) return path.split(/[\\/]/).pop();
    } catch (e) { }
    return '未命名表格';
  }

  // 收集所有已打开 workbook 的工作表名（去重），供「工作表」下拉选择
  function collectSheetOptions() {
    const map = new Map();   // sheet 名 -> { label }
    try {
      if (Engine.getBooks) {
        const books = Engine.getBooks();
        books.forEach(b => {
          const name = b.path ? b.path.split(/[\\/]/).pop() : '未命名表格';
          (b.sheetNames || []).forEach(sn => {
            if (!map.has(sn)) {
              // 多个表格存在同名 sheet 时，label 带表格名前缀提示
              const dup = books.some(bb => bb !== b && (bb.sheetNames || []).includes(sn));
              map.set(sn, { label: dup ? `${name} · ${sn}` : sn });
            }
          });
        });
      }
    } catch (e) { }
    const opts = Array.from(map.entries()).map(([value, o]) => ({ value, label: o.label }));
    if (!opts.length) opts.push({ value: 'Sheet1', label: 'Sheet1' });
    return opts;
  }

  function ensureExcelGrid() {
    if (excelGrid) return excelGrid;
    excelGrid = window.ExcelGrid($('#excel-grid-wrap'), {
      getRows: () => { try { return Engine.excelToArray(); } catch (e) { return []; } },
      getRawRows: () => { try { return Engine.excelRawArray(); } catch (e) { return []; } },
      setCell: (r, c, v) => Engine.setCellValue(r, c, v),
      onEdit: (r, c, v) => {
        updateExcelStatus();
        syncExcelFormulaBar();
        scheduleVarsRefresh();     // 改完立刻反映到底部数据表格
        // 录制：写入单元格（整块粘贴/填充等无坐标的改动不单独记录）
        if (state.recording && r !== undefined && r !== null) {
          addRecordedStep('excelWrite', { cell: Engine.colName(c) + (r + 1), value: v });
          log(`已录制：写入单元格 ${Engine.colName(c)}${r + 1}`);
        }
      },
      // 复制/粘贴通知（快捷键 Ctrl+C/Ctrl+V 或右键菜单也会走这里，供「录制表格」用）
      onClipboard: (action, range) => {
        if (!state.recording || state.recordMode !== 'table') return;
        if (action === 'copy') {
          state.recordTableSrc = {
            bookId: Engine.getActiveBookId ? Engine.getActiveBookId() : null,
            bookName: currentBookName(),
            sheetName: Engine.getExcelSheetName ? Engine.getExcelSheetName() : 'Sheet1',
            range: range
          };
          log(`📊 已录制复制源：${state.recordTableSrc.bookName} / ${state.recordTableSrc.sheetName} / ${range}`, 'time');
        } else if (action === 'paste' && state.recordTableSrc) {
          const src = state.recordTableSrc;
          const dstBookName = currentBookName();
          const dstSheet = Engine.getExcelSheetName ? Engine.getExcelSheetName() : 'Sheet1';
          const isSameBook = src.bookId && Engine.getActiveBookId && src.bookId === Engine.getActiveBookId();
          addRecordedStep('excelSheetCopyPaste', {
            fromBook: isSameBook ? '' : (src.bookName || ''),
            fromSheet: src.sheetName,
            fromRange: src.range,
            toBook: isSameBook ? '' : (dstBookName || ''),
            toSheet: dstSheet,
            toRange: range,
            mode: '全部粘贴'
          });
          log(`📊 已录制表格复制粘贴：${src.bookName}/${src.sheetName}/${src.range} → ${dstBookName}/${dstSheet}/${range}`, 'success');
        }
      },
      onSelectChange: () => { syncExcelFormulaBar(); updateExcelStatus(); },
      onStats: renderExcelStats,
      onStructure: (action, index, count) => excelStructure(action, index, count),
      onRestore: (rows) => { try { Engine.setSheetValues(rows); } catch (e) { } },
      colName: (c) => Engine.colName(c),
      minRows: 20,
      minCols: 10
    });
    return excelGrid;
  }

  // 编辑栏（名称框 + 内容框，对齐 WPS）
  function syncExcelFormulaBar() {
    if (!excelGrid) return;
    try {
      const range = excelGrid.getSelRange();
      $('#excel-namebox').textContent = range;
      $('#excel-cell-info').textContent = range;
      const sel = excelGrid.getSel();
      const addr = Engine.colName(sel.c) + (sel.r + 1);
      // 公式单元格显示公式（WPS 行为）
      $('#excel-formula').value = Engine.cellText ? Engine.cellText(addr) : (Engine.excelRead(addr) ?? '');
    } catch (e) { }
  }

  // 状态栏选区统计（WPS 行为）
  function renderExcelStats(st) {
    const el = $('#excel-stat');
    if (!el) return;
    if (!st) { el.textContent = ''; return; }
    const r6 = (n) => Math.round(n * 1e6) / 1e6;
    const parts = ['计数: ' + st.count];
    if (st.numCount) parts.push('求和: ' + r6(st.sum), '平均值: ' + r6(st.avg));
    el.textContent = parts.join('   ');
  }

  // Ctrl+滚轮缩放 Excel 网格
  function setupExcelZoom() {
    const wrap = $('#excel-grid-wrap');
    wrap.addEventListener('wheel', (e) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.1 : -0.1;
      excelState.zoom = Math.min(3, Math.max(0.5, excelState.zoom + delta));
      wrap.style.zoom = excelState.zoom;
      log(`Excel 缩放：${Math.round(excelState.zoom * 100)}%`, 'success');
    }, { passive: false });
  }

  // 打开 Excel 编辑器：mode = 'external'（独立窗口，默认）| 'embed'（嵌入主界面内部）
  async function openExcelEditor(mode = 'external') {
    // 判断是否已有 Excel 打开（用工作表名判断，空表也能识别）
    let hasExcel = false;
    try { hasExcel = !!(Engine.getExcelSheetName && Engine.getExcelSheetName()); } catch (e) { hasExcel = false; }
    if (!hasExcel) {
      // 仅内存新建空表，不写盘
      try { Engine.excelNewInMemory('Sheet1'); } catch (e) { }
    }
    if (mode === 'embed') {
      // 嵌入主界面内部显示
      $('#excel-modal').classList.remove('hidden');
      renderExcelGrid();
      renderTaskbar();
      return;
    }
    // 默认：独立窗口（挂件）。同一张表格已弹出过 → 直接聚焦，不重复开窗
    const bookId = Engine.getActiveBookId ? Engine.getActiveBookId() : null;
    if (bookId && state.excelEditors[bookId]) {
      const r = await window.yingdao.excel.focusEditor(state.excelEditors[bookId]);
      if (r && r.ok) { renderTaskbar(); return; }
      delete state.excelEditors[bookId];
    }
    let rows = [];
    try { rows = Engine.excelToArray(); } catch (e) { rows = []; }
    const snapshot = {
      bookId: bookId,
      path: Engine.getExcelPath ? Engine.getExcelPath() : '',
      sheetName: Engine.getExcelSheetName ? Engine.getExcelSheetName() : 'Sheet1',
      rows: rows
    };
    const res = await window.yingdao.excel.popout(snapshot);
    if (res && res.id && bookId) state.excelEditors[bookId] = res.id;
    log('已弹出 Excel 独立窗口（可同时打开多个表格窗口，底部任务栏可切换）', 'success');
    renderTaskbar();
  }

  function closeExcelEditor() {
    $('#excel-modal').classList.add('hidden');
  }

  // 渲染 Excel 网格（复用同一实例，避免每次重建监听器）
  function renderExcelGrid() {
    renderExcelSheets();
    ensureExcelGrid().reload();
    updateExcelStatus();
    syncExcelFormulaBar();
  }

  function updateExcelStatus() {
    const pathEl = $('#excel-path');
    const dimEl = $('#excel-dim');
    const sheetEl = $('#excel-sheet-name');
    try {
      const p = Engine.getExcelPath ? Engine.getExcelPath() : '';
      if (pathEl) pathEl.textContent = p || '未保存的新文件';
      if (sheetEl) sheetEl.textContent = Engine.getExcelSheetName ? (' - ' + Engine.getExcelSheetName()) : '';
      const arr = Engine.excelToArray();
      const cols = arr.reduce((m, r) => Math.max(m, r.length), 0);
      if (dimEl) dimEl.textContent = arr.length + ' 行 × ' + cols + ' 列';
    } catch (e) {
      if (pathEl) pathEl.textContent = '未打开文件';
      if (dimEl) dimEl.textContent = '';
    }
  }

  // 渲染 sheet 标签栏
  function renderExcelSheets() {
    const bar = $('#excel-sheets');
    if (!bar) return;
    let sheetNames = [];
    try { sheetNames = Engine.getSheetNames ? Engine.getSheetNames() : []; } catch (e) { sheetNames = []; }
    const active = Engine.getActiveSheetName ? Engine.getActiveSheetName() : (sheetNames[0] || '');
    let html = '';
    sheetNames.forEach(name => {
      const cls = (name === active) ? 'sheet-tab active' : 'sheet-tab';
      html += `<span class="${cls}" data-sheet="${escapeHtml(name)}">${escapeHtml(name)}</span>`;
    });
    html += `<span class="sheet-add" id="sheet-add-btn" title="新增工作表">＋</span>`;
    bar.innerHTML = html;

    // 切换 sheet
    bar.querySelectorAll('.sheet-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        try { Engine.switchSheet(tab.dataset.sheet); } catch (e) { log(e.message, 'error'); }
        renderExcelSheets();
        renderExcelGrid();
        renderTaskbar();
      });
    });
    // 新增 sheet
    const addBtn = bar.querySelector('#sheet-add-btn');
    if (addBtn) {
      addBtn.addEventListener('click', () => {
        const name = 'Sheet' + (sheetNames.length + 1);
        try { Engine.addSheet(name); } catch (e) { log(e.message, 'error'); }
        log('已新增工作表：' + name, 'success');
        renderExcelSheets();
        renderExcelGrid();
        renderTaskbar();
      });
    }
  }

  // 保存格式按钮：显示当前勾选的格式（默认 xlsx）
  function refreshExcelFmtBtn() {
    const el = $('#excel-fmt');
    if (!el || !window.ExcelSaveFormat) return;
    const list = window.ExcelSaveFormat.getFormats();
    el.textContent = '格式：' + window.ExcelSaveFormat.label(Engine, list);
    el.title = '已选保存格式：' + list.join('、') + '\n可多选，一次保存多个文件';
  }

  // 绑定 Excel 编辑器工具栏
  function bindExcelToolbar() {
    setupExcelZoom();
    if (window.ExcelSaveFormat) window.ExcelSaveFormat.applyToEngine(Engine);
    refreshExcelFmtBtn();
    $('#excel-close').addEventListener('click', closeExcelEditor);

    // 编辑栏：回车写入当前单元格
    $('#excel-formula').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const sel = excelGrid.getSel();
        try {
          Engine.setCellValue(sel.r, sel.c, $('#excel-formula').value);
          excelGrid.reload();
          excelGrid.setSel(sel.r, sel.c);
          updateExcelStatus();
        } catch (err) { log(err.message, 'error'); }
      } else if (e.key === 'Escape') {
        syncExcelFormulaBar();
        excelGrid.focus();
      }
      e.stopPropagation();
    });
    $('#excel-formula').addEventListener('blur', () => syncExcelFormulaBar());

    // 撤销 / 重做 / 查找
    $('#excel-undo').addEventListener('click', () => {
      if (!excelGrid.undo()) log('没有可撤销的操作', 'error'); else log('已撤销', 'success');
    });
    $('#excel-redo').addEventListener('click', () => {
      if (!excelGrid.redo()) log('没有可重做的操作', 'error'); else log('已重做', 'success');
    });
    $('#excel-find').addEventListener('click', () => excelGrid.find());

    $('#excel-new').addEventListener('click', async () => {
      await Engine.excelNew('', 'Sheet1');
      log('已新建 Excel', 'success');
      renderExcelGrid();
      if (state.recording) { addRecordedStep('excelNew', { path: '', sheetName: 'Sheet1' }); log('已录制：新建Excel'); }
    });
    $('#excel-open').addEventListener('click', async () => {
      const path = await window.yingdao.openFile();
      if (!path) return;
      try {
        await Engine.excelOpen(path);
        log('已打开 Excel：' + path, 'success');
        renderExcelGrid();
        if (state.recording) { addRecordedStep('excelOpen', { path: path }); log('已录制：打开Excel ' + path); }
      } catch (e) {
        log('打开失败：' + e.message, 'error');
      }
    });
    $('#excel-save').addEventListener('click', async () => {
      try {
        const written = await Engine.excelSave('');
        log('Excel 已保存：' + (written || []).map(p => p.split(/[\\/]/).pop()).join('、'), 'success');
        updateExcelStatus();
        if (state.recording) { addRecordedStep('excelSave', { path: '' }); log('已录制：保存Excel'); }
      } catch (e) {
        log('保存失败：' + e.message, 'error');
      }
    });
    $('#excel-saveas').addEventListener('click', async () => {
      const btn = $('#excel-saveas');
      // 弹面板选命名方式：默认存到原表格目录、文件名"原名-1/2/3…"递增，不覆盖原文件
      const choice = (window.ExcelSaveAs && window.ExcelSaveAs.pick)
        ? await window.ExcelSaveAs.pick(Engine, btn)
        : { naming: '后缀递增', prefix: '', startIndex: 1 };
      if (!choice) return;
      try {
        if (choice.path) {
          // 用户点了「换到其它位置…」：按指定路径存
          const written = await Engine.excelSave(choice.path);
          log('已另存为：' + (written || []).map(p => p.split(/[\\/]/).pop()).join('、'), 'success');
          if (state.recording) addRecordedStep('excelSave', { path: choice.path });
        } else {
          const r = await Engine.excelSaveAs(choice);
          log('已另存为（' + r.naming + '）：' + (r.written || []).map(p => p.split(/[\\/]/).pop()).join('、'), 'success');
          if (state.recording) addRecordedStep('excelSaveAs', { naming: r.naming, prefix: choice.prefix || '', startIndex: choice.startIndex || 1 });
        }
        updateExcelStatus();
        renderTaskbar();
      } catch (e) {
        log('另存为失败：' + e.message, 'error');
      }
    });
    // 保存格式：可多选，默认只勾 xlsx（选择后持久化，下次沿用）
    $('#excel-fmt').addEventListener('click', async (e) => {
      e.stopPropagation();
      if (!window.ExcelSaveFormat) return;
      const picked = await window.ExcelSaveFormat.pick(Engine, $('#excel-fmt'));
      if (picked) {
        refreshExcelFmtBtn();
        log('保存格式：' + picked.join('、'), 'success');
      }
    });
    // 行列操作（基于当前选中单元格，行列号从 1 开始）
    $('#excel-insrow').addEventListener('click', () => {
      const s = excelGrid.getSel();
      if (excelStructure('insertRowBefore', s.r + 1, 1, '已在第 ' + (s.r + 1) + ' 行前插入一行')) renderExcelGrid();
    });
    $('#excel-inscol').addEventListener('click', () => {
      const s = excelGrid.getSel();
      if (excelStructure('insertColBefore', s.c + 1, 1, '已在第 ' + Engine.colName(s.c) + ' 列前插入一列')) renderExcelGrid();
    });
    $('#excel-delrow').addEventListener('click', () => {
      const s = excelGrid.getSel();
      if (excelStructure('deleteRow', s.r + 1, 1, '已删除第 ' + (s.r + 1) + ' 行')) renderExcelGrid();
    });
    $('#excel-delcol').addEventListener('click', () => {
      const s = excelGrid.getSel();
      if (excelStructure('deleteCol', s.c + 1, 1, '已删除第 ' + Engine.colName(s.c) + ' 列')) renderExcelGrid();
    });
    // 复制选中区域（全局剪贴板 + 系统剪贴板，支持跨 sheet/跨文件/跨应用）
    $('#excel-copy').addEventListener('click', () => {
      try {
        const range = excelGrid.getSelRange();
        Engine.copyToClipboard(range);
        excelGrid.copy();   // 内部会触发 onClipboard('copy') → 录制表格模式记录源
        log('已复制区域：' + range + '（可跨 sheet/跨文件粘贴）', 'success');
      } catch (e) { log(e.message, 'error'); }
    });
    // 粘贴（全局剪贴板，支持跨 sheet/跨文件，默认全部粘贴）
    $('#excel-paste').addEventListener('click', () => {
      const sel = excelGrid.getSel();
      const to = Engine.colName(sel.c) + (sel.r + 1);
      try {
        Engine.pasteFromClipboard(to, '全部粘贴');
        log(`已粘贴到 ${to}`, 'success');
        renderExcelGrid();
        if (state.recording) {
          if (state.recordMode === 'table' && state.recordTableSrc) {
            // 录制表格模式：生成「表格复制粘贴」指令（记录源表格→目标表格）
            const src = state.recordTableSrc;
            const dstBookName = currentBookName();
            const dstSheet = Engine.getExcelSheetName ? Engine.getExcelSheetName() : 'Sheet1';
            const isSameBook = src.bookId && Engine.getActiveBookId && src.bookId === Engine.getActiveBookId();
            addRecordedStep('excelSheetCopyPaste', {
              fromBook: isSameBook ? '' : (src.bookName || ''),
              fromSheet: src.sheetName,
              fromRange: src.range,
              toBook: isSameBook ? '' : (dstBookName || ''),
              toSheet: dstSheet,
              toRange: to,
              mode: '全部粘贴'
            });
            log(`📊 已录制表格复制粘贴：${src.bookName}/${src.sheetName}/${src.range} → ${dstBookName}/${dstSheet}/${to}`, 'success');
          } else {
            addRecordedStep('excelCopyPaste', { from: '剪贴板', to: to, mode: '全部粘贴' });
            log('已录制：粘贴到 ' + to);
          }
        }
      } catch (e) {
        log(e.message, 'error');
      }
    });
    // 读取选中区域到变量
    $('#excel-readrange').addEventListener('click', () => {
      const range = excelGrid.getSelRange();
      const data = Engine.excelReadRange(range);
      Engine.vars['变量1'] = data;
      log(`已读取区域 ${range} 到变量「变量1」`, 'success');
      renderVars();
      if (state.recording) {
        addRecordedStep('excelReadRange', { range: range, varName: '变量1' });
        log('已录制：读取区域 ' + range);
      }
    });
    // 获取行数到变量
    $('#excel-getrows').addEventListener('click', () => {
      const rows = Engine.excelGetRows();
      Engine.vars['行数'] = rows;
      log('已获取行数 ' + rows + ' 到变量「行数」', 'success');
      renderVars();
      if (state.recording) {
        addRecordedStep('excelGetRows', { varName: '行数' });
        log('已录制：获取行数 ' + rows);
      }
    });
  }
  // ===== 右键菜单（拖拽出来） =====
  const ctxMenu = () => $('#ctx-menu');
  let ctxTarget = null; // 'browser' 或 'excel'

  function showCtxMenu(x, y, target) {
    ctxTarget = target;
    const menu = ctxMenu();
    menu.classList.remove('hidden');
    // 定位（防止超出窗口）
    const mw = 180, mh = 120;
    const px = Math.min(x, window.innerWidth - mw);
    const py = Math.min(y, window.innerHeight - mh);
    menu.style.left = px + 'px';
    menu.style.top = py + 'px';
  }
  function hideCtxMenu() {
    ctxMenu().classList.add('hidden');
    ctxTarget = null;
  }

  function setupCtxMenu() {
    // 点击其它地方关闭菜单
    document.addEventListener('click', hideCtxMenu);
    document.addEventListener('contextmenu', (e) => {
      // 浏览器已是独立窗口，只有 Excel 编辑器里右键才显示自定义菜单
      const inExcel = e.target.closest('#excel-modal');
      if (!inExcel) return;
      e.preventDefault();
      ctxTarget = 'excel';
      showCtxMenu(e.clientX, e.clientY, 'excel');
    });

    // 拖拽出来（仅 Excel）
    $('#ctx-popout').addEventListener('click', async () => {
      if (ctxTarget === 'excel') {
        // 统一走 openExcelEditor：带 bookId、同一表格不重复开窗
        $('#excel-modal').classList.add('hidden');
        openExcelEditor();
      }
      hideCtxMenu();
    });

    // 全屏（仅 Excel）
    $('#ctx-fullscreen').addEventListener('click', () => {
      if (ctxTarget === 'excel') {
        $('#excel-modal').classList.remove('hidden');
        if (window.yingdao.browser) window.yingdao.browser.maximize();
      }
      hideCtxMenu();
    });

    // 嵌入回去（仅 Excel）
    $('#ctx-embed').addEventListener('click', async () => {
      if (ctxTarget === 'excel') {
        await window.yingdao.excel.embed();
        log('Excel 已嵌入回窗口', 'success');
        $('#excel-modal').classList.remove('hidden');
        renderExcelGrid();
      }
      hideCtxMenu();
    });

    // 独立 Excel 窗口关闭后，主应用自动嵌入显示内部编辑器
    if (window.yingdao.excel && window.yingdao.excel.onStandaloneClosed) {
      window.yingdao.excel.onStandaloneClosed(async (info) => {
        const bookId = info && info.bookId;
        if (bookId) delete state.excelEditors[bookId];
        // 点「嵌入回去」：把这张表格嵌入主窗口；直接点 X 关闭则只同步数据
        if (info && info.embedded) {
          if (bookId && Engine.getBooks().some(b => b.id === bookId)) Engine.switchBook(bookId);
          log('Excel 独立窗口已嵌入回主窗口', 'time');
          openExcelEditor('embed');
        } else {
          log('Excel 独立窗口已关闭', 'time');
          renderVars();
        }
        renderTaskbar();
      });
    }
    // 多个独立 Excel 窗口的数据更新：按 bookId 更新对应表格（不新建标签）
    if (window.yingdao.excel && window.yingdao.excel.onSnapshotUpdated) {
      window.yingdao.excel.onSnapshotUpdated((snap) => {
        if (!snap || !snap.rows) return;
        try {
          if (snap.bookId && Engine.updateBook && Engine.updateBook(snap.bookId, snap)) {
            // 已就地更新对应表格
          } else {
            Engine.loadSnapshot ? Engine.loadSnapshot(snap) : null;
          }
        } catch (e) { }
        renderVars();
        renderTaskbar();
      });
    }
    // 拖出的单个 sheet 独立窗口编辑后，合并回主 Excel
    if (window.yingdao.excel && window.yingdao.excel.onSheetUpdated) {
      window.yingdao.excel.onSheetUpdated((data) => {
        if (data && data.rows) {
          log(`工作表「${data.sheetName}」已在独立窗口更新`, 'time');
          // 在主 Excel 里就地更新该 sheet（不再重建新标签，改完即可见）
          try {
            const bid = Engine.getActiveBookId ? Engine.getActiveBookId() : null;
            if (Engine.getSheetNames && Engine.getSheetNames().includes(data.sheetName)) {
              Engine.switchSheet(data.sheetName);
            } else {
              Engine.addSheet(data.sheetName);
            }
            Engine.updateSheet(bid, data.sheetName, data.rows, data.cells);
          } catch (e) { }
          renderVars();
        }
      });
    }
  }

  // ===== 事件绑定 =====
  function bindEvents() {
    $('#search-cmd').addEventListener('input', (e) => renderCommands(e.target.value));
    // 双击「未命名流程」标题改名
    const appNameEl = $('.app-name');
    if (appNameEl) {
      appNameEl.title = '双击修改流程名称';
      appNameEl.style.cursor = 'text';
      appNameEl.addEventListener('dblclick', () => {
        const newName = prompt('给流程命名：', state.flowName);
        if (newName && newName.trim()) {
          state.flowName = newName.trim();
          appNameEl.textContent = state.flowName;
          log('流程已命名为：' + state.flowName, 'success');
        }
      });
    }
    $('#btn-add-flow').addEventListener('click', addFlow);
    $('#btn-run').addEventListener('click', () => runFlow(0));
    $('#btn-stop').addEventListener('click', stopFlow);
    // 运行方式下拉：↓ 按钮弹出菜单，可选「从头运行」或「从选中步骤开始运行」
    const btnRunMenu = $('#btn-run-menu');
    const runMenu = $('#run-menu');
    if (btnRunMenu && runMenu) {
      btnRunMenu.addEventListener('click', (e) => {
        e.stopPropagation();
        runMenu.classList.toggle('show');
      });
      runMenu.querySelectorAll('.run-menu-item').forEach(item => {
        item.addEventListener('click', () => {
          runMenu.classList.remove('show');
          const mode = item.dataset.mode;
          if (mode === 'from-selected') {
            // 从当前选中的步骤开始往下运行
            const idx = state.selectedIdx;
            if (idx < 0 || idx >= state.steps.length) {
              log('请先选中一个步骤作为起点', 'error');
              return;
            }
            runFlow(idx);
          } else {
            runFlow(0);
          }
        });
      });
      // 点击别处关闭菜单
      document.addEventListener('click', (e) => {
        if (!runMenu.contains(e.target) && !btnRunMenu.contains(e.target)) {
          runMenu.classList.remove('show');
        }
      });
    }
    // 录制按钮：点击弹出下拉菜单（两个选项），录制中点击=停止
    $('#btn-record').addEventListener('click', (e) => {
      e.stopPropagation();
      if (state.recording) {
        stopRecord();
      } else {
        toggleRecordMenu(!$('#record-menu').classList.contains('show'));
      }
    });
    // 下拉菜单选项
    $('#record-web').addEventListener('click', () => { toggleRecordMenu(false); startRecord('web'); });
    $('#record-win').addEventListener('click', () => { toggleRecordMenu(false); startRecord('win'); });
    $('#record-table').addEventListener('click', () => { toggleRecordMenu(false); startRecord('table'); });
    // 点击其它地方关闭下拉菜单
    document.addEventListener('click', (e) => {
      if (!e.target.closest('#record-menu-wrap')) toggleRecordMenu(false);
    });
    $('#btn-save').addEventListener('click', saveFlow);
    $('#btn-open').addEventListener('click', openFlow);
    $('#btn-flow-to-sheet').addEventListener('click', flowToSheet);
    $('#btn-sheet-to-flow').addEventListener('click', sheetToFlow);
    $('#btn-export').addEventListener('click', exportRunable);
    // 打开浏览器按钮：每次新建一个独立窗口（可同时开多个）
    $('#btn-browser-open').addEventListener('click', () => {
      if (window.__newBrowserWindow) window.__newBrowserWindow();
      else if (window.__showBrowser) window.__showBrowser();
    });
    // 浏览器引擎切换：内置 / Edge / 内置Chrome（便携版）
    if (window.yingdao.browser && window.yingdao.browser.listEngines) {
      $('#btn-browser-open').addEventListener('contextmenu', async (e) => {
        e.preventDefault();
        await showEngineMenu(e.clientX, e.clientY);
      });
    }
    // Excel 编辑器按钮
    const btnExcel = $('#btn-excel');
    if (btnExcel) btnExcel.addEventListener('click', openExcelEditor);
    // 左侧指令面板折叠/展开
    const btnCollapseLeft = $('#btn-collapse-left');
    if (btnCollapseLeft) {
      btnCollapseLeft.addEventListener('click', () => {
        const panel = document.querySelector('.panel-left');
        const collapsed = panel.classList.toggle('collapsed');
        btnCollapseLeft.textContent = collapsed ? '»' : '«';
        btnCollapseLeft.title = collapsed ? '展开指令面板' : '收起指令面板';
      });
    }
    bindExcelToolbar();
    setupCtxMenu();
    setupTaskbar();
    // 三个面板分隔条：指令面板宽 / 属性面板宽 / 底部日志高（可拖动调整，尺寸记住）
    setupPanelSplitters();
    // 界面内的 Excel 编辑器窗口：支持拖拽移动 + 右下角缩放（位置尺寸记住）
    makePanelDraggable($('#excel-modal'), 'rpa.excelModal.geom');

    // 把流程 json 拖到 exe 上打开：
    //   - 程序已经在跑 → 主进程会推 flow:open 过来
    //   - 程序没在跑（拖到 exe 图标上启动）→ 主进程先存着，这里主动来取
    if (window.yingdao.onOpenFlow) {
      window.yingdao.onOpenFlow((payload) => {
        if (payload && payload.path) loadFlowFromPath(payload.path);
      });
    }
    if (window.yingdao.getPendingFlow) {
      window.yingdao.getPendingFlow().then((pending) => {
        if (pending && pending.path) loadFlowFromPath(pending.path);
      }).catch(() => { });
    }

    // 底部标签切换
    document.querySelectorAll('.btab').forEach(tab => {
      tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // 拖拽流程画布
    flowCanvas.addEventListener('dragover', (e) => e.preventDefault());
    flowCanvas.addEventListener('drop', (e) => {
      e.preventDefault();
      const cmdId = e.dataTransfer.getData('cmdId');
      if (cmdId) addStep(cmdId);
    });

    // 画布空白处鼠标框选（范围选择）；单击空白 = 取消选择
    flowCanvas.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return;
      if (e.target.closest('.flow-step')) return;   // 点在卡片上交给卡片处理
      if (state.running) return;
      const startX = e.clientX, startY = e.clientY;
      let moved = false;
      const box = document.createElement('div');
      box.className = 'flow-marquee';
      box.style.display = 'none';
      flowCanvas.appendChild(box);

      const hitRects = (x, y, w, h) => {
        const html = [];
        flowCanvas.querySelectorAll('.flow-step').forEach(el => {
          const r = el.getBoundingClientRect();
          const hit = r.left < x + w && r.right > x && r.top < y + h && r.bottom > y;
          el.classList.toggle('selected', hit);
          if (hit) html.push(el);
        });
        return html;
      };

      const onMove = (ev) => {
        if (!moved && (Math.abs(ev.clientX - startX) > 3 || Math.abs(ev.clientY - startY) > 3)) moved = true;
        if (!moved) return;
        const x = Math.min(startX, ev.clientX), y = Math.min(startY, ev.clientY);
        const w = Math.abs(ev.clientX - startX), h = Math.abs(ev.clientY - startY);
        box.style.display = 'block';
        box.style.cssText = `display:block;left:${x - flowCanvas.getBoundingClientRect().left + flowCanvas.scrollLeft}px;` +
          `top:${y - flowCanvas.getBoundingClientRect().top + flowCanvas.scrollTop}px;width:${w}px;height:${h}px`;
        hitRects(x, y, w, h);   // 实时高亮（只切 class，不整体重绘，避免框选元素被销毁）
      };
      const onUp = (ev) => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        box.remove();
        if (!moved) {
          // 单击空白：取消选择
          clearSel();
        } else {
          // 定格：按最终矩形计算选中集合
          const x = Math.min(startX, ev.clientX), y = Math.min(startY, ev.clientY);
          const w = Math.abs(ev.clientX - startX), h = Math.abs(ev.clientY - startY);
          const hitEls = hitRects(x, y, w, h);
          const uids = hitEls.map(el => uidAt(+el.dataset.idx)).filter(Boolean);
          if (uids.length) {
            state.selUids = new Set(uids);
            state.anchorUid = uids[uids.length - 1];
          } else {
            clearSel();
          }
          syncSelectedIdx();
        }
        renderFlow();
        renderProps();
      };
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });

    // 键盘删除 + 复制粘贴 + 多选
    document.addEventListener('keydown', (e) => {
      // 忽略在输入框内的按键（避免干扰输入）；也忽略 WPS 网格内的按键（网格自己处理复制/粘贴/删除）
      const tag = (e.target && e.target.tagName) || '';
      const inGrid = !!(e.target && e.target.closest && e.target.closest('.xgrid-wrap'));
      const inInput = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || inGrid;
      if (inInput || state.running) return;
      const ctrl = e.ctrlKey || e.metaKey;
      const selList = selIdxList();

      // Ctrl/⌘+A：全选流程步骤
      if (ctrl && (e.key === 'a' || e.key === 'A')) {
        if (!state.steps.length) return;
        e.preventDefault();
        selectAllSteps();
        renderFlow(); renderProps();
        log(`已全选 ${state.steps.length} 条指令`, 'success');
        return;
      }
      // Esc：取消选择
      if (e.key === 'Escape') {
        if (!state.selUids.size && state.selectedIdx < 0) return;
        clearSel(); renderFlow(); renderProps();
        return;
      }
      // Tab：选中步骤缩进到上方最近的「循环」指令内（列入循环体）；Shift+Tab 取消缩进
      if (e.key === 'Tab' && selList.length) {
        e.preventDefault();
        if (e.shiftKey) {
          // 取消缩进：level 减 1（最小 0）
          let changed = 0;
          selList.forEach(i => {
            const s = state.steps[i];
            if ((s.level || 0) > 0) { s.level = (s.level || 0) - 1; changed++; }
          });
          renderFlow();
          log(changed ? `已取消缩进 ${changed} 条指令` : '选中的指令已是最顶层', changed ? 'success' : 'time');
        } else {
          // 缩进：level = 上方最近的循环指令 level + 1
          let changed = 0, skipped = 0;
          selList.forEach(i => {
            const s = state.steps[i];
            const loopLevel = findLoopLevelAbove(i);
            if (loopLevel === null) { skipped++; return; }
            s.level = loopLevel + 1;
            changed++;
          });
          renderFlow();
          if (changed) log(`已缩进 ${changed} 条指令到循环内（Tab），Shift+Tab 可取消`, 'success');
          if (skipped) log(`有 ${skipped} 条上方没有「循环」指令，未缩进`, 'time');
        }
        return;
      }
      // Delete/Backspace：删除选中的一条或多条
      if ((e.key === 'Delete' || e.key === 'Backspace') && selList.length) {
        e.preventDefault();
        const n = deleteSelected();
        renderFlow(); renderProps();
        log(`已删除选中 ${n} 条指令`, 'success');
        return;
      }
      // Ctrl/⌘+C：复制选中（单条或多条）
      if (ctrl && (e.key === 'c' || e.key === 'C') && selList.length) {
        e.preventDefault();
        state.clipboardSteps = selList.map(i => {
          const s = state.steps[i];
          return { id: s.id, name: s.name, category: s.category, color: s.color, params: JSON.parse(JSON.stringify(s.params)), level: s.level || 0 };
        });
        state.clipboardStep = state.clipboardSteps.length === 1 ? state.clipboardSteps[0] : null; // 兼容旧逻辑
        log(`已复制 ${state.clipboardSteps.length} 条指令`, 'success');
        return;
      }
      // Ctrl/⌘+V：粘贴到主选之后（支持多条）
      if (ctrl && (e.key === 'v' || e.key === 'V')) {
        const group = (state.clipboardSteps && state.clipboardSteps.length) ? state.clipboardSteps
          : (state.clipboardStep ? [state.clipboardStep] : null);
        if (!group || !group.length) return;
        e.preventDefault();
        const insertAt = (state.selectedIdx >= 0) ? state.selectedIdx + 1 : state.steps.length;
        const added = group.map(clip => {
          const ns = {
            id: clip.id, name: clip.name, category: clip.category, color: clip.color,
            params: JSON.parse(JSON.stringify(clip.params)), level: clip.level || 0,
            _uid: 'u' + (stepUidSeq++)
          };
          state.collapsedSteps.add(ns._uid);   // 粘贴的步骤默认折叠
          return ns;
        });
        state.steps.splice(insertAt, 0, ...added);
        // 选中刚粘贴的这一组
        state.selUids = new Set(added.map(s => s._uid));
        state.anchorUid = added[added.length - 1]._uid;
        syncSelectedIdx();
        renderFlow(); renderProps();
        log(`已粘贴 ${added.length} 条指令到选中之后`, 'success');
        return;
      }
      // Ctrl/⌘+D：复制选中步骤到其后（不占用剪贴板）
      if (ctrl && (e.key === 'd' || e.key === 'D') && selList.length) {
        e.preventDefault();
        const src = selList.map(i => state.steps[i]);
        const insertAt = selList[selList.length - 1] + 1;
        const added = src.map(s => ({
          id: s.id, name: s.name, category: s.category, color: s.color,
          params: JSON.parse(JSON.stringify(s.params)), level: s.level || 0,
          _uid: 'u' + (stepUidSeq++)
        }));
        added.forEach(s => state.collapsedSteps.add(s._uid));
        state.steps.splice(insertAt, 0, ...added);
        state.selUids = new Set(added.map(s => s._uid));
        state.anchorUid = added[added.length - 1]._uid;
        syncSelectedIdx();
        renderFlow(); renderProps();
        log(`已复制 ${added.length} 条指令`, 'success');
      }
    });

    // 复制全部日志
    const btnCopyLog = $('#btn-copy-log');
    if (btnCopyLog) {
      btnCopyLog.addEventListener('click', async () => {
        const lines = Array.from(document.querySelectorAll('#log-view .log-line')).map(l => l.textContent);
        const text = lines.join('\n');
        if (!text) { log('日志为空，无可复制内容', 'error'); return; }
        try {
          await navigator.clipboard.writeText(text);
          log('已复制 ' + lines.length + ' 条日志到剪贴板', 'success');
        } catch (e) {
          // 降级：用临时 textarea
          const ta = document.createElement('textarea');
          ta.value = text;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
          log('已复制 ' + lines.length + ' 条日志到剪贴板', 'success');
        }
      });
    }

    // 清空日志
    const btnClearLog = $('#btn-clear-log');
    if (btnClearLog) {
      btnClearLog.addEventListener('click', () => {
        $('#log-view').innerHTML = '';
        state.logCount = 0;
      });
    }
  }

  // ===== 初始化 =====
  // 逐个安全初始化：任一步失败不影响后续（尤其是录制监听必须装上）
  const safeInit = (label, fn) => { try { fn(); } catch (e) { console.error('初始化失败[' + label + ']:', e); try { log('初始化异常[' + label + ']：' + e.message, 'error'); } catch (e2) { } } };
  safeInit('指令库', () => renderCommands());
  safeInit('流程Tab', () => renderFlowTabs());
  safeInit('流程渲染', () => renderFlow());
  safeInit('属性面板', () => renderProps());
  safeInit('事件绑定', () => bindEvents());
  safeInit('浏览器', () => setupBrowser());
  safeInit('录制(电脑)', () => setupWinRecord());
  safeInit('任务栏', () => renderTaskbar());
  log('欢迎使用世博自动化！从左侧拖拽指令到流程区开始搭建自动化流程。', 'time');
})();

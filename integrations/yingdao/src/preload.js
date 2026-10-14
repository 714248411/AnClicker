const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('yingdao', {
  // 文件对话框
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  saveFile: (name) => ipcRenderer.invoke('dialog:saveFile', name),
  openDir: (title) => ipcRenderer.invoke('dialog:openDir', title),
  exportFlowRunner: (payload) => ipcRenderer.invoke('export:flowRunner', payload),
  // 文件读写
  readFile: (path) => ipcRenderer.invoke('fs:readFile', path),
  readText: (path) => ipcRenderer.invoke('fs:readText', path),
  writeText: (path, content) => ipcRenderer.invoke('fs:writeText', path, content),
  writeFile: (path, arrayBuffer) => ipcRenderer.invoke('fs:writeFile', path, arrayBuffer),
  // 文件操作（复制/移动/删除/重命名/存在判断/新建文件夹/列出目录）
  copyFile: (src, dst) => ipcRenderer.invoke('fs:copy', src, dst),
  moveFile: (src, dst) => ipcRenderer.invoke('fs:move', src, dst),
  deleteFile: (filePath) => ipcRenderer.invoke('fs:delete', filePath),
  fileExists: (filePath) => ipcRenderer.invoke('fs:exists', filePath),
  mkdir: (dirPath) => ipcRenderer.invoke('fs:mkdir', dirPath),
  listDir: (dirPath) => ipcRenderer.invoke('fs:listDir', dirPath),

  // 独立浏览器窗口控制
  browser: {
    loadURL: (url, target, loginMode, engine, waitForLoad) => ipcRenderer.invoke('browser:loadURL', url, target, loginMode, engine, waitForLoad),
    back: () => ipcRenderer.invoke('browser:back'),
    forward: () => ipcRenderer.invoke('browser:forward'),
    reload: () => ipcRenderer.invoke('browser:reload'),
    execJS: (jsCode, timeoutMs) => ipcRenderer.invoke('browser:execJS', jsCode, timeoutMs),
    // 跨框架执行：主文档找不到就去各个 iframe 里试（跨域 iframe 也能操作）
    execJSFrames: (jsCode, timeoutMs) => ipcRenderer.invoke('browser:execJSFrames', jsCode, timeoutMs),
    // 发真实按键（回车等，能触发原生表单提交；modifiers 传 ['control'] 之类的修饰键）
    sendKey: (key, times, modifiers) => ipcRenderer.invoke('browser:sendKey', key, times, modifiers),
    getURL: () => ipcRenderer.invoke('browser:getURL'),
    getTitle: () => ipcRenderer.invoke('browser:getTitle'),
    // 弹出/嵌入/全屏（现均为独立窗口，兼容旧接口）
    popout: () => ipcRenderer.invoke('browser:popout'),
    embed: () => ipcRenderer.invoke('browser:embed'),
    togglePopout: () => ipcRenderer.invoke('browser:togglePopout'),
    isPoppedOut: () => ipcRenderer.invoke('browser:isPoppedOut'),
    toggleFullscreen: () => ipcRenderer.invoke('browser:toggleFullscreen'),
    maximize: () => ipcRenderer.invoke('browser:maximize'),
    consumeEvents: () => ipcRenderer.invoke('browser:consumeEvents'),
    pickElement: () => ipcRenderer.invoke('browser:pickElement'),
    pickForScrape: () => ipcRenderer.invoke('browser:pickForScrape'),
    // 坐标拾取（多点，最多 9 个）：在浏览器里点几个点，返回坐标列表
    pickPoints: (maxPoints, initialPoints) => ipcRenderer.invoke('browser:pickPoints', maxPoints, initialPoints),
    // 缩放
    setZoomLevel: (level) => ipcRenderer.invoke('browser:setZoomLevel', level),
    resetZoom: () => ipcRenderer.invoke('browser:resetZoom'),
    // 多窗口（loginMode 决定该窗口用哪个登录会话：独立登录 / 共用登录）
    newTab: (url, loginMode) => ipcRenderer.invoke('browser:newTab', url, loginMode),
    newWindow: (url, loginMode) => ipcRenderer.invoke('browser:newTab', url, loginMode),
    switchTab: (id) => ipcRenderer.invoke('browser:switchTab', id),
    closeTab: (id) => ipcRenderer.invoke('browser:closeTab', id),
    getTabs: () => ipcRenderer.invoke('browser:getTabs'),
    // 多账号：清空浏览器登录数据 / 取登录方式选项
    clearData: () => ipcRenderer.invoke('browser:clearData'),
    getLoginModes: () => ipcRenderer.invoke('browser:getLoginModes'),
    // 浏览器引擎：内置（自带内核）/ Edge / 内置Chrome（便携版）
    listEngines: () => ipcRenderer.invoke('browser:listEngines'),
    setEngine: (key) => ipcRenderer.invoke('browser:setEngine', key),
    onDataCleared: (cb) => ipcRenderer.on('browser:dataCleared', (_e, info) => cb(info)),
    // 事件监听
    onNavigated: (cb) => ipcRenderer.on('browser:navigated', (_e, payload) => cb(payload)),
    onLoadFailed: (cb) => ipcRenderer.on('browser:loadFailed', (_e, info) => cb(info)),
    onTitleUpdated: (cb) => ipcRenderer.on('browser:titleUpdated', (_e, payload) => cb(payload)),
    onWindowClosed: (cb) => ipcRenderer.on('browser:windowClosed', (_e, payload) => cb(payload)),
    onScrapePicked: (cb) => ipcRenderer.on('browser:scrapePicked', (_e, payload) => cb(payload)),
    onZoomChanged: (cb) => ipcRenderer.on('browser:zoomChanged', (_e, pct) => cb(pct))
  },

  // 平台信息
  platform: process.platform,
  getDesktopPath: () => ipcRenderer.invoke('app:getDesktopPath'),
  // 系统剪贴板（复制到剪贴板 / 粘贴到单元格 / 粘贴到网页元素 用）
  clipboardWrite: (text) => ipcRenderer.invoke('clipboard:write', text),
  clipboardRead: () => ipcRenderer.invoke('clipboard:read'),
  // 把流程 json 拖到 exe 上打开
  getPendingFlow: () => ipcRenderer.invoke('flow:getPending'),
  onOpenFlow: (cb) => ipcRenderer.on('flow:open', (_e, payload) => cb(payload)),
  openPath: (p) => ipcRenderer.invoke('shell:openPath', p),
  showInFolder: (p) => ipcRenderer.invoke('shell:showInFolder', p),

  // Excel 编辑器弹出为独立窗口（支持同时打开多个）
  excel: {
    popout: (snapshot) => ipcRenderer.invoke('excel:popout', snapshot),
    embed: () => ipcRenderer.invoke('excel:embed'),
    getSnapshot: () => ipcRenderer.invoke('excel:getSnapshot'),
    setSnapshot: (snapshot) => ipcRenderer.send('excel:setSnapshot', snapshot),
    focusEditor: (id) => ipcRenderer.invoke('excel:focusEditor', id),
    closeEditor: (id) => ipcRenderer.invoke('excel:closeEditor', id),
    getEditors: () => ipcRenderer.invoke('excel:getEditors'),
    // 单个 sheet 拖出为独立窗口
    popoutSheet: (sheetData) => ipcRenderer.invoke('excel:popoutSheet', sheetData),
    getSheetData: (sheetId) => ipcRenderer.invoke('excel:getSheetData', sheetId),
    mySheetId: () => ipcRenderer.invoke('excel:mySheetId'),
    setSheetData: (sheetId, data) => ipcRenderer.send('excel:setSheetData', sheetId, data),
    onSheetUpdated: (cb) => ipcRenderer.on('excel:sheetUpdated', (_e, data) => cb(data)),
    onSnapshotUpdated: (cb) => ipcRenderer.on('excel:snapshotUpdated', (_e, s) => cb(s)),
    onStandaloneClosed: (cb) => ipcRenderer.on('excel:standaloneClosed', (_e, info) => cb(info))
  }
});

// Only the local hidden renderer receives the host's instruction requests.
contextBridge.exposeInMainWorld('acHost', {
  agent: params => ipcRenderer.invoke('ac:agent',params),
  recordControl: action => ipcRenderer.invoke('ac:recordControl',action),
  windowTitles: () => ipcRenderer.invoke('ac:windowTitles'),
  ready: () => ipcRenderer.send('ac:ready'),
  onRequest: cb => ipcRenderer.on('ac:request', (_e, msg) => cb(msg)),
  respond: msg => ipcRenderer.send('ac:response', msg),
  screenshot: (selector, path) => ipcRenderer.invoke('ac:browserScreenshot', selector, path)
});

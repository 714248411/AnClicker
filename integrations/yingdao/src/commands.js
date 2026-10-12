// 指令库 —— 中文指令名对齐世博自动化 RPA 术语
// 每个指令：id(英文键)、name(中文名)、category(分类)、params(参数定义)
window.COMMANDS = [
  // ===== 网页自动化 =====
  { id: 'openUrl', name: '打开网页', category: '网页自动化', color: '#4a6cf7',
    params: [
      { key: 'url', label: '网页地址', type: 'text', default: 'https://' },
      { key: 'engine', label: '用哪个内核(朗坤6.5等老系统选Edge)', type: 'select', default: '跟随当前', options: ['跟随当前', 'Chrome', 'Edge'] },
      { key: 'target', label: '打开方式', type: 'select', default: '新窗口', options: ['新窗口', '当前标签页', '新标签页'] },
      { key: 'loginMode', label: '登录方式(多账号做隔离)', type: 'select', default: '独立登录(每次全新)', options: [
        '独立登录(每次全新)',
        '独立登录(按账号位保存)',
        '共用登录(沿用已有登录)'
      ] },
      { key: 'waitType', label: '等待加载', type: 'select', default: '加载完成', options: ['加载完成', '立即返回'] }
    ] },
  { id: 'click', name: '点击元素', category: '网页自动化', color: '#4a6cf7',
    params: [
      { key: 'selector', label: '元素定位', type: 'text', default: '' },
      { key: 'anchor', label: '锚点元素(可选，多个用;分隔)', type: 'text', default: '' },
      { key: 'anchorRel', label: '目标相对锚点的方位', type: 'select', default: '下方', options: ['下方', '上方', '右侧', '左侧', '内部', '相邻'] },
      { key: 'clickType', label: '点击方式', type: 'select', default: '单击', options: ['单击', '双击', '右键'] },
      { key: 'by', label: '定位方式', type: 'select', default: '智能匹配', options: ['CSS选择器', 'XPath', '文本内容', '坐标定位', '智能匹配', '锚点定位'] }
    ] },
  { id: 'input', name: '输入文本', category: '网页自动化', color: '#4a6cf7',
    params: [
      { key: 'selector', label: '元素定位', type: 'text', default: '' },
      { key: 'anchor', label: '锚点元素(可选，多个用;分隔)', type: 'text', default: '' },
      { key: 'anchorRel', label: '目标相对锚点的方位', type: 'select', default: '下方', options: ['下方', '下方第1个', '上方', '右侧', '左侧', '内部', '相邻'] },
      { key: 'text', label: '输入内容', type: 'text', default: '' },
      { key: 'pressEnter', label: '输入后按回车', type: 'select', default: '否', options: ['否', '是'] },
      { key: 'clear', label: '输入前清空', type: 'select', default: '是', options: ['是', '否'] },
      { key: 'by', label: '定位方式', type: 'select', default: '智能匹配', options: ['CSS选择器', 'XPath', '文本内容', '智能匹配', '锚点定位'] }
    ] },
  { id: 'getText', name: '获取文本', category: '网页自动化', color: '#4a6cf7',
    params: [
      { key: 'selector', label: '元素定位', type: 'text', default: '' },
      { key: 'anchor', label: '锚点元素(可选，多个用;分隔)', type: 'text', default: '' },
      { key: 'anchorRel', label: '目标相对锚点的方位', type: 'select', default: '下方', options: ['下方', '上方', '右侧', '左侧', '内部', '相邻'] },
      { key: 'varName', label: '保存到变量', type: 'text', default: '变量1' },
      { key: 'by', label: '定位方式', type: 'select', default: '智能匹配', options: ['CSS选择器', 'XPath', '文本内容', '智能匹配', '锚点定位'] }
    ] },
  { id: 'screenshot', name: '网页截图', category: '网页自动化', color: '#4a6cf7',
    params: [
      { key: 'selector', label: '元素定位(可选)', type: 'text', default: '' },
      { key: 'path', label: '保存路径', type: 'text', default: '' }
    ] },
  { id: 'waitElement', name: '等待元素出现', category: '网页自动化', color: '#4a6cf7',
    params: [
      { key: 'selector', label: '元素定位', type: 'text', default: '' },
      { key: 'anchor', label: '锚点元素(可选，多个用;分隔)', type: 'text', default: '' },
      { key: 'anchorRel', label: '目标相对锚点的方位', type: 'select', default: '下方', options: ['下方', '上方', '右侧', '左侧', '内部', '相邻'] },
      { key: 'timeout', label: '超时(秒)', type: 'number', default: 10 },
      { key: 'fallbackToXY', label: '超时还没出现怎么办', type: 'select', default: '只报错', options: ['只报错', '点击坐标'] },
      { key: 'xyPoints', label: '兜底点击坐标(没出现时点这里，最多9个点用;分隔)', type: 'text', default: '' },
      { key: 'xyInterval', label: '兜底点击的间隔(秒)', type: 'number', default: 1 },
      { key: 'by', label: '定位方式', type: 'select', default: '智能匹配', options: ['CSS选择器', 'XPath', '文本内容', '智能匹配', '锚点定位'] }
    ] },
  { id: 'waitPageReady', name: '等待页面加载完成', category: '网页自动化', color: '#4a6cf7',
    params: [
      { key: 'timeout', label: '最长等多久(秒)', type: 'number', default: 20 }
    ] },
  { id: 'diagnosePage', name: '诊断页面(排错)', category: '网页自动化', color: '#98a2b3',
    params: [] },
  { id: 'clickXY', name: '坐标点击(可多点)', category: '网页自动化', color: '#4a6cf7',
    params: [
      { key: 'points', label: '点击坐标(最多9个点，用;分隔，如 100,200; 300,400)', type: 'text', default: '' },
      { key: 'interval', label: '每个点之间间隔(秒)', type: 'number', default: 1 },
      { key: 'clickType', label: '点击方式', type: 'select', default: '单击', options: ['单击', '双击', '右键'] },
      { key: 'x', label: 'X坐标(只在单点、且上面没填时用)', type: 'number', default: 0 },
      { key: 'y', label: 'Y坐标(只在单点、且上面没填时用)', type: 'number', default: 0 }
    ] },
  { id: 'browserWait', name: '等待(秒)', category: '网页自动化', color: '#4a6cf7',
    params: [
      { key: 'seconds', label: '等待时间(秒)', type: 'number', default: 1 }
    ] },
  { id: 'pressKey', name: '按键', category: '网页自动化', color: '#4a6cf7',
    params: [
      { key: 'key', label: '按哪个键', type: 'select', default: '回车(Enter)', options: [
        '回车(Enter)',
        'Tab',
        'ESC(Esc)',
        '空格(Space)',
        '退格(Backspace)',
        '删除(Delete)',
        '方向键↑',
        '方向键↓',
        '方向键←',
        '方向键→',
        'F5(刷新页面)',
        'Ctrl+A(全选)',
        'Ctrl+C(复制)',
        'Ctrl+V(粘贴)',
        'Ctrl+X(剪切)',
        'Ctrl+Z(撤销)',
        'Ctrl+F(查找)',
        'Ctrl+S(保存)',
        '自定义'
      ] },
      { key: 'customKey', label: '自定义按键(选「自定义」时填，如 F5、a、Ctrl+Shift+A)', type: 'text', default: '' },
      { key: 'times', label: '按几次', type: 'number', default: 1 }
    ] },
  { id: 'clickSelectCopy', name: '点击并全选复制', category: '网页自动化', color: '#4a6cf7',
    params: [
      { key: 'selector', label: '元素定位(点它并把它里面的内容全选复制)', type: 'text', default: '' },
      { key: 'anchor', label: '锚点元素(可选，多个用;分隔)', type: 'text', default: '' },
      { key: 'anchorRel', label: '目标相对锚点的方位', type: 'select', default: '下方', options: ['下方', '上方', '右侧', '左侧', '内部', '相邻'] },
      { key: 'clickType', label: '点击方式', type: 'select', default: '单击', options: ['单击', '双击', '右键'] },
      { key: 'by', label: '定位方式', type: 'select', default: '智能匹配', options: ['CSS选择器', 'XPath', '文本内容', '智能匹配', '锚点定位'] }
    ] },
  { id: 'clickPaste', name: '点击并粘贴', category: '网页自动化', color: '#4a6cf7',
    params: [
      { key: 'selector', label: '元素定位(点它然后粘贴；也可填坐标如 100,200)', type: 'text', default: '' },
      { key: 'anchor', label: '锚点元素(可选，多个用;分隔)', type: 'text', default: '' },
      { key: 'anchorRel', label: '目标相对锚点的方位', type: 'select', default: '下方', options: ['下方', '上方', '右侧', '左侧', '内部', '相邻'] },
      { key: 'clickType', label: '点击方式', type: 'select', default: '单击', options: ['单击', '双击', '右键'] },
      { key: 'by', label: '定位方式', type: 'select', default: '智能匹配', options: ['CSS选择器', 'XPath', '文本内容', '智能匹配', '锚点定位', '坐标定位'] }
    ] },
  { id: 'clipboardCopy', name: '复制到剪贴板', category: '网页自动化', color: '#e67e22',
    params: [
      { key: 'from', label: '复制什么', type: 'select', default: '文本(下面填的内容)', options: ['文本(下面填的内容)', '网页里选中的内容', '元素里的文本'] },
      { key: 'content', label: '要复制的文本(可用 ${变量})', type: 'text', default: '' },
      { key: 'selector', label: '元素定位(上面选「元素里的文本」时填)', type: 'text', default: '' },
      { key: 'by', label: '定位方式', type: 'select', default: '智能匹配', options: ['CSS选择器', 'XPath', '文本内容', '智能匹配'] }
    ] },
  { id: 'pasteToElement', name: '粘贴到网页元素', category: '网页自动化', color: '#4a6cf7',
    params: [
      { key: 'selector', label: '元素定位(要粘贴到哪个元素)', type: 'text', default: '' },
      { key: 'anchor', label: '锚点元素(可选，多个用;分隔)', type: 'text', default: '' },
      { key: 'anchorRel', label: '目标相对锚点的方位', type: 'select', default: '下方', options: ['下方', '上方', '右侧', '左侧', '内部', '相邻'] },
      { key: 'mode', label: '粘贴方式', type: 'select', default: '真实粘贴(Ctrl+V)', options: ['真实粘贴(Ctrl+V)', '直接把内容写进去'] },
      { key: 'by', label: '定位方式', type: 'select', default: '智能匹配', options: ['CSS选择器', 'XPath', '文本内容', '智能匹配', '锚点定位'] }
    ] },
  { id: 'pasteToCell', name: '粘贴到单元格', category: 'Excel', color: '#16a085',
    params: [
      { key: 'toPath', label: '写到哪个表格(可拖文件进来，留空=新建到桌面)', type: 'text', default: '' },
      { key: 'toSheet', label: '工作表名(留空=第一个表)', type: 'text', default: '' },
      { key: 'toCell', label: '从哪个单元格开始粘贴(如 A1、B2)', type: 'text', default: 'A1' },
      { key: 'save', label: '保存方式', type: 'select', default: '保存', options: ['保存', '另存为'] }
    ] },
  { id: 'extractTextToTable', name: '提取文本到表格', category: '网页自动化', color: '#e67e22',
    params: [
      { key: 'selector', label: '元素定位(要提取哪些元素的文本)', type: 'text', default: '' },
      { key: 'anchor', label: '锚点元素(可选，多个用;分隔)', type: 'text', default: '' },
      { key: 'anchorRel', label: '目标相对锚点的方位', type: 'select', default: '下方', options: ['下方', '上方', '右侧', '左侧', '内部', '相邻'] },
      { key: 'by', label: '定位方式', type: 'select', default: '智能匹配', options: ['CSS选择器', 'XPath', '文本内容', '智能匹配', '锚点定位'] },
      { key: 'all', label: '提取数量', type: 'select', default: '全部匹配', options: ['单个', '全部匹配'] },
      { key: 'filter', label: '内容过滤(选一个，或直接填 2-3 表示取第2~3个字符)', type: 'text', default: '文本与数字', options: [
        '文本与数字',
        '纯数字',
        '纯文本',
        '带小数点的数字'
      ] },
      { key: 'toPath', label: '写到哪个表格(可拖文件进来，留空=新建到桌面)', type: 'text', default: '' },
      { key: 'toSheet', label: '工作表名(留空=第一个表)', type: 'text', default: '' },
      { key: 'toCell', label: '从哪个单元格开始写(如 A1、B2)', type: 'text', default: 'A1' },
      { key: 'save', label: '保存方式', type: 'select', default: '保存', options: ['保存', '另存为'] }
    ] },
  { id: 'pickElement', name: '拾取元素', category: '网页自动化', color: '#4a6cf7',
    params: [
      { key: 'hint', label: '说明', type: 'text', default: '在浏览器里点击目标元素' }
    ] },

  // ===== 数据抓取（Scraping） =====
  { id: 'scrapeText', name: '抓取文本', category: '数据抓取', color: '#e67e22',
    params: [
      { key: 'selector', label: '元素定位', type: 'text', default: '' },
      { key: 'varName', label: '保存到变量', type: 'text', default: '抓取结果' },
      { key: 'by', label: '定位方式', type: 'select', default: '智能匹配', options: ['CSS选择器', 'XPath', '文本内容', '智能匹配'] },
      { key: 'all', label: '抓取数量', type: 'select', default: '单个', options: ['单个', '全部匹配'] }
    ] },
  { id: 'scrapeAttr', name: '抓取属性', category: '数据抓取', color: '#e67e22',
    params: [
      { key: 'selector', label: '元素定位', type: 'text', default: '' },
      { key: 'attr', label: '属性名(如href)', type: 'text', default: 'href' },
      { key: 'varName', label: '保存到变量', type: 'text', default: '抓取结果' },
      { key: 'by', label: '定位方式', type: 'select', default: '智能匹配', options: ['CSS选择器', 'XPath', '智能匹配'] },
      { key: 'all', label: '抓取数量', type: 'select', default: '全部匹配', options: ['单个', '全部匹配'] }
    ] },
  { id: 'scrapeList', name: '抓取列表', category: '数据抓取', color: '#e67e22',
    params: [
      { key: 'selector', label: '列表项定位', type: 'text', default: '' },
      { key: 'fields', label: '字段(定位:字段名,逗号分隔)', type: 'text', default: '' },
      { key: 'varName', label: '保存到变量(二维数组)', type: 'text', default: '抓取列表' },
      { key: 'by', label: '定位方式', type: 'select', default: '智能匹配', options: ['CSS选择器', 'XPath', '智能匹配'] }
    ] },
  { id: 'scrapeExport', name: '抓取导出Excel', category: '数据抓取', color: '#e67e22',
    params: [
      { key: 'varName', label: '数据变量(二维数组)', type: 'text', default: '抓取列表' },
      { key: 'path', label: '保存路径(留空存桌面)', type: 'text', default: '' }
    ] },

  // ===== 鼠标键盘 =====
  { id: 'typeText', name: '模拟按键', category: '鼠标键盘', color: '#f7a24a',
    params: [
      { key: 'text', label: '按键/文本', type: 'text', default: '' }
    ] },
  { id: 'mouseClick', name: '鼠标点击', category: '鼠标键盘', color: '#f7a24a',
    params: [
      { key: 'x', label: 'X坐标', type: 'number', default: 0 },
      { key: 'y', label: 'Y坐标', type: 'number', default: 0 },
      { key: 'button', label: '按键', type: 'select', default: '左键', options: ['左键', '右键', '中键'] }
    ] },
  { id: 'hotkey', name: '快捷键', category: '鼠标键盘', color: '#f7a24a',
    params: [
      { key: 'keys', label: '组合键', type: 'text', default: 'Ctrl+C' }
    ] },

  // ===== 循环（一级分类） =====
  { id: 'loop', name: '循环', category: '循环', color: '#e67e22',
    params: [
      { key: 'mode', label: '循环方式', type: 'select', default: '按次数', options: ['按次数', '按时间'] },
      { key: 'count', label: '循环次数(按次数时用)', type: 'number', default: 10 },
      { key: 'seconds', label: '循环时长秒(按时间时用)', type: 'number', default: 60 }
    ] },
  { id: 'loopForever', name: '无限循环', category: '循环', color: '#e67e22', params: [] },
  { id: 'breakLoop', name: '跳出循环', category: '循环', color: '#e67e22', params: [] },

  // ===== 流程控制 =====
  { id: 'if', name: '条件判断', category: '流程控制', color: '#9b59b6',
    params: [
      { key: 'left', label: '变量A', type: 'text', default: '' },
      { key: 'op', label: '比较', type: 'select', default: '等于', options: ['等于', '不等于', '大于', '小于', '包含'] },
      { key: 'right', label: '变量B', type: 'text', default: '' }
    ] },
  { id: 'mark', name: '标记(跳转目标)', category: '流程控制', color: '#9b59b6',
    params: [
      { key: 'name', label: '标记名', type: 'text', default: '分支A' }
    ] },
  { id: 'goto', name: '跳转', category: '流程控制', color: '#9b59b6',
    params: [
      { key: 'target', label: '跳到哪(可输入或下拉选流程/第几步/标记)', type: 'targetlist', default: '' }
    ] },
  { id: 'callFlow', name: '调用子流程', category: '流程控制', color: '#9b59b6',
    params: [
      { key: 'flowName', label: '子流程名', type: 'text', default: '' }
    ] },
  { id: 'end', name: '结束流程', category: '流程控制', color: '#9b59b6', params: [] },

  // ===== 等待 =====
  { id: 'sleep', name: '等待', category: '等待', color: '#27ae60',
    params: [
      { key: 'seconds', label: '等待时间(秒)', type: 'number', default: 1 }
    ] },

  // ===== 数据处理 =====
  { id: 'setVar', name: '设置变量', category: '数据处理', color: '#e74c3c',
    params: [
      { key: 'name', label: '变量名', type: 'text', default: '变量1' },
      { key: 'value', label: '变量值', type: 'text', default: '' }
    ] },
  { id: 'printLog', name: '打印日志', category: '数据处理', color: '#e74c3c',
    params: [
      { key: 'text', label: '日志内容', type: 'text', default: '' }
    ] },

  // ===== Excel =====
  { id: 'excelOpen', name: '打开Excel', category: 'Excel', color: '#16a085',
    params: [
      { key: 'path', label: '文件路径', type: 'text', default: '' }
    ] },
  { id: 'excelRead', name: '读取单元格', category: 'Excel', color: '#16a085',
    params: [
      { key: 'cell', label: '单元格(如A1)', type: 'text', default: 'A1' },
      { key: 'varName', label: '保存到变量', type: 'text', default: '变量1' }
    ] },
  { id: 'excelWrite', name: '写入单元格', category: 'Excel', color: '#16a085',
    params: [
      { key: 'cell', label: '单元格(如A1)', type: 'text', default: 'A1' },
      { key: 'value', label: '写入内容', type: 'text', default: '' }
    ] },
  { id: 'excelReadRange', name: '读取区域', category: 'Excel', color: '#16a085',
    params: [
      { key: 'range', label: '区域(如A1:C5)', type: 'text', default: 'A1:C5' },
      { key: 'varName', label: '保存到变量(二维数组)', type: 'text', default: '变量1' }
    ] },
  { id: 'excelWriteRange', name: '写入区域', category: 'Excel', color: '#16a085',
    params: [
      { key: 'range', label: '起始单元格(如A1)', type: 'text', default: 'A1' },
      { key: 'data', label: '数据(变量名,二维数组)', type: 'text', default: '变量1' }
    ] },
  { id: 'excelCopyPaste', name: '复制粘贴(选择性粘贴)', category: 'Excel', color: '#16a085',
    params: [
      { key: 'from', label: '源区域(如A1:B5)', type: 'text', default: 'A1:B5' },
      { key: 'to', label: '目标起始单元格(如D1)', type: 'text', default: 'D1' },
      { key: 'mode', label: '粘贴方式', type: 'select', default: '全部粘贴', options: [
        '全部粘贴',
        '只粘贴值',
        '只粘贴公式',
        '只粘贴格式',
        '保留公式',
        '值与数字格式',
        '公式与数字格式',
        '不覆盖原有内容'
      ] }
    ] },
  { id: 'excelSheetCopyPaste', name: '表格复制粘贴', category: 'Excel', color: '#16a085',
    params: [
      { key: 'fromBook', label: '源表格(留空=当前)', type: 'text', default: '' },
      { key: 'fromSheet', label: '源工作表', type: 'sheet', default: 'Sheet1' },
      { key: 'fromRange', label: '源区域(如A1:C5)', type: 'text', default: 'A1:C5' },
      { key: 'toBook', label: '目标表格(留空=当前)', type: 'text', default: '' },
      { key: 'toSheet', label: '目标工作表', type: 'sheet', default: 'Sheet1' },
      { key: 'toRange', label: '目标起始单元格(如A1)', type: 'text', default: 'A1' },
      { key: 'mode', label: '粘贴方式', type: 'select', default: '全部粘贴', options: [
        '全部粘贴',
        '只粘贴值',
        '只粘贴公式',
        '只粘贴格式',
        '保留公式',
        '值与数字格式',
        '公式与数字格式',
        '不覆盖原有内容'
      ] }
    ] },
  { id: 'excelInsertRow', name: '插入行', category: 'Excel', color: '#16a085',
    params: [
      { key: 'row', label: '在第几行前插入', type: 'number', default: 1 },
      { key: 'count', label: '插入行数', type: 'number', default: 1 }
    ] },
  { id: 'excelInsertCol', name: '插入列', category: 'Excel', color: '#16a085',
    params: [
      { key: 'col', label: '在第几列前插入', type: 'number', default: 1 },
      { key: 'count', label: '插入列数', type: 'number', default: 1 }
    ] },
  { id: 'excelDeleteRow', name: '删除行', category: 'Excel', color: '#16a085',
    params: [
      { key: 'row', label: '起始行', type: 'number', default: 1 },
      { key: 'count', label: '删除行数', type: 'number', default: 1 }
    ] },
  { id: 'excelDeleteCol', name: '删除列', category: 'Excel', color: '#16a085',
    params: [
      { key: 'col', label: '起始列', type: 'number', default: 1 },
      { key: 'count', label: '删除列数', type: 'number', default: 1 }
    ] },
  { id: 'excelGetRows', name: '获取行数', category: 'Excel', color: '#16a085',
    params: [
      { key: 'varName', label: '保存到变量', type: 'text', default: '行数' }
    ] },
  { id: 'excelNew', name: '新建Excel', category: 'Excel', color: '#16a085',
    params: [
      { key: 'path', label: '保存路径', type: 'text', default: '' },
      { key: 'sheetName', label: '工作表名', type: 'text', default: 'Sheet1' }
    ] },
  { id: 'excelSave', name: '保存Excel', category: 'Excel', color: '#16a085',
    params: [
      { key: 'path', label: '另存为(留空保存原文件)', type: 'text', default: '' }
    ] },
  { id: 'excelSaveAs', name: '表格另存为', category: 'Excel', color: '#16a085',
    params: [
      { key: 'naming', label: '命名方式', type: 'select', default: '后缀递增', options: ['后缀递增', '加前缀', '覆盖'] },
      { key: 'prefix', label: '前缀(选「加前缀」时用)', type: 'text', default: '' },
      { key: 'startIndex', label: '后缀从几开始(默认1)', type: 'number', default: 1 }
    ] },

  // ===== 文件操作 =====
  { id: 'fileReadText', name: '读取文本文件', category: '文件操作', color: '#8e44ad',
    params: [
      { key: 'path', label: '文件路径', type: 'text', default: '' },
      { key: 'varName', label: '保存到变量', type: 'text', default: '文件内容' }
    ] },
  { id: 'fileWriteText', name: '写入文本文件', category: '文件操作', color: '#8e44ad',
    params: [
      { key: 'path', label: '文件路径', type: 'text', default: '' },
      { key: 'content', label: '写入内容', type: 'text', default: '' },
      { key: 'append', label: '写入方式', type: 'select', default: '覆盖', options: ['覆盖', '追加'] }
    ] },
  { id: 'fileCopy', name: '复制文件', category: '文件操作', color: '#8e44ad',
    params: [
      { key: 'src', label: '源文件路径', type: 'text', default: '' },
      { key: 'sortBy', label: '排序依据(文件夹时生效)', type: 'select', default: '字符', options: ['字符', '修改时间', '大小'] },
      { key: 'order', label: '排序方式', type: 'select', default: '顺序', options: ['顺序', '逆序'] },
      { key: 'index', label: '取第几个文件(1开始,0=不取)', type: 'number', default: 0 },
      { key: 'dst', label: '目标路径', type: 'text', default: '' }
    ] },
  { id: 'fileMove', name: '移动/重命名文件', category: '文件操作', color: '#8e44ad',
    params: [
      { key: 'src', label: '源文件路径', type: 'text', default: '' },
      { key: 'dst', label: '目标路径', type: 'text', default: '' }
    ] },
  { id: 'fileDelete', name: '删除文件', category: '文件操作', color: '#8e44ad',
    params: [
      { key: 'path', label: '文件路径', type: 'text', default: '' },
      { key: 'sortBy', label: '排序依据(文件夹时生效)', type: 'select', default: '字符', options: ['字符', '修改时间', '大小'] },
      { key: 'order', label: '排序方式', type: 'select', default: '顺序', options: ['顺序', '逆序'] },
      { key: 'index', label: '删除第几个文件(1开始,0=不取)', type: 'number', default: 0 }
    ] },
  { id: 'fileExists', name: '判断文件是否存在', category: '文件操作', color: '#8e44ad',
    params: [
      { key: 'path', label: '文件路径', type: 'text', default: '' },
      { key: 'varName', label: '保存到变量(true/false)', type: 'text', default: '是否存在' }
    ] },
  { id: 'fileMkdir', name: '新建文件/文件夹', category: '文件操作', color: '#8e44ad',
    params: [
      { key: 'folder', label: '在哪个文件夹里新建', type: 'text', default: '' },
      { key: 'name', label: '叫什么名字(带后缀=文件，逗号隔开可建多个)', type: 'text', default: '新建文件.txt' },
      { key: 'content', label: '文件内容(留空=空文件)', type: 'text', default: '' }
    ] },
  { id: 'fileListDir', name: '列出目录文件', category: '文件操作', color: '#8e44ad',
    params: [
      { key: 'path', label: '目录路径', type: 'text', default: '' },
      { key: 'sortBy', label: '排序依据', type: 'select', default: '字符', options: ['字符', '修改时间', '大小'] },
      { key: 'order', label: '排序方式', type: 'select', default: '顺序', options: ['顺序', '逆序'] },
      { key: 'varName', label: '保存到变量', type: 'text', default: '文件列表' }
    ] },

  // ===== 白话指令（一句大白话搞定文件操作，尽量少用变量） =====
  { id: 'fileOp', name: '处理文件(白话)', category: '白话指令', color: '#d35400',
    params: [
      { key: 'action', label: '做什么', type: 'select', default: '删除', options: ['删除', '复制', '移动', '列出文件名'] },
      { key: 'folder', label: '哪个文件夹', type: 'text', default: '' },
      { key: 'sortBy', label: '按什么排序', type: 'select', default: '文件名', options: ['文件名', '修改时间', '文件大小'] },
      { key: 'order', label: '排序方向', type: 'order', default: '从小到大', options: ['从小到大', '从大到小'] },
      { key: 'index', label: '第几个文件(如 1、1,3,5、1-3、-1=倒数第1)', type: 'text', default: '1' },
      { key: 'dst', label: '复制/移动到哪(文件夹或新路径)', type: 'text', default: '' }
    ] },
  { id: 'fileRename', name: '重命名文件(白话)', category: '白话指令', color: '#d35400',
    params: [
      { key: 'folder', label: '哪个文件夹', type: 'text', default: '' },
      { key: 'sortBy', label: '按什么排序', type: 'select', default: '文件名', options: ['文件名', '修改时间', '文件大小'] },
      { key: 'order', label: '排序方向', type: 'order', default: '从小到大', options: ['从小到大', '从大到小'] },
      { key: 'index', label: '第几个文件(如 1、1-3、1,3,5、-1=倒数第1)', type: 'text', default: '1' },
      { key: 'mode', label: '命名方式', type: 'select', default: '加前缀', options: ['加前缀', '删前缀', '加后缀', '删后缀', '替换文字', '删除文字', '按分隔符重组'] },
      { key: 'text', label: '标识内容(前缀/后缀/替换文字)', type: 'text', default: '' },
      { key: 'type', label: '标识类型(留空=用上面文字)', type: 'select', default: '自定义文字', options: ['自定义文字', '数字序号', '字母序号', '日期'] },
      { key: 'sep', label: '分隔符(重组用，如 _ - 空格)', type: 'text', default: '_' },
      { key: 'parts', label: '取哪几段重组(如 2,1，留空=全部)', type: 'text', default: '' }
    ] },
  { id: 'fileFind', name: '查找文件(白话)', category: '白话指令', color: '#d35400',
    params: [
      { key: 'folder', label: '在哪个文件夹找', type: 'text', default: '' },
      { key: 'keyword', label: '文件名包含什么字(留空=列出全部)', type: 'text', default: '' },
      { key: 'ext', label: '只找这种类型(如 txt，留空=全部)', type: 'text', default: '' }
    ] },
  { id: 'fileCount', name: '统计文件(白话)', category: '白话指令', color: '#d35400',
    params: [
      { key: 'folder', label: '统计哪个文件夹', type: 'text', default: '' },
      { key: 'ext', label: '只统计这种类型(如 txt，留空=全部)', type: 'text', default: '' }
    ] },
  { id: 'excelTableCopyPaste', name: '表格复制粘贴(白话)', category: '白话指令', color: '#d35400',
    params: [
      { key: 'fromPath', label: '① 源表格路径(可把Excel文件拖进来)', type: 'text', default: '' },
      { key: 'fromRanges', label: '② 复制哪几列/区域(如 A1-A9,B2-B4；留空=整个表格)', type: 'text', default: '' },
      { key: 'fromSheet', label: '③ 源工作表名(留空=第一个表)', type: 'text', default: '' },
      { key: 'toPath', label: '④ 目标表格路径(可拖文件进来，留空=新建到桌面)', type: 'text', default: '' },
      { key: 'toSheet', label: '⑤ 目标工作表名(留空=第一个表)', type: 'text', default: '' },
      { key: 'toCell', label: '⑥ 从哪个单元格开始粘贴(如 B1、D2)', type: 'text', default: 'A1' },
      { key: 'mode', label: '⑦ 粘贴方式', type: 'select', default: '只粘贴文本', options: [
        '只粘贴文本',
        '全部粘贴',
        '只粘贴值',
        '只粘贴公式',
        '只粘贴格式',
        '保留公式',
        '值与数字格式',
        '公式与数字格式',
        '不覆盖原有内容'
      ] },
      { key: 'save', label: '⑧ 粘贴后是否保存表格', type: 'select', default: '保存', options: ['保存', '不保存'] }
    ] }
];

// 按分类分组
window.CATEGORIES = [];
window.COMMANDS.forEach(c => {
  if (!window.CATEGORIES.includes(c.category)) window.CATEGORIES.push(c.category);
});

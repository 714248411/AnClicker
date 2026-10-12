# Excel、白话与网页自动化重建

基于 v1.4.5，于 2026-10-12 重建。这是新的本地实现，不是找回的原 1.4.6，也未发布到远端。

## 已接入

- Excel 16 条：打开、新建、读写单元格/区域、选择性粘贴、跨工作簿工作表粘贴、插删行列、行数、保存/另存为、剪贴板粘贴。旧“写入单元格”保留为“写入单元格（独立文件）”，保证旧任务兼容。
- 白话 5 条：处理文件、重命名、查找、统计、表格复制粘贴。保留原选项及默认值，重命名增加“替换为”，修复参考实现替换文字无效果的问题。无效文件序号报错，不退回整目录操作。
- 网页及抓取 21 条：打开网页、定位/点击/输入、等待、按键、剪贴板、取文本、截图、抓取文本/属性/列表、写入 Excel。内置浏览器窗口固定名为“极速网页AC”；Edge 选项使用外部 Edge 自己的窗口。
- 指令栏：离线识字OCR与在线识字OCR分别包含既有本地和在线执行器，旧 type_id 不变。
- 快捷操作：双击快捷截图开始操作；完成后在该条目下展开下一步，双击或拖动创建指令。再次发起任一快捷操作会清除上一组下拉条目，包括取消新截图的情形。

## 使用

双击项目根目录的“启动开发版.cmd”。开发环境已建立。另已生成 Windows x64 便携测试包：上一级目录 AnClicker-local-test-20261012.zip，完整解压后运行 AnClicker/AnClicker.exe。

Excel 连续操作共享当前打开的工作簿；“写入”修改内存工作簿，使用“保存Excel”落盘。白话复制粘贴可直接指定源和目标路径。网页指令先执行“打开网页”，再使用元素定位；设置窗口的“拾取元素”可在打开的网页中点选。

新增指令均使用原生 Qt 设置窗口，支持重复次数、异常策略、备注、测试指令与取消测试。变量支持参考项目的 ${变量} 与 AnClicker 的 {{变量}}、☾变量☽。读单元格等“保存到变量”字段可打开现有变量管理。

## 源码结构

- instructions/ 下的新增独立模块、.ui 和 _ui.py：由 tools/generate_rpa_instructions.py 从 integrations/yingdao/commands.json 生成。
- instructions/common/rpa_instruction.py：宿主参数、变量和执行接口。
- instructions/common/rpa_bridge.py：仅监听回环地址的临时连接，随机凭据校验，串行执行，停止和退出关闭所属引擎。
- integrations/yingdao/src：来自用户提供的 yingdao-rpa 副本；原项目没有改动。保留原始实现和许可证说明。
- runtime/electron：当前 Windows 运行时。换电脑可使用 tools/setup_rpa_runtime.py 安装同版运行时，或 --from-directory 离线复制。

## 验证

.venv\Scripts\python.exe tools\run_tests.py test\test_rpa_integration.py test\test_instruction_registry.py test\test_ocr_palette_groups.py -q

Windows 下使用原生 Qt 后端；此机器的 Qt5 offscreen 后端显示异常提示框时会原生崩溃，tools/run_tests.py 选择 windows 后端。网页端到端验证使用本机测试页，不代表已验收所有业务网站。

打包仍遵守原项目 Python 3.10.11 基线；本机开发环境为 Python 3.10.22。打包脚本已包含 RPA 引擎资源，本地便携测试包已使用 Python 3.10.11 构建，并通过成品启动、界面、OCR、Excel 和网页自检；尚未公开发布。

## 本机验证结果（2026-10-12）

- 完整回归：592 passed、1 skipped、750 subtests passed。
- 最后一次新增指令/注册表/OCR 分组回归：16 passed、591 subtests passed。包含新增宿主数据库保存后执行、变量传递、元素拾取结果映射、重命名替换和无效序号拒绝测试。
- 实际 Electron 测试：Excel 文件读写、白话复制重命名、网页输入点击抓取、截图、导出 Excel、窗口标题、取消后重启。
- 原生 Qt：浅色/深色全部指令设置窗口，372 个数字控件无裁切；原程序截图确认添加流程正常。
- main.py 开发版启动成功，窗口可见、窗口控制有效。验证记录位于 validation/。

运行时沿用参考项目 Electron 31.7.7。外部 Edge 路径尚未在本轮实机验证；本轮网页测试使用内置浏览器。

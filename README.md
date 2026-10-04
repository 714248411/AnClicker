# YanYiClicker

YanYiClicker 是一款基于 PySide6 的 Windows 自动化工具，由 Clicker 项目扩展而来。启动入口为 `main.py`，主窗口控制器位于 `Start_Win.py`。

## 当前架构

### 流程图复刻与运行语义

流程图按“先插入节点、再自由连线”的方式工作。节点可从指令栏拖入，也可在画布空白处右键创建；左侧五分之一区域用于拉入前置线，右侧五分之一区域用于拉出后置线。节点支持多选、框选、移动、调整大小、备注、双击配置和保存为模板，画布支持平移、30%–250% 缩放及适应视图。

连线角色会随数据库保存：条件判断使用“是/否”，循环和条件循环使用“循环体/完成”。循环体可以回连到循环节点；运行时不再按表格位置猜测分支，而是逐条沿已保存连线执行。流程完成后，表格和多功能视图会立即联动刷新，多功能内容中同时生成可核对的流程连线说明。

主窗口采用从左到右层次清晰的三栏布局，并提供五个互相联动的工作视图：

- 左侧为可搜索、可拖拽的指令树，内容完全由 `instructions.registry` 生成。
- 指令栏在“表格”和“流程图”中显示，可从指令栏拖拽添加，并可从工具栏移到左侧/右侧或折叠。
- 表格页采用上下布局：上方维护指令，下方持续显示运行日志；中间分隔条可拖动调整高度。
- 右侧为统一的“控制与操作”面板，包含循环设置、运行、暂停/恢复和结束任务。
- 五个视图依次为“主界面、表格、流程图、多功能、导航”；原初级视图的功能入口集中到最后的“导航”页，不再保留预览视图。
- “流程图”支持先拖拽或右键插入未连接指令，再自由连线；节点左侧五分之一区域拉入线，右侧五分之一区域拉出线，右键节点可删除全部、前置或后置流程连接。
- 流程允许分支、汇合以及由循环节点控制的回连。所有节点都从开始可达且最终通向结束后，系统按稳定顺序生成表格和多功能内容。
- 新增“循环、条件判断、条件循环”控制节点；循环框直接显示次数，条件节点使用菱形，上方输出为“是”、下方输出为“否”，箭头尺寸也已加大。
- 顶部工具栏可切换默认深色与浅色主题，主题采用灰阶和蓝紫强调色、圆角控件，并自动保存选择；五个视图可使用 `Ctrl+1` 至 `Ctrl+5` 打开。

正式流程从“开始”沿持久化连线运行到“结束”。节点连线由 `graph_repository.py` 事务性保存；普通连线进入下一步，条件节点只进入“是”或“否”分支，循环节点在“循环体”和“完成”之间切换。只有包含循环或条件循环节点的结构化环路才允许保存和运行。

```text
instructions/               # 35 条独立指令及唯一注册表
├─ registry.py              # InstructionSpec 清单和惰性加载入口
├─ models.py                # InstructionDraft、CommandRecord、ExecutionContext
├─ base.py                  # 参数编辑器与执行器统一接口
└─ <分类>/<指令名>/
   ├─ <指令名>.ui
   ├─ <指令名>_ui.py
   └─ <指令名>.py          # 独立参数窗口类和执行类
node_editor/                # 可嵌入节点画布与左侧指令树
graph_repository.py         # 命令、节点、连线和 Excel 协议
old_ins/                    # 旧导航窗口和单体指令代码，只读参考归档
```

`old_ins/` 不属于运行时模块，也不会进入打包流程。活动代码不得从该目录导入任何对象。

## 添加或维护指令

1. 在 `instructions/<分类>/<指令名>/` 中维护该指令自己的 `.ui`、生成的 `_ui.py`、参数编辑器和执行器。
2. 参数窗口通过 `InstructionDraft` 加载、校验并返回 JSON 可序列化参数，不直接拼接 SQL。
3. 执行器统一接收 `ExecutionContext + CommandRecord`，不得使用 `eval()` 读取参数。
4. 在 `instructions/registry.py` 的唯一清单中登记 `InstructionSpec`。主窗口指令树、编辑器加载、执行映射和 PyInstaller hidden imports 会自动使用此注册信息。
5. 修改 `.ui` 后使用项目虚拟环境重新生成对应 Python 文件，例如：

   ```powershell
   .\.venv\Scripts\pyside6-uic.exe instructions\键鼠\图像点击\图像点击.ui -o instructions\键鼠\图像点击\图像点击_ui.py
   ```

## 数据目录

可迁移数据统一保存在程序同级的 `data` 文件夹：

```text
data/
├─ 命令集.db     # 设置、变量、资源记录，以及命令和节点图
├─ images/       # 截图和应用自有图片
├─ exports/      # 默认导出目录
├─ logs/         # 操作日志
└─ temp/         # 可随时清理的临时文件
```

迁移或备份时复制整个 `data` 文件夹即可。`flat`、`Window`、`instructions` 和图标目录是程序静态资源。用户添加的外部资源目录与外部文件仍保留原路径引用。

Excel 导入导出采用节点协议，工作表固定为“命令、节点、连线、设置”。导入会先完整验证 JSON、指令类型、节点引用和分支拓扑，验证成功后才事务性替换数据；旧表格格式不再兼容。

## 开发与运行

优先使用项目虚拟环境：

```powershell
.\.venv\Scripts\python.exe main.py
```

依赖清单见 `requirements.txt` 和 `pyproject.toml`。生成主窗口 UI：

```powershell
.\.venv\Scripts\pyside6-uic.exe Window\mainwindow.ui -o Window\mainwindow_ui.py
```

PyInstaller 打包说明见 `packaging/打包文件说明.md`。

## 贡献者

- FasterThanLight
- 邮箱：federalsadler@sohu.com
- QQ：2309636438
- QQ 群 1：308994839（[加入群聊](https://qm.qq.com/q/3ih3PE16Mg)）
- QQ 群 2：84284936（[加入群聊](http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=XCOQZMwDVB3y-vIz4LXdMITq-7sqGP3A&authKey=6FPrdTF0o6JIfJoc58deZ1cEWvUURazs%2FDh%2BJOz1aJI2DS%2BMFr3jRIai2%2F7bbvwN&noverify=0&group_code=84284936)）

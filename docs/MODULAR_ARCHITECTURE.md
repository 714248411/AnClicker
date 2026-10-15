# 模块结构与兼容约定

本轮以 `0c7f811` 为基线，版本仍为 v1.6.2。未修改项目数据协议、发布配置中的应用标识或数据目录规则。

## 实现目录

| 包 | 职责 |
| --- | --- |
| `anclicker.app` | 主窗口组装、应用状态、Qt 工作线程与定时任务适配、启动与路径 |
| `anclicker.ui` | 页面、画布、参数编辑器、主题与界面控制器 |
| `anclicker.domain` | 指令与图模型、参数描述、图校验、表达式和代码协议 |
| `anclicker.execution` | 无界面执行引擎、协作控制、流程运行、Agent 与执行辅助 |
| `anclicker.storage` | SQLite 仓储、数据库迁移、资源索引、工作簿解析与序列化 |
| `anclicker.platform` | 系统输入、窗口、后台组件、OCR 与浏览器桥接 |
| `anclicker.instructions` | 指令注册表、独立参数 schema 与执行器 |

根目录仅保留 `main.py` 与构建元数据 `info.py` 两个 Python 文件。原顶层模块的 86 个兼容入口集中放在 `legacy/`；原指令模块、`node_editor`、`WindowControl` 等包也已集中到 `legacy/`，保留兼容导入。多数兼容文件将旧名称绑定到同一个实现模块，而非复制实现，因此旧路径的 monkeypatch 与新路径访问一致。

应用和项目内工具通过加载 `anclicker` 注册兼容目录。外部脚本需要先 `import anclicker`，再使用旧顶层模块名，或者同时将根目录及 `legacy/` 加入 `PYTHONPATH`。这项源码导入初始化要求以及迁移后的命令行入口见 [兼容说明](../legacy/README.md)。新代码直接使用所属包。

后台 PowerShell/C#/JSON 文件放在 `resources/background/`，图标及 QRC 源放在 `resources/`，生成的 Qt 资源绑定放在 `anclicker/ui/generated/`。QRC 通过 alias 保留原来的 Qt URL。OCR 和后台工作进程位于 `anclicker/platform/`，通过包入口启动；源码 OCR 子进程显式使用安装根目录作为工作目录。后台独立 Python 的绝对路径适配保留在 `legacy/`，打包配置同时收集适配脚本和资源。生成的指令 UI 和第三方源码继续使用各自专用目录。

跨职责拆分的旧模块通过重导出保留类与函数。测试替换内部依赖时应使用实际所属模块：例如 RPA 执行器的 `get_bridge` 位于 `anclicker.instructions.common.rpa_instruction`，路径常量位于 `anclicker.app.paths`。宿主扩展优先使用执行服务注入接口。

`functions.py` 仅重导出路径、图像、系统和时间工具。新代码应直接导入相应模块。只使用路径时导入 `anclicker.app.paths`，不加载 Qt 或图像依赖。

## 执行与存储

- `ExecutionEngine.execute(snapshot, context, control, mode)` 支持显式快照运行；`CommandThread` 负责 Qt 信号和线程生命周期，并保留旧控制方法。
- `ExecutionControl` 使用 Python 锁、条件变量和事件管理协作停止、暂停及调度让出。不会强制终止持锁工作线程。
- `ExecutionServices` 注入日志、指令定位、异常交互、缓存清理和指令服务；`RuntimeDependencies` 提供数据库、等待、子项目调用和 OCR 池。
- `EditorContext` 单独持有编辑窗口能力；运行期上下文不再注入主窗口。为注入服务和扩展兼容，`database`、`wait_interruptibly`、`run_project` 仍作为旧 metadata 键提供，内部执行器优先读取显式依赖。
- `ApplicationState` 实时汇总主任务、指令测试、录制、定时任务、Agent 与更新状态。Agent 使用独立活动状态，不占用指令测试标记。
- `DatabaseOperation` 是组合门面，转发配置、变量、资源、最近项目和迁移操作。提示音和窗口恢复由平台服务执行。
- 工作簿解析先完成数据校验，仓储随后在一个事务中替换指令、节点、连线和关联设置；解析器本身不写数据库。

## 指令维护与生成

注册项保留旧 `module_path`，增加可选的 `editor_module_path`、`executor_module_path` 和 `schema_module_path`。缺省编辑器或执行器路径时仍回退到旧模块。`hidden_imports()` 返回完整动态依赖，`ui_hidden_imports()` 单独返回生成 UI 路径。

每条指令的 schema 是参数名称、默认值和选项的唯一来源，编辑器与 Agent 都使用它。执行器可以独立导入，不加载编辑器。保存到项目中的中文 type_id 和参数键名保持不变；包含标点的模块目录在内部使用合法 Python 标识符。

RPA 与后台指令的生成规则：

1. 修改 canonical schema 中的参数定义和`resources/ui/instructions/` 中的 Designer `.ui` 源码；公共行为修改共享编辑器或执行器。
2. 对应 RPA 命令增加或变更时，同步 `integrations/yingdao/commands.json`。
3. 使用下面的显式入口生成薄编辑器适配和 Qt 绑定；生成器不覆盖 schema 或 `.ui` 输入。

```powershell
.venv-build\Scripts\python.exe tools/generate_rpa_instructions.py
.venv-build\Scripts\python.exe tools/generate_background_instructions.py
.venv-build\Scripts\python.exe tools/generate_rpa_instructions.py --check
.venv-build\Scripts\python.exe tools/generate_background_instructions.py --check
```

`--output-root <目录>` 可生成到临时目录；`--check` 在临时目录重新生成并比较（忽略平台换行差异），不修改源码。原有手写编辑器（例如本地 Word 答题器）不由这些生成器覆盖。网页多点取点和随机偏移的手写逻辑位于 `instruction_editors/extensions/coordinate_click.py`，生成适配器继承该扩展。检查使用 Windows PySide2 锁定工具链；其他 Qt 编译器版本生成的绑定可能具有不同格式。

## 验证

Windows 开发和成品基线为 Python 3.10.11 / PySide2 5.15.2.1。自动化测试目录 `test/` 及专用运行器已按要求删除；此前的测试结果仅作为历史记录，见 `MODULAR_REFACTOR_VALIDATION.md`。应用内指令测试、本地构建与成品验收入口保留，验收使用隔离数据目录，不覆盖现有 `.venv`。

```powershell
.venv-build\Scripts\python.exe tools/import_policy.py
.venv-build\Scripts\python.exe tools/build_local_test.py
.venv-build\Scripts\python.exe tools/packaging/smoke_release.py --dist artifacts/dist/local-test
.venv-build\Scripts\python.exe main.py
```

离线 OCR 源码测试使用 `.local/models/rapidocr`，可从锁定版本 `rapidocr_onnxruntime` 安装目录的 `models` 复制三份 ONNX 文件，不需要另行下载。成品构建也会使用这些模型或依赖包中的同版模型。

成品启动使用隔离数据，并检查 OCR、Excel、测试网页及 Agent 页面。Linux/macOS 的路径分支由自动测试覆盖，原生成品验收需要在各自平台执行。

完整的目录去向、环境保留方式、资源定位和历史脚本入口见 [目录说明](DIRECTORY_LAYOUT.md)。更新流程位于 `anclicker/app/updates/`，更新对话框位于 `anclicker/ui/dialogs/update_notice.py`，Qt 与 OCR 兼容实现位于 `anclicker/platform/`。

## 导入统一管理

图像素材的相对路径、外部图片导入和旧路径兼容规则见 [图像素材路径](IMAGE_RESOURCES.md)。

项目 Python 源码的 `import`、`from ... import ...` 语句统一放在文件头部，不能放在函数、类、条件分支中，也不能散落在模块的业务代码之后。独立脚本必要的 `sys.path` 头部初始化可以保留；`__future__` 导入继续遵守 Python 的位置规则。

普通依赖使用常规顶部导入。Qt、Windows 专用组件、可选库以及需要避免循环依赖的模块，在文件顶部通过 `anclicker._imports.DeferredImports` 集中声明，原调用边界按声明键取得真实模块、函数或类。不会把代理类传给 `isinstance`、Qt 或执行器，也不会提前初始化可选组件。每次解析读取实际模块属性，保留原有补丁、平台选择和异常处理行为。

```python
from anclicker._imports import DeferredImports as _DeferredImports

_module_imports = _DeferredImports(globals(), {
    'QFileDialog': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QFileDialog',), 0),
})
```

在需要该功能的调用边界使用 `_module_imports.load('QFileDialog')`；依赖路径和成员清单只在文件头部维护。注册表根据指令类型选择模块的动态加载协议继续保留。

```powershell
.venv-build\Scripts\python.exe tools/import_policy.py
```

该检查扫描应用、兼容层、工具、示例及历史源码目录，不扫描虚拟环境、依赖缓存或历史构建产物；构建入口和 GitHub 工作流均调用此检查。打包配置静态解析顶部依赖声明，收集真实模块与子模块；解析过程不会执行被检查的模块，Windows 独立后台 Python 所需源码也包含共享导入辅助模块。

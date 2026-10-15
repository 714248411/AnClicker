# 模块化改造验证记录

维护说明：自动化测试源码及 `tools/run_tests.py`、`tools/run_isolated_tests.py` 已按要求删除，本文测试命令、路径和结果均为删除前的历史记录。当前保留静态检查、本地构建、成品验收及应用内指令测试功能。删除后导入位置检查覆盖 1446 个 Python 文件，0 处违规，依赖锁检查通过。自动审批拦截了测试缓存删除，`test/__pycache__/` 中的 `.pyc` 暂留，不包含测试源码。

日期：2026-10-15。基线提交：`0c7f811`。应用版本仍为 `v1.6.2`。

## 改造交付

| 轮次 | 主要变化 | 阶段验证 |
| --- | --- | --- |
| 第一轮 | 清理不可达执行分支，提取路径、图像、系统、时间和主题职责 | 92 项测试、5 项子测试通过 |
| 第二轮 | 提取图模型、纯校验、工作簿协议；组合存储仓储；拆分表格、导航和代码控制器 | 84 项测试通过 |
| 第三轮 | 分离执行引擎、协作控制、Qt 适配、服务和上下文；统一活动状态，Agent 独立占用状态 | 183 项测试通过 |
| 第四轮 | 迁入 `anclicker`，保留兼容入口，分离 108 条指令的 schema/执行器/编辑器，更新生成和打包规则 | 完整回归、生成检查、协议比对和 Windows 成品验证见下文 |

指令 type_id、参数键名、数据库字段、工作簿协议和应用标识保持兼容。旧包的子模块保持相同类型身份，旧指令包的星号导出及原命令行入口保留。执行器与参数描述可以在不加载 Qt/编辑器的进程中导入。

编辑上下文向执行上下文转换时不传递窗口或编辑回调。Qt 适配层的事件转发、调度子类钩子和页面控制器使用弱引用，减少新增的所有权循环。

## 环境与完整回归

- 使用独立 `.build-python` / `.venv-build`：Python **3.10.11**、PySide2 **5.15.2.1**、锁定依赖；原 `.venv` 保留。
- 已逐文件执行全部 **132** 个 `test_*.py` 文件；其中 3 个辅助文件没有测试用例。
- 最终结果：**1,287 项测试、873 项子测试通过；2 项失败；1 项跳过；0 项收集/运行错误**。JUnit 合计 2,163 项检查。
- 新增架构与接口回归 **14 项通过**：覆盖轻量路径导入、无界面执行器/存储、依赖边界、显式快照执行、协作控制、窗口生命周期、上下文隔离、旧入口和 Agent 协议。
- RPA 84 个、后台 20 个生成文件通过一致性检查；生成入口可安全导入，支持临时输出和 `--check`。
- Agent v1 的工具、目录和 **108** 条指令参数协议，与版本化 `docs/agent-protocol-v1.json` 语义完全一致。
- 修改及新增 Python 源码通过 AST 解析和 Ruff 未定义名称检查；`git diff --check` 通过。
- `info.py`、`pyproject.toml`、`uv.lock` 无变更。

大批 Qt 用例在同一进程内存在原生状态累积问题：改造前基线曾在按键捕获处发生 access violation，改造后的单进程运行也出现过原生异常。最终完整覆盖使用逐文件新进程，保留每个文件的日志、JUnit 和汇总；失败和超时不会被当作通过。针对修复和接口调整的文件已复测并更新汇总。

测试运行器默认使用临时数据目录。初始基线测试生成的后台组件缓存已归档到 `build/refactor/baseline-created-data`，后续验证使用隔离目录。OCR 验证使用锁定依赖包自带的三份 ONNX 模型；Agent 请求使用替身，不调用付费模型服务或下载 Agent 权重。

## Windows 成品验证

构建更新了兼容模块、动态指令和新包的收集规则；最终使用 `collect_submodules('anclicker')` 补齐 `importlib` 入口的冻结依赖。

实际验证对象：`dist/local-test/AnClicker`。使用 `packaging/smoke_release.py --dist dist/local-test`，退出码为 **0**。

| 场景 | 结果 |
| --- | --- |
| 第一次启动，界面缩放 1 倍 | 就绪；7 个工作视图及窗口控制检查通过 |
| 第二次启动，界面缩放 2 倍 | 就绪；7 个工作视图及窗口控制检查通过 |
| 参数编辑器 | 两次均检查 406 个数字控件，图像点击布局与模态添加通过 |
| 旧项目迁移 | 2 条指令、工作簿往返及错误回滚通过 |
| 图像执行 | 14 项真实 OpenCV 检查通过，使用合成屏幕，不发送原生输入 |
| 离线 OCR | RapidOCR、独立工作进程及合成文字图检查通过 |
| RPA | 实际 Excel、内置浏览器、本地测试页、截图、窗口标题与网页录制通过 |
| 独立迁移入口 | 启动、转换测试文件并写出报告通过 |

成品验证确认 Agent 页面加载；模型推理、GPU 调度策略主要通过可控替身验证，不代表真实大模型推理或业务网站验收。Linux/macOS 已保留路径分支检查，未进行原生成品验证；也未进行其他 Windows 版本的实机验收。

## 保留的基线问题与记录位置

1. `test_background_appearance.py` 的绑定窗口参数面板，浅色/深色两个用例均测得高度 **629 px**，断言要求 `< 620 px`。同一失败现象已在重构前基线复现，本轮保持布局行为。
2. `test_real_extracted_wechat` 因缺少用户提供的 Windows 微信 OCR 运行时跳过。

本机详细记录位于以下忽略目录，不纳入源码提交：

```text
build/refactor/baseline.txt
build/refactor/baseline-first-failure.txt
build/refactor/round1.txt
build/refactor/round2-retry.txt
build/refactor/round3-verified.txt
build/refactor/all-isolated/summary.json
build/refactor/all-isolated/*.xml
build/refactor/all-isolated/*.txt
build/refactor/packaged-smoke-verified.txt
validation/local-build.log
```

改动保留在工作区，未提交、推送、上传或发布。新目录、接口和复现命令见 `MODULAR_ARCHITECTURE.md`。

## 根目录收尾（2026-10-15）

原先根目录的 86 个 Python 文件收敛为 `main.py`、`info.py` 两个，兼容入口集中到 `legacy/`；其中三个验收辅助模块移入 `anclicker/app/`，两个工作进程移入 `anclicker/platform/`，生成的 Qt 资源绑定移入 `anclicker/ui/generated/`。后台脚本、JSON 与 C# 资源归入 `resources/background/`，图标及 QRC 放入 `resources/`，专项说明文档归入 `docs/`。根目录剩余 13 个文件均为启动入口、配置、依赖、项目说明和许可证。

旧顶层名称通过 `anclicker` 初始化兼容目录；应用和项目内工具已处理。外部脚本需要先 `import anclicker`，或将 `legacy/` 与项目根目录同时放入 `PYTHONPATH`。旧的根目录脚本路径已迁移，命令行入口和兼容边界见 `legacy/README.md`。打包显式收集全部兼容名称及后台脚本适配。

本次增量验证结果：

- 10 个相关测试文件：**146 passed、860 subtests passed，失败/错误/跳过均为 0**（JUnit 共 1006 项检查）。覆盖路径、OCR、后台运行、注册表、执行、Agent、工作区和 RPA。架构检查增加根目录约束、兼容模块收集、资源 alias 与新进程导入验证，共 17 项通过。
- RPA 84 个、后台 20 个生成文件一致性检查通过；770 个 Python 文件 AST 解析通过；`git diff --check` 通过。
- 隔离数据的源码启动通过：7 个页面、406 个参数控件、迁移往返与回滚、14 项 OpenCV 检查、真实 RapidOCR 子进程、Excel、浏览器和网页录制。
- Python 3.10.11 / Windows PySide2 本地成品重新构建成功；成品首次和二次启动（缩放 1、2）及独立迁移入口通过，同样实际覆盖上述 OCR、Excel、浏览器和页面检查。
- `info.py`、`pyproject.toml`、`uv.lock` 未变化；原 `.venv`、`.idea/` 和用户数据保留。

记录位于 `build/refactor/root-cleanup/summary.json`、该目录下的 JUnit/日志、`build/refactor/root-cleanup-source-smoke.txt`、`build/refactor/root-cleanup-packaged-smoke.txt` 与 `validation/local-build.log`。本次收尾运行相关回归；上文全量测试是此前四轮改造的记录。已有两个布局基线失败、其他平台成品和真实 Agent 模型验证限制继续适用。未提交、推送、上传或发布。

## 目录归并验收（2026-10-15）

剩余旧包已经集中到 `legacy/`，生成绑定与 Designer 输入分别归入 `anclicker/ui/generated/` 和 `resources/ui/`；更新流程、更新界面、Qt 和 OCR 适配按职责归入应用包。历史示例和旧实现分别进入 `examples/`、`archive/`。此前残留在兼容目录中的跳转编辑器实现也已移入正式 UI 模块。

构建、成品、历史交付和验证记录归入 `artifacts/`；工具链、Electron、OCR 模型与缓存归入 `.local/`。原构建环境保留备份后，使用迁移后的 Python 3.10.11、锁定依赖从本地缓存重建 `.venv-build/`。原 `.venv/`、用户数据库、IDE 配置和 Agent 锁目录保持原位。具体去向及兼容边界见 [目录说明](DIRECTORY_LAYOUT.md)。此前各节记录的 `build/` 已移至 `artifacts/build/`，原 `validation/` 的历史内容保存在 `artifacts/validation/screenshots/`。

### 自动化结果

| 范围 | 最终结果 |
| --- | --- |
| 全量隔离回归 | **132 个文件，1294 passed、515 subtests passed、2 failed、1 skipped**；JUnit 共 1812 项检查、0 errors |
| 失败项复测 | 根目录脚本调用、资源路径、浏览器原生交互和连接历史均通过复测；只剩原有绑定参数面板浅/深色高度断言失败，仍为 629 px、要求 `< 620 px` |
| 架构检查 | 21 项通过：新增顶层目录约束、内部规范导入、旧包子模块身份、源码/成品资源路径分支、跨工作目录历史 CLI 与源码压缩包检查 |
| 生成一致性 | RPA 84 个、后台 20 个、OCR 22 个生成文件检查通过；OCR 旧生成脚本已转为共享生成入口，不再覆盖兼容目录中的实现 |
| 静态检查 | 活跃源码、工具、示例、兼容入口与测试共 1567 个 Python 文件 AST 解析通过；Ruff F821 通过；`git diff --check` 通过 |
| 工具与配置 | 依赖锁离线检查通过；两份 GitHub 工作流 YAML 解析通过；构建、输出和下载目录已同步；未运行远程 CI |

此前微信 OCR 真实运行时缺失所导致的 1 项跳过继续保留。单进程大量 Qt 用例的基线原生崩溃风险仍通过每文件独立进程规避。测试默认使用临时数据库与隔离数据目录。

### 实际启动与打包

- 从临时工作目录启动源码成功，7 个页面、406 个参数控件、迁移往返/回滚、14 项 OpenCV 检查、真实 RapidOCR 子进程、Excel、独立浏览器与网页录制通过；实际使用迁移后的 `.local/` 运行库和模型。
- Windows PySide2 本地成品重新构建；同一隔离数据目录中的首次与二次启动（缩放 1 和 2）以及独立迁移入口通过，覆盖上述界面、OCR、Excel 和浏览器检查。
- 额外发现并修复了外部后台 Python 解释器无法读取 PyInstaller PYZ 的问题：spec 从同一份实现中收集后台工作进程所需的最小源码及元数据。成品验收使用 `python -I`、临时工作目录直接导入成品中的后台工作进程与历史入口，确认资源可读、不依赖源码工作区、不加载 Qt。未调用用户提供的后台 DLL。
- 原用户 `data/` 文件、`.idea/` 文件的 SHA-256 与整理前一致；原 `.venv/pyvenv.cfg` 未变化。`info.py`、`uv.lock` 与项目名称/版本/依赖定义未变化；`pyproject.toml` 仅新增 pytest、Ruff 缓存目录配置。

最终记录：

```text
artifacts/validation/directory-suite/summary.json
artifacts/validation/directory-suite/*.xml
artifacts/validation/directory-suite/*.txt
artifacts/validation/directory-suite-recheck-progress.txt
artifacts/validation/directory-source-ready.json
artifacts/validation/directory-source-smoke.txt
artifacts/validation/directory-packaged-smoke-final.txt
artifacts/validation/local-build.log
artifacts/validation/generator-{rpa,background,ocr}.txt
artifacts/validation/directory-ruff.txt
artifacts/validation/directory-diff-check.txt
artifacts/validation/directory-preservation.json
```

主窗口绑定保留既有调整，本次没有重新生成；生成一致性结果仅针对上述三套指令生成器。Linux/macOS 成品、其他 Windows 版本、真实 Agent 模型/GPU 推理、用户后台 DLL 及缺失的微信 OCR 运行时未实际验收；Agent 使用可控替身，没有调用付费接口或下载模型权重。没有提交、推送、上传或发布。


## 导入统一管理验收（2026-10-15）

本轮将 278 个文件中的 1236 条原非头部导入集中到文件头部。普通依赖直接顶部导入；涉及 Qt、平台差异、可选组件和循环依赖的部分在顶部声明，通过共享 `DeferredImports` 在原边界取得真实对象，保留原加载时机、异常捕获、类身份和补丁行为。没有通过提前加载所有组件改变启动及无界面运行语义。协议式动态注册表继续保留。

新增 `tools/import_policy.py` 和导入行为回归，构建入口、两份 GitHub 工作流同步加入位置检查。架构边界检查同时读取顶部依赖声明；PyInstaller 静态收集声明中的真实模块与子模块，不执行被扫描的源码；外部后台解释器的最小源码集合包含共享加载辅助模块。

回归中发现旧 `instructions.common` 包把同名编辑器子模块解析为规范执行器的问题，已收紧兼容门面的属性转发范围，保持两类模块各自原有入口，并增加独立进程的同名子模块回归。

| 范围 | 本轮结果 |
| --- | --- |
| 导入位置 | 1583 个 Python 文件，0 处违规；覆盖应用、兼容层、工具、测试、示例和历史源码，排除环境、缓存及构建产物 |
| 全量隔离回归 | 133 个文件，**1303 passed、515 subtests passed、2 failed、1 skipped**；JUnit 共 1821 项检查，0 errors |
| 失败与跳过 | 原有浅/深色绑定参数面板高度仍为 629 px，要求 `< 620 px`；微信 OCR 实际运行时缺失导致 1 项跳过；已修复的旧入口失败复测通过 |
| 专项回归 | 8 项导入加载/检查回归、22 项架构检查通过；保留可选依赖错误时机、相对路径、类身份、导入钩子和同名旧入口 |
| 静态及生成 | Ruff F821、`git diff --check`、两份工作流 YAML 解析通过；RPA 84、后台 20、OCR 22 个生成文件一致性通过 |
| 业务结构核对 | 对本轮导入整理涉及的 163 个应用、兼容入口和启动文件去除导入声明/绑定后做 AST 比较，业务结构差异为 0；另有上述显式兼容门面修复 |
| 数据与环境 | 用户数据库及 `.idea/` 哈希不变，原 `.venv/pyvenv.cfg` 不变，Agent 锁目录保留；版本信息与依赖锁不变，HEAD 仍为 `0c7f811`，暂存区为空 |

全量测试结果已包含最终的导入专项及旧入口复测。记录位于 `artifacts/validation/import-suite/summary.json`、该目录 JUnit/日志，以及 `import-suite-recheck.txt`、`import-totals.json`、`import-policy.txt`、`import-business-audit.json`、`import-preservation.json`、`import-generator-*.txt`。历史各轮记录保持原义。


源码从临时工作目录启动通过；Windows PySide2 成品已重新构建，并通过同一隔离数据目录的首次、二次启动（缩放 1、2）。两者均实际覆盖 7 个页面、406 个参数控件、数据库迁移往返与回滚、14 项 OpenCV 检查、真实 RapidOCR 子进程、Excel、独立浏览器与网页录制。成品独立迁移入口，以及临时目录中使用 `python -I` 导入成品后台工作进程/旧入口、资源读取和无 Qt 检查通过。

启动记录为 `artifacts/validation/import-source-ready.json`、`import-source-smoke.txt`、`import-packaged-smoke.txt`；构建日志为 `artifacts/validation/local-build.log`。源码及成品验证全部使用临时数据；没有调用付费模型接口或下载模型权重。Linux/macOS 原生成品、真实 Agent 模型/GPU、用户后台 DLL 与缺失的微信 OCR 运行时未实际验证。未提交、推送、上传或发布。

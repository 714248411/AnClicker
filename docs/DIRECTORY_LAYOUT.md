# 工作区目录与迁移约定

## 顶层职责

```text
anclicker/        应用实现：app、ui、domain、execution、storage、platform、instructions
resources/       随应用分发的 UI 源、样式、图标、动画、后台协议与许可
integrations/    独立 Electron/JavaScript 自动化引擎
legacy/          旧 Python 模块名的薄转发
examples/        可运行示例（原 node_test）
archive/         只供人工对照的历史源码（原 old_ins）
tools/           开发、生成、验证和打包工具
docs/            项目说明与验证记录
data/            用户数据库、资源、模板和运行日志
artifacts/       构建中间物、成品、历史交付物、验证记录
.local/          本机工具链、运行库、模型、缓存及环境备份
```

根目录 Python 文件仍只有 `main.py` 和构建元数据 `info.py`。`.github/`、`.gitee/`、`.config/` 保留平台与工具发现入口；`.venv/`、`.venv-build/` 分别保留开发与锁定构建环境；`.agent-runtime/` 保留既有 Agent 运行包与进程锁规则。IDE 配置与 Python 自动缓存不属于应用模块。

## 原目录去向

| 原目录 | 当前归属 |
| --- | --- |
| `instructions/` | 历史入口在 `legacy/instructions/`；Designer 源在 `resources/ui/instructions/`；生成绑定在 `anclicker/ui/generated/instructions/`；实现按原模块化职责归属 |
| `node_editor/`、`WindowControl/` | 兼容入口在 `legacy/`，实现仍在 `anclicker/ui/` |
| `Window/` | `.ui` 在 `resources/ui/windows/`，绑定在 `anclicker/ui/generated/windows/`，图像和图标在 `resources/images/windows/`、`resources/icons/windows/` |
| `flat/`、`Window/flatwhite/` | `resources/styles/`、`resources/icons/`、`resources/animations/` |
| `update/` | 更新流程及线程在 `anclicker/app/updates/`；更新提示界面在 `anclicker/ui/dialogs/update_notice.py`；旧入口在 `legacy/update/` |
| `qt_compat/`、`wxocr_client/` | `anclicker/platform/qt_compat/`、`anclicker/platform/ocr/wxocr_client/`；旧入口在 `legacy/` |
| `node_test/`、`old_ins/` | `examples/node_editor/`、`archive/old_ins/`，不进入正式应用的模块收集 |
| `packaging/` | `tools/packaging/`，包括 spec、平台说明、构建及发布脚本 |
| `build/`、`dist/`、`release/` | `artifacts/build/`、`artifacts/dist/`、`artifacts/release/` |
| `validation/`、`.release-validation/` | 原记录分别保存在 `artifacts/validation/screenshots/`、`artifacts/validation/releases/`；新验证记录统一写入 `artifacts/validation/` |
| `.build-python/`、`.runtime-tools/` | `.local/toolchains/python-3.10.11/`、`.local/cache/` |
| `runtime/`、`ocr_models/` | `.local/runtimes/`、`.local/models/` |

所有既有构建产物均保留。原构建虚拟环境归档在 `.local/backups/venv-build-before-directory-layout/`，仅作保留备份；当前 `.venv-build/` 使用迁移后的 Python 3.10.11 工具链、按 `uv.lock` 从本地缓存重新创建。原 `.venv/`、`.idea/` 和 `data/` 未移动或覆盖。

## 导入、脚本和资源兼容

应用内代码使用 `anclicker.*`。外部源码脚本如继续使用旧顶层模块名，先 `import anclicker`，或将仓库根目录及 `legacy/` 同时加入 `PYTHONPATH`。兼容文件共享实现类和函数，旧包的子模块转发不会再次定义业务类。

```python
import anclicker
from instructions.registry import get_instruction_spec
from node_editor.items import NodeItem
```

物理脚本目录已经归并，外部调用方应更新硬编码路径。历史 Python 脚本名称也可通过统一入口运行：

```powershell
.venv-build\Scripts\python.exe tools/run_legacy.py migration_tool.py --help
.venv-build\Scripts\python.exe tools/run_legacy.py packaging/build_release.py --help
```

包内工作进程继续支持应用原有命令行标志。源码 OCR、更新工作进程通过资源定位接口获得项目根目录，不按新的源码深度推导安装位置。Qt 资源 URL 保留原 `:/按钮图标/Window/...`；QRC 文件路径和 Designer 的资源引用已更新。旧 `resource_path('flat/startup.gif')` 等已知资源别名仍可解析。

独立配置的后台 Python 无法读取应用的 PyInstaller PYZ。spec 会从现有实现中收集该工作进程所需的最小源码、公共元数据和资源；不维护第二份业务实现。Windows 成品验收会用隔离解释器验证该入口，不需要 Qt 或源码工作区。

本机 Electron 使用 `runtime_path('electron')` 定位到 `.local/runtimes/electron/`，OCR 使用 `model_path('rapidocr')` 定位到 `.local/models/rapidocr/`。构建时从这些位置取输入，成品内仍保留 `runtime/electron/`、`ocr_models/rapidocr/` 的运行包格式；Linux/macOS 分支与 Windows 共用定位接口。用户数据继续通过原数据目录规则及 `ANCLICKER_DATA_DIR` 管理。

## 常用命令

```powershell
# 准备锁定构建环境；已有 .venv 保持不变
python tools/prepare_build.py
.venv-build\Scripts\python.exe main.py

# 生成器支持 --output-root 与 --check，维护输入为 schema 和 resources/ui
.venv-build\Scripts\python.exe tools/generate_rpa_instructions.py --check
.venv-build\Scripts\python.exe tools/generate_background_instructions.py --check
.venv-build\Scripts\python.exe tools/packaging/generate_local_ocr.py --check

# 静态检查；本地构建与成品验收使用隔离数据
.venv-build\Scripts\python.exe tools/import_policy.py
.venv-build\Scripts\python.exe tools/build_local_test.py
.venv-build\Scripts\python.exe tools/packaging/smoke_release.py --dist artifacts/dist/local-test

# 源码导出只包含明确列出的源码目录，可指定临时输出位置验证
.venv-build\Scripts\python.exe tools/export_source.py --output artifacts/dist/source/AnClicker-source.zip
```

主窗口的维护输入在 `resources/ui/windows/`，现有绑定保留在 `anclicker/ui/generated/windows/`。这些绑定包含既有调整，不能使用 README 历史版本中的旧 `Window/` 路径命令直接覆盖；本次没有重新生成主窗口绑定。三套指令生成器有独立的一致性检查。

GitHub 工作流的源码、资源和构建产物路径已同步调整；本轮只进行了本地检查与 Windows 验证，没有触发远程构建或发布。其他平台成品仍需对应平台验收。

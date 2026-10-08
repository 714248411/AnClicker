# AI 打包并发布说明

本说明适用于 AnClicker 的 Windows x64 Velopack 绿色便携版。所有命令从项目根目录执行。参考 BrowserRPA_Lingle 的便携包流程，但以本项目实际脚本、版本和数据目录为准。

## 交付要求与边界

- 只生成绿色便携 ZIP，不生成 Setup 或 MSI。构建必须使用 `--noInst`，资产清单必须包含 Portable，不能包含 Installer。
- 用户交付文件为 `delivery/AnClicker-v<版本>-Portable.zip`。完整解压后双击根目录 `An Clicker.exe`，不要单独移动 EXE 或 `current`。
- Full、可选 Delta、更新索引和内部 Portable 文件用于更新与构建管理，不作为普通用户安装入口。内部文件名保持 Velopack 原样，不直接改名破坏资产引用。
- `build_velopack.py` 只做本地构建；`发布Velopack.py` 恢复历史七牛 Kodo 直传。只有用户明确授权生产发布时，才执行 `publish --yes` 或 `build --publish --yes`。不要照抄其他项目的凭据、项目标识或云端清理逻辑。
- 保留已有用户改动、数据及历史产物；不得为打包执行仓库回退或清空已有输出目录。新建独立输出目录，失败重试也使用新目录。
- 不并行运行多个构建：它们共用 `build/velopack` 和 `dist/velopack`。升级验证在构建完成后执行。

## 配置来源

更新相关设置只维护 `info.py` 中的 `UPDATE_CONFIG` 字典：包标识、通道、公开域名、项目目录、索引及便携包文件名、根启动器名、七牛桶/区域和环境变量名称。客户端、构建和发布直接读取同一个字典，不再保留独立的更新常量。派生字段紧接字典定义统一计算；AK/SK 实际值仍只在发布时从环境变量读取。

| 项目 | 本项目约定 |
| --- | --- |
| 应用版本 | `info.py` 的 `CURRENT_VERSION`；去掉开头的 `v` 后传给 Velopack |
| 版本策略 | 沿用本项目三段版本，例如 `v1.3.2`；不套用其他项目的年月版本，不擅自递增 |
| 更新说明 | `packaging/RELEASE_NOTES.md`，仅写实际用户可见变化 |
| Windows 文件版本 | 由 `info.py` 的版本派生，打包自动生成 Windows 版本资源 |
| 包标识 | `AnClicker` |
| 平台与通道 | `win-x64` |
| 更新源 | `info.py` 的 `UPDATE_CONFIG['url']`，当前为 `https://updates.ytsoftware.cn/an-clicker/win-x64` |
| SDK 与工具 | Python `velopack==1.2.0`、`.config/dotnet-tools.json` 固定 `vpk` 1.2.0 |
| 构建入口 | `packaging/build_velopack.py` |
| 验收入口 | 构建自动调用 `packaging/发布门槛.py`；完整本地升级另运行 `packaging/smoke_velopack.py` |

`pyproject.toml` 的元数据版本也从 `info.VERSION` 派生；程序版本以 `info.py` 为准，不从旧 ZIP 文件名猜测。更改版本、更新源或工具版本前先核对当前任务要求；工具提示存在新版不代表应当升级。

## 准备环境

使用 Windows x64、项目 `.venv` 和已安装的 .NET SDK。当前项目要求 Python >= 3.10；已有可用环境无需重复重建。

```powershell
Set-Location D:\PycharmProjects\AnClicker
git status --short
uv lock --check
dotnet --version
.\.venv\Scripts\python.exe -c "import PySide6, PyInstaller, velopack"
```

仅在环境缺失或依赖不完整时执行：

```powershell
uv sync --locked
dotnet tool restore
```

若锁文件与项目不一致，先查明差异，不用无关依赖升级掩盖问题。后续直接调用项目 Python。

## 构建与验证命令

项目已移除 `test` 测试脚本；构建时仍须执行下述打包验收和本地升级验证。

使用带版本和时间的全新输出目录，并保存日志：

```powershell
$releaseVersion = (& .\.venv\Scripts\python.exe -c "from info import CURRENT_VERSION; print(CURRENT_VERSION.removeprefix('v'))").Trim()
$releaseStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$releaseOutput = "release/portable-$releaseVersion-$releaseStamp"
New-Item -ItemType Directory -Force -Path build | Out-Null
$releaseLog = "build/portable-$releaseVersion-$releaseStamp.log"
.\.venv\Scripts\python.exe packaging/build_velopack.py --output $releaseOutput 2>&1 | Tee-Object -FilePath $releaseLog
if ($LASTEXITCODE -ne 0) { throw '构建或验收失败，不得交付' }
```

需要生成增量包时，在上述构建命令追加 `--base <上一版本完整包的实际路径>`。基线必须是同包标识、同通道且版本更低的 `AnClicker-<版本>-win-x64-full.nupkg`，不能使用 Delta 或测试版本包。脚本复制基线到新输出目录；缺少可靠基线时构建完整包，并明确记录未验证本次正式版本的增量升级。

构建成功后运行隔离的本地升级验证：

```powershell
.\.venv\Scripts\python.exe packaging/smoke_velopack.py 2>&1 | Tee-Object -FilePath "build/portable-upgrade-$releaseStamp.log"
if ($LASTEXITCODE -ne 0) { throw '本地升级验证失败，不得声称升级验收通过' }
```

该脚本使用刚构建的 `dist/velopack/AnClicker`，在 `build/velopack-upgrade/<唯一标识>` 创建 0.0.1 和 0.0.2 测试包，通过本地目录更新源验证升级。测试包不得交付或上传；它们的版本不改变正式应用版本。

## 必须通过的检查

构建脚本已自动执行以下门槛，不要仅凭 PyInstaller 或 `vpk pack` 返回成功就交付：

1. 拒绝 Setup 和 Installer 资产；便携 ZIP 必须包含 `.portable`、`Update.exe`、`An Clicker.exe`、`current/AnClicker.exe`、`current/sq.version`。
2. 检查程序目录和归档路径安全、CRC、Windows GUI EXE；禁止用户数据库和可变 `data`、`profiles` 混入。`defaults/命令集.db` 必须是构建时生成的空白种子。
3. 实际启动 onedir EXE、Portable `current` EXE 和根目录启动器，检查窗口、版本和启动报告；再次启动验证数据库及文件保留。根启动器会先退出，必须等待子程序报告，不能把启动器退出码当作成功。
4. 若生成 Delta，实际还原并逐项比较与目标 Full 的文件集合和内容，再启动还原后的程序。缺少或存在多个不明确的基线时不得绕过失败。
5. 验收成功后自动导出带版本号的交付 ZIP，通过 `.partial` 中间文件复制并校验大小和 SHA-256。同名文件或未完成的中间文件不会被覆盖。

本地完整升级脚本还验证从根启动器进入应用、下载、应用更新、重启及数据库和图片目录文件保留。保留它输出的结果报告路径。重新构建的产物需要重新验证，不沿用旧包结果。

## 数据与依赖注意事项

- 便携版数据默认在根目录 `data`，与 `current` 同级；不可放入会被升级替换的 `current`。`ANCLICKER_DATA_DIR` 优先，无写权限时保留现有用户目录回退。
- 验证使用隔离数据，不运行真实自动化任务、不发送消息、不登录外部服务。迁移已有数据时先退出程序、备份整个目录，不覆盖合并已有目标数据。
- 构建脚本已隔离 PATH，防止其他工具的 ICU/Qt DLL 污染。遇到 QtCore 加载失败时检查实际依赖来源，不照抄其他项目的 DLL 排除列表。
- `packaging/build_release.py` 和现有 GitHub 工作流是另一套普通 ZIP 流程，不等于本指南的 Velopack 便携包构建。不要以推送 tag 或触发工作流代替本地构建。

## 交付与生产发布

向用户提供本次 `$releaseOutput/delivery/AnClicker-v<版本>-Portable.zip` 的真实路径，并报告版本、测试结果、启动与升级验证结果，以及是否上传。可用以下命令记录交付哈希：

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath "$releaseOutput/delivery/AnClicker-v$releaseVersion-Portable.zip"
```

`validation.json` 不是当前构建脚本自动生成的文件；若另行生成，只记录本次实际执行结果，不复制旧报告中的成功结论。

### 七牛发布环境

仅发布环境需要 `uv sync --locked --group release`，包含固定版本 `qiniu==7.17.0` 和测试依赖。七牛 SDK 及发布模块禁止进入客户端包，发布前检查实际 EXE 内的 Python 模块清单。

| 环境变量 | 默认值 / 用途 |
| --- | --- |
| `QINIU_BUCKET` | `ytsoftware-velopack` |
| `QINIU_REGION` | `z0`（华东） |
| `QINIU_KEY_PREFIX` | `an-clicker/win-x64` |
| `QINIU_PUBLIC_BASE_URL` | `https://updates.ytsoftware.cn`，仅 HTTPS 域名 |
| `QINIU_ACCESS_KEY` | 发布必需，由维护者环境或 CI Secrets 注入 |
| `QINIU_SECRET_KEY` | 发布必需，由维护者环境或 CI Secrets 注入 |

不读取 qshell 账号文件。不把 AK/SK 写进代码、客户端、文档、命令历史、日志或仓库配置；不要执行打印环境变量的命令。只读检查和构建不需要上传凭据。`info.py`、包内自动生成的 `update-source.json` 快照和上传目标必须一致。根目录不再维护 JSON 配置文件，客户端直接读取 `info.py`；快照只用于构建发布核验，不含任何凭据。

### 两阶段及一键发布

以下命令中的 `$releaseOutput` 采用前面生成的新目录；第一条会检查公网版本并自动下载、校验最新 Full 基线，无历史版本时构建完整包。只有 feed 返回 404 才视为首次发布，其他网络、TLS 或格式错误必须停止。

```powershell
# 联网检查并构建，不上传
.\.venv\Scripts\python.exe packaging/发布Velopack.py build --output $releaseOutput

# 对该目录重新执行门槛并上传；仅在用户授权后执行
.\.venv\Scripts\python.exe packaging/发布Velopack.py publish --output $releaseOutput --yes

# 或一键构建上传，必须使用新的输出目录且已获发布授权
.\.venv\Scripts\python.exe packaging/发布Velopack.py build --output $releaseOutput --publish --yes
```

上述流程与前面的离线构建二选一，不向已完成构建的目录再次运行 build。发布已有产物时默认对应 `dist/velopack/AnClicker`，可用 `--app-dir <对应程序目录>` 指定保留的构建。Full、Portable 与程序目录会逐文件比对，任一不一致就停止。产物路径不能代替验证。

### 上传顺序与恢复

发布版本必须严格高于线上版本。上传前重新验证产物、公开更新源、桶、区域及公开访问属性。仅上传当前 Full 和可选 Delta；逐包通过公网大小和 SHA-256 校验后，再检查一次远程版本，最后写入 feed、刷新 CDN，并同时验证缓存规避 URL 和客户端原始 URL。

Portable、delivery、assets、RELEASES 和本地测试包不上传；历史远端包不自动删除。禁止多人同时发布同一前缀，本流程没有跨机器事务锁。

包上传失败且 feed 尚未发布时，可以重试同一批产物；同名远端包仅在内容完全相同时复用。feed 已写入但刷新或验证失败时，可能已经对用户可见：保留产物和日志，先核对云端及 CDN 状态，不自动重建、覆盖同版本或降级。修复通过更高版本发布，不手工绕过门槛。

“接入上传功能”不等于授权执行生产发布。2026-10-08 的索引 404 是历史检查结果，不代表当前状态。

本地构建成功不等于线上发布，测试源升级成功也不等于生产客户端升级成功。未来上线后还需独立检查公网索引和下载包，并验证实际客户端升级。

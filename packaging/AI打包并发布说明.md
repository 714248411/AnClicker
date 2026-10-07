# AI 打包并发布说明

本项目 Windows x64 使用 PyInstaller onedir + Velopack 1.2.0。发布工具直接访问七牛 Kodo，客户端只读取公开 HTTPS feed 和更新包，不使用后端上传服务。macOS/Linux 沿用原 ZIP / GitHub Release 流程。

## 配置与版本

在项目根目录使用 Windows x64 Python 3.11、uv 和 .NET SDK。执行 `uv sync --python 3.11 --group release`、`dotnet tool restore`。vpk 使用仓库固定版本，七牛 SDK 仅在 release 依赖组中。

`info.py` 的 `CURRENT_VERSION` 是版本来源，保持三段数字；打包版本去掉 v 前缀。发布前更新 `packaging/RELEASE_NOTES.md`。正式版本必须高于远程索引，不可覆盖已发布版本。

发布配置均从环境变量读取：

| 变量 | 含义 / 缺省值 |
| --- | --- |
| QINIU_BUCKET | 公有桶，默认 ytsoftware-velopack |
| QINIU_REGION | 区域，默认 z0（华东） |
| QINIU_KEY_PREFIX | 对象目录，默认 an-clicker/win-x64 |
| QINIU_PUBLIC_BASE_URL | 必填，绑定对应桶的公开 HTTPS 域名，仅域名，不带目录 |
| QINIU_ACCESS_KEY | 发布时必填，由维护者环境注入 |
| QINIU_SECRET_KEY | 发布时必填，由维护者环境注入 |

构建不需要 AK/SK，会将公开地址写入程序资源 `update-source.json`，用户无需配置环境变量。发布时必须与该地址一致。客户端不读取云端密钥；发布脚本不读取 qshell 账号文件。不要将密钥写入源码、文档、命令历史、.env 或日志，CI 使用 Secrets 注入。当前测试域名 HTTPS 证书校验失败，必须先绑定有效 HTTPS 域名；工具不会关闭证书验证。

## 构建与验证

```powershell
uv run --group release python packaging/发布Velopack.py build
```

输出位于 `dist/velopack/win-x64`：Portable ZIP、Full nupkg、可选 Delta 与 `releases.win-x64.json`。Portable ZIP 本地保存，更新源仅发布当前 Full/Delta 和 feed。Portable 根目录入口为 `An Clicker.exe`，独立迁移入口使用 `"An Clicker.exe" --migration-tool`。

构建先读取远程 feed，检查版本，并下载校验最新 Full 作为增量基线。首次发布 feed 为 404 时生成完整包；其他网络错误不得当成首次发布。数据种子在临时目录生成，只将空白默认数据库放在只读 `defaults` 中，不能打包开发者 data。

build 和 publish 都执行发布门槛：检查路径安全、CRC、GUI EXE、Full/Portable 与构建一致、空白数据库种子、真实程序首次及重复启动、数据库及用户文件保留；存在 Delta 时还原并比较 Full，再启动还原程序。Portable 实际入口位于 `current`，根目录启动器需要检查派生进程的报告，不能只依赖启动器退出码。

源码和普通 ZIP 不自更新。Windows Velopack 程序启动后后台检查和下载，状态栏显示进度，帮助菜单提供“检查更新”和“重启更新”。不会启动时自动安装。任务、录制、指令测试或模态编辑中不能应用更新；重启前询问保存，保存取消则取消更新。SDK 检查/下载中退出会提示稍后重试，避免销毁正在运行的线程。

## 发布

```powershell
uv run --group release python packaging/发布Velopack.py publish --yes
# 或构建并发布
uv run --group release python packaging/发布Velopack.py build --publish --yes
```

顺序为：本地门槛 → 公网版本检查 → SDK 验证桶及区域 → 上传 Full/Delta → 公网下载核对大小及 SHA-256 → 再核对远程版本 → 最后上传 feed → 刷新 feed CDN 缓存 → 核对带参数及客户端原始 URL 的 feed。HTTPS 证书必须有效，桶及域名应允许无认证下载。不要多人同时向同一前缀发布，七牛 feed 覆盖没有跨发布进程事务锁。

上传中断且 feed 未变时，可重试相同产物；同名版本包只有内容完全相同才允许复用。feed 已写入而刷新/验证失败时可能已对用户可见，先核对七牛和公网状态，完成 CDN 刷新；不要重建或覆盖同一版本。回滚采用更高版本发布修复，不降低版本号。历史包默认保留，不自动删除。公网验证失败不输出发布成功。此流程不代替从客户机 Portable 正式入口进行实际更新验收。

## 旧版迁移与验证边界

旧 ZIP 无更新器，需手动解压首次 Portable 到新目录，关闭旧程序后将原 `data` 复制到新安装根目录，与 `current` 并列。不要放进 `current`，也不要复制开发者根目录旧数据库。先备份再迁移；外部 xlsx、图片和 Excel 资源需保持原路径或重新配置。

Velopack 将程序更新到可替换的 `current`，数据库、设置、模板及默认资源留在根目录 `data`。`ANCLICKER_DATA_DIR` 仍可覆盖位置；Windows 不可写目录回退到 LOCALAPPDATA/AnClicker。macOS/Linux 原行为不变。

缺少正式域名时，可本地构建 PyInstaller 与使用本地更新源进行隔离验证，但不能声称正式七牛构建或公网更新已验收。AK/SK 缺失不妨碍客户端和本地验证，阻止实际发布。GitHub 工作流保持原有 ZIP 发布，不自动向七牛写入。

## 本地更新验收工具

使用带公开配置资源的 Windows onedir 构建后运行：

```powershell
uv run --group release python packaging/verify_local_update.py
```

该工具不访问七牛，生成当前二进制的两个包版本，低版本仅为合成更新器基线（不是旧版产品代码）。输出到忽略的 `.release-validation/releases`，通过 Delta 还原验证和 Portable 根目录启动器完成 SDK 下载、应用、重启，检查安装外侧 data 中数据库及用户文件保留，并从升级后的根目录入口验证 GUI 就绪。验收结果保存为 `.release-validation/local-update-evidence.json`。需要 patch >= 1；默认要求新的输出目录，避免混入旧包；`--output` 可指定另一空目录。

此验收覆盖更新器流程，不代替真实历史版本的数据库迁移兼容性测试，也不代表七牛公网发布成功。

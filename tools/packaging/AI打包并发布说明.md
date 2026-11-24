# AnClicker Windows x64 打包与内部更新

`info.py` 定义应用版本和包身份。`publish.json` 对应正式渠道，`publish.beta.json` 对应测试渠道。两者沿用软件标识 `an-clicker`、Pack ID `AnClicker`，更新索引均为 `releases.win-x64.json`。

| 渠道 | 更新地址 | 输出目录 |
| --- | --- | --- |
| stable | `https://www.ytsoftware.cn/api/v1/internal-updates/an-clicker/stable/` | `build/updates/stable/<版本>/` |
| beta | `https://www.ytsoftware.cn/api/v1/internal-updates/an-clicker/beta/` | `build/updates/beta/<版本>/` |

## 本地构建

使用 Windows x64、Python 3.10.11、项目锁定的 PySide2 和 Velopack 1.2.0，以及发布机上的 software-publisher 1.3.0。安装依赖后，从 GitHub v1.9.2 Release 取得 `AnClicker-v1.9.2-win.zip`。准备命令会核对已发布 SHA-256，在新目录解压便携基线，并安装此次构建所需的运行时输入。

```powershell
uv sync --locked --python 3.10.11 --group release
dotnet tool restore
$py = '.\.venv\Scripts\python.exe'
$baseline = & $py tools/packaging/prepare_update_baseline.py AnClicker-v1.9.2-win.zip artifacts/baseline/extracted
& $py tools/release_workflow.py build --channel beta --runtime-bundle $baseline
& $py tools/release_workflow.py build --channel stable --runtime-bundle $baseline
& $py tools/release_workflow.py freeze --channel beta
& $py tools/release_workflow.py freeze --channel stable
```

各渠道构建会检查归档内容、应用启动、用户数据保留和包内更新地址。构建要求使用空输出目录。冻结前对照 Full、完整便携 ZIP 和索引验证渠道、大小与哈希。冻结清单仅包含 Full 更新，便携 ZIP 留在各渠道的 `delivery` 子目录供首装分发。

```powershell
& $py tools/packaging/smoke_internal_update.py --legacy (Split-Path $baseline) `
  --beta build/updates/beta/1.9.3 --stable build/updates/stable/1.9.3 `
  --output artifacts/validation/internal-update-1.9.3
```

烟雾测试在隔离目录启动上一版本，验证下载、确认更新、重启、用户文件保留和升级后的正式渠道选择。两个渠道的索引分别通过本地 HTTP 验证。

## 数据与依赖注意事项

- 便携版数据默认在根目录 `data`，与 `current` 同级；不可放入会被升级替换的 `current`。`ANCLICKER_DATA_DIR` 优先，无写权限时保留现有用户目录回退。
- 验证使用隔离数据，不运行真实自动化任务、不发送消息、不登录外部服务。迁移已有数据时先退出程序、备份整个目录，不覆盖合并已有目标数据。
- 构建脚本已隔离 PATH，防止其他工具的 ICU/Qt DLL 污染。遇到 QtCore 加载失败时检查实际依赖来源，不照抄其他项目的 DLL 排除列表。
- `tools/packaging/build_release.py` 和现有 GitHub 工作流是另一套普通 ZIP 流程，不等于本指南的 Velopack 便携包构建。不要以推送 tag 或触发工作流代替本地构建。

## 获得上线授权后

确认候选版本高于现有分发版本，确认软件中心内部更新使用公有七牛桶 `ytsoftware-velopack-public`，并设好正式和测试环境各自的对象前缀。发布机通过进程环境设置 `YT_PUBLISH_PASSWORD`。

```powershell
yt-software-publish publish --build build/updates/beta/1.9.3/unified-build.json --recovery-dir build/publisher-recovery --yes
# beta 验证真实更新通过后发布 stable
yt-software-publish publish --build build/updates/stable/1.9.3/unified-build.json --recovery-dir build/publisher-recovery --yes
```

从软件卡片复制两个渠道的实际地址。用隔离安装验证真实环境下载、应用和升级，再核对 stable 公网索引及 Full 的 SHA-256。上传结果不明确时，用原冻结清单核对服务端状态后恢复发布。

旧版迁移仅在内部 stable 已可匿名下载同一 Full 时执行。以下命令使用旧七牛仓的发布环境，先验证内部 stable，再上传相同的 Full 并刷新旧索引。迁移后用一份旧安装确认应用自动切换到新地址。

```powershell
& $py tools/packaging/发布Velopack.py publish --output build/updates/stable/1.9.3 --yes
```

## v1.4.9 更新中退出

检查和下载在独立子进程运行，普通关闭先询问“继续结束”或“等待”。继续结束先保存多功能代码，然后停止本次检查/下载子进程，不触碰已安装版本，不提前标记更新就绪。本地升级探针同时覆盖打包后的检查/下载子进程。

## v1.5.2 起的文件命名

Windows 完整包为 `AnClicker-v<版本>-win.zip`，对应源码包为 `AnClicker-v<版本>-win-DaiMa.zip`。Linux 和 macOS 后续原生构建沿用 `linux`、`mac` 平台后缀，源码在平台后加 `-DaiMa`；不得将 Windows 二进制改名作为其他平台的可运行包。哈希文件在 ZIP 名称后添加 `.sha256`。

## v1.8.3 完整七牛更新包

普通 onedir ZIP 不含 Velopack 根启动器和 current/sq.version，不能自动更新。当前完整发布流程为 check_release_183.py → check_release_models_183.py → build_release_183.py → package_release_183.py --stage → qiniu_release_183.py pack → export_qiniu_183.py → qiniu_release_183.py validate → smoke_qiniu_183_upgrade.py → qiniu_release_183.py publish <外部凭据文件>。上传必须在明确授权后执行。

产物位于 artifacts/release/v1.8.3-qiniu，交付包位于 delivery。只向七牛上传正式 Full 和索引，发布脚本负责公网完整哈希及 CDN 索引校验。保留双模型、OCR、Electron、Crawl4AI 与 CPU/Vulkan 运行库。更新门槛禁止省略这些文件。

Data 位于根启动器同级，不能置于可替换的 current 中。旧普通 ZIP 用户需退出旧程序、备份 Data，换用完整受管理包后再使用七牛更新。启动仅检查一次，20 秒超时静默结束；下载与安装需手动进入检查更新并确认。

升级验证使用正式 Full，通过隔离目录中的较低 sq.version 元数据模拟旧版本，实际验证检查、下载、手动确认、安装、重启及数据库/图片保留。这不是对真实旧版二进制的兼容性测试，也不上传测试元数据。

验收子进程设置 PYTHONDONTWRITEBYTECODE=1，避免依赖导入生成缓存改变验收文件清单。依赖 wheel 的包专属 .libs 路径及 pip/setuptools 启动器模板按实际用途校验，不删除必备运行文件。

公网大包校验按 16 MiB 分段读取，连接中断仅重试当前段；逐段范围和最终 SHA-256 均须匹配。任何校验失败都禁止写入新索引。已上传但尚未发布索引的同内容包可安全复用。


### 下个版本：复制 Data 手动迁移
关闭新旧程序，将旧 Data 的全部内容复制到新版根目录 Data（包括命令集.db、exports 和 images），然后启动新版。启动会将已复制且相对路径匹配的最近项目、当前项目、项目控制设置和定时任务路径改为新版 Data，并在 migration_backups 中保留数据库备份。图片仍优先有效绝对路径，再搜索 Data。外部未复制文件不会被猜测替换。
空目录中误粘贴为 Data/Data 时，可直接使用内层数据；外层已存在数据库时不自动覆盖，以外层为准。
发布前运行 tools/check_portable_data_migration.py 以及图片路径回归。下一版根目录启动器统一为 AnClicker.exe（不含空格），同步打包标题、校验和说明。

### v1.8.4 发布流程
使用 check_release_184.py、check_release_models_184.py、build_release_184.py、package_release_184.py --stage、check_frozen_data_migration_184.py、qiniu_release_184.py pack/startup/validate、smoke_qiniu_184_upgrade.py、export_qiniu_184.py。升级测试使用已发布的真实 v1.8.3 便携包，验证启动器改名、安装重启和 Data 保留。发布仍仅上传七牛完整更新包与版本索引；校验全部公网字节后才更新索引。

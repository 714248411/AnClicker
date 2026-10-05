# An Clicker v1.0.0 Beat

本版本提供 Windows、macOS 和 Linux 三个平台的独立压缩包，其中 macOS 同时提供 Intel 与 Apple Silicon 原生版本。

### 启动修复

- 修复双击 AnClicker.exe 提示 `No module named 'Start_Win'`：主窗口及依赖完整打包。
- 首次启动自动创建图像、导出、日志、临时目录，并初始化数据库与默认配置，无需安装 Python 或手动执行 pip。
- Windows 安装目录无写权限时自动使用当前用户的 LocalAppData/AnClicker 数据目录。
- 启动异常自动保存 startup-error.log 并提示具体路径。
- 发布前必须运行打包程序两次，验证五个视图主窗口真正就绪，避免将错误对话框误判为启动成功。

- 统一平台数据目录、文件/文件夹打开方式、提示音与窗口恢复逻辑。
- Windows 保留原有全局快捷键和便携式 `data` 目录行为。
- Linux 在桌面环境支持时启用全局快捷键；Wayland 或无桌面会自动降级为界面按钮。
- macOS 无可用全局快捷键后端时自动降级为界面按钮，不影响表格、流程图、多功能和导航视图。
- 各平台包均由对应 GitHub Actions 原生运行器构建；不是交叉编译产物。

首次运行自动创建可写数据目录。macOS 如阻止未签名应用，可在“系统设置 → 隐私与安全性”中允许打开；键鼠自动化功能需要授予辅助功能与屏幕录制权限。Linux 键鼠自动化需要 X11 或桌面兼容层支持。

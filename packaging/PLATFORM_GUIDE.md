# v1.5.0 平台使用说明

Windows、Linux、Mac 分别提供完整应用和对应源码。Mac 下载包包含 Intel 与 Apple Silicon 两个原生版本，请按电脑芯片选择文件夹。

## Mac

完整解压后，Intel Mac 使用 `Intel/AnClicker.app`，M 系列使用 `Apple-Silicon/AnClicker.app`。应用尚未使用 Apple Developer ID 签名或公证，系统可能阻止首次打开；确认来源后，可在“系统设置 → 隐私与安全性”中允许打开。

键鼠自动化、录制和截图需要按系统提示授予辅助功能、输入监控、屏幕录制权限。CI 使用 macOS 15 的 Intel 和 Apple Silicon 系统验证；其他系统版本与真实桌面权限交互仍需实际环境测试。

## Linux

使用 Ubuntu 24.04 x64 或兼容环境，并登录 X11 桌面会话。完整解压后运行 `AnClicker/AnClicker`。Wayland 桌面的全局键鼠和截图功能未验证。

Ubuntu 系统依赖可安装：

```sh
sudo apt-get install scrot xdotool libegl1 libgl1 libopengl0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0 libxcb-shape0 libxkbcommon-x11-0 libnss3 libasound2t64 libgtk-3-0
```

Ubuntu 24.04 的沙箱限制可能要求配置内置浏览器的沙箱辅助程序。将程序放在可信的固定目录，校验下载文件后，在解压目录执行一次：

```sh
sudo chown root:root AnClicker/runtime/electron/chrome-sandbox
sudo chmod 4755 AnClicker/runtime/electron/chrome-sandbox
```

日常启动使用普通用户，不要以 root 运行主程序。不要关闭浏览器沙箱。CI 在 Ubuntu 24.04、X11 虚拟显示器及上述沙箱配置下验证。

## 源码与验证

macOS/Linux 构建流程见 `.github/workflows/platforms.yml`。需原生平台的 Python 3.10（包含 Tcl/Tk）、uv，以及流程中列出的系统依赖；依赖使用 `uv.lock` 锁定。Windows 包保持既有正式版，源码来自对应已发布版本。

成品检查覆盖完整解压、版本、两次启动、界面、图像识别、离线 OCR、表格、内置浏览器、网页录制及旧数据迁移。图像和录制检查使用测试数据，不能代替用户桌面上的权限授权与真实业务验收。

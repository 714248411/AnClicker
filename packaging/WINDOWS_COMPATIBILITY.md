# Windows 统一兼容构建

目标为 Windows 10 1607（build 14393）起的 **x64** Windows 10 / Windows 11，同一套界面和业务功能。32 位 Windows 与 ARM 原生构建不在此包范围内。

Windows 锁定 Python 3.10.11、PySide2 5.15.2.1（Qt 5.15.2）、NumPy 1.26.4、OpenCV 4.10.0.84。非 Windows 继续使用 PySide6；应用经 `qt_compat` 访问 Qt，不按系统版本切换功能代码。`uv.lock` 为构建依赖依据；`requirements.txt` 从锁文件导出。

Qt 6.8 官方 Windows 下限为 1809，不能覆盖 1607。这里使用 Qt 5 并集中适配菜单执行、事件坐标、信号阻断与表单控件；图像点击仍使用当前模板、当前截图和点击前位置复核。Qt 5 的控件所有权差异已在图像面板中显式处理。

界面使用 Fusion 控件样式和 Microsoft YaHei UI 字体，保留原有明暗主题。DPI 设置早于输入库导入；支持新接口时使用 Per Monitor V2，旧系统回退到 Per Monitor。调用方或 manifest 已设置 DPI 时保持原策略。单实例采用 Qt 5/6 均具备的 QLockFile，并保留独立测试实例的环境变量。

## 验证结果与边界

当前验证机：Windows 10 Pro 22H2，build 19045，x64。

- 原有 564 项测试和 454 项子测试通过；1 项需本地专有组件的测试跳过。
- 新增 DPI 回退、既有 DPI 策略、信号作用域和菜单实例绑定测试通过。
- 打包后的启动、图像识别、OCR 独立进程、迁移和数据保留通过。
- 本地 0.0.1 → 0.0.2 更新、重启及 delta 还原通过（测试元数据，不改变正式版本）。
- 原生 Windows 插件在 100%、125%、150%、200% Qt 缩放下完成启动和功能验证；明暗主题已渲染检查。

这些是当前机器上的结果，**不等同于已实测 Windows 10 1607 或 Windows 11**。PE 依赖静态检查也不能证明所有延迟加载 API 和驱动环境兼容。兼容候选包不得凭上述结果标为全系统正式验证完成。

在干净的 Windows 10 1607 x64 与 Windows 11 x64 上，完整解压便携包，将 `check_windows_compatibility.ps1` 放到根目录，运行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\check_windows_compatibility.ps1
```

脚本仅对本次 PowerShell 进程指定执行策略，不修改系统策略。它以独立数据目录执行四档缩放的真实程序验证，将操作系统、EXE 哈希、Qt/Python 版本及各项结果保存到 `compatibility-report-*/result.json`，不会运行用户项目。

仍需手工检查跨显示器拖动、系统实际缩放切换、截图后替换图像、真实目标点击、快捷键、录制回放、窗口最大化/还原及数据迁移。旧系统实测通过并关联到同一 EXE 哈希后，才能把候选包提升为正式兼容下载。

参考：[Qt 6.8 Windows 范围](https://doc.qt.io/qt-6.8/windows.html)、[Python 3.10 Windows 范围](https://docs.python.org/3.10/using/windows.html)、[微软 DPI 回退规则](https://learn.microsoft.com/en-us/windows/win32/hidpi/setting-the-default-dpi-awareness-for-a-process)。

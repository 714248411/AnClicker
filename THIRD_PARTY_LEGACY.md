# 旧系统版许可证与对应源码

此版的原始 AnClicker 文件保留根目录 LICENSE（木兰宽松许可证第 2 版）及原有版权声明。
本次 Qt5 适配代码按 GPL-3.0-only 提供；包含 GPL PyQt5 的组合发行版按 GPLv3 分发。
许可证全文见 COPYING-GPL-3.0.txt。发行包无担保，允许按对应许可证修改、重新分发。
同一 Release 的 AnClicker-v1.2.6-pyqt5-legacy-source.zip 是应用的对应源码，含构建脚本、依赖版本及测试。

第三方组件仍保留各自许可证，并非全部重新许可为 GPL：

- PyQt5 5.15.10：Riverbank Computing，GPLv3（本次使用开源版）。源码与许可证：https://pypi.org/project/PyQt5/5.15.10/#files
- PyQt5-sip 12.15.0：Riverbank Computing，许可证及源码：https://pypi.org/project/PyQt5-sip/12.15.0/#files
- Qt 5.15.2：The Qt Company 与贡献者；动态链接，开源 LGPL/GPL 组件的许可证随 Qt 发行提供。未修改 Qt，可替换兼容动态库；Qt 对应源码：https://download.qt.io/archive/qt/5.15/5.15.2/single/
- QtPy 2.4.3：MIT，源码：https://github.com/spyder-ide/qtpy/tree/v2.4.3
- Python 3.10：PSF 许可证，源码：https://www.python.org/downloads/source/

构建：Windows x64 安装 Python 3.10，创建虚拟环境，执行
`python -m pip install -r requirements.txt pytest`、`python -m pytest`、
`python -m PyInstaller --clean -y packaging/main.spec`、`python packaging/smoke_release.py`，
最后执行 `python packaging/build_legacy_release.py`（源码目录必须来自 Git checkout）。

此版不捆绑七牛配置、密钥或本机 data；发布目录中 PyQt/Qt 运行库不得删减后再分发。

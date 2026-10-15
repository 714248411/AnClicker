# 历史 Python 入口

此目录只存放兼容转发，业务实现位于 `anclicker/`。应用和项目内工具先加载
`anclicker`，统一注册此目录；旧模块名仍指向同一个实现模块。

旧的 `instructions/`、`node_editor/`、`WindowControl/`、`Window/`、
`qt_compat/`、`update/`、`wxocr_client/` 已集中到此目录。包级兼容门面保留
自己的子模块搜索路径，子模块转发共享实现对象，避免同一业务类被定义两次。

外部脚本若原来直接从仓库根目录导入旧名称，需要先初始化兼容入口：

```python
import anclicker
from graph_repository import GraphRepository
```

也可以同时将项目根目录和 `legacy/` 加入 `PYTHONPATH`。新代码直接导入
`anclicker.storage.graph_repository` 等所属模块。

原来的根目录脚本路径已迁移；命令行使用包入口，例如：

```console
python -m anclicker.storage.migration_tool --help
python -m anclicker.platform.local_ocr_worker
python -m anclicker.platform.background_dm_worker
```

需要继续按历史脚本名称调用时，可使用统一分发入口：

```console
python tools/run_legacy.py migration_tool.py --help
python tools/run_legacy.py packaging/build_release.py --help
```

物理路径 `packaging/*.py` 已变为 `tools/packaging/*.py`，外部硬编码路径需同步修改。

工作进程使用标准输入/输出协议，通常由应用启动。`legacy/background_dm_worker.py`
保留给独立后台 Python 运行环境使用的绝对路径启动适配。

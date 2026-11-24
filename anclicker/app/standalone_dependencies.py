"""Conservative runtime selection for exported, non-editor projects."""
import json
from pathlib import Path

# These categories run entirely on the retained desktop/vision/Excel libraries.
DESKTOP_CATEGORIES = frozenset({'键鼠', '等待', '获取变量', 'Excel', '本地OCR', '窗口键鼠', '白话指令'})
DESKTOP_COMMANDS = frozenset({'时间等待', '打印日志', '屏幕截图', '窗口控制', '窗口排布', '提示音', '提示窗口', '快速文件操作', '折叠步骤', '暂不运行以下指令', '暂不运行以上指令', '终止流程', '多线程启动', '多线程关闭', '报错跳转', '变量比较', '循环', '条件判断', '条件循环'})

def runtime_profile(data):
    """Inspect every bundled workbook; uncertainty keeps the complete runtime.

    Subprojects and dynamic Python deliberately use the full fallback, including
    libraries they can load indirectly. This never removes project resources.
    """
    from openpyxl import load_workbook
    from anclicker.instructions.registry import get_instruction_spec
    kinds = set()
    try:
        books = [p for p in Path(data).rglob('*') if p.suffix.lower() in {'.xlsx', '.xlsm'}]
        for path in books:
            book = load_workbook(path, read_only=True, data_only=False)
            try:
                if '命令' not in book:
                    # A legacy command workbook cannot be classified safely.
                    if any('指令类型' in [c.value for c in sheet[1]] for sheet in book):
                        return {'mode': 'full', 'reason': 'legacy-project'}
                    continue
                sheet = book['命令']
                headers = [c.value for c in sheet[1]]
                if '类型标识' not in headers:
                    return {'mode': 'full', 'reason': 'unknown-project-format'}
                index = headers.index('类型标识')
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    if row[0] is not None:
                        kinds.add(str(row[index]))
            finally:
                book.close()
        if not kinds:
            return {'mode': 'full', 'reason': 'empty-or-unknown-project'}
        for kind in sorted(kinds):
            spec = get_instruction_spec(kind)
            if kind not in DESKTOP_COMMANDS and spec.category not in DESKTOP_CATEGORIES:
                return {'mode': 'full', 'reason': 'dependency:' + kind}
        return {'mode': 'desktop', 'excluded_directories': ['models', 'runtime'], 'commands': sorted(kinds)}
    except Exception:
        return {'mode': 'full', 'reason': 'dependency-analysis-unavailable'}

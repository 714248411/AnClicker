import contextlib
import ctypes
import datetime
import json
import os
import re
import sqlite3
import time

import win32con
import win32gui
import winsound

from functions import DATA_FOLDER, DATABASE_PATH, IMAGES_FOLDER
from graph_repository import COMMAND_COLUMNS, GraphRepository

SETTING_TYPE_BASIC = "基础设置"
SETTING_TYPE_THIRD_PARTY = "三方接口"
SETTING_TYPE_SHORTCUT = "全局快捷键"
SETTING_TYPE_ACTIVATION = "激活信息"

ACTIVATION_SETTING_ITEMS = frozenset({"激活月份", "激活状态", "激活校验日期"})
THIRD_PARTY_SETTING_ITEMS = frozenset({"appId", "apiKey", "secretKey", "云码Token"})


def get_setting_type(setting_item: str) -> str:
    """根据设置项名称返回统一的中文分类。"""
    if setting_item in ACTIVATION_SETTING_ITEMS:
        return SETTING_TYPE_ACTIVATION
    if setting_item in THIRD_PARTY_SETTING_ITEMS:
        return SETTING_TYPE_THIRD_PARTY
    if setting_item.startswith("快捷键-"):
        return SETTING_TYPE_SHORTCUT
    return SETTING_TYPE_BASIC

DEFAULT_SETTINGS = {
    "图像匹配精度": "0.8",
    "退出提醒清空指令": "False",
    "系统提示音": "False",
    "显示工具栏": "False",
    "任务完成后显示主窗口": "False",
    "当前文件路径": "None",
    "运行重复次数": "1",
    "执行中隐藏主窗口": "False",
    "appId": "",
    "apiKey": "",
    "secretKey": "",
    "云码Token": "",
    "快捷键-开始运行": "f10",
    "快捷键-结束运行": "f11",
    "快捷键-暂停和恢复": "alt+f11",
}

REMOVED_SETTING_ITEMS = (
    "模式",
    "时间间隔",
    "持续时间",
    "暂停时间",
    "启动检查更新",
    "高DPI自适应",
)

LEGACY_WINDOW_SETTING_KEYS = (
    "Clicker",
    "设置",
    "全局参数",
    "关于",
    "选择变量",
    "指令参数",
)


class DatabaseOperation:
    MIN_WINDOW_WIDTH = 120
    MIN_WINDOW_HEIGHT = 80
    _LEGACY_WINDOW_SIZE_PATTERN = re.compile(
        r"^[\(\[]\s*(-?\d+)\s*,\s*(-?\d+)\s*[\)\]]$"
    )
    _LEGACY_WINDOW_STATE_PATTERN = re.compile(
        r'''^\{\s*["']size["']\s*:\s*[\(\[]\s*(-?\d+)\s*,\s*(-?\d+)'''
        r'''\s*[\)\]]\s*,\s*["']maximized["']\s*:\s*(True|False)\s*\}$'''
    )

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.create_all_tables()
        self.ensure_setting_values(DEFAULT_SETTINGS)

    def create_all_tables(self) -> None:
        """创建配置相关表，并迁移旧版数据库中的全局参数。"""
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            cursor = conn.cursor()
            self._migrate_settings_table(cursor)
            cursor.execute(
                "DELETE FROM 设置 WHERE 设置项 IN ({})".format(
                    ",".join("?" for _ in REMOVED_SETTING_ITEMS)
                ),
                REMOVED_SETTING_ITEMS,
            )
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS 窗口大小 ("
                "窗口 TEXT NOT NULL PRIMARY KEY, 大小 TEXT NOT NULL)"
            )
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS 资源文件夹 ("
                "路径 TEXT NOT NULL PRIMARY KEY, 排序 INTEGER NOT NULL)"
            )
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS 最近打开 ("
                "文件路径 TEXT NOT NULL, 打开时间 INTEGER NOT NULL)"
            )
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS 变量池 ("
                "变量名称 TEXT NOT NULL UNIQUE, 备注 TEXT, 值 TEXT)"
            )
            GraphRepository.initialize_schema(conn)
            self._migrate_legacy_window_settings(cursor)
            self._migrate_legacy_global_parameters(cursor)
            cursor.execute(
                "INSERT OR IGNORE INTO 资源文件夹(路径, 排序) VALUES (?, 0)",
                (self.portable_resource_path(IMAGES_FOLDER),),
            )
            image_path = self.portable_resource_path(IMAGES_FOLDER)
            resource_rows = cursor.execute(
                "SELECT 路径 FROM 资源文件夹 "
                "ORDER BY CASE WHEN 路径=? THEN 0 ELSE 1 END, 排序, rowid",
                (image_path,),
            ).fetchall()
            for order_, (resource_path,) in enumerate(resource_rows):
                cursor.execute(
                    "UPDATE 资源文件夹 SET 排序=? WHERE 路径=?",
                    (order_, resource_path),
                )
            conn.commit()

    @staticmethod
    def _create_settings_table(cursor, table_name: str = "设置") -> None:
        cursor.execute(
            f'CREATE TABLE "{table_name}" ('
            "类型 TEXT NOT NULL, "
            "设置项 TEXT NOT NULL PRIMARY KEY, "
            "值 TEXT NOT NULL)"
        )

    @classmethod
    def _migrate_settings_table(cls, cursor) -> None:
        """将旧设置表无损迁移为“类型、设置项、值”三字段结构。"""
        table_exists = cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='设置'"
        ).fetchone()
        if not table_exists:
            cls._create_settings_table(cursor)
            return

        table_info = cursor.execute("PRAGMA table_info('设置')").fetchall()
        column_names = [column[1] for column in table_info]
        desired_constraints = [
            ("类型", 1, 0),
            ("设置项", 1, 1),
            ("值", 1, 0),
        ]
        current_constraints = [
            (column[1], column[3], column[5]) for column in table_info
        ]

        if column_names == ["类型", "设置项", "值"]:
            rows = cursor.execute(
                "SELECT 设置项, 值 FROM 设置 ORDER BY rowid"
            ).fetchall()
            if current_constraints == desired_constraints:
                cursor.executemany(
                    "UPDATE 设置 SET 类型=? WHERE 设置项=?",
                    [(get_setting_type(item), item) for item, _ in rows],
                )
                return
        elif column_names in (["设置类型", "值"], ["设置项", "值"]):
            item_column = column_names[0]
            rows = cursor.execute(
                f'SELECT "{item_column}", 值 FROM 设置 ORDER BY rowid'
            ).fetchall()
        else:
            raise RuntimeError(
                f"无法迁移未知的设置表结构：{', '.join(column_names)}"
            )

        cursor.execute('DROP TABLE IF EXISTS "设置_迁移"')
        cls._create_settings_table(cursor, "设置_迁移")
        cursor.executemany(
            "INSERT INTO 设置_迁移(类型, 设置项, 值) VALUES (?, ?, ?)",
            [
                (get_setting_type(str(item)), str(item), str(value))
                for item, value in rows
            ],
        )
        cursor.execute("DROP TABLE 设置")
        cursor.execute('ALTER TABLE "设置_迁移" RENAME TO "设置"')

    def _migrate_legacy_window_settings(self, cursor) -> None:
        resolution = self.get_screen_resolution()
        for setting_key in LEGACY_WINDOW_SETTING_KEYS:
            row = cursor.execute(
                "SELECT 值 FROM 设置 WHERE 设置项=?", (setting_key,)
            ).fetchone()
            if not row:
                continue
            state = self._parse_window_state(row[0])
            if state is not None:
                cursor.execute(
                    "INSERT OR IGNORE INTO 窗口大小(窗口, 大小) VALUES (?, ?)",
                    (
                        f"{setting_key}-{resolution}",
                        self._serialize_window_state(state),
                    ),
                )
            cursor.execute("DELETE FROM 设置 WHERE 设置项=?", (setting_key,))

    def _migrate_legacy_global_parameters(self, cursor) -> None:
        row = cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='全局参数'"
        ).fetchone()
        if not row:
            return
        resource_order = cursor.execute("SELECT COUNT(*) FROM 资源文件夹").fetchone()[0]
        for (resource_path,) in cursor.execute(
            "SELECT 资源文件夹路径 FROM 全局参数 ORDER BY rowid"
        ).fetchall():
            if resource_path:
                cursor.execute(
                    "INSERT OR IGNORE INTO 资源文件夹(路径, 排序) VALUES (?, ?)",
                    (self.portable_resource_path(resource_path), resource_order),
                )
                resource_order += 1
        cursor.execute("DROP TABLE 全局参数")

    @staticmethod
    def resolve_resource_path(path: str) -> str:
        if not path:
            return path
        return os.path.normpath(
            path if os.path.isabs(path) else os.path.join(DATA_FOLDER, path)
        )

    @staticmethod
    def portable_resource_path(path: str) -> str:
        normalized_path = os.path.normpath(path)
        try:
            if os.path.commonpath((DATA_FOLDER, normalized_path)) == os.path.normpath(DATA_FOLDER):
                return os.path.relpath(normalized_path, DATA_FOLDER)
        except ValueError:
            pass
        return normalized_path

    def get_setting_value(self, setting_item: str):
        """从设置表获取指定设置值。"""
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 值 FROM 设置 WHERE 设置项 = ?",
                (setting_item,),
            )
            result = cursor.fetchone()
        return result[0] if result else None

    def get_setting_values(self, setting_items: list[str]) -> dict:
        """批量从设置表获取设置值。"""
        if not setting_items:
            return {}
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 设置项, 值 FROM 设置 WHERE 设置项 IN ({})".format(
                    ",".join("?" * len(setting_items))
                ),
                setting_items,
            )
            result = dict(cursor.fetchall())
        return {setting_item: result.get(setting_item) for setting_item in setting_items}

    def set_setting_value(self, setting_item: str, value: str) -> None:
        """向设置表写入单个设置值。"""
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO 设置(类型, 设置项, 值) VALUES (?, ?, ?) "
                "ON CONFLICT(设置项) DO UPDATE SET "
                "类型=excluded.类型, 值=excluded.值",
                (get_setting_type(setting_item), setting_item, str(value)),
            )
            conn.commit()

    def set_setting_values(self, settings: dict[str, str]) -> None:
        """批量向设置表写入设置值。"""
        if not settings:
            return
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT INTO 设置(类型, 设置项, 值) VALUES (?, ?, ?) "
                "ON CONFLICT(设置项) DO UPDATE SET "
                "类型=excluded.类型, 值=excluded.值",
                [
                    (get_setting_type(item), item, str(value))
                    for item, value in settings.items()
                ],
            )
            conn.commit()

    def ensure_setting_values(self, settings: dict[str, str]) -> dict:
        """确保设置表中存在指定键，不存在时写入默认值。"""
        if not settings:
            return {}
        current_values = self.get_setting_values(list(settings.keys()))
        missing_settings = {
            key: value
            for key, value in settings.items()
            if current_values.get(key) is None
        }
        if missing_settings:
            self.set_setting_values(missing_settings)
            current_values.update(missing_settings)
        return current_values

    def get_bool_setting(self, setting_item: str, default: bool = False) -> bool:
        value = self.get_setting_value(setting_item)
        if value is None:
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def get_setting_data(self, *setting_items: str):
        if len(setting_items) == 1:
            return self.get_setting_value(setting_items[0])
        return self.get_setting_values(list(setting_items))

    def update_settings(self, **settings) -> None:
        self.set_setting_values({key: str(value) for key, value in settings.items()})

    def get_ocr_info(self) -> dict:
        return self.get_setting_values(["appId", "apiKey", "secretKey", "云码Token"])

    def get_global_shortcut(self) -> dict:
        actions = ("开始运行", "结束运行", "暂停和恢复")
        values = self.get_setting_values([f"快捷键-{action}" for action in actions])
        return {
            action: str(values.get(f"快捷键-{action}") or "").lower().split("+")
            for action in actions
        }

    def set_global_shortcut(self, **shortcuts) -> None:
        values = {}
        for action, shortcut in shortcuts.items():
            normalized = ["ctrl" if str(key).lower() == "control" else str(key) for key in shortcut]
            values[f"快捷键-{action}"] = "+".join(normalized).lower()
        self.set_setting_values(values)

    @staticmethod
    def get_screen_resolution() -> str:
        user32 = ctypes.windll.user32
        return f"{user32.GetSystemMetrics(0)}*{user32.GetSystemMetrics(1)}"

    @classmethod
    def _parse_size_value(cls, value):
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            return None
        try:
            width, height = int(value[0]), int(value[1])
        except (TypeError, ValueError):
            return None
        if width < cls.MIN_WINDOW_WIDTH or height < cls.MIN_WINDOW_HEIGHT:
            return None
        return width, height

    @classmethod
    def _parse_window_state(cls, value):
        parsed = value
        if isinstance(value, str):
            text_ = value.strip()
            try:
                parsed = json.loads(text_)
            except (json.JSONDecodeError, TypeError):
                size_match_ = cls._LEGACY_WINDOW_SIZE_PATTERN.fullmatch(text_)
                state_match_ = cls._LEGACY_WINDOW_STATE_PATTERN.fullmatch(text_)
                if size_match_:
                    parsed = [int(size_match_.group(1)), int(size_match_.group(2))]
                elif state_match_:
                    parsed = {
                        "size": [int(state_match_.group(1)), int(state_match_.group(2))],
                        "maximized": state_match_.group(3) == "True",
                    }
                else:
                    return None
        if isinstance(parsed, dict):
            size = cls._parse_size_value(parsed.get("size"))
            return None if size is None else {
                "size": size,
                "maximized": bool(parsed.get("maximized", False)),
            }
        size = cls._parse_size_value(parsed)
        return None if size is None else {"size": size, "maximized": False}

    @staticmethod
    def _serialize_window_state(state) -> str:
        return json.dumps(
            {
                "size": list(state["size"]),
                "maximized": bool(state.get("maximized", False)),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def get_window_state(self, window_name: str):
        if not window_name:
            return None
        window_info = f"{window_name}-{self.get_screen_resolution()}"
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            row = conn.execute(
                "SELECT 大小 FROM 窗口大小 WHERE 窗口 = ?", (window_info,)
            ).fetchone()
        return self._parse_window_state(row[0]) if row else None

    def save_window_size(
        self,
        win_width: int,
        win_height: int,
        window_name: str,
        maximized: bool = False,
    ) -> None:
        if not window_name:
            return
        save_size = self._parse_size_value((win_width, win_height))
        if save_size is None:
            existing = self.get_window_state(window_name)
            if existing is None:
                return
            save_size = existing["size"]
        payload = self._serialize_window_state(
            {"size": save_size, "maximized": bool(maximized)}
        )
        window_info = f"{window_name}-{self.get_screen_resolution()}"
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO 窗口大小(窗口, 大小) VALUES (?, ?) "
                "ON CONFLICT(窗口) DO UPDATE SET 大小=excluded.大小",
                (window_info, payload),
            )
            conn.commit()

    def writes_to_resource_folder_path(self, path: str) -> bool:
        path = self.portable_resource_path(path)
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            if conn.execute("SELECT 1 FROM 资源文件夹 WHERE 路径=?", (path,)).fetchone():
                return False
            order_ = conn.execute("SELECT COALESCE(MAX(排序), -1) + 1 FROM 资源文件夹").fetchone()[0]
            conn.execute("INSERT INTO 资源文件夹(路径, 排序) VALUES (?, ?)", (path, order_))
            conn.commit()
        return True

    def del_resource_folder_path(self, path: str) -> bool:
        path = self.portable_resource_path(path)
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.execute("DELETE FROM 资源文件夹 WHERE 路径=?", (path,))
            self._normalize_order(conn, "资源文件夹", "路径")
            conn.commit()
            return cursor.rowcount > 0

    def move_resource_folder_up_and_down(self, path: str, direction: str) -> bool:
        path = self.portable_resource_path(path)
        return self._move_ordered_row("资源文件夹", "路径", path, direction)

    def extract_resource_folder_path(self) -> list:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            rows = conn.execute("SELECT 路径 FROM 资源文件夹 ORDER BY 排序, rowid").fetchall()
        paths = [self.resolve_resource_path(row[0]) for row in rows]
        if IMAGES_FOLDER not in paths:
            paths.insert(0, IMAGES_FOLDER)
        return paths

    def get_all_png_images_from_resource_folders(self) -> list:
        return [
            file
            for path in self.extract_resource_folder_path()
            for _, _, files in os.walk(path)
            for file in files
            if file.lower().endswith(".png")
        ]

    def matched_complete_path_from_resource_folders(self, file_name: str) -> str:
        for path in self.extract_resource_folder_path():
            for root, _, files in os.walk(path):
                if file_name in files:
                    return os.path.normpath(os.path.join(root, file_name))
        return ""

    @staticmethod
    def _normalize_order(conn, table: str, key_column: str) -> None:
        rows = conn.execute(
            f'SELECT "{key_column}" FROM "{table}" ORDER BY 排序, rowid'
        ).fetchall()
        for order_, (key,) in enumerate(rows):
            conn.execute(
                f'UPDATE "{table}" SET 排序=? WHERE "{key_column}"=?', (order_, key)
            )

    def _move_ordered_row(
        self, table: str, key_column: str, key: str, direction: str
    ) -> bool:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            rows = conn.execute(
                f'SELECT "{key_column}" FROM "{table}" ORDER BY 排序, rowid'
            ).fetchall()
            keys = [row[0] for row in rows]
            if key not in keys:
                return False
            index = keys.index(key)
            target = index - 1 if direction == "up" else index + 1
            if target < 0 or target >= len(keys):
                return False
            keys[index], keys[target] = keys[target], keys[index]
            for order_, item in enumerate(keys):
                conn.execute(
                    f'UPDATE "{table}" SET 排序=? WHERE "{key_column}"=?',
                    (order_, item),
                )
            conn.commit()
        return True

    def export_settings_to_excel(self, workbook) -> None:
        if "设置" in workbook.sheetnames:
            del workbook["设置"]
        sheet = workbook.create_sheet("设置")
        sheet.append(["类型", "名称", "值", "附加值", "排序"])
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            for setting_type, name, value in conn.execute(
                "SELECT 类型, 设置项, 值 FROM 设置 ORDER BY 类型, 设置项"
            ):
                sheet.append(["设置", name, value, setting_type, None])
            for name, value in conn.execute("SELECT 窗口, 大小 FROM 窗口大小 ORDER BY 窗口"):
                sheet.append(["窗口大小", name, value, None, None])
            for path, order_ in conn.execute("SELECT 路径, 排序 FROM 资源文件夹 ORDER BY 排序"):
                sheet.append(["资源文件夹", path, None, None, order_])

    @classmethod
    def _read_settings_from_excel(cls, workbook):
        if "设置" not in workbook.sheetnames:
            return None
        sheet = workbook["设置"]
        if sheet.max_column != 5:
            return None
        headers = [sheet.cell(1, column).value for column in range(1, 6)]
        if headers != ["类型", "名称", "值", "附加值", "排序"]:
            return None
        grouped = {"设置": [], "窗口大小": [], "资源文件夹": []}
        seen_names = {category: set() for category in grouped}
        seen_resource_orders = set()
        seen_resource_paths = set()
        for row_index, row in enumerate(
            sheet.iter_rows(min_row=2, max_col=5, values_only=True), start=0
        ):
            category, name, value, extra, order_ = row
            if all(item is None for item in row):
                continue
            if category not in grouped or not isinstance(name, str) or not name.strip():
                return None
            name = name.strip()
            if name in seen_names[category]:
                return None
            seen_names[category].add(name)
            if category == "设置" and str(name) in REMOVED_SETTING_ITEMS:
                continue
            if category == "窗口大小" and cls._parse_window_state(value) is None:
                return None
            if category == "资源文件夹":
                name = cls.portable_resource_path(name)
                if name in seen_resource_paths:
                    return None
                seen_resource_paths.add(name)
                if order_ is None:
                    order_ = row_index
                if (
                    isinstance(order_, bool)
                    or not isinstance(order_, int)
                    or order_ < 0
                    or order_ in seen_resource_orders
                ):
                    return None
                seen_resource_orders.add(order_)
            grouped[category].append((str(name), value, extra, order_))
        return grouped

    def validate_settings_excel(self, workbook) -> bool:
        return self._read_settings_from_excel(workbook) is not None

    def import_settings_from_excel(self, workbook) -> bool:
        grouped = self._read_settings_from_excel(workbook)
        if grouped is None:
            return False
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            self._apply_parsed_settings(conn, grouped)
            conn.commit()
        self.ensure_setting_values(DEFAULT_SETTINGS)
        return True

    @classmethod
    def _apply_parsed_settings(cls, conn, grouped) -> None:
        """在调用方事务中应用已验证的设置工作表数据。"""
        for name, value, _, _ in grouped["设置"]:
            conn.execute(
                "INSERT INTO 设置(类型, 设置项, 值) VALUES (?, ?, ?) "
                "ON CONFLICT(设置项) DO UPDATE SET "
                "类型=excluded.类型, 值=excluded.值",
                (get_setting_type(name), name, "" if value is None else str(value)),
            )
        if grouped["窗口大小"]:
            conn.execute("DELETE FROM 窗口大小")
            conn.executemany(
                "INSERT INTO 窗口大小(窗口, 大小) VALUES (?, ?)",
                [
                    (name, cls._serialize_window_state(cls._parse_window_state(value)))
                    for name, value, _, _ in grouped["窗口大小"]
                ],
            )
        if grouped["资源文件夹"]:
            conn.execute("DELETE FROM 资源文件夹")
            ordered_resources = sorted(
                grouped["资源文件夹"],
                key=lambda row_: int(row_[3]),
            )
            conn.executemany(
                "INSERT INTO 资源文件夹(路径, 排序) VALUES (?, ?)",
                [
                    (cls.portable_resource_path(path), index)
                    for index, (path, _, _, _) in enumerate(ordered_resources)
                ],
            )

    def system_prompt_tone(self, judge: str) -> None:
        if not self.get_bool_setting("系统提示音"):
            return
        if judge == "线程结束":
            for _ in range(3):
                winsound.Beep(500, 300)
        elif judge == "全局快捷键":
            winsound.Beep(500, 300)
        elif judge == "执行异常":
            winsound.Beep(1000, 1000)

    def show_normal_window_with_specified_title(self, title: str) -> None:
        if not self.get_bool_setting("任务完成后显示主窗口"):
            return
        titles = {}
        win32gui.EnumWindows(lambda hwnd, result: result.update({hwnd: win32gui.GetWindowText(hwnd)}), titles)
        for hwnd, window_title in titles.items():
            if window_title == title:
                time.sleep(0.5)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
                break

    def extract_excel_from_resource_folders(self) -> list:
        """从所有资源文件夹路径中提取全部 Excel 文件
        :return: Excel文件列表"""
        resource_folder_path_list = self.extract_resource_folder_path()
        excel_files = []
        for folder_path in resource_folder_path_list:
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if (
                                file.endswith(".xlsx") or file.endswith(".xls")
                        ) and not file.startswith("~$"):
                            excel_files.append(os.path.normpath(os.path.join(root, file)))
        return excel_files

    def clear_all_ins(self):
        """清空数据库中的全部指令。"""
        self.get_graph_repository().clear()

    def extracted_ins_from_database(self) -> list:
        """按图顺序提取单一指令流。"""
        return self.get_graph_repository().list_commands()

    def extracted_ins_target_id_from_database(self, id_: int) -> list:
        """获取目标 ID 的指令。
        :param id_: 目标id"""
        command = self.get_graph_repository().get_command(id_)
        return [] if command is None else [command]

    def get_graph_repository(self) -> GraphRepository:
        """返回绑定当前数据库的节点图仓储。"""
        return GraphRepository(self.db_path)

    def export_instruction_workbook(self, workbook) -> None:
        self.get_graph_repository().export_to_workbook(workbook, self)

    def import_instruction_workbook(self, workbook) -> None:
        self.get_graph_repository().import_from_workbook(workbook)

    def writes_to_recently_opened_files(self, file_path: str):
        """将最近打开的文件写入数据库
        :param file_path: 文件路径"""

        def write_to_new_file(cursor_, file_path_, time_stamp_) -> None:
            # 查找数据库中是否存在该文件路径,如果存在则更新打开时间，如果不存在则插入数据
            cursor_.execute("SELECT * FROM 最近打开 WHERE 文件路径 = ?", (file_path_,))
            result = cursor_.fetchone()
            if result:
                cursor_.execute(
                    "UPDATE 最近打开 SET 打开时间=? WHERE 文件路径 = ?",
                    (time_stamp_, file_path_),
                )
            else:
                cursor_.execute(
                    "INSERT INTO 最近打开(文件路径, 打开时间) VALUES (?, ?)",
                    (file_path_, time_stamp_),
                )

        def delete_the_oldest_file(cursor_, con_, keep_number=10) -> None:
            """从数据库中删除最早的文件"""
            try:
                cursor_.execute("SELECT 文件路径 FROM 最近打开 ORDER BY 打开时间 ")
                result_ = cursor_.fetchall()

                if len(result_) > keep_number:
                    # 只保留最近打开的3个文件
                    files_to_keep = [item[0] for item in result_[-keep_number:]]
                    print(files_to_keep)
                    # 根据文件路径删除记录
                    cursor_.execute(
                        "DELETE FROM 最近打开"
                        " WHERE 文件路径 not IN ({})".format(
                            ",".join("?" * len(files_to_keep))
                        ),
                        files_to_keep,
                    )
                else:
                    print("数据库中没有足够的文件需要删除")
            except Exception as e_:
                print("An error occurred:", e_)
            finally:
                con_.commit()

        # 将时间转化为13位时间戳
        time_stamp = int(datetime.datetime.now().timestamp() * 1000)
        try:
            with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
                cursor = conn.cursor()
                write_to_new_file(cursor, file_path, time_stamp)
                delete_the_oldest_file(cursor, conn)  # 删除最早打开的文件
        except Exception as e:
            print("An error occurred:", e)

    def get_recently_opened_file(self, judge="单文件"):
        """获取最近打开的文件
        :param judge: 返回类型（单文件、文件列表）
        :return: 最近打开的文件"""
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 文件路径 FROM 最近打开 ORDER BY 打开时间 DESC")
            result = cursor.fetchall()
            if judge == "单文件":
                return os.path.normpath([item[0] for item in result][0])
            elif judge == "文件列表":
                return [item[0] for item in result]

    def remove_recently_opened_file(self, file_path: str):
        """从最近打开的文件中删除指定的文件
        :param file_path: 文件路径"""
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM 最近打开 WHERE 文件路径 = ?", (file_path,))
            conn.commit()

    def get_value_from_variable_table(self):
        """从变量池表中获取全部变量。"""
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM 变量池")
            result = cursor.fetchall()
        return result

    def set_value_to_variable_table(self, variable_list: list):
        """将指定变量写入变量池窗口的表格
        :param variable_list: 将要写入的变量列表（变量名称、备注、变量值）"""
        # 查询数据库中的现有值
        with contextlib.closing(sqlite3.connect(self.db_path)) as con:
            cursor = con.cursor()
            try:
                cursor.execute("SELECT * FROM 变量池")
                existing_values = cursor.fetchall()
                # 将现有值存储为字典，便于比较
                existing_values_dict = {row[0]: (row[1], row[2]) for row in existing_values}
                # 遍历传入的变量列表
                for variable_name, remark, value in variable_list:
                    # 如果变量名称在数据库中已存在且对应的备注值不等于传入值，则更新备注值
                    if variable_name in existing_values_dict:
                        cursor.execute(
                            "UPDATE 变量池 SET 备注 = ?, 值 = ? WHERE 变量名称 = ?",
                            (remark, value, variable_name),
                        )
                    # 如果变量名称不在数据库中，则插入新的记录
                    elif variable_name not in existing_values_dict:
                        cursor.execute(
                            "INSERT INTO 变量池(变量名称, 备注, 值) VALUES (?, ?, ?)",
                            (variable_name, remark, value),
                        )
                        cursor.execute(
                            "UPDATE 变量池 SET 值 = ? WHERE 变量名称 = ?",
                            (value, variable_name),
                        )
                # 检查变量池中是否有未在传入变量列表中的变量，如果有，则删除这些记录
                for variable_name in existing_values_dict:
                    if variable_name not in [v[0] for v in variable_list]:
                        cursor.execute(
                            "DELETE FROM 变量池 WHERE 变量名称 = ?", (variable_name,)
                        )
                con.commit()
            except sqlite3.IntegrityError:
                print("An error occurred: 数据库中已存在该变量名称")

    def get_variable_info(self, return_type: str):
        """从变量名中获取变量信息，可以选择返回类型为字典或列表
        :param return_type: 指定返回类型，'dict'表示返回字典，'list'表示返回列表"""
        # cursor, conn = sqlitedb()
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            try:
                if return_type == "dict":
                    cursor.execute(f"SELECT 变量名称, 值 FROM 变量池")
                    result = {
                        item[0]: item[1] for item in cursor.fetchall()
                    }  # 获取变量名称和值的字典
                elif return_type == "list":
                    cursor.execute(f"SELECT 变量名称 FROM 变量池")
                    result = [item[0] for item in cursor.fetchall()]  # 获取变量名称的列表
                else:
                    raise ValueError("Invalid return_type. Use 'dict' or 'list'.")
            except Exception as e:
                print(f"An error occurred: {e}")
                result = None
            return result

    def set_variable_value(self, variable_name, new_value) -> None:
        """设置变量池中的变量的值
        :param variable_name: 变量名称
        :param new_value: 新的值"""
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE 变量池 SET 值 = ? WHERE 变量名称 = ?", (new_value, variable_name)
                )
                conn.commit()
            except Exception as e:
                print(f"An error occurred: {e}")


if __name__ == "__main__":
    pass

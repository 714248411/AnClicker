"""SettingsRepository operations."""
from __future__ import annotations
import contextlib
import json
import re
import sqlite3
from anclicker.storage.base import Repository
from anclicker.storage.settings_defaults import *

from anclicker.storage.resources import ResourceCatalog

class SettingsRepository(Repository):
    def __init__(self, db_path, screen_resolution=lambda: '1920*1080'):
        super().__init__(db_path)
        self.screen_resolution = screen_resolution

    portable_resource_path = staticmethod(ResourceCatalog.portable_resource_path)
    MIN_WINDOW_WIDTH = 120

    MIN_WINDOW_HEIGHT = 80

    _LEGACY_WINDOW_SIZE_PATTERN = re.compile(
        r"^[\(\[]\s*(-?\d+)\s*,\s*(-?\d+)\s*[\)\]]$"
    )

    _LEGACY_WINDOW_STATE_PATTERN = re.compile(
        r'''^\{\s*["']size["']\s*:\s*[\(\[]\s*(-?\d+)\s*,\s*(-?\d+)'''
        r'''\s*[\)\]]\s*,\s*["']maximized["']\s*:\s*(True|False)\s*\}$'''
    )

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


    def get_screen_resolution(self):
        return self.screen_resolution()


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

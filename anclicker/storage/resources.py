"""ResourceCatalog operations."""
from __future__ import annotations
import contextlib
import os
import sqlite3
from anclicker.app.paths import DATA_FOLDER, IMAGES_FOLDER
from anclicker.storage.base import Repository
from anclicker.storage.settings_defaults import *


class ResourceCatalog(Repository):
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

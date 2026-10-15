"""DatabaseMigrator operations."""
from __future__ import annotations
import contextlib
import datetime
import json
import os
import re
import sqlite3
import time
from anclicker.app.paths import DATA_FOLDER, DATABASE_PATH, IMAGES_FOLDER
from anclicker.storage.base import Repository
from anclicker.storage.settings_defaults import *

from anclicker.storage.resources import ResourceCatalog
from anclicker.storage.graph_repository import GraphRepository
from anclicker.storage.settings import SettingsRepository

class DatabaseMigrator(Repository):
    def __init__(self, db_path, screen_resolution=lambda: '1920*1080'):
        super().__init__(db_path)
        self.screen_resolution = screen_resolution

    portable_resource_path = staticmethod(ResourceCatalog.portable_resource_path)
    _parse_window_state = SettingsRepository._parse_window_state
    _serialize_window_state = staticmethod(SettingsRepository._serialize_window_state)

    def get_screen_resolution(self):
        return self.screen_resolution()

    def create_all_tables(self) -> None:
        """创建配置相关表，并迁移旧版数据库中的全局参数。"""
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            cursor = conn.cursor()
            self._migrate_settings_table(cursor)
            toolbar_layout_version = cursor.execute(
                "SELECT 值 FROM 设置 WHERE 设置项='工具栏紧凑布局版本'"
            ).fetchone()
            if toolbar_layout_version is None:
                # Older releases seeded this preference as hidden.  Migrate
                # once to the new visible-by-default compact toolbar while
                # preserving any choice the user makes afterwards.
                cursor.execute(
                    "INSERT INTO 设置(类型, 设置项, 值) VALUES (?, '显示工具栏', 'True') "
                    "ON CONFLICT(设置项) DO UPDATE SET 值='True'",
                    (get_setting_type("显示工具栏"),),
                )
                cursor.execute(
                    "INSERT INTO 设置(类型, 设置项, 值) VALUES (?, '工具栏紧凑布局版本', '2')",
                    (get_setting_type("工具栏紧凑布局版本"),),
                )
            light_theme_version = cursor.execute(
                "SELECT 值 FROM 设置 WHERE 设置项='浅色默认主题版本'"
            ).fetchone()
            if light_theme_version is None:
                # Apply the new light default once to existing installations;
                # later theme choices are preserved by the migration marker.
                cursor.execute(
                    "INSERT INTO 设置(类型, 设置项, 值) VALUES (?, '界面主题', 'light') "
                    "ON CONFLICT(设置项) DO UPDATE SET 值='light'",
                    (get_setting_type("界面主题"),),
                )
                cursor.execute(
                    "INSERT INTO 设置(类型, 设置项, 值) VALUES (?, '浅色默认主题版本', '1')",
                    (get_setting_type("浅色默认主题版本"),),
                )
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
            columns = {row[1] for row in cursor.execute('PRAGMA table_info(变量池)')}
            if '作用域' not in columns:
                cursor.execute("ALTER TABLE 变量池 ADD COLUMN 作用域 TEXT NOT NULL DEFAULT '全局变量'")
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

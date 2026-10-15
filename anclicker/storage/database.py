"""Compatibility facade composing focused storage repositories."""
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

from anclicker.storage.graph_repository import COMMAND_COLUMNS, GraphRepository
from anclicker.platform.services import get_screen_resolution
from anclicker.platform.configured_services import ConfiguredSystemServices
from anclicker.storage.resources import ResourceCatalog
from anclicker.storage.recent_projects import RecentProjectsRepository
from anclicker.storage.variables import VariableRepository
from anclicker.storage.settings import SettingsRepository
from anclicker.storage.migrations import DatabaseMigrator

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
        # Editors can initialize storage before the main startup bootstrap.
        # A clean checkout/installation must not depend on a bundled live DB.
        if db_path and os.fspath(db_path) != ':memory:':
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.resources = ResourceCatalog(db_path)
        self.recent_projects = RecentProjectsRepository(db_path)
        self.variables = VariableRepository(db_path)
        self.settings = SettingsRepository(db_path)
        self.migrations = DatabaseMigrator(db_path)
        self.settings.screen_resolution = lambda: self.get_screen_resolution()
        self.migrations.screen_resolution = lambda: self.get_screen_resolution()
        self.system_services = ConfiguredSystemServices(self)
        self.create_all_tables()
        self.ensure_setting_values(DEFAULT_SETTINGS)

    def create_all_tables(self) -> None:
        return self.migrations.create_all_tables()

    _create_settings_table = staticmethod(DatabaseMigrator._create_settings_table)

    _migrate_settings_table = DatabaseMigrator._migrate_settings_table

    def _migrate_legacy_window_settings(self, cursor) -> None:
        return self.migrations._migrate_legacy_window_settings(cursor)

    def _migrate_legacy_global_parameters(self, cursor) -> None:
        return self.migrations._migrate_legacy_global_parameters(cursor)

    resolve_resource_path = staticmethod(ResourceCatalog.resolve_resource_path)

    portable_resource_path = staticmethod(ResourceCatalog.portable_resource_path)

    def get_setting_value(self, setting_item: str):
        return self.settings.get_setting_value(setting_item)

    def get_setting_values(self, setting_items: list[str]) -> dict:
        return self.settings.get_setting_values(setting_items)

    def set_setting_value(self, setting_item: str, value: str) -> None:
        return self.settings.set_setting_value(setting_item, value)

    def set_setting_values(self, settings: dict[str, str]) -> None:
        return self.settings.set_setting_values(settings)

    def ensure_setting_values(self, settings: dict[str, str]) -> dict:
        return self.settings.ensure_setting_values(settings)

    def get_bool_setting(self, setting_item: str, default: bool=False) -> bool:
        return self.settings.get_bool_setting(setting_item, default)

    def get_setting_data(self, *setting_items: str):
        return self.settings.get_setting_data(*setting_items)

    def update_settings(self, **settings) -> None:
        return self.settings.update_settings(**settings)

    def get_ocr_info(self) -> dict:
        return self.settings.get_ocr_info()

    def get_global_shortcut(self) -> dict:
        return self.settings.get_global_shortcut()

    def set_global_shortcut(self, **shortcuts) -> None:
        return self.settings.set_global_shortcut(**shortcuts)

    get_screen_resolution = staticmethod(get_screen_resolution)

    _parse_size_value = SettingsRepository._parse_size_value

    _parse_window_state = SettingsRepository._parse_window_state

    _serialize_window_state = staticmethod(SettingsRepository._serialize_window_state)

    def get_window_state(self, window_name: str):
        return self.settings.get_window_state(window_name)

    def save_window_size(self, win_width: int, win_height: int, window_name: str, maximized: bool=False) -> None:
        return self.settings.save_window_size(win_width, win_height, window_name, maximized)

    def writes_to_resource_folder_path(self, path: str) -> bool:
        return self.resources.writes_to_resource_folder_path(path)

    def del_resource_folder_path(self, path: str) -> bool:
        return self.resources.del_resource_folder_path(path)

    def move_resource_folder_up_and_down(self, path: str, direction: str) -> bool:
        return self.resources.move_resource_folder_up_and_down(path, direction)

    def extract_resource_folder_path(self) -> list:
        return self.resources.extract_resource_folder_path()

    def get_all_png_images_from_resource_folders(self) -> list:
        return self.resources.get_all_png_images_from_resource_folders()

    def matched_complete_path_from_resource_folders(self, file_name: str) -> str:
        return self.resources.matched_complete_path_from_resource_folders(file_name)

    _normalize_order = staticmethod(ResourceCatalog._normalize_order)

    def _move_ordered_row(self, table: str, key_column: str, key: str, direction: str) -> bool:
        return self.resources._move_ordered_row(table, key_column, key, direction)

    def export_settings_to_excel(self, workbook) -> None:
        return self.settings.export_settings_to_excel(workbook)

    _read_settings_from_excel = SettingsRepository._read_settings_from_excel

    def validate_settings_excel(self, workbook) -> bool:
        return self.settings.validate_settings_excel(workbook)

    def import_settings_from_excel(self, workbook) -> bool:
        return self.settings.import_settings_from_excel(workbook)

    _apply_parsed_settings = SettingsRepository._apply_parsed_settings

    def system_prompt_tone(self, judge: str) -> None:
        return self.system_services.system_prompt_tone(judge)


    def show_normal_window_with_specified_title(self, title: str) -> None:
        return self.system_services.show_normal_window_with_specified_title(title)


    def extract_excel_from_resource_folders(self) -> list:
        return self.resources.extract_excel_from_resource_folders()

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
        return self.recent_projects.writes_to_recently_opened_files(file_path)

    def get_recently_opened_file(self, judge='单文件'):
        return self.recent_projects.get_recently_opened_file(judge)

    def remove_recently_opened_file(self, file_path: str):
        return self.recent_projects.remove_recently_opened_file(file_path)

    def get_value_from_variable_table(self):
        return self.variables.get_value_from_variable_table()

    def set_value_to_variable_table(self, variable_list: list):
        return self.variables.set_value_to_variable_table(variable_list)

    def get_variable_definitions(self):
        return self.variables.get_variable_definitions()

    def save_variable_definitions(self, rows):
        return self.variables.save_variable_definitions(rows)

    def persist_global_variables(self, values):
        return self.variables.persist_global_variables(values)

    def get_variable_info(self, return_type: str):
        return self.variables.get_variable_info(return_type)

    def set_variable_value(self, variable_name, new_value) -> None:
        return self.variables.set_variable_value(variable_name, new_value)

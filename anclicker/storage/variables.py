"""VariableRepository operations."""
from __future__ import annotations
import contextlib
import sqlite3
from anclicker.storage.base import Repository
from anclicker.storage.settings_defaults import *


class VariableRepository(Repository):
    def get_value_from_variable_table(self):
        """从变量池表中获取全部变量。"""
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 变量名称, 备注, 值 FROM 变量池")
            result = cursor.fetchall()
        return result


    def set_value_to_variable_table(self, variable_list: list):
        """将指定变量写入变量池窗口的表格
        :param variable_list: 将要写入的变量列表（变量名称、备注、变量值）"""
        # 查询数据库中的现有值
        with contextlib.closing(sqlite3.connect(self.db_path)) as con:
            cursor = con.cursor()
            try:
                cursor.execute("SELECT 变量名称, 备注, 值 FROM 变量池")
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


    def get_variable_definitions(self):
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            return conn.execute('SELECT 变量名称, 备注, 值, 作用域 FROM 变量池 ORDER BY rowid').fetchall()


    def save_variable_definitions(self, rows):
        normalized = []
        names = set()
        for name, remark, value, scope in rows:
            name = str(name or '').strip()
            if not name:
                raise ValueError('变量名称不能为空')
            if name in names:
                raise ValueError(f'变量名称重复：{name}')
            if scope not in ('全局变量', '普通变量'):
                raise ValueError('请选择全局变量或普通变量')
            names.add(name)
            normalized.append((name, str(remark or ''), str(value if value is not None else ''), scope))
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                conn.execute('DELETE FROM 变量池')
                conn.executemany('INSERT INTO 变量池(变量名称,备注,值,作用域) VALUES (?,?,?,?)', normalized)


    def persist_global_variables(self, values):
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                conn.executemany("UPDATE 变量池 SET 值=? WHERE 变量名称=? AND 作用域='全局变量'",
                                 [(str(value), str(name)) for name, value in values.items()])


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

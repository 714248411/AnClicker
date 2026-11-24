"""RecentProjectsRepository operations."""
from __future__ import annotations
import contextlib
import datetime
import os
import sqlite3
from anclicker.storage.base import Repository
from anclicker.storage.settings_defaults import *


class RecentProjectsRepository(Repository):
    def writes_to_recently_opened_files(self, file_path: str):
        self.add_recent_files([file_path])

    def add_recent_files(self, file_paths):
        """Add a batch atomically; imported partitions retain every project."""
        unique = {}
        for path in file_paths:
            path = os.path.normpath(os.path.abspath(os.fspath(path)))
            unique.setdefault(os.path.normcase(path), path)
        if not unique:
            return 0
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                cursor = conn.cursor()
                existing = cursor.execute('SELECT 文件路径 FROM 最近打开').fetchall()
                matches = {}
                for (path,) in existing:
                    key = os.path.normcase(os.path.abspath(path))
                    if key in unique:
                        matches.setdefault(key, []).append(path)
                # Keep the filename-sorted batch ahead of older entries even
                # when two imports happen in the same millisecond.
                newest = cursor.execute('SELECT MAX(打开时间) FROM 最近打开').fetchone()[0] or 0
                stamp = max(int(datetime.datetime.now().timestamp()*1000), int(newest)+1)
                count = len(unique)
                for index, (key, path) in enumerate(unique.items()):
                    cursor.executemany('DELETE FROM 最近打开 WHERE 文件路径 = ?',
                                       [(old,) for old in matches.get(key, [])])
                    cursor.execute('INSERT INTO 最近打开(文件路径, 打开时间) VALUES (?, ?)',
                                   (path, stamp + count - index))
                keep_all = cursor.execute('SELECT 值 FROM 设置 WHERE 设置项=?',
                                          ('项目最近文件全部保留',)).fetchone()
                if not keep_all or str(keep_all[0]).lower() != 'true':
                    cursor.execute(
                        "DELETE FROM 最近打开 WHERE rowid NOT IN "
                        "(SELECT rowid FROM 最近打开 ORDER BY 打开时间 DESC, rowid DESC LIMIT 20)")
        return len(unique)


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

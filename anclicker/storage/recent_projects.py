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

import sqlite3
from 数据库操作 import DatabaseOperation

def test_creates_missing_database_directory_and_keeps_existing_data(tmp_path):
    path=tmp_path/'clean'/'data'/'commands.db'
    assert not path.parent.exists()
    db=DatabaseOperation(str(path))
    db.set_setting_value('运行未连接模块','False')
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE keep_user_data (value TEXT)')
        conn.execute("INSERT INTO keep_user_data VALUES ('preserved')")
    again=DatabaseOperation(str(path))
    assert again.get_setting_value('运行未连接模块')=='False'
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT value FROM keep_user_data').fetchone()==('preserved',)

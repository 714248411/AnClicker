"""SQLite repository sharing a caller-selected database path."""
class Repository:
    def __init__(self, db_path):
        self.db_path = db_path

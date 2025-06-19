import sqlite3

class Database:
    def __init__(self, db_file):
        self.conncetion = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        
    def add_user(self, user_id):
        with self.connection:
           self.cursor.execut("INSERT INTO 'users" ('iser_id')) 
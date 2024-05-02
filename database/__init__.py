import sqlite3

def dict_factory(cursor, row):
    d = {}
    for i, col in enumerate(cursor.description):
        d[col[0]] = row[i]
    return d

class Connection:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = dict_factory

        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.commit()
        self.conn.close()

    def lastrowid(self):
        return self.cursor.lastrowid

    def execute(self, string=None, args=None):
        if string:
            if args:
                self.cursor.execute(string, args)
            else:
                self.cursor.execute(string)

        return self

    def one(self):
        data = self.cursor.fetchone()
        self.close()
        return data

    def all(self):
        data = self.cursor.fetchall()
        self.close()
        return data

    def executescript(self, string):
        data = self.cursor.executescript(string)
        self.close()
        return data

class Database:
    def __init__(self, path):
        self.path = path

    def __call__(self, string=None, args=None):
        return Connection(self.path).execute(string, args)

    def execute_file(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            self().executescript(file.read())


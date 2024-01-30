from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

# Class including all the actions' functionality
class Actions:
    def __init__(self,):
        self.host = os.getenv('HOST')
        self.dbname = os.getenv('DATABASE')
        self.user = os.getenv('USERNAME')
        self.password = os.getenv('PASSWORD')
        self.port = os.getenv("PORT")
        self.conn = None

    # To connect the database
    def connect(self):
        if self.conn is None:
            self.conn = psycopg2.connect(
                host=self.host,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                port=self.port
            )
            print('Database connected successfully!')


    def get_all_users_info(self):
        self.connect()
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM "User";')
        rows = cur.fetchall()
        for row in rows:
            return row
        

    def get_user_preference(self, user_id):
        self.connect()
        cur = self.conn.cursor()
        cur.execute('SELECT paper_category, paper_interest FROM "User"\
                     WHERE id = %s;', (user_id,))
        print(f'Fetching Interest & Category for {user_id}')
        rows = cur.fetchone()
        return rows




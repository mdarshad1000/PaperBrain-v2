# database.py
import logging
from psycopg2 import pool
from psycopg2.extras import DictCursor

# Create a logger object
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Action:
    def __init__(self, host, dbname, user, password, port):
        self.conn_pool = pool.SimpleConnectionPool(1, 20,
            host=host,
            dbname=dbname,
            user=user,
            password=password,
            port=port
        )
        logger.info("Initialized connection pool")

    def execute_query(self, query, params=None):
        conn = self.conn_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
            logger.info("Executed query: %s", query)
        finally:
            self.conn_pool.putconn(conn)

    def execute_and_fetch(self, query, params=None):
        conn = self.conn_pool.getconn()
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(query, params)
                result = cur.fetchall()
                logger.info("Executed and fetched results for query: %s", query)
                return [dict(row) for row in result]
        finally:
            self.conn_pool.putconn(conn)

    def update_podcast_status(self, paper_id, status):
        query = 'UPDATE "Podcast" SET status = %s WHERE paper_id = %s'
        self.execute_query(query, (status, paper_id))

    def update_podcast_information(self, paper_id, title, authors, abstract, transcript, s3_url):
        query = 'UPDATE "Podcast" SET title = %s, authors = %s, abstract = %s, transcript = %s, s3_url = %s WHERE paper_id = %s'
        self.execute_query(query, (title, authors, abstract, transcript, s3_url, paper_id))

    def add_new_podcast(self, paper_id, status):
        query = f'INSERT INTO "Podcast" (paper_id, status) VALUES (%s, %s)'
        self.execute_query(query, (paper_id, status))

    def get_podcast_info(self, paper_id):
        query = 'SELECT * FROM "Podcast" WHERE paper_id = %s'
        result = self.execute_and_fetch(query, (paper_id, ))
        return result[0]

    def check_pending_status(self, paper_id):
        query = 'SELECT * FROM "Podcast" WHERE paper_id = %s'
        result = self.execute_and_fetch(query, (paper_id,))
        return result

    def check_podcast_exists(self, paper_id):
        query = 'SELECT * FROM "Podcast" WHERE paper_id = %s AND status = %s'
        result = self.execute_and_fetch(query, (paper_id, "SUCCESS"))
        return len(result) > 0

    def get_all_users_info(self):
        query = 'SELECT * FROM "User";'
        return self.execute_and_fetch(query)

    def get_user_preference(self, user_id):
        query = 'SELECT paper_category, paper_interest FROM "User" WHERE id = %s;'
        return self.execute_and_fetch(query, (user_id,))
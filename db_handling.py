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

    def update_podcast_information(self, paper_id, title, authors, abstract, transcript, keyinsights, s3_url, status):
        query = 'UPDATE "Podcast" SET title = %s, authors = %s, abstract = %s, transcript = %s, keyinsights = %s, s3_url = %s, status = %s WHERE paper_id = %s'
        self.execute_query(query, (title, authors, abstract, transcript, keyinsights, s3_url, status, paper_id))

    def add_new_podcast(self, paper_id, status):
        query = 'INSERT INTO "Podcast" (paper_id, status) VALUES (%s, %s)'
        self.execute_query(query, (paper_id, status))

    def check_user_podcast_relation(self, userId, podcast_id):
        query = 'SELECT * FROM "UserPodcast" WHERE "userId" = %s AND "podcastId" = %s'
        result = self.execute_and_fetch(query, (userId, podcast_id))
        return len(result) > 0
    
    def update_user_podcast(self, i_d, userId, podcastId):
        query = 'INSERT INTO "UserPodcast" (id, "userId", "podcastId") VALUES (%s, %s, %s)'
        self.execute_query(query, (i_d, userId, podcastId))

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

    def delete_podcast(self, paper_id):
        query = 'DELETE FROM "Podcast" WHERE paper_id = %s'
        self.execute_query(query, (paper_id,))

    def get_all_users_info(self):
        query = 'SELECT * FROM "User";'
        return self.execute_and_fetch(query)

    def get_user_preference(self, user_id):
        query = 'SELECT paper_category, paper_interest FROM "User" WHERE id = %s;'
        return self.execute_and_fetch(query, (user_id,))    
    
    def get_all_podcasts(self):
        query = 'SELECT title, paper_id, abstract, s3_url, authors FROM "Podcast";'
        results = self.execute_and_fetch(query)
        podcasts = []
        for result in results:
            podcast = {
                "title": result['title'],
                "id": "https://arxiv.org/pdf/" + result['paper_id'] + ".pdf",
                "summary": result['abstract'],
                "url": result['s3_url'],
                "authors": result['authors'],
                "image": "https://picsum.photos/200/300",  # static image URL
            }
            podcasts.append(podcast)
        return podcasts



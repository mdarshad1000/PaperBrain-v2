# database handling
import os
import time
import logging
import random
import psycopg2
from psycopg2 import pool
from psycopg2.extras import DictCursor
from psycopg2 import errorcodes

def with_retry(func):
    def wrapper(*args, **kwargs):
        max_attempts = 5
        retryable_errors = {
            errorcodes.ADMIN_SHUTDOWN,
            errorcodes.CONNECTION_EXCEPTION,
            errorcodes.CONNECTION_DOES_NOT_EXIST,
            errorcodes.CONNECTION_FAILURE,
            errorcodes.SQLCLIENT_UNABLE_TO_ESTABLISH_SQLCONNECTION,
            errorcodes.SQLSERVER_REJECTED_ESTABLISHMENT_OF_SQLCONNECTION,
            errorcodes.TRANSACTION_RESOLUTION_UNKNOWN,
            errorcodes.LOCK_NOT_AVAILABLE,
        }
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except psycopg2.DatabaseError as e:
                if e.pgcode in retryable_errors and attempt < max_attempts - 1:
                    time.sleep((2 ** attempt) + random.random())
                else:
                    raise
    return wrapper

# Create a logger object
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Action:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Action, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'conn_pool'):
            self.conn_pool = pool.ThreadedConnectionPool(1, 20,
                host=os.getenv('HOST'),
                dbname=os.getenv('DATABASE'),
                user=os.getenv('USERNAME'),
                password=os.getenv('PASSWORD'),
                port=os.getenv('PORT')
            )
            logger.info("Initialized connection pool")

    def get_connection(self):
        conn = self.conn_pool.getconn()
        conn.poll()
        if conn.closed:
            self.conn_pool.putconn(conn, close=True)
            conn = self.conn_pool.getconn()
        return conn
    
    @with_retry
    def execute_query(self, query, params=None):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
            logger.info("Executed query: %s", query)
        finally:
            self.conn_pool.putconn(conn)

    @with_retry
    def execute_and_fetch(self, query, params=None):
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(query, params)
                result = cur.fetchall()
                logger.info("Executed and fetched results for query: %s", query)
                return [dict(row) for row in result]
        finally:
            self.conn_pool.putconn(conn)

    def update_podcast_information(self, paper_id, title, authors, abstract, transcript, keyinsights, s3_url, status, thumbnail):
        query = 'UPDATE "Podcast" SET title = %s, authors = %s, abstract = %s, transcript = %s, keyinsights = %s, s3_url = %s, status = %s, thumbnail = %s WHERE paper_id = %s'
        self.execute_query(query, (title, authors, abstract, transcript, keyinsights, s3_url, status, thumbnail, paper_id))

    def add_new_podcast(self, paper_id, status):
        query = f'INSERT INTO "Podcast" (paper_id, status) VALUES (%s, %s)'
        self.execute_query(query, (paper_id, status))

    def check_user_podcast_relation(self, userId, podcast_id):
        query = 'SELECT * FROM "UserPodcast" WHERE "userId" = %s AND "podcastId" = %s'
        result = self.execute_and_fetch(query, (userId, podcast_id))
        return len(result) > 0
    
    def update_user_podcast(self, userId, podcastId):
        query = 'INSERT INTO "UserPodcast" ("userId", "podcastId") VALUES (%s, %s)'
        self.execute_query(query, (userId, podcastId))

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
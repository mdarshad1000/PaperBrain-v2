from redis import Redis
from rq import Queue
import os
from dotenv import load_dotenv

load_dotenv()

redis_conn = Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    password=os.getenv('REDIS_PASSWORD')  # Uncommented for security
)

job_queue = Queue(connection=redis_conn)
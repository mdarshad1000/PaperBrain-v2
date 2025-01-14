from redis import Redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_client = Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    # password=os.getenv('REDIS_PASSWORD')  # Uncommented for security
)
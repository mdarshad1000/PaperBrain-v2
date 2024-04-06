from redis import Redis
from rq import Worker
import os
from dotenv import load_dotenv

load_dotenv()

r = Redis(
  host=os.getenv('REDIS_HOST'),
  port=os.getenv('REDIS_PORT'),
  password=os.getenv('REDIS_PASSWORD')
)
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

w = Worker(['default'], connection=r)
w.work()

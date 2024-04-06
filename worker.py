from redis import Redis
from rq import Worker
import os
from dotenv import load_dotenv

os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

load_dotenv()

r = Redis(
  host=os.getenv('REDIS_HOST'),
  port=os.getenv('REDIS_PORT'),
  password=os.getenv('REDIS_PASSWORD')
)

w = Worker(['default'], connection=r)
w.work()

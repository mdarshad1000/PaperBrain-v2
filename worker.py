from redis import Redis
from rq import Worker
import os

os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

w = Worker(['default'], connection=Redis())
w.work()

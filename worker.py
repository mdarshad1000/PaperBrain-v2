from redis import Redis
from rq import Worker
import os
import psutil
from dotenv import load_dotenv
import time
import threading
from app.service.redis_service import redis_conn

load_dotenv()

os.getenv('OBJC_DISABLE_INITIALIZE_FORK_SAFETY')


def log_memory_usage(interval=1, duration=None):
    start_time = time.time()
    while True:
        memory_info = psutil.virtual_memory()
        print(f"Memory Usage: {memory_info.percent}%")
        current_time = time.time()
        elapsed_time = current_time - start_time
        if duration and elapsed_time >= duration:
            break
        time.sleep(interval)

# Function to start worker and log memory usage


def start_worker_with_logging():
    r = redis_conn
    # Start logging memory usage in a separate thread
    memory_logging_thread = threading.Thread(
        target=log_memory_usage, args=(1,))
    memory_logging_thread.start()

    # Start RQ worker
    w = Worker(['default'], connection=r)
    w.work()


if __name__ == "__main__":
    start_worker_with_logging()




















                                                                                                                   
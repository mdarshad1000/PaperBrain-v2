from redis import Redis
from rq import Worker
import os
import psutil
from dotenv import load_dotenv
import time
import threading

os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

load_dotenv()

def log_cpu_usage(interval=1, duration=None):
    start_time = time.time()
    while True:
        cpu_percent = psutil.cpu_percent(interval=interval)
        current_time = time.time()
        elapsed_time = current_time - start_time
        print(f"CPU Usage: {cpu_percent}%")
        if duration and elapsed_time >= duration:
            break
        time.sleep(interval)

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

def log_disk_usage(interval=1, duration=None):
    start_time = time.time()
    while True:
        disk_usage = psutil.disk_usage('/')
        print(f"Disk Usage: {disk_usage.percent}%")
        current_time = time.time()
        elapsed_time = current_time - start_time
        if duration and elapsed_time >= duration:
            break
        time.sleep(interval)

# Function to start worker and log CPU, memory, and disk usage
def start_worker_with_logging():
    r = Redis(
      host=os.getenv('REDIS_HOST'),
      port=os.getenv('REDIS_PORT'),
    #   password=os.getenv('REDIS_PASSWORD')
    )

    # Start logging CPU usage in a separate thread
    cpu_logging_thread = threading.Thread(target=log_cpu_usage, args=(1,))
    # cpu_logging_thread.start()

    # Start logging memory usage in a separate thread
    memory_logging_thread = threading.Thread(target=log_memory_usage, args=(1,))
    memory_logging_thread.start()

    # Start logging disk usage in a separate thread
    disk_logging_thread = threading.Thread(target=log_disk_usage, args=(1,))
    # disk_logging_thread.start()

    # Start RQ worker
    w = Worker(['default'], connection=r)
    w.work()

if __name__ == "__main__":
    start_worker_with_logging()



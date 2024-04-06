web: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2 --limit-concurrency 1000 --ws-ping-timeout 120
worker: python3 worker.py

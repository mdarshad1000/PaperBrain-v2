web: uvicorn app:app --host 0.0.0.0 --port $PORT --workers 2 --limit-concurrency 1000 --ws-ping-timeout 360
worker: python worker.py

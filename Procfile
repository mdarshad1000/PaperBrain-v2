web: ./wait-for-it.sh db_host:db_port --timeout=60 && uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2 --limit-concurrency 1000
worker: python3 worker.py

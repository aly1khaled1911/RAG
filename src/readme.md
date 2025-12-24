for alembic : 
run first

- cd /src/model/db_schemas/mini_rag
- alembic revision --autogenerate -m "init"
- alembic upgrade head

for running the server on specific {port} run :
- python3 -m uvicorn main:app --host 0.0.0.0 --port {port}

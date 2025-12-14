for alembic : 
run first

- cd /src/models/db_schemas/mini_rag
- alembic revision --autogenerate -m "init"
- alembic upgrade head
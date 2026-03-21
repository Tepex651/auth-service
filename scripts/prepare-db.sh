uv run python - <<'PY'
import os, sqlalchemy

host = os.environ["DB_HOST"]
port = os.environ["DB_PORT"]
user = os.environ["DB_USER"]
password = os.environ["DB_PASSWORD"]
db_name = os.environ["DB_NAME"]

base_url = f"postgresql://{user}:{password}@{host}:{port}/postgres"

engine = sqlalchemy.create_engine(base_url, isolation_level="AUTOCOMMIT")

with engine.connect() as conn:
    exists = conn.execute(
        sqlalchemy.text("SELECT 1 FROM pg_database WHERE datname = :name"),
        {"name": db_name}
    ).scalar()

    if not exists:
        conn.execute(sqlalchemy.text(f'CREATE DATABASE "{db_name}"'))
        print(f">>> Database '{db_name}' created")
    else:
        print(f">>> Database '{db_name}' already exists, skipping")

engine.dispose()
PY

uv run alembic upgrade head

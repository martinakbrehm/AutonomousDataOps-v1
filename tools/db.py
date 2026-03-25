import duckdb
from sqlalchemy import create_engine, text


def query_sqlite(db_path: str, sql: str):
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(text(sql))]


def query_duckdb(sql: str, connection: duckdb.DuckDBPyConnection = None):
    con = connection or duckdb.connect(database=':memory:')
    return con.execute(sql).fetchall()

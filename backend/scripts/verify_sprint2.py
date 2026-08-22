"""Manual Sprint 2 verification: init_db + inspect sqlite_master."""

import os
import sys

from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.connection import get_engine, init_db

db_path = os.path.join(os.path.dirname(__file__), "manual_check.db")
if os.path.exists(db_path):
    os.remove(db_path)

os.environ["CAREER_OS_DB_PATH"] = db_path
engine = get_engine()
init_db(engine)

with engine.connect() as conn:
    tables = sorted(r[0] for r in conn.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )))
    triggers = sorted(r[0] for r in conn.execute(text(
        "SELECT name FROM sqlite_master WHERE type='trigger'"
    )))

print(f"TABLES ({len(tables)}):")
for t in tables:
    print(f"  {t}")
print(f"TRIGGERS ({len(triggers)}):")
for t in triggers:
    print(f"  {t}")

engine.dispose()
os.remove(db_path)

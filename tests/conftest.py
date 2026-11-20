"""Test altyapısı.

Gerçek bir PostgreSQL gerekir. Testler YALNIZCA `tekstil_test` adlı ayrı bir veritabanını
siler ve yeniden oluşturur; canlı `tekstil` veritabanınıza dokunmaz.

Bağlantı: TEST_ADMIN_URL ortam değişkeni (varsayılan postgresql://postgres:postgres@localhost:5432/postgres)
"""
import os
import pathlib
import sys

import psycopg
import pytest
from psycopg import sql

ROOT = pathlib.Path(__file__).resolve().parent.parent
ADMIN_URL = os.getenv("TEST_ADMIN_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
TEST_DB = "tekstil_test"
TEST_URL = ADMIN_URL.rsplit("/", 1)[0] + "/" + TEST_DB

# main.py DSN'i içe aktarılırken okur; bu yüzden önce ayarlanmalı.
os.environ["DATABASE_URL"] = TEST_URL
sys.path.insert(0, str(ROOT / "app"))


@pytest.fixture(scope="session")
def database():
    try:
        admin = psycopg.connect(ADMIN_URL, autocommit=True)
    except psycopg.OperationalError as e:
        pytest.exit(
            "Test veritabanına bağlanılamadı. PostgreSQL çalışıyor mu ve TEST_ADMIN_URL doğru mu?\n"
            f"Ayrıntı: {e}", returncode=2)
    with admin:
        admin.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(TEST_DB)))
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(TEST_DB)))
    with psycopg.connect(TEST_URL, autocommit=True) as c:
        c.execute((ROOT / "tekstil_planlama_schema.sql").read_text(encoding="utf-8"))
    yield


@pytest.fixture(autouse=True)
def clean_db(database):
    """Her testten önce tüm tabloları boşaltır ve örnek veriyi yeniden yükler."""
    with psycopg.connect(TEST_URL, autocommit=True) as c:
        names = [r[0] for r in c.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")]
        c.execute(sql.SQL("TRUNCATE {} RESTART IDENTITY CASCADE").format(
            sql.SQL(", ").join(map(sql.Identifier, names))))
        c.execute((ROOT / "db" / "seed.sql").read_text(encoding="utf-8"))
    yield


@pytest.fixture
def db(database):
    with psycopg.connect(TEST_URL, autocommit=True) as c:
        yield c


@pytest.fixture(scope="session")
def client(database):
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app)

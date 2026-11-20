"""Test altyapısı.

Gerçek bir PostgreSQL gerekir. Testler YALNIZCA `tekstil_test` adlı ayrı bir veritabanını
siler ve yeniden oluşturur; canlı `tekstil` veritabanınıza dokunmaz.

Bağlantı: TEST_ADMIN_URL ortam değişkeni (varsayılan postgresql://postgres:postgres@127.0.0.1:5432/postgres)
"""
import os
import pathlib
import sys

import psycopg
import pytest
from psycopg import sql

ROOT = pathlib.Path(__file__).resolve().parent.parent
# "localhost" Windows'ta önce IPv6'yı dener ve reddedilen her bağlantı ~1 sn bekletir; 127.0.0.1 bunu önler.
ADMIN_URL = os.getenv("TEST_ADMIN_URL", "postgresql://postgres:postgres@127.0.0.1:5432/postgres").replace("@localhost", "@127.0.0.1")
TEST_DB = "tekstil_test"
TEST_URL = ADMIN_URL.rsplit("/", 1)[0] + "/" + TEST_DB

# main.py DSN'i içe aktarılırken okur; bu yüzden önce ayarlanmalı.
os.environ["DATABASE_URL"] = TEST_URL
sys.path.insert(0, str(ROOT / "app"))

SEED = (ROOT / "db" / "seed.sql").read_text(encoding="utf-8")

# Satır içeren tablolar ...
DIRTY_ROWS = """
SELECT c.relname FROM pg_class c
WHERE c.relnamespace = 'public'::regnamespace AND c.relkind = 'r'
  AND (xpath('/row/c/text()', query_to_xml(format('SELECT count(*) AS c FROM %I', c.relname), false, true, '')))[1]::text::int > 0
"""
# ... ve numara sayacı ilerlemiş (kayıt eklenip silinmiş) tablolar
DIRTY_SEQ = """
SELECT DISTINCT c.relname FROM pg_class c
JOIN pg_depend d ON d.refobjid = c.oid AND d.deptype IN ('a', 'i')
JOIN pg_class s ON s.oid = d.objid AND s.relkind = 'S'
JOIN pg_sequences ps ON ps.schemaname = 'public' AND ps.sequencename = s.relname
WHERE c.relnamespace = 'public'::regnamespace AND c.relkind = 'r' AND ps.last_value IS NOT NULL
"""


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
        # Yalnızca test veritabanı: her işlemde diske senkronizasyon beklenmez (özellikle Windows'ta büyük fark yaratır).
        admin.execute(sql.SQL("ALTER DATABASE {} SET synchronous_commit = off").format(sql.Identifier(TEST_DB)))
    with psycopg.connect(TEST_URL, autocommit=True) as c:
        c.execute((ROOT / "tekstil_planlama_schema.sql").read_text(encoding="utf-8"))
    yield


@pytest.fixture(scope="session")
def _conn(database):
    """Temizlik ve doğrudan veritabanı testleri için oturum boyunca tek bağlantı."""
    with psycopg.connect(TEST_URL, autocommit=True) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_db(_conn):
    """Her testten önce yalnızca kirlenmiş tabloları boşaltır ve örnek veriyi yeniden yükler."""
    kirli = {r[0] for r in _conn.execute(DIRTY_ROWS)} | {r[0] for r in _conn.execute(DIRTY_SEQ)}
    with _conn.transaction():          # boşaltma + örnek veri tek işlemde: tek bir kayıt/senkronizasyon
        if kirli:
            _conn.execute(sql.SQL("TRUNCATE {} RESTART IDENTITY CASCADE").format(
                sql.SQL(", ").join(map(sql.Identifier, sorted(kirli)))))
        _conn.execute(SEED)
    yield


@pytest.fixture
def db(_conn):
    return _conn


@pytest.fixture(scope="session")
def client(database):
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app)

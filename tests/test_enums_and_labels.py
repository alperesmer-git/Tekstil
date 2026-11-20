"""Seçim listesi ayrıştırması ve Türkçe etiket sözlüklerinin şemayla uyumu."""
import pathlib
import re

import pytest

import main

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = (ROOT / "tekstil_planlama_schema.sql").read_text(encoding="utf-8")
LABELS = (ROOT / "app" / "static" / "labels.js").read_text(encoding="utf-8")


# ---------- parse_enum ----------
def test_parse_text_sutun():
    d = "CHECK ((role = ANY (ARRAY['admin'::text, 'planner'::text, 'viewer'::text])))"
    assert main.parse_enum(d) == ("role", ["admin", "planner", "viewer"])


def test_parse_varchar_sutun():
    d = ("CHECK (((status)::text = ANY ((ARRAY['planned'::character varying, "
         "'in_production'::character varying])::text[])))")
    assert main.parse_enum(d) == ("status", ["planned", "in_production"])


def test_parse_tirnakli_deger():
    assert main.parse_enum("CHECK ((x = ANY (ARRAY['it''s'::text])))") == ("x", ["it's"])


@pytest.mark.parametrize("d", ["CHECK ((qty > 0))", "CHECK ((end_at > start_at))",
                               "CHECK (((a)::text <> ''::text))", ""])
def test_parse_liste_olmayan_kisitlar(d):
    assert main.parse_enum(d) is None


# ---------- şemadaki tüm IN kısıtları API'de seçim listesi olarak gelir ----------
def test_tum_kisitlar_seceneklere_donusur(client):
    beklenen = {(c, tuple(re.findall(r"'([^']*)'", v)))
                for c, v in re.findall(r"CHECK \((\w+) IN \(([^)]*)\)\)", SCHEMA)}
    assert len(beklenen) >= 15
    bulunan = set()
    for t in client.get("/api/tables").json():
        for f in client.get(f"/api/t/{t}").json()["form"]:
            if f["options"]:
                bulunan.add((f["name"], tuple(f["options"])))
    assert beklenen == bulunan


# ---------- Türkçe etiket kapsamı ----------
def _anahtarlar(ad):
    govde = re.search(r"const " + ad + r" = \{(.*?)\n\};", LABELS, re.S).group(1)
    return {a or b for a, b in re.findall(r"(?:^|[\s,{])(?:'([^']+)'|(\w+)):\s*'", govde)}


def _db_listesi(db, q):
    return {r[0] for r in db.execute(q).fetchall()}


def test_her_tablonun_turkce_adi_var(db):
    tablolar = _db_listesi(db, "SELECT table_name FROM information_schema.tables "
                               "WHERE table_schema='public' AND table_type='BASE TABLE'")
    assert tablolar - _anahtarlar("TABLES") == set()


def test_sozlukte_olmayan_tablo_yok(db):
    tablolar = _db_listesi(db, "SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    assert _anahtarlar("TABLES") - tablolar == set()


def test_her_sutunun_turkce_adi_var(db):
    sutunlar = _db_listesi(db, "SELECT DISTINCT column_name FROM information_schema.columns "
                               "WHERE table_schema='public'")
    assert sutunlar - _anahtarlar("COLS") == set()


def test_her_veri_tipinin_turkce_adi_var(db):
    tipler = _db_listesi(db, "SELECT DISTINCT data_type FROM information_schema.columns "
                             "WHERE table_schema='public'")
    assert tipler - _anahtarlar("TYPES") == set()


def test_her_secenek_degerinin_turkce_adi_var():
    degerler = {v for _, liste in re.findall(r"CHECK \((\w+) IN \(([^)]*)\)\)", SCHEMA)
                for v in re.findall(r"'([^']*)'", liste)}
    assert degerler - _anahtarlar("VALUES") == set()

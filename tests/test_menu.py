"""Menü tanımı (app/static/menu.js) şemayla uyumlu olmalı: her tablo tam bir kez, bir grupta."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
MENU = (ROOT / "app" / "static" / "menu.js").read_text(encoding="utf-8")
SCHEMA = (ROOT / "tekstil_planlama_schema.sql").read_text(encoding="utf-8")


def ogeler():
    return [i for lst in re.findall(r"items:\[(.*?)\]", MENU) for i in re.findall(r"'([\w@]+)'", lst)]


def test_her_tablo_menude_var():
    tablolar = set(re.findall(r"CREATE TABLE\s+(\w+)\s*\(", SCHEMA))
    assert tablolar - set(ogeler()) == set()


def test_menude_olmayan_tablo_yok():
    tablolar = set(re.findall(r"CREATE TABLE\s+(\w+)\s*\(", SCHEMA))
    assert set(ogeler()) - tablolar - {"@plan"} == set()


def test_hicbir_oge_tekrarlanmaz():
    o = ogeler()
    assert len(o) == len(set(o))


def test_menu_dosyasi_sunuluyor(client):
    r = client.get("/static/menu.js")
    assert r.status_code == 200 and "const MENU" in r.text


def test_ana_sayfa_menuyu_yukler(client):
    h = client.get("/").text
    assert "/static/menu.js" in h and 'id="menu"' in h and 'id="t-data"' not in h


def test_gruplar_turkce_ve_benzersiz():
    basliklar = re.findall(r"title:'([^']+)'", MENU)
    assert len(basliklar) == len(set(basliklar)) == 13

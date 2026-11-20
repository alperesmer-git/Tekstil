"""Yabancı anahtar alanları: arayüzde açılır liste olarak sunulacak seçenekler ve okunabilir etiketler."""
import pathlib
import re

import pytest

import main

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = (ROOT / "tekstil_planlama_schema.sql").read_text(encoding="utf-8")


def sema_fk():
    """Şema metninden (tablo, sütun, başvurulan tablo) üçlüleri."""
    out = set()
    for t, body in re.findall(r"CREATE TABLE\s+(\w+)\s*\((.*?)\n\);", SCHEMA, re.S):
        for line in body.split("\n"):
            m = re.match(r"\s*(\w+)\s+\w[^,]*?REFERENCES\s+(\w+)\(", line)
            if m:
                out.add((t, m.group(1), m.group(2)))
    return out


def form(client, tablo):
    return {f["name"]: f for f in client.get(f"/api/t/{tablo}").json()["form"]}


def etiketler(client, tablo, sutun):
    return [o["l"] for o in form(client, tablo)[sutun]["fk"]["options"]]


# ---------- kapsam: şemadaki HER yabancı anahtar liste olarak gelir (tüm etiket sorguları çalışır) ----------
def test_tum_yabanci_anahtarlar_liste_olarak_gelir(client):
    beklenen = sema_fk()
    assert len(beklenen) >= 100
    bulunan = set()
    for t in client.get("/api/tables").json():
        for ad, f in form(client, t).items():
            if f["fk"]:
                assert isinstance(f["fk"]["options"], list)
                bulunan.add((t, ad, f["fk"]["table"]))
    assert beklenen == bulunan


def test_her_basvurulan_tablonun_etiketi_tanimli():
    basvurulan = {r for _, _, r in sema_fk()}
    assert basvurulan - set(main.LABELS) == set()


def test_etiket_sozlugunde_olmayan_tablo_yok(db):
    tablolar = {r[0] for r in db.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")}
    assert set(main.LABELS) - tablolar == set()


def test_yabanci_anahtar_olmayan_alanlarda_fk_yok(client):
    f = form(client, "app_user")
    assert f["email"]["fk"] is None and f["role"]["fk"] is None and f["full_name"]["fk"] is None
    assert f["role"]["options"] and f["tenant_id"]["options"] is None      # seçim listesi ≠ yabancı anahtar


# ---------- örnek veriyle etiketler ----------
def test_firma_etiketi(client):
    assert form(client, "app_user")["tenant_id"]["fk"] == {
        "table": "tenant", "options": [{"v": 1, "l": "Demo Tekstil"}]}


def test_siparis_ve_model_etiketleri(client):
    assert etiketler(client, "order_line", "sales_order_id") == ["SIP-0001"]
    assert etiketler(client, "order_line", "style_id") == ["PNT-200 – Chino pantolon", "TSH-100 – Basic tişört"]


def test_is_emri_etiketleri(client):
    assert etiketler(client, "work_order", "order_line_id") == ["SIP-0001 / PNT-200", "SIP-0001 / TSH-100"]
    adimlar = etiketler(client, "work_order", "routing_step_id")
    assert "TSH-100 v1 › 2. Dikim" in adimlar and "PNT-200 v1 › 1. Kesim" in adimlar
    assert "BANT-1 – Bant 1" in etiketler(client, "work_order", "line_id")


def test_musteri_ve_departman_etiketi(client):
    assert etiketler(client, "style", "customer_id") == ["MUS-001 – Örnek Müşteri A.Ş."]
    assert etiketler(client, "production_line", "department_id") == ["Dikim", "Kesim", "Ütü-Paket"]


def test_anahtar_metin_olan_tablo(client):
    # material.uom -> unit_of_measure(code): değer metin kodudur
    o = form(client, "material")["uom"]["fk"]["options"]
    assert {"v": "ADET", "l": "ADET – Adet"} in o


def test_dolu_olmayan_tabloda_bos_liste(client):
    assert form(client, "bom_line")["bom_id"]["fk"]["options"] == []


def test_kendine_baglanan_alan(client):
    assert form(client, "bom_line")["parent_line_id"]["fk"]["table"] == "bom_line"


def test_yeni_kayit_listede_gorunur(client):
    r = client.post("/api/t/style", json={"tenant_id": 1, "customer_id": 1, "style_code": "GMK-300",
                                          "description": "Gömlek", "size_scale_id": 1})
    assert r.status_code == 200
    assert "GMK-300 – Gömlek" in etiketler(client, "order_line", "style_id")


def test_aciklamasiz_model_yalniz_kodla_gorunur(client):
    client.post("/api/t/style", json={"tenant_id": 1, "style_code": "XYZ-1", "size_scale_id": 1})
    assert "XYZ-1" in etiketler(client, "order_line", "style_id")


def test_secilen_deger_metin_olarak_gonderilince_kaydedilir(client):
    # arayüz seçilen değeri metin ("1") olarak gönderir
    r = client.post("/api/t/order_line", json={"sales_order_id": "1", "style_id": "2", "ship_date": "2031-01-01"})
    assert r.status_code == 200 and r.json()["style_id"] == 2


def test_siralama_etikete_gore(client):
    for kod in ("C-3", "A-1", "B-2"):
        client.post("/api/t/color", json={"tenant_id": 1, "code": kod, "name": "x"})
    l = etiketler(client, "style_variant", "color_id")
    sira = [next(i for i, e in enumerate(l) if e.startswith(k)) for k in ("A-1", "B-2", "C-3")]
    assert sira == sorted(sira)


def test_is_emri_etiketleri_numarayla_siralanir(client):
    for _ in range(9):
        client.post("/api/t/work_order", json={"order_line_id": 1, "routing_step_id": 2, "planned_qty": 1})
    ids = [o["v"] for o in form(client, "production_log")["work_order_id"]["fk"]["options"]]
    assert ids == sorted(ids) and len(ids) == 12

"""Plan Panosu API'si: pano verisi, hat atama, çakışma ve plan kaldırma."""
from datetime import datetime, timedelta, timezone

import pytest


def tz(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def pano(client):
    return client.get("/api/plan").json()


def is_emri(client, i):
    return next(o for o in pano(client)["orders"] if o["id"] == i)


def ata(client, wo, hat, bas, bit):
    return client.put(f"/api/plan/{wo}", json={"line_id": hat,
                                              "planned_start": bas.isoformat() if bas else None,
                                              "planned_end": bit.isoformat() if bit else None})


def uzak(gun, saat=8, sure=9):
    """Seed verisiyle çakışmayan, ileri tarihli aralık."""
    b = datetime.now(timezone.utc).replace(hour=saat, minute=0, second=0, microsecond=0) + timedelta(days=gun)
    return b, b + timedelta(hours=sure)


# ---------- pano verisi ----------
def test_pano_yapisi(client):
    p = pano(client)
    assert [h["code"] for h in p["lines"]] == ["BANT-1", "BANT-2", "KESIM-1"]
    assert len(p["orders"]) == 3
    assert {"id", "line_id", "planned_qty", "planned_start", "planned_end", "status",
            "dept", "style_code", "order_no", "ship_date"} <= set(p["orders"][0])


def test_ornek_is_emirleri(client):
    o1, o2, o3 = (is_emri(client, i) for i in (1, 2, 3))
    assert (o1["line_id"], o1["style_code"], o1["dept"], o1["order_no"]) == (1, "TSH-100", "DIKIM", "SIP-0001")
    assert o1["planned_start"] and o1["planned_end"]
    assert (o2["line_id"], o2["style_code"], o2["dept"]) == (None, "PNT-200", "DIKIM")
    assert (o3["line_id"], o3["dept"]) == (None, "KESIM")
    assert o2["ship_date"] and o2["planned_qty"] == 2500


def test_siralama_atanmamislar_once(client):
    ids = [o["id"] for o in pano(client)["orders"]]
    assert ids[-1] == 1 and set(ids[:2]) == {2, 3}


def test_iptal_edilen_panoda_yok(client):
    r = client.post("/api/t/work_order", json={"order_line_id": 1, "routing_step_id": 2,
                                               "planned_qty": 5, "status": "cancelled"})
    assert r.status_code == 200
    assert r.json()["id"] not in [o["id"] for o in pano(client)["orders"]]


def test_yeni_is_emri_atanmamis_gorunur(client):
    r = client.post("/api/t/work_order", json={"order_line_id": 2, "routing_step_id": 3, "planned_qty": 100}).json()
    o = is_emri(client, r["id"])
    assert o["line_id"] is None and o["planned_start"] is None


# ---------- atama ----------
def test_basarili_atama(client):
    b, s = uzak(6)
    assert ata(client, 2, 2, b, s).json() == {"ok": True}
    o = is_emri(client, 2)
    assert o["line_id"] == 2 and tz(o["planned_start"]) == b and tz(o["planned_end"]) == s


def test_farkli_hatta_ayni_zaman_serbest(client):
    o1 = is_emri(client, 1)
    assert ata(client, 2, 2, tz(o1["planned_start"]), tz(o1["planned_end"])).status_code == 200


def test_ayni_hatta_cakisma_409(client):
    o1 = is_emri(client, 1)
    r = ata(client, 2, 1, tz(o1["planned_start"]) + timedelta(hours=1), tz(o1["planned_end"]) - timedelta(hours=1))
    assert r.status_code == 409
    assert "çakışma" in r.json()["detail"] and "#1" in r.json()["detail"]
    assert is_emri(client, 2)["line_id"] is None          # kayıt değişmedi


def test_kismi_cakisma_409(client):
    o1 = is_emri(client, 1)
    r = ata(client, 2, 1, tz(o1["planned_end"]) - timedelta(hours=2), tz(o1["planned_end"]) + timedelta(hours=5))
    assert r.status_code == 409


def test_bitisik_aralik_cakisma_degil(client):
    o1 = is_emri(client, 1)
    bas = tz(o1["planned_end"])
    assert ata(client, 2, 1, bas, bas + timedelta(hours=8)).status_code == 200
    ayni_bitis = tz(o1["planned_start"])
    assert ata(client, 3, 1, ayni_bitis - timedelta(hours=8), ayni_bitis).status_code == 200


def test_kendi_araligiyla_cakisma_sayilmaz(client):
    o1 = is_emri(client, 1)
    assert ata(client, 1, 1, tz(o1["planned_start"]) + timedelta(hours=1),
               tz(o1["planned_end"]) + timedelta(hours=1)).status_code == 200


def test_iptal_edilen_is_emri_hatti_bloklamaz(client):
    b, s = uzak(7)
    assert client.post("/api/t/work_order", json={
        "order_line_id": 1, "routing_step_id": 2, "planned_qty": 5, "status": "cancelled",
        "line_id": 2, "planned_start": b.isoformat(), "planned_end": s.isoformat()}).status_code == 200
    assert ata(client, 2, 2, b, s).status_code == 200


def test_art_arda_iki_is_ayni_hatta(client):
    b, s = uzak(8)
    assert ata(client, 2, 2, b, s).status_code == 200
    assert ata(client, 3, 2, s, s + timedelta(hours=9)).status_code == 200
    assert ata(client, 3, 2, b + timedelta(hours=1), s).status_code == 409


# ---------- doğrulama hataları ----------
@pytest.mark.parametrize("fark", [timedelta(0), timedelta(hours=-1)])
def test_bitis_baslangictan_once_ya_da_esit(client, fark):
    b, _ = uzak(6)
    r = ata(client, 2, 2, b, b + fark)
    assert r.status_code == 400 and "Geçerli başlangıç/bitiş" in r.json()["detail"]


def test_hat_var_zaman_yok(client):
    b, s = uzak(6)
    assert ata(client, 2, 2, None, s).status_code == 400
    assert ata(client, 2, 2, b, None).status_code == 400
    assert ata(client, 2, 2, None, None).status_code == 400


def test_olmayan_hat(client):
    b, s = uzak(6)
    r = ata(client, 2, 999, b, s)
    assert r.status_code == 400 and "Bağlı kayıt" in r.json()["detail"]


def test_olmayan_is_emri_404(client):
    b, s = uzak(6)
    assert ata(client, 999, 2, b, s).status_code == 404
    assert client.put("/api/plan/999", json={}).status_code == 404


def test_gecersiz_tarih_metni_422(client):
    r = client.put("/api/plan/2", json={"line_id": 2, "planned_start": "yarın", "planned_end": "öbür gün"})
    assert r.status_code == 422


# ---------- plan kaldırma ----------
def test_plani_kaldir(client):
    assert client.put("/api/plan/1", json={}).json() == {"ok": True}
    o = is_emri(client, 1)
    assert o["line_id"] is None and o["planned_start"] is None and o["planned_end"] is None


def test_hatsiz_gonderilen_zaman_temizlenir(client):
    b, s = uzak(6)
    r = client.put("/api/plan/1", json={"planned_start": b.isoformat(), "planned_end": s.isoformat()})
    assert r.status_code == 200
    assert is_emri(client, 1)["planned_start"] is None


def test_kaldirilan_plan_hatti_serbest_birakir(client):
    o1 = is_emri(client, 1)
    client.put("/api/plan/1", json={})
    assert ata(client, 2, 1, tz(o1["planned_start"]), tz(o1["planned_end"])).status_code == 200

"""Müşteri senaryoları: sipariş girişinden bantta planlamaya uçtan uca akış (API üzerinden)."""
from datetime import datetime, timedelta, timezone


def post(client, tablo, veri):
    r = client.post(f"/api/t/{tablo}", json=veri)
    assert r.status_code == 200, r.text
    return r.json()


def siparis_ac(client, no, model=2, termin="2031-03-01", rota=2):
    s = post(client, "sales_order", {"tenant_id": 1, "order_no": no, "customer_id": 1})
    sat = post(client, "order_line", {"sales_order_id": s["id"], "style_id": model,
                                      "ship_date": termin, "routing_id": rota})
    return s, sat


def test_siparisten_plana_tam_akis(client):
    # 1) sipariş + satır
    s, sat = siparis_ac(client, "SIP-0002")
    # 2) dikim adımı için iş emri (rota 2, adım 4 = dikim)
    wo = post(client, "work_order", {"order_line_id": sat["id"], "routing_step_id": 4, "planned_qty": 1800})
    # 3) panoda atanmamış olarak görünür
    o = next(x for x in client.get("/api/plan").json()["orders"] if x["id"] == wo["id"])
    assert (o["order_no"], o["style_code"], o["dept"], o["line_id"]) == ("SIP-0002", "PNT-200", "DIKIM", None)
    assert o["ship_date"] == "2031-03-01" and o["planned_qty"] == 1800
    # 4) BANT-2'ye ata
    b = datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=5)
    r = client.put(f"/api/plan/{wo['id']}", json={"line_id": 2, "planned_start": b.isoformat(),
                                                   "planned_end": (b + timedelta(days=2)).isoformat()})
    assert r.status_code == 200
    o = next(x for x in client.get("/api/plan").json()["orders"] if x["id"] == wo["id"])
    assert o["line_id"] == 2
    # 5) plan kaldırılınca iş emri durur, silinmez
    client.put(f"/api/plan/{wo['id']}", json={})
    assert any(x["id"] == wo["id"] for x in client.get("/api/plan").json()["orders"])


def test_iki_siparis_ayni_bantta_sirayla(client):
    _, s1 = siparis_ac(client, "SIP-0003")
    _, s2 = siparis_ac(client, "SIP-0004", model=1, rota=1)
    w1 = post(client, "work_order", {"order_line_id": s1["id"], "routing_step_id": 4, "planned_qty": 500})
    w2 = post(client, "work_order", {"order_line_id": s2["id"], "routing_step_id": 2, "planned_qty": 700})
    b = datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=9)
    kayit = lambda w, bas, bit: client.put(f"/api/plan/{w}", json={
        "line_id": 2, "planned_start": bas.isoformat(), "planned_end": bit.isoformat()})
    assert kayit(w1["id"], b, b + timedelta(days=1)).status_code == 200
    assert kayit(w2["id"], b + timedelta(hours=12), b + timedelta(days=2)).status_code == 409   # çakışır
    assert kayit(w2["id"], b + timedelta(days=1), b + timedelta(days=2)).status_code == 200      # sıradan


def test_ayni_siparis_numarasi_tekrar_girilemez(client):
    post(client, "sales_order", {"tenant_id": 1, "order_no": "SIP-0009", "customer_id": 1})
    r = client.post("/api/t/sales_order", json={"tenant_id": 1, "order_no": "SIP-0009", "customer_id": 1})
    assert r.status_code == 400 and "zaten var" in r.json()["detail"]


def test_silme_sirasi_bagimliliga_uyar(client):
    _, sat = siparis_ac(client, "SIP-0005")
    wo = post(client, "work_order", {"order_line_id": sat["id"], "routing_step_id": 4, "planned_qty": 10})
    assert client.delete(f"/api/t/order_line/{sat['id']}").status_code == 400     # iş emri var
    assert client.delete(f"/api/t/work_order/{wo['id']}").status_code == 200
    assert client.delete(f"/api/t/order_line/{sat['id']}").status_code == 200
    assert client.delete(f"/api/t/sales_order/{sat['sales_order_id']}").status_code == 200


def test_yeni_model_tanimlama_sirasi(client):
    m = post(client, "style", {"tenant_id": 1, "customer_id": 1, "style_code": "GMK-300",
                               "description": "Gömlek", "product_group": "gömlek", "size_scale_id": 1})
    rota = post(client, "routing", {"style_id": m["id"]})
    adim = post(client, "routing_step", {"routing_id": rota["id"], "seq": 1, "department_id": 2, "total_smv": 14.5})
    assert adim["total_smv"] in (14.5, "14.500")
    r = client.post("/api/t/style", json={"tenant_id": 1, "style_code": "GMK-300", "size_scale_id": 1})
    assert r.status_code == 400 and "zaten var" in r.json()["detail"]

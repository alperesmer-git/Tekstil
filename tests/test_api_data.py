"""Veri ekranının API'si: tablo listesi, kayıt ekleme/listeleme/silme ve hata mesajları."""
import pytest

ROLLER = ["admin", "planner", "manager", "operator", "quality", "viewer"]


def kullanici(**kw):
    d = {"tenant_id": 1, "email": "yeni@test.com", "full_name": "Yeni Kullanıcı", "role": "planner"}
    d.update(kw)
    return d


def ekle(client, tablo, veri):
    return client.post(f"/api/t/{tablo}", json=veri)


# ---------- tablo listesi ve meta veri ----------
def test_tablo_listesi(client):
    t = client.get("/api/tables").json()
    assert len(t) == 54
    assert t == sorted(t)
    assert {"app_user", "work_order", "sales_order", "unit_of_measure"} <= set(t)


def test_liste_yapisi(client):
    j = client.get("/api/t/app_user").json()
    assert set(j) == {"form", "enums", "rows", "deletable"}
    assert j["deletable"] is True
    assert j["rows"] == []


def test_form_alanlari_ve_zorunluluk(client):
    form = {f["name"]: f for f in client.get("/api/t/app_user").json()["form"]}
    assert "id" not in form                      # otomatik numara forma girmez
    assert form["email"]["required"] is True
    assert form["role"]["required"] is True
    assert form["is_active"]["required"] is False  # varsayılanı var
    assert form["role"]["options"] == ROLLER
    assert form["email"]["options"] is None


def test_enums_alani_listeyi_icerir(client):
    assert client.get("/api/t/app_user").json()["enums"]["role"] == ROLLER


def test_idsiz_tablo_silinemez_isaretlenir(client):
    j = client.get("/api/t/unit_of_measure").json()
    assert j["deletable"] is False
    assert {r["code"] for r in j["rows"]} == {"ADET", "MT", "KG"}


def test_limit(client):
    assert len(client.get("/api/t/size?limit=2").json()["rows"]) == 2
    assert len(client.get("/api/t/size").json()["rows"]) == 4


def test_gecersiz_limit_422(client):
    assert client.get("/api/t/size?limit=abc").status_code == 422


def test_en_yeni_kayit_ustte(client):
    a = ekle(client, "app_user", kullanici(email="a@t.com")).json()
    b = ekle(client, "app_user", kullanici(email="b@t.com")).json()
    rows = client.get("/api/t/app_user").json()["rows"]
    assert [r["id"] for r in rows] == [b["id"], a["id"]]


# ---------- ekleme: başarılı durumlar ----------
@pytest.mark.parametrize("rol", ROLLER)
def test_her_rolle_ekleme(client, rol):
    r = ekle(client, "app_user", kullanici(role=rol, email=f"{rol}@t.com"))
    assert r.status_code == 200
    assert r.json()["role"] == rol


def test_ekleme_kaydi_ve_id_dondurur(client):
    j = ekle(client, "app_user", kullanici()).json()
    assert j["id"] >= 1 and j["email"] == "yeni@test.com" and j["is_active"] is True


def test_bos_alan_varsayilani_kullanir(client):
    j = ekle(client, "app_user", kullanici(is_active="")).json()
    assert j["is_active"] is True


@pytest.mark.parametrize("deger,beklenen", [("true", True), ("false", False), (True, True), (False, False)])
def test_evet_hayir_alani(client, deger, beklenen):
    j = ekle(client, "app_user", kullanici(is_active=deger)).json()
    assert j["is_active"] is beklenen


def test_bilinmeyen_alan_yok_sayilir(client):
    r = ekle(client, "app_user", kullanici(foo="x", **{'role"; DROP TABLE tenant; --': "x"}))
    assert r.status_code == 200
    assert client.get("/api/t/tenant").status_code == 200


def test_turkce_karakter_ve_tirnak(client):
    ad = "İşçi Şükrü Ğ'nin Öğesi"
    j = ekle(client, "app_user", kullanici(full_name=ad)).json()
    assert j["full_name"] == ad
    assert client.get("/api/t/app_user").json()["rows"][0]["full_name"] == ad


def test_idsiz_tabloya_ekleme(client):
    r = ekle(client, "unit_of_measure", {"code": "TOP", "name": "Top"})
    assert r.status_code == 200 and r.json()["code"] == "TOP"


def test_tarih_alani(client):
    r = ekle(client, "order_line", {"sales_order_id": 1, "style_id": 1, "ship_date": "2030-05-01"})
    assert r.status_code == 200
    assert r.json()["ship_date"] == "2030-05-01"
    assert r.json()["priority"] == 5            # varsayılan


# ---------- ekleme: hata mesajları (Türkçe) ----------
def hata(r):
    assert r.status_code == 400, r.text
    return r.json()["detail"]


def test_bos_govde(client):
    assert "Boş kayıt" in hata(ekle(client, "app_user", {}))


def test_yalnizca_bos_degerler(client):
    assert "Boş kayıt" in hata(ekle(client, "app_user", {"email": "", "role": ""}))


def test_gecersiz_rol(client):
    d = hata(ekle(client, "app_user", kullanici(role="Yönetici")))
    assert "izin verilen aralığın dışında" in d and "app_user_role_check" in d


def test_tekrarli_eposta(client):
    ekle(client, "app_user", kullanici())
    assert "zaten var" in hata(ekle(client, "app_user", kullanici()))


def test_olmayan_firma(client):
    assert "Bağlı kayıt" in hata(ekle(client, "app_user", kullanici(tenant_id=999)))


def test_zorunlu_alan_eksik(client):
    d = hata(ekle(client, "app_user", {"tenant_id": 1, "role": "viewer", "full_name": "X"}))
    assert "Zorunlu" in d and "email" in d


def test_sayi_alanina_metin(client):
    assert "Geçersiz değer biçimi" in hata(ekle(client, "app_user", kullanici(tenant_id="abc")))


def test_gecersiz_tarih(client):
    d = hata(ekle(client, "order_line", {"sales_order_id": 1, "style_id": 1, "ship_date": "2026-13-45"}))
    assert "Geçersiz tarih" in d


def test_idsiz_tabloda_tekrar(client):
    assert "zaten var" in hata(ekle(client, "unit_of_measure", {"code": "ADET", "name": "Kopya"}))


# ---------- silme ----------
def test_silme(client):
    i = ekle(client, "app_user", kullanici()).json()["id"]
    assert client.delete(f"/api/t/app_user/{i}").json() == {"ok": True}
    assert client.get("/api/t/app_user").json()["rows"] == []


def test_olmayan_kaydi_silmek_hata_vermez(client):
    assert client.delete("/api/t/app_user/9999").status_code == 200


def test_kullanilan_kayit_silinemez(client):
    d = hata(client.delete("/api/t/tenant/1"))
    assert "Bağlı kayıt" in d


def test_idsiz_tabloda_silme_reddedilir(client):
    assert "tekil id yok" in hata(client.delete("/api/t/unit_of_measure/1"))


def test_bagli_kayitlar_kaldirilinca_silinebilir(client):
    # sipariş satırı -> iş emri bağı: önce iş emri silinmeli
    assert client.delete("/api/t/order_line/1").status_code == 400
    for wo in (1, 3):
        assert client.delete(f"/api/t/work_order/{wo}").status_code == 200
    assert client.delete("/api/t/order_line/1").status_code == 200


# ---------- bilinmeyen / kötü niyetli tablo adları ----------
@pytest.mark.parametrize("ad", ["yok_boyle_tablo", "app_user%3BDROP", "pg_user", "information_schema"])
def test_bilinmeyen_tablo_404(client, ad):
    assert client.get(f"/api/t/{ad}").status_code == 404
    assert client.post(f"/api/t/{ad}", json={"a": 1}).status_code == 404
    assert client.delete(f"/api/t/{ad}/1").status_code in (400, 404)


def test_sql_enjeksiyonu_tablolari_bozmaz(client):
    client.get("/api/t/app_user%3BDROP%20TABLE%20tenant")
    assert len(client.get("/api/t/tenant").json()["rows"]) == 1

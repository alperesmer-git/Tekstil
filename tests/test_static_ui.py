"""Sayfanın ve statik dosyaların sunulması."""


def test_ana_sayfa(client):
    r = client.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    h = r.text
    assert '<html lang="tr"' in h
    for metin in ("Tekstil Planlama", "Plan Panosu", "Veri", "Planı kaldır", "Kaydet", "Ekle"):
        assert metin in h
    assert "/static/labels.js" in h


def test_etiket_dosyasi_sunuluyor(client):
    r = client.get("/static/labels.js")
    assert r.status_code == 200
    for ad in ("const TABLES", "const COLS", "const VALUES", "const TYPES"):
        assert ad in r.text


def test_olmayan_statik_dosya(client):
    assert client.get("/static/yok.js").status_code == 404


def test_api_belgesi_acik(client):
    assert client.get("/openapi.json").status_code == 200

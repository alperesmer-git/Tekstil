"""Tarayıcıda (Chromium) gerçek kullanıcı senaryoları.

Kurulum (bir kez):  pip install playwright   ve   python -m playwright install chromium
(Chromium açılmazsa testler otomatik olarak kurulu Edge/Chrome'u dener.)
Çalıştırma:         python -m pytest -m e2e      (atlamak için: python -m pytest -m "not e2e")
"""
import sys
import threading
import time
from datetime import datetime, timedelta

import pytest

pw = pytest.importorskip("playwright.sync_api", reason="playwright kurulu değil")
pytestmark = pytest.mark.e2e
PORT = 8765


@pytest.fixture(scope="session")
def live_server(database):
    import uvicorn
    import main
    server = uvicorn.Server(uvicorn.Config(main.app, host="127.0.0.1", port=PORT, log_level="warning"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{PORT}"
    server.should_exit = True
    t.join(timeout=5)


@pytest.fixture(scope="session")
def browser():
    """Önce Playwright'ın Chromium'unu, olmazsa kurulu Edge ve Chrome'u dener.
    Belirli bir tarayıcı için: $env:E2E_BROWSER_CHANNEL = "msedge"  (ya da "chrome")"""
    import os
    with pw.sync_playwright() as p:
        kanal = os.getenv("E2E_BROWSER_CHANNEL")
        denemeler = [kanal] if kanal else [None, "msedge", "chrome"]
        hatalar, b = [], None
        for k in denemeler:
            try:
                b = p.chromium.launch(channel=k) if k else p.chromium.launch()
                break
            except Exception as e:
                hatalar.append(f"{k or 'chromium'}: {str(e).splitlines()[0]}")
        if b is None:
            pytest.skip("Hiçbir tarayıcı açılamadı. " + " | ".join(hatalar))
        yield b
        b.close()


@pytest.fixture
def page(browser, live_server):
    ctx = browser.new_context(locale="tr-TR")
    pg = ctx.new_page()
    pg.js_errors = []
    pg.on("pageerror", lambda e: pg.js_errors.append(str(e)))
    pg.goto(live_server)
    pg.wait_for_selector("#board .row")
    yield pg
    errors = pg.js_errors
    ctx.close()
    assert not errors, f"Sayfada JavaScript hatası: {errors}"


def dt_local(gun, saat):
    d = datetime.now().replace(hour=saat, minute=0, second=0, microsecond=0) + timedelta(days=gun)
    return d.strftime("%Y-%m-%dT%H:%M")


def sec_is_emri(page, i, hat, bas, bit):
    page.click(f'#olist tr[data-id="{i}"]')
    page.select_option("#a-line", str(hat))
    page.fill("#a-s", bas)
    page.fill("#a-e", bit)
    page.click("#a-save")


def veri_tablosu(page, tablo):
    page.click("#t-data")
    page.wait_for_selector("#tbl option", state="attached")
    page.select_option("#tbl", tablo)
    # Form, seçilen tablo için çizilene kadar bekle (önceki tablonun formunu okumamak için)
    page.wait_for_selector(f'#v-data[data-table="{tablo}"] #dform [data-c]')


# ---------- genel ----------
def test_baslik_ve_sekmeler(page):
    assert page.title() == "Tekstil Planlama"
    assert page.inner_text("#t-plan") == "Plan Panosu"
    assert page.inner_text("#t-data") == "Veri"


def test_sekme_gecisi(page):
    page.click("#t-data")
    assert page.is_visible("#v-data") and not page.is_visible("#v-plan")
    page.click("#t-plan")
    assert page.is_visible("#v-plan") and not page.is_visible("#v-data")


# ---------- plan panosu ----------
def test_pano_baslangic_durumu(page):
    assert page.locator("#board .row").count() == 3
    assert page.locator("#board .bar").count() == 1
    assert page.locator("#olist tr").count() == 3
    assert page.locator("#days span").count() == 14


def test_is_emri_secince_forma_gelir(page):
    page.click('#olist tr[data-id="2"]')
    assert page.input_value("#a-id") == "2"
    assert page.input_value("#a-s") and page.input_value("#a-e")      # önerilen saatler


def test_is_emrini_hatta_atama(page):
    sec_is_emri(page, 2, 2, dt_local(6, 8), dt_local(6, 17))
    page.wait_for_function("document.querySelectorAll('#board .bar').length == 2")
    assert page.locator('#olist tr[data-id="2"] td').nth(6).inner_text() == "BANT-2"


def test_cakisma_uyarisi(page):
    sec_is_emri(page, 2, 1, dt_local(1, 8), dt_local(1, 17))
    page.wait_for_function("document.querySelector('#a-err').textContent.length > 0")
    assert "çakışma" in page.inner_text("#a-err")
    assert page.locator("#board .bar").count() == 1                    # atama yapılmadı


def test_hatali_aralik_uyarisi(page):
    sec_is_emri(page, 2, 2, dt_local(6, 17), dt_local(6, 8))
    page.wait_for_function("document.querySelector('#a-err').textContent.length > 0")
    assert "başlangıç" in page.inner_text("#a-err")


def test_plani_kaldir(page):
    page.click('.bar[data-id="1"]')
    assert page.input_value("#a-id") == "1"
    page.click("#a-clear")
    page.wait_for_function("document.querySelectorAll('#board .bar').length == 0")
    assert page.locator('#olist tr[data-id="1"] td').nth(6).inner_text() == "—"


def test_cubuga_tiklayinca_form_dolar(page):
    page.click('.bar[data-id="1"]')
    assert page.input_value("#a-line") == "1"


def test_atama_sayfa_yenilenince_kalir(page):
    sec_is_emri(page, 2, 2, dt_local(6, 8), dt_local(6, 17))
    page.wait_for_function("document.querySelectorAll('#board .bar').length == 2")
    page.reload()
    page.wait_for_selector("#board .row")
    assert page.locator("#board .bar").count() == 2


# ---------- veri ekranı ----------
def test_tablo_adlari_turkce(page):
    page.click("#t-data")
    page.wait_for_selector("#tbl option", state="attached")
    secenekler = page.locator("#tbl option").all_inner_texts()
    assert len(secenekler) == 54
    for ad in ("Kullanıcılar", "İş emirleri", "Siparişler", "Üretim hatları (bantlar)"):
        assert ad in secenekler


def test_alan_etiketleri_turkce(page):
    veri_tablosu(page, "app_user")
    etiketler = " ".join(page.locator("#dform label").all_inner_texts())
    for ad in ("Firma No", "E-posta", "Ad Soyad", "Rol", "Aktif mi"):
        assert ad in etiketler


def test_rol_secim_listesi(page):
    veri_tablosu(page, "app_user")
    secenekler = page.locator('#dform [data-c="role"] option').all_inner_texts()
    assert secenekler == ["Seçiniz…", "Yönetici", "Planlamacı", "Üretim müdürü",
                          "Operatör", "Kalite sorumlusu", "Yalnızca görüntüleyen"]
    assert page.locator('#dform select[data-c="role"]').count() == 1       # yazı kutusu değil


def test_evet_hayir_listesi(page):
    veri_tablosu(page, "app_user")
    assert page.locator('#dform [data-c="is_active"] option').all_inner_texts() == ["—", "Evet", "Hayır"]


def test_kullanici_ekleme(page):
    veri_tablosu(page, "app_user")
    page.fill('[data-c="tenant_id"]', "1")
    page.fill('[data-c="email"]', "yeni@test.com")
    page.fill('[data-c="full_name"]', "Yeni Kullanıcı")
    page.select_option('[data-c="role"]', "planner")
    page.click("#add")
    page.wait_for_selector("#dtable td:has-text('yeni@test.com')")
    assert "Planlamacı" in page.inner_text("#dtable")                    # ham değer değil, Türkçe etiket
    assert "Evet" in page.inner_text("#dtable")                          # varsayılan: aktif


def test_tekrarli_kayit_uyarisi(page):
    veri_tablosu(page, "app_user")
    for _ in range(2):
        page.fill('[data-c="tenant_id"]', "1")
        page.fill('[data-c="email"]', "ayni@test.com")
        page.fill('[data-c="full_name"]', "Aynı")
        page.select_option('[data-c="role"]', "viewer")
        page.click("#add")
        page.wait_for_load_state("networkidle")
    page.wait_for_function("document.querySelector('#d-err').textContent.length > 0")
    assert "zaten var" in page.inner_text("#d-err")


def test_olmayan_firma_uyarisi(page):
    veri_tablosu(page, "app_user")
    page.fill('[data-c="tenant_id"]', "2")
    page.fill('[data-c="email"]', "x@test.com")
    page.fill('[data-c="full_name"]', "X")
    page.select_option('[data-c="role"]', "manager")
    page.click("#add")
    page.wait_for_function("document.querySelector('#d-err').textContent.length > 0")
    assert "Bağlı kayıt" in page.inner_text("#d-err")


def test_zorunlu_alan_uyarisi(page):
    veri_tablosu(page, "app_user")
    page.fill('[data-c="tenant_id"]', "1")
    page.select_option('[data-c="role"]', "viewer")
    page.click("#add")
    page.wait_for_function("document.querySelector('#d-err').textContent.length > 0")
    assert "Zorunlu" in page.inner_text("#d-err")


def test_bos_form_uyarisi(page):
    veri_tablosu(page, "app_user")
    page.click("#add")
    page.wait_for_function("document.querySelector('#d-err').textContent.length > 0")
    assert "Boş kayıt" in page.inner_text("#d-err")


def test_kayit_silme(page):
    veri_tablosu(page, "app_user")
    page.fill('[data-c="tenant_id"]', "1")
    page.fill('[data-c="email"]', "sil@test.com")
    page.fill('[data-c="full_name"]', "Silinecek")
    page.select_option('[data-c="role"]', "operator")
    page.click("#add")
    page.wait_for_selector("#dtable td:has-text('sil@test.com')")
    page.once("dialog", lambda d: d.accept())
    page.click("[data-del]")
    page.wait_for_function("!document.querySelector('#dtable').innerText.includes('sil@test.com')")


def test_silmeyi_iptal_etme(page):
    veri_tablosu(page, "app_user")
    page.fill('[data-c="tenant_id"]', "1")
    page.fill('[data-c="email"]', "kal@test.com")
    page.fill('[data-c="full_name"]', "Kalacak")
    page.select_option('[data-c="role"]', "operator")
    page.click("#add")
    page.wait_for_selector("#dtable td:has-text('kal@test.com')")
    page.once("dialog", lambda d: d.dismiss())
    page.click("[data-del]")
    assert "kal@test.com" in page.inner_text("#dtable")


def test_kullanilan_kayit_silme_uyarisi(page):
    veri_tablosu(page, "tenant")
    page.once("dialog", lambda d: d.accept())
    page.click("[data-del]")
    page.wait_for_function("document.querySelector('#d-err').textContent.length > 0")
    assert "Bağlı kayıt" in page.inner_text("#d-err")


def test_idsiz_tabloda_sil_dugmesi_yok(page):
    veri_tablosu(page, "unit_of_measure")
    assert page.locator("[data-del]").count() == 0


def test_durum_degerleri_turkce_gorunur(page):
    veri_tablosu(page, "work_order")
    tablo = page.inner_text("#dtable")
    assert "Planlandı" in tablo and "planned" not in tablo


def test_secim_listesinden_is_emri_durumu(page):
    veri_tablosu(page, "work_order")
    secenekler = page.locator('#dform [data-c="status"] option').all_inner_texts()
    assert "Tamamlandı" in secenekler and "İptal edildi" in secenekler

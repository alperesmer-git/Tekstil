"""Veritabanı şemasının kuralları (kısıtlar, varsayılanlar, çakışma engeli)."""
import pytest
from psycopg import errors

ROLLER = ["admin", "planner", "manager", "operator", "quality", "viewer"]


def sayi(db, q):
    return db.execute(q).fetchone()[0]


def test_tablo_sayisi(db):
    assert sayi(db, "SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_type='BASE TABLE'") == 54


def test_ornek_veri_yuklendi(db):
    assert sayi(db, "SELECT count(*) FROM production_line") == 3
    assert sayi(db, "SELECT count(*) FROM work_order") == 3
    assert sayi(db, "SELECT count(*) FROM sales_order") == 1


@pytest.mark.parametrize("rol", ROLLER)
def test_gecerli_roller(db, rol):
    db.execute("INSERT INTO app_user(tenant_id,email,full_name,role) VALUES (1,%s,'Test',%s)",
               (f"{rol}@t.com", rol))


@pytest.mark.parametrize("rol", ["Yönetici", "Admin", "ADMIN", "", "boss"])
def test_gecersiz_rol_reddedilir(db, rol):
    with pytest.raises(errors.CheckViolation):
        db.execute("INSERT INTO app_user(tenant_id,email,full_name,role) VALUES (1,'x@t.com','T',%s)", (rol,))


def test_eposta_benzersiz(db):
    q = "INSERT INTO app_user(tenant_id,email,full_name,role) VALUES (1,'a@t.com','A','viewer')"
    db.execute(q)
    with pytest.raises(errors.UniqueViolation):
        db.execute(q)


def test_olmayan_firma_reddedilir(db):
    with pytest.raises(errors.ForeignKeyViolation):
        db.execute("INSERT INTO app_user(tenant_id,email,full_name,role) VALUES (999,'a@t.com','A','viewer')")


def test_kullanilan_firma_silinemez(db):
    with pytest.raises(errors.ForeignKeyViolation):
        db.execute("DELETE FROM tenant WHERE id=1")


def test_is_active_varsayilan_true(db):
    v = db.execute("INSERT INTO app_user(tenant_id,email,full_name,role) VALUES (1,'a@t.com','A','viewer') "
                   "RETURNING is_active").fetchone()[0]
    assert v is True


def test_is_emri_varsayilan_durum(db):
    d = db.execute("INSERT INTO work_order(order_line_id,routing_step_id,planned_qty) VALUES (1,1,10) "
                   "RETURNING status").fetchone()[0]
    assert d == "planned"


def test_is_emri_gecersiz_durum(db):
    with pytest.raises(errors.CheckViolation):
        db.execute("INSERT INTO work_order(order_line_id,routing_step_id,planned_qty,status) "
                   "VALUES (1,1,10,'bitti')")


def test_hat_kodu_firma_icinde_benzersiz(db):
    with pytest.raises(errors.UniqueViolation):
        db.execute("INSERT INTO production_line(tenant_id,department_id,code,name) VALUES (1,2,'BANT-1','Kopya')")


def test_rota_adim_sirasi_benzersiz(db):
    with pytest.raises(errors.UniqueViolation):
        db.execute("INSERT INTO routing_step(routing_id,seq,department_id) VALUES (1,1,1)")


# ---- plan_assignment: aynı senaryoda aynı hatta zaman çakışması engeli ----
def _senaryo(db, ad="S1"):
    return db.execute("INSERT INTO plan_scenario(tenant_id,name,generated_by) VALUES (1,%s,'manual') "
                      "RETURNING id", (ad,)).fetchone()[0]


def _ata(db, sc, wo, hat, bas, bit):
    db.execute("INSERT INTO plan_assignment(scenario_id,work_order_id,line_id,start_at,end_at) "
               "VALUES (%s,%s,%s,%s,%s)", (sc, wo, hat, bas, bit))


def test_ayni_hat_ayni_senaryo_cakisma_engellenir(db):
    sc = _senaryo(db)
    _ata(db, sc, 1, 1, "2030-01-01 08:00+00", "2030-01-01 17:00+00")
    with pytest.raises(errors.ExclusionViolation):
        _ata(db, sc, 2, 1, "2030-01-01 12:00+00", "2030-01-01 20:00+00")


def test_farkli_hat_cakisma_degil(db):
    sc = _senaryo(db)
    _ata(db, sc, 1, 1, "2030-01-01 08:00+00", "2030-01-01 17:00+00")
    _ata(db, sc, 2, 2, "2030-01-01 08:00+00", "2030-01-01 17:00+00")


def test_farkli_senaryo_cakisma_degil(db):
    a, b = _senaryo(db, "A"), _senaryo(db, "B")
    _ata(db, a, 1, 1, "2030-01-01 08:00+00", "2030-01-01 17:00+00")
    _ata(db, b, 1, 1, "2030-01-01 08:00+00", "2030-01-01 17:00+00")


def test_bitisik_araliklar_cakisma_degil(db):
    sc = _senaryo(db)
    _ata(db, sc, 1, 1, "2030-01-01 08:00+00", "2030-01-01 17:00+00")
    _ata(db, sc, 2, 1, "2030-01-01 17:00+00", "2030-01-02 08:00+00")


def test_bitis_baslangictan_once_olamaz(db):
    sc = _senaryo(db)
    with pytest.raises(errors.CheckViolation):
        _ata(db, sc, 1, 1, "2030-01-01 17:00+00", "2030-01-01 08:00+00")


def test_senaryo_silinince_atamalar_silinir(db):
    sc = _senaryo(db)
    _ata(db, sc, 1, 1, "2030-01-01 08:00+00", "2030-01-01 17:00+00")
    db.execute("DELETE FROM plan_scenario WHERE id=%s", (sc,))
    assert sayi(db, "SELECT count(*) FROM plan_assignment") == 0

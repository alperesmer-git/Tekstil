import os
import re
import threading
from datetime import datetime
from typing import Optional

import psycopg
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from psycopg import sql
from psycopg.rows import dict_row
from pydantic import BaseModel

try:  # isteğe bağlı: bağlantı havuzu (pip install psycopg-pool). Yoksa her istekte yeni bağlantı açılır.
    from psycopg_pool import ConnectionPool
except ImportError:  # pragma: no cover
    ConnectionPool = None

# Windows'ta "localhost" önce IPv6 (::1) denenir ve reddedilen her bağlantı ~1 sn bekletir; 127.0.0.1 bunu önler.
DSN = os.getenv("DATABASE_URL", "postgresql://tekstil:tekstil@127.0.0.1:5432/tekstil").replace("@localhost", "@127.0.0.1")
HERE = os.path.dirname(__file__)
app = FastAPI(title="Tekstil Planlama")


HATA = {
    "23505": "Bu kayıt zaten var (benzersiz alan tekrarı)",
    "23503": "Bağlı kayıt bulunamadı ya da bu kayıt başka kayıtlarca kullanılıyor",
    "23502": "Zorunlu bir alan boş bırakıldı",
    "23514": "Girilen değer izin verilen aralığın dışında",
    "23P01": "Zaman çakışması: aynı kaynak aynı anda iki kez kullanılamaz",
    "22P02": "Geçersiz değer biçimi (sayı, tarih veya evet/hayır alanlarını kontrol edin)",
    "22007": "Geçersiz tarih biçimi",
    "22008": "Geçersiz tarih/saat değeri",
}


_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    global _pool
    if ConnectionPool is None:
        return None
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = ConnectionPool(DSN, min_size=1, max_size=8, timeout=10, open=True,
                                       kwargs={"row_factory": dict_row})
    return _pool


def run(query, params=None):
    try:
        pool = _get_pool()
        if pool is not None:
            with pool.connection() as conn:
                cur = conn.execute(query, params)
                return cur.fetchall() if cur.description else []
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            cur = conn.execute(query, params)
            return cur.fetchall() if cur.description else []
    except psycopg.Error as e:
        msg = HATA.get(e.sqlstate)
        detay = getattr(e.diag, "message_primary", None) or str(e)
        ek = getattr(e.diag, "column_name", None) or getattr(e.diag, "constraint_name", None)
        if msg:
            raise HTTPException(400, f"{msg}" + (f" [{ek}]" if ek else ""))
        raise HTTPException(400, f"Veritabanı hatası: {detay}")


def columns(table: str):
    rows = run(
        """SELECT column_name, data_type, is_nullable, column_default, is_generated
           FROM information_schema.columns
           WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position""",
        (table,),
    )
    if not rows:
        raise HTTPException(404, "Tablo bulunamadı")
    return rows


app.mount("/static", StaticFiles(directory=os.path.join(HERE, "static")), name="static")


ENUM_RE = re.compile(r"^CHECK \(+(\w+)\)?(?:::\w+)? = ANY")


def parse_enum(defn: str):
    """'CHECK ((role = ANY (ARRAY['a'::text, 'b'::text])))' -> ('role', ['a', 'b'])"""
    m = ENUM_RE.match(defn)
    if not m or "ARRAY[" not in defn:
        return None
    arr = defn[defn.index("ARRAY["):]
    vals = [v.replace("''", "'") for v in re.findall(r"'((?:[^']|'')*)'", arr)]
    return (m.group(1), vals) if vals else None


def enums(table: str):
    rows = run(
        "SELECT pg_get_constraintdef(oid) AS d FROM pg_constraint "
        "WHERE contype = 'c' AND conrelid = to_regclass(%s::text)",
        ("public." + table,),
    )
    out = {}
    for r in rows:
        parsed = parse_enum(r["d"])
        if parsed:
            out[parsed[0]] = parsed[1]
    return out


# Yabancı anahtar listelerinde gösterilecek etiketler. Takma ad `t`, başvurulan tablodur.
LABELS = {
    "app_user": "t.full_name",
    "bom": "(SELECT s.style_code FROM style s WHERE s.id = t.style_id) || ' BOM v' || t.version",
    "bom_line": "'#' || t.id || ' ' || (SELECT m.code FROM material m WHERE m.id = t.material_id)",
    "business_partner": "t.code || ' – ' || t.name",
    "color": "t.code || ' – ' || t.name",
    "cutting_order": "'#' || t.id || COALESCE(' · ' || t.planned_date::text, '')",
    "defect_type": "t.code || ' – ' || t.name",
    "department": "t.name",
    "inspection": "'#' || t.id || ' · ' || t.stage",
    "marker": "COALESCE(t.marker_name, '#' || t.id)",
    "material": "t.code || ' – ' || t.name",
    "material_lot": "t.lot_no",
    "operation": "t.name",
    "operator": "t.full_name",
    "order_line": "(SELECT so.order_no || ' / ' || s.style_code FROM sales_order so, style s "
                  "WHERE so.id = t.sales_order_id AND s.id = t.style_id)",
    "plan_scenario": "t.name",
    "production_line": "t.code || ' – ' || t.name",
    "purchase_order": "t.po_no",
    "purchase_order_line": "(SELECT po.po_no || ' / ' || m.code FROM purchase_order po, material m "
                           "WHERE po.id = t.purchase_order_id AND m.id = t.material_id)",
    "routing": "(SELECT s.style_code FROM style s WHERE s.id = t.style_id) || ' rota v' || t.version",
    "routing_step": "(SELECT s.style_code || ' v' || r.version || ' › ' || t.seq || '. ' || d.name "
                    "FROM routing r, style s, department d "
                    "WHERE r.id = t.routing_id AND s.id = r.style_id AND d.id = t.department_id)",
    "sales_order": "t.order_no",
    "season": "t.code || ' – ' || t.name",
    "size": "t.code",
    "size_scale": "t.name",
    "style": "t.style_code || COALESCE(' – ' || t.description, '')",
    "style_variant": "(SELECT s.style_code || ' / ' || c.code || ' / ' || z.code FROM style s, color c, size z "
                     "WHERE s.id = t.style_id AND c.id = t.color_id AND z.id = t.size_id)",
    "subcontract_order": "'#' || t.id",
    "subcontract_shipment": "COALESCE(t.waybill_no, '#' || t.id)",
    "tenant": "t.name",
    "unit_of_measure": "t.code || ' – ' || t.name",
    "work_order": "(SELECT '#' || t.id || ' ' || so.order_no || ' / ' || s.style_code || ' / ' || d.name "
                  "FROM order_line ol, sales_order so, style s, routing_step rs, department d "
                  "WHERE ol.id = t.order_line_id AND so.id = ol.sales_order_id AND s.id = ol.style_id "
                  "AND rs.id = t.routing_step_id AND d.id = rs.department_id)",
    "working_calendar": "t.name",
}
ORDER_BY_KEY = {"bom_line", "cutting_order", "inspection", "subcontract_order", "work_order", "subcontract_shipment"}
FK_LIMIT = 2000

FK_SQL = """
SELECT a.attname AS col, cf.relname AS ref, af.attname AS refcol
FROM pg_constraint c
JOIN pg_attribute a  ON a.attrelid = c.conrelid  AND a.attnum  = c.conkey[1]
JOIN pg_class cf     ON cf.oid = c.confrelid
JOIN pg_attribute af ON af.attrelid = c.confrelid AND af.attnum = c.confkey[1]
WHERE c.contype = 'f' AND array_length(c.conkey, 1) = 1 AND c.conrelid = to_regclass(%s::text)
"""


def foreign_keys(table: str):
    return {r["col"]: (r["ref"], r["refcol"]) for r in run(FK_SQL, ("public." + table,))}


def fk_options(ref: str, key: str):
    expr = LABELS.get(ref, "'#' || t." + '"' + key + '"')
    order = "v" if ref in ORDER_BY_KEY else "l"
    q = sql.SQL("SELECT t.{k} AS v, COALESCE(({e}), t.{k}::text) AS l FROM {r} t ORDER BY {o} LIMIT %s").format(
        k=sql.Identifier(key), e=sql.SQL(expr), r=sql.Identifier(ref), o=sql.SQL(order))
    return run(q, (FK_LIMIT,))


@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "static", "index.html"))


# ---------- Genel veri ekranı (tüm tablolar) ----------
@app.get("/api/tables")
def tables():
    r = run("""SELECT table_name FROM information_schema.tables
               WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY 1""")
    return [x["table_name"] for x in r]


@app.get("/api/t/{table}")
def list_rows(table: str, limit: int = 200):
    cols = columns(table)
    has_id = any(c["column_name"] == "id" for c in cols)
    order = sql.SQL(" ORDER BY id DESC") if has_id else sql.SQL("")
    q = sql.SQL("SELECT * FROM {}{} LIMIT %s").format(sql.Identifier(table), order)
    en = enums(table)
    fks, cache = foreign_keys(table), {}

    def fk_info(col):
        if col not in fks:
            return None
        ref, key = fks[col]
        if (ref, key) not in cache:
            cache[(ref, key)] = fk_options(ref, key)
        return {"table": ref, "options": cache[(ref, key)]}

    form = [
        {"name": c["column_name"], "type": c["data_type"],
         "required": c["is_nullable"] == "NO" and c["column_default"] is None,
         "options": en.get(c["column_name"]), "fk": fk_info(c["column_name"])}
        for c in cols
        if c["is_generated"] != "ALWAYS" and not (c["column_default"] or "").startswith("nextval")
    ]
    return {"form": form, "enums": en, "rows": run(q, (limit,)), "deletable": has_id}


@app.post("/api/t/{table}")
def insert_row(table: str, data: dict = Body(...)):
    allowed = {c["column_name"] for c in columns(table) if c["is_generated"] != "ALWAYS"}
    items = {k: v for k, v in data.items() if k in allowed and v not in ("", None)}
    if not items:
        raise HTTPException(400, "Boş kayıt")
    q = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
        sql.Identifier(table),
        sql.SQL(",").join(sql.Identifier(k) for k in items),
        sql.SQL(",").join([sql.Placeholder()] * len(items)),
    )
    return run(q, list(items.values()))[0]


@app.delete("/api/t/{table}/{row_id}")
def delete_row(table: str, row_id: int):
    if not any(c["column_name"] == "id" for c in columns(table)):
        raise HTTPException(400, "Bu tabloda tekil id yok")
    run(sql.SQL("DELETE FROM {} WHERE id=%s").format(sql.Identifier(table)), (row_id,))
    return {"ok": True}


# ---------- Plan panosu (manuel bant planlama) ----------
@app.get("/api/plan")
def plan():
    lines = run("SELECT id, code, name FROM production_line ORDER BY code")
    orders = run(
        """SELECT w.id, w.line_id, w.planned_qty, w.planned_start, w.planned_end, w.status,
                  d.code AS dept, s.style_code, so.order_no, ol.ship_date
           FROM work_order w
           JOIN routing_step rs ON rs.id = w.routing_step_id
           JOIN department d ON d.id = rs.department_id
           JOIN order_line ol ON ol.id = w.order_line_id
           JOIN style s ON s.id = ol.style_id
           JOIN sales_order so ON so.id = ol.sales_order_id
           WHERE w.status <> 'cancelled' ORDER BY w.planned_start NULLS FIRST, w.id"""
    )
    return {"lines": lines, "orders": orders}


class Assign(BaseModel):
    line_id: Optional[int] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None


@app.put("/api/plan/{wo_id}")
def assign(wo_id: int, a: Assign):
    if a.line_id:
        if not (a.planned_start and a.planned_end) or a.planned_end <= a.planned_start:
            raise HTTPException(400, "Geçerli başlangıç/bitiş girin")
        clash = run(
            """SELECT id FROM work_order WHERE line_id=%s AND id<>%s AND status<>'cancelled'
               AND planned_start < %s AND planned_end > %s""",
            (a.line_id, wo_id, a.planned_end, a.planned_start),
        )
        if clash:
            raise HTTPException(409, f"Hatta çakışma var: iş emri #{clash[0]['id']}")
    else:
        a.planned_start = a.planned_end = None
    done = run("UPDATE work_order SET line_id=%s, planned_start=%s, planned_end=%s WHERE id=%s RETURNING id",
               (a.line_id, a.planned_start, a.planned_end, wo_id))
    if not done:
        raise HTTPException(404, "İş emri bulunamadı")
    return {"ok": True}

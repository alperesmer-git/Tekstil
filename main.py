import os
import re
from datetime import datetime
from typing import Optional

import psycopg
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from psycopg import sql
from psycopg.rows import dict_row
from pydantic import BaseModel

DSN = os.getenv("DATABASE_URL", "postgresql://tekstil:tekstil@localhost:5432/tekstil")
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


def run(query, params=None):
    try:
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
    form = [
        {"name": c["column_name"], "type": c["data_type"],
         "required": c["is_nullable"] == "NO" and c["column_default"] is None,
         "options": en.get(c["column_name"])}
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
    run("UPDATE work_order SET line_id=%s, planned_start=%s, planned_end=%s WHERE id=%s",
        (a.line_id, a.planned_start, a.planned_end, wo_id))
    return {"ok": True}

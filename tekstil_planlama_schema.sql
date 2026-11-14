-- =====================================================================
-- Tekstil Üretim Planlama Sistemi - PostgreSQL Şeması (v1 taslak)
-- Modüller: 0 Çekirdek | 1 Ürün/Varyant | 2 BOM | 3 Rota/Operasyon
--           4 Kapasite/Hat | 5 Sipariş | 6 Malzeme/Lot | 7 Kesim/Pastal
--           8 Fason | 9 Üretim Takibi | 10 Kalite | 11 Planlama | 12 AI/ML
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ---------------------------------------------------------------------
-- 0. ÇEKİRDEK
-- ---------------------------------------------------------------------
CREATE TABLE tenant (                       -- çok müşterili (SaaS) veya tek kurulum için
    id            BIGSERIAL PRIMARY KEY,
    name          TEXT NOT NULL
);

CREATE TABLE app_user (
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    email         TEXT NOT NULL UNIQUE,
    full_name     TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('admin','planner','manager','operator','quality','viewer')),
    is_active     BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE unit_of_measure (
    code          TEXT PRIMARY KEY,         -- ADET, MT, KG, TOP, M2
    name          TEXT NOT NULL
);

CREATE TABLE business_partner (             -- müşteri, tedarikçi, fason atölye
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    code          TEXT NOT NULL,
    name          TEXT NOT NULL,
    is_customer   BOOLEAN NOT NULL DEFAULT FALSE,
    is_supplier   BOOLEAN NOT NULL DEFAULT FALSE,
    is_subcontractor BOOLEAN NOT NULL DEFAULT FALSE,
    erp_ref       TEXT,                     -- Logo/Netsis/SAP cari kodu
    UNIQUE (tenant_id, code)
);

CREATE TABLE working_calendar (             -- vardiya, tatil, bayram
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    name          TEXT NOT NULL
);
CREATE TABLE working_calendar_day (
    calendar_id   BIGINT NOT NULL REFERENCES working_calendar(id),
    day           DATE NOT NULL,
    is_working    BOOLEAN NOT NULL DEFAULT TRUE,
    work_minutes  INT NOT NULL DEFAULT 480,
    PRIMARY KEY (calendar_id, day)
);

-- ---------------------------------------------------------------------
-- 1. ÜRÜN / VARYANT (sezon > model > renk > beden)
-- ---------------------------------------------------------------------
CREATE TABLE season (
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    code          TEXT NOT NULL,            -- SS27, AW26
    name          TEXT NOT NULL,
    UNIQUE (tenant_id, code)
);

CREATE TABLE size_scale (                   -- beden serisi: S-M-L-XL veya 36-38-40
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    name          TEXT NOT NULL
);
CREATE TABLE size (
    id            BIGSERIAL PRIMARY KEY,
    size_scale_id BIGINT NOT NULL REFERENCES size_scale(id),
    code          TEXT NOT NULL,
    sort_order    INT NOT NULL,
    UNIQUE (size_scale_id, code)
);

CREATE TABLE color (
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    code          TEXT NOT NULL,
    name          TEXT NOT NULL,
    UNIQUE (tenant_id, code)
);

CREATE TABLE style (                        -- model
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    season_id     BIGINT REFERENCES season(id),
    customer_id   BIGINT REFERENCES business_partner(id),
    style_code    TEXT NOT NULL,
    description   TEXT,
    product_group TEXT,                     -- tişört, pantolon, gömlek...
    size_scale_id BIGINT NOT NULL REFERENCES size_scale(id),
    UNIQUE (tenant_id, style_code)
);

CREATE TABLE style_variant (                -- SKU: model x renk x beden
    id            BIGSERIAL PRIMARY KEY,
    style_id      BIGINT NOT NULL REFERENCES style(id),
    color_id      BIGINT NOT NULL REFERENCES color(id),
    size_id       BIGINT NOT NULL REFERENCES size(id),
    sku           TEXT NOT NULL UNIQUE,
    barcode       TEXT UNIQUE,
    UNIQUE (style_id, color_id, size_id)
);

-- ---------------------------------------------------------------------
-- 2. MALZEME TANIMI + BOM
-- ---------------------------------------------------------------------
CREATE TABLE material (
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    code          TEXT NOT NULL,
    name          TEXT NOT NULL,
    material_type TEXT NOT NULL CHECK (material_type IN ('fabric','yarn','trim','accessory','packaging','label')),
    uom           TEXT NOT NULL REFERENCES unit_of_measure(code),
    UNIQUE (tenant_id, code)
);

CREATE TABLE fabric_spec (                  -- sadece kumaşlara ait teknik veri
    material_id        BIGINT PRIMARY KEY REFERENCES material(id),
    composition        TEXT,                -- %95 pamuk %5 elastan
    gsm                NUMERIC(7,2),        -- gramaj
    usable_width_cm    NUMERIC(6,2),        -- kullanılabilir en
    shrink_warp_pct    NUMERIC(5,2),        -- boy çekmesi
    shrink_weft_pct    NUMERIC(5,2),        -- en çekmesi
    yarn_type          TEXT,
    knit_or_woven      TEXT CHECK (knit_or_woven IN ('knit','woven'))
);

CREATE TABLE bom (                          -- model bazlı ürün ağacı (versiyonlu)
    id            BIGSERIAL PRIMARY KEY,
    style_id      BIGINT NOT NULL REFERENCES style(id),
    version       INT NOT NULL DEFAULT 1,
    status        TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','approved','obsolete')),
    valid_from    DATE,
    UNIQUE (style_id, version)
);

CREATE TABLE bom_line (
    id                 BIGSERIAL PRIMARY KEY,
    bom_id             BIGINT NOT NULL REFERENCES bom(id),
    material_id        BIGINT NOT NULL REFERENCES material(id),
    parent_line_id     BIGINT REFERENCES bom_line(id),   -- hiyerarşi (alt montaj) için
    qty_per_unit       NUMERIC(12,4) NOT NULL,           -- birim ürün başına net tüketim
    waste_pct          NUMERIC(5,2) NOT NULL DEFAULT 0,  -- planlanan fire
    -- varyant filtreleri: NULL = tüm renk/bedenler için geçerli
    applies_color_id   BIGINT REFERENCES color(id),
    applies_size_id    BIGINT REFERENCES size(id),
    usage_note         TEXT                              -- ön beden, astar, cep...
);
CREATE INDEX ON bom_line (bom_id);

-- ---------------------------------------------------------------------
-- 3. ROTA / OPERASYON / SMV
-- ---------------------------------------------------------------------
CREATE TABLE department (
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    code          TEXT NOT NULL,            -- KESIM, DIKIM, BASKI, NAKIS, YIKAMA, UTU_PAKET
    name          TEXT NOT NULL,
    UNIQUE (tenant_id, code)
);

CREATE TABLE routing (                      -- model bazlı üretim rotası
    id            BIGSERIAL PRIMARY KEY,
    style_id      BIGINT NOT NULL REFERENCES style(id),
    version       INT NOT NULL DEFAULT 1,
    status        TEXT NOT NULL DEFAULT 'draft',
    UNIQUE (style_id, version)
);

CREATE TABLE routing_step (                 -- departman seviyesinde adım
    id                BIGSERIAL PRIMARY KEY,
    routing_id        BIGINT NOT NULL REFERENCES routing(id),
    seq               INT NOT NULL,
    department_id     BIGINT NOT NULL REFERENCES department(id),
    is_subcontractable BOOLEAN NOT NULL DEFAULT FALSE,
    total_smv         NUMERIC(8,3),         -- adım toplam SMV (operasyonlardan türetilebilir)
    UNIQUE (routing_id, seq)
);

CREATE TABLE operation (                    -- dikim operasyonları (hat dengeleme için)
    id                BIGSERIAL PRIMARY KEY,
    routing_step_id   BIGINT NOT NULL REFERENCES routing_step(id),
    seq               INT NOT NULL,
    name              TEXT NOT NULL,        -- yaka takma, kol bağlama...
    smv               NUMERIC(8,3) NOT NULL,
    machine_type      TEXT,                 -- düz makine, overlok, reçme
    required_skill_level INT DEFAULT 1,
    UNIQUE (routing_step_id, seq)
);

-- ---------------------------------------------------------------------
-- 4. KAPASİTE / HAT / MAKİNE / OPERATÖR
-- ---------------------------------------------------------------------
CREATE TABLE production_line (              -- bant, kesim masası, baskı hattı...
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    department_id BIGINT NOT NULL REFERENCES department(id),
    code          TEXT NOT NULL,
    name          TEXT NOT NULL,
    calendar_id   BIGINT REFERENCES working_calendar(id),
    operator_count INT,
    default_efficiency_pct NUMERIC(5,2) NOT NULL DEFAULT 60,
    UNIQUE (tenant_id, code)
);

CREATE TABLE machine (
    id            BIGSERIAL PRIMARY KEY,
    line_id       BIGINT REFERENCES production_line(id),
    machine_type  TEXT NOT NULL,
    asset_code    TEXT UNIQUE,
    status        TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE operator (
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    full_name     TEXT NOT NULL,
    home_line_id  BIGINT REFERENCES production_line(id),
    is_active     BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE operator_skill (               -- operatör x operasyon tipi verimliliği
    operator_id   BIGINT NOT NULL REFERENCES operator(id),
    machine_type  TEXT NOT NULL,
    skill_level   INT NOT NULL,
    avg_efficiency_pct NUMERIC(5,2),
    PRIMARY KEY (operator_id, machine_type)
);

CREATE TABLE changeover_time (              -- model değişim süreleri (çizelgeleme için kritik)
    id            BIGSERIAL PRIMARY KEY,
    line_id       BIGINT NOT NULL REFERENCES production_line(id),
    from_product_group TEXT,                -- NULL = herhangi
    to_product_group   TEXT,
    minutes       INT NOT NULL
);

-- ---------------------------------------------------------------------
-- 5. SİPARİŞ
-- ---------------------------------------------------------------------
CREATE TABLE sales_order (
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    order_no      TEXT NOT NULL,
    customer_id   BIGINT NOT NULL REFERENCES business_partner(id),
    order_date    DATE NOT NULL DEFAULT CURRENT_DATE,
    status        TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('draft','open','in_production','shipped','closed','cancelled')),
    erp_ref       TEXT,
    UNIQUE (tenant_id, order_no)
);

CREATE TABLE order_line (                   -- sipariş kalemi = model + teslim tarihi
    id               BIGSERIAL PRIMARY KEY,
    sales_order_id   BIGINT NOT NULL REFERENCES sales_order(id),
    style_id         BIGINT NOT NULL REFERENCES style(id),
    ship_date        DATE NOT NULL,          -- yükleme/termin
    priority         INT NOT NULL DEFAULT 5,
    bom_id           BIGINT REFERENCES bom(id),
    routing_id       BIGINT REFERENCES routing(id),
    unit_price       NUMERIC(12,4)
);

CREATE TABLE order_line_qty (               -- renk-beden matrisi
    order_line_id    BIGINT NOT NULL REFERENCES order_line(id),
    variant_id       BIGINT NOT NULL REFERENCES style_variant(id),
    qty_ordered      INT NOT NULL CHECK (qty_ordered >= 0),
    qty_tolerance_pct NUMERIC(5,2) DEFAULT 0,
    PRIMARY KEY (order_line_id, variant_id)
);

-- ---------------------------------------------------------------------
-- 6. MALZEME TEDARİK / STOK / LOT
-- ---------------------------------------------------------------------
CREATE TABLE purchase_order (
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    supplier_id   BIGINT NOT NULL REFERENCES business_partner(id),
    po_no         TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'open',
    UNIQUE (tenant_id, po_no)
);
CREATE TABLE purchase_order_line (
    id               BIGSERIAL PRIMARY KEY,
    purchase_order_id BIGINT NOT NULL REFERENCES purchase_order(id),
    material_id      BIGINT NOT NULL REFERENCES material(id),
    color_id         BIGINT REFERENCES color(id),
    qty              NUMERIC(14,3) NOT NULL,
    promised_date    DATE,                  -- tedarikçi söz tarihi
    received_date    DATE                   -- gerçekleşen (tedarik gecikme analizi)
);

CREATE TABLE material_lot (                 -- kumaş partisi / ton takibi
    id             BIGSERIAL PRIMARY KEY,
    material_id    BIGINT NOT NULL REFERENCES material(id),
    color_id       BIGINT REFERENCES color(id),
    lot_no         TEXT NOT NULL,           -- boyahane parti no
    shade_group    TEXT,                    -- ton grubu (A, B, C)
    roll_count     INT,
    qty_received   NUMERIC(14,3) NOT NULL,
    actual_width_cm NUMERIC(6,2),
    actual_gsm     NUMERIC(7,2),
    measured_shrink_warp_pct NUMERIC(5,2),
    measured_shrink_weft_pct NUMERIC(5,2),
    purchase_order_line_id BIGINT REFERENCES purchase_order_line(id),
    received_at    DATE,
    UNIQUE (material_id, lot_no)
);

CREATE TABLE stock_movement (
    id             BIGSERIAL PRIMARY KEY,
    material_id    BIGINT NOT NULL REFERENCES material(id),
    lot_id         BIGINT REFERENCES material_lot(id),
    movement_type  TEXT NOT NULL CHECK (movement_type IN ('receipt','issue_cutting','issue_subcontract','return','adjustment')),
    qty            NUMERIC(14,3) NOT NULL,   -- + giriş, - çıkış
    ref_table      TEXT,
    ref_id         BIGINT,
    moved_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE material_requirement (         -- MRP çıktısı: sipariş bazlı ihtiyaç
    id             BIGSERIAL PRIMARY KEY,
    order_line_id  BIGINT NOT NULL REFERENCES order_line(id),
    material_id    BIGINT NOT NULL REFERENCES material(id),
    color_id       BIGINT REFERENCES color(id),
    net_qty        NUMERIC(14,3) NOT NULL,
    gross_qty      NUMERIC(14,3) NOT NULL,   -- fire dahil
    required_by    DATE,
    covered_qty    NUMERIC(14,3) NOT NULL DEFAULT 0
);

-- ---------------------------------------------------------------------
-- 7. KESİM / PASTAL
-- ---------------------------------------------------------------------
CREATE TABLE marker (                       -- pastal (CAD çıktısından içe aktarılır)
    id              BIGSERIAL PRIMARY KEY,
    style_id        BIGINT NOT NULL REFERENCES style(id),
    fabric_material_id BIGINT NOT NULL REFERENCES material(id),
    marker_name     TEXT NOT NULL,
    length_m        NUMERIC(8,3) NOT NULL,
    width_cm        NUMERIC(6,2) NOT NULL,
    efficiency_pct  NUMERIC(5,2),            -- pastal verimi
    source          TEXT DEFAULT 'cad_import' -- Lectra/Gerber/manuel
);
CREATE TABLE marker_size_ratio (            -- pastal içindeki beden dağılımı
    marker_id   BIGINT NOT NULL REFERENCES marker(id),
    size_id     BIGINT NOT NULL REFERENCES size(id),
    pieces      INT NOT NULL,
    PRIMARY KEY (marker_id, size_id)
);

CREATE TABLE cutting_order (
    id              BIGSERIAL PRIMARY KEY,
    order_line_id   BIGINT NOT NULL REFERENCES order_line(id),
    marker_id       BIGINT REFERENCES marker(id),
    color_id        BIGINT NOT NULL REFERENCES color(id),
    lot_id          BIGINT REFERENCES material_lot(id),
    planned_plies   INT,
    actual_plies    INT,
    fabric_used_m   NUMERIC(10,3),
    end_loss_m      NUMERIC(10,3),           -- uç fire
    planned_date    DATE,
    status          TEXT NOT NULL DEFAULT 'planned'
);

-- ---------------------------------------------------------------------
-- 8. FASON
-- ---------------------------------------------------------------------
CREATE TABLE subcontract_capacity (
    subcontractor_id BIGINT NOT NULL REFERENCES business_partner(id),
    department_id    BIGINT NOT NULL REFERENCES department(id),
    daily_capacity   INT NOT NULL,
    price_per_unit   NUMERIC(12,4),
    PRIMARY KEY (subcontractor_id, department_id)
);

CREATE TABLE subcontract_order (
    id               BIGSERIAL PRIMARY KEY,
    order_line_id    BIGINT NOT NULL REFERENCES order_line(id),
    subcontractor_id BIGINT NOT NULL REFERENCES business_partner(id),
    department_id    BIGINT NOT NULL REFERENCES department(id),
    planned_out_date DATE,
    planned_back_date DATE,
    unit_price       NUMERIC(12,4),
    status           TEXT NOT NULL DEFAULT 'planned'
);
CREATE TABLE subcontract_shipment (         -- sevk ve dönüş irsaliyeleri
    id               BIGSERIAL PRIMARY KEY,
    subcontract_order_id BIGINT NOT NULL REFERENCES subcontract_order(id),
    direction        TEXT NOT NULL CHECK (direction IN ('out','in')),
    waybill_no       TEXT,
    shipped_at       DATE NOT NULL
);
CREATE TABLE subcontract_shipment_line (
    shipment_id      BIGINT NOT NULL REFERENCES subcontract_shipment(id),
    variant_id       BIGINT NOT NULL REFERENCES style_variant(id),
    qty              INT NOT NULL,
    defect_qty       INT NOT NULL DEFAULT 0,   -- dönüşte hatalı
    PRIMARY KEY (shipment_id, variant_id)
);

-- ---------------------------------------------------------------------
-- 9. ÜRETİM TAKİBİ (iş emri + sahadan veri)
-- ---------------------------------------------------------------------
CREATE TABLE work_order (                   -- order_line x rota adımı
    id               BIGSERIAL PRIMARY KEY,
    order_line_id    BIGINT NOT NULL REFERENCES order_line(id),
    routing_step_id  BIGINT NOT NULL REFERENCES routing_step(id),
    line_id          BIGINT REFERENCES production_line(id),     -- NULL ise fason
    subcontract_order_id BIGINT REFERENCES subcontract_order(id),
    planned_qty      INT NOT NULL,
    planned_start    TIMESTAMPTZ,
    planned_end      TIMESTAMPTZ,
    actual_start     TIMESTAMPTZ,
    actual_end       TIMESTAMPTZ,
    status           TEXT NOT NULL DEFAULT 'planned'
                     CHECK (status IN ('planned','released','running','done','blocked','cancelled'))
);
CREATE INDEX ON work_order (line_id, planned_start);

CREATE TABLE work_order_variant_qty (       -- iş emri bazında renk-beden adedi
    work_order_id    BIGINT NOT NULL REFERENCES work_order(id),
    variant_id       BIGINT NOT NULL REFERENCES style_variant(id),
    qty_planned      INT NOT NULL,
    PRIMARY KEY (work_order_id, variant_id)
);

CREATE TABLE production_log (               -- tablet/barkoddan gelen adet girişi
    id               BIGSERIAL PRIMARY KEY,
    client_uuid      UUID NOT NULL UNIQUE,   -- çevrimdışı kayıtta tekrar gönderimi önler
    work_order_id    BIGINT NOT NULL REFERENCES work_order(id),
    variant_id       BIGINT REFERENCES style_variant(id),
    operator_id      BIGINT REFERENCES operator(id),
    qty_good         INT NOT NULL DEFAULT 0,
    logged_at        TIMESTAMPTZ NOT NULL,   -- cihaz saati
    synced_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON production_log (work_order_id, logged_at);

CREATE TABLE downtime_log (                 -- duruş kayıtları
    id               BIGSERIAL PRIMARY KEY,
    line_id          BIGINT NOT NULL REFERENCES production_line(id),
    work_order_id    BIGINT REFERENCES work_order(id),
    reason           TEXT NOT NULL CHECK (reason IN ('machine_breakdown','material_wait','changeover','no_operator','power','other')),
    started_at       TIMESTAMPTZ NOT NULL,
    ended_at         TIMESTAMPTZ
);

CREATE TABLE line_balance (                 -- hat dengeleme: istasyon-operatör-operasyon
    id               BIGSERIAL PRIMARY KEY,
    work_order_id    BIGINT NOT NULL REFERENCES work_order(id),
    station_no       INT NOT NULL,
    operation_id     BIGINT NOT NULL REFERENCES operation(id),
    operator_id      BIGINT REFERENCES operator(id),
    target_per_hour  NUMERIC(8,2)
);

-- ---------------------------------------------------------------------
-- 10. KALİTE
-- ---------------------------------------------------------------------
CREATE TABLE defect_type (
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    code          TEXT NOT NULL,
    name          TEXT NOT NULL,
    category      TEXT CHECK (category IN ('fabric','sewing','print','wash','finishing','measurement')),
    UNIQUE (tenant_id, code)
);

CREATE TABLE inspection (
    id            BIGSERIAL PRIMARY KEY,
    work_order_id BIGINT REFERENCES work_order(id),
    lot_id        BIGINT REFERENCES material_lot(id),     -- kumaş kabul kontrolü için
    stage         TEXT NOT NULL CHECK (stage IN ('incoming_fabric','inline','endline','final','subcontract_return')),
    inspected_qty INT,
    inspected_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    inspector_id  BIGINT REFERENCES app_user(id)
);
CREATE TABLE inspection_defect (
    inspection_id BIGINT NOT NULL REFERENCES inspection(id),
    defect_type_id BIGINT NOT NULL REFERENCES defect_type(id),
    variant_id    BIGINT REFERENCES style_variant(id),
    qty           INT NOT NULL,
    disposition   TEXT CHECK (disposition IN ('repair','second_quality','scrap')),
    PRIMARY KEY (inspection_id, defect_type_id, variant_id)
);

-- ---------------------------------------------------------------------
-- 11. PLANLAMA (optimizasyon çıktıları, onay akışı)
-- ---------------------------------------------------------------------
CREATE TABLE plan_scenario (
    id            BIGSERIAL PRIMARY KEY,
    tenant_id     BIGINT NOT NULL REFERENCES tenant(id),
    name          TEXT NOT NULL,
    generated_by  TEXT NOT NULL CHECK (generated_by IN ('manual','rule_based','ortools')),
    status        TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','proposed','approved','rejected','superseded')),
    objective_json JSONB,                    -- ağırlıklar: gecikme, changeover, vb.
    created_by    BIGINT REFERENCES app_user(id),
    approved_by   BIGINT REFERENCES app_user(id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE plan_assignment (              -- senaryoya ait iş emri -> hat/zaman ataması
    id             BIGSERIAL PRIMARY KEY,
    scenario_id    BIGINT NOT NULL REFERENCES plan_scenario(id) ON DELETE CASCADE,
    work_order_id  BIGINT NOT NULL REFERENCES work_order(id),
    line_id        BIGINT REFERENCES production_line(id),
    start_at       TIMESTAMPTZ NOT NULL,
    end_at         TIMESTAMPTZ NOT NULL,
    is_locked      BOOLEAN NOT NULL DEFAULT FALSE,   -- planlamacı sabitledi
    CHECK (end_at > start_at)
);
-- aynı hatta aynı senaryoda çakışma olmasın
ALTER TABLE plan_assignment ADD CONSTRAINT no_line_overlap
    EXCLUDE USING gist (scenario_id WITH =, line_id WITH =, tstzrange(start_at, end_at) WITH &&)
    WHERE (line_id IS NOT NULL);

-- ---------------------------------------------------------------------
-- 12. AI / ML DESTEK TABLOLARI
-- ---------------------------------------------------------------------
CREATE TABLE efficiency_history (           -- gerçekleşen verim: model x hat x gün
    id             BIGSERIAL PRIMARY KEY,
    line_id        BIGINT NOT NULL REFERENCES production_line(id),
    style_id       BIGINT NOT NULL REFERENCES style(id),
    day            DATE NOT NULL,
    produced_qty   INT NOT NULL,
    earned_minutes NUMERIC(10,2) NOT NULL,   -- adet x SMV
    available_minutes NUMERIC(10,2) NOT NULL,
    efficiency_pct NUMERIC(5,2) GENERATED ALWAYS AS
        (CASE WHEN available_minutes > 0 THEN earned_minutes / available_minutes * 100 END) STORED,
    UNIQUE (line_id, style_id, day)
);

CREATE TABLE actual_waste_history (         -- gerçekleşen kumaş fire oranı
    id             BIGSERIAL PRIMARY KEY,
    style_id       BIGINT NOT NULL REFERENCES style(id),
    material_id    BIGINT NOT NULL REFERENCES material(id),
    planned_waste_pct NUMERIC(5,2),
    actual_waste_pct  NUMERIC(5,2),
    cutting_order_id BIGINT REFERENCES cutting_order(id)
);

CREATE TABLE delivery_prediction (          -- termin tahminleri (kural tabanlı ve ML)
    id             BIGSERIAL PRIMARY KEY,
    order_line_id  BIGINT NOT NULL REFERENCES order_line(id),
    method         TEXT NOT NULL CHECK (method IN ('rule_based','ml')),
    model_version  TEXT,
    predicted_finish DATE NOT NULL,
    delay_probability NUMERIC(4,3),
    predicted_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    actual_finish  DATE                      -- sonradan doldurulur, model başarısını ölçmek için
);

CREATE TABLE assistant_audit_log (          -- LLM asistanı çağrıları (tool calling denetimi)
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT REFERENCES app_user(id),
    question      TEXT NOT NULL,
    tool_calls    JSONB,
    answer        TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

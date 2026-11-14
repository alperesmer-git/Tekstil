# Tekstil – Yapay Zeka Destekli Üretim Planlama Yazılımı

Klasik üretim takip kurallarını (ERP/MRP) yapay zeka tabanlı tahminleme ve optimizasyon algoritmalarıyla birleştiren, tekstil sektörünün dinamik yapısına (renk-beden varyantları, fire oranları, fason takibi) uygun bir üretim planlama sistemi.

> **Durum:** Veritabanı şeması (v1 taslak) ve 1. Faz'ın yerel web arayüzü (Plan Panosu + Veri ekranı) hazır. 2. ve 3. Faz yol haritasına göre geliştirilecektir.

---

## 1. Sektörel Veri Mimarisi ve Temel Modüller

Yapay zekanın doğru çalışabilmesi için öncelikle temiz bir veri tabanı altyapısı kurulmalıdır.

- **Ürün Ağacı (BOM) ve Varyant Yönetimi:** Kumaş gramajı, iplik cinsi, aksesuarlar ile renk-beden matrislerini tutan veri yapısı.
- **Operasyon ve Rota Tanımları:** Kesim, dikim, baskı/nakış, yıkama ve ütü-paket departmanlarının standart süreleri (SMV – Standart Dakika Değeri).
- **Kapasite ve Makine Parkuru:** Bant sayısı, operatör verimliliği ve fason atölyelerin günlük üretim kapasiteleri.
- **Sipariş ve Termin Takibi:** Müşteri siparişlerinin yükleme tarihleri ve hammadde tedarik süreleri (kumaş/aksesuar geliş tarihleri).

## 2. Yapay Zeka ve Optimizasyon Yetenekleri

Yazılımı standart bir Excel veya ERP programından ayıran kısım yapay zeka katmanıdır.

- **Akıllı Çizelgeleme (AI Scheduling):** Google OR-Tools veya OptaPlanner ile en az bant değişimi ve en yüksek verimlilikle iş emirlerinin bantlara otomatik atanması.
- **Termin ve Gecikme Tahmini:** Geçmiş üretim verilerini (makine arızaları, fason gecikmeleri, kumaş hataları) analiz eden makine öğrenmesi modelleriyle siparişin gerçek bitiş tarihinin tahmini.
- **Fire ve Kumaş Optimizasyonu:** Pastal planlama ve kesim firelerinin geçmiş verilere göre hesaplanması; sipariş bazlı gerçek maliyet ve kumaş ihtiyacı tahmini.
- **Doğal Dil Asistanı (LLM Entegrasyonu):** Üretim müdürlerinin "X müşterisinin siparişi yetişir mi?" veya "3 numaralı bantta darboğaz var mı?" gibi sorularını anlık verilerle yanıtlayan sohbet arayüzü.

## 3. Önerilen Teknoloji Yığını

| Katman | Teknoloji | Not |
|---|---|---|
| Arayüz (Frontend) | React / Next.js | Gantt şemaları ve sürükle-bırak planlama ekranları |
| Arka Uç ve Yapay Zeka | Python (FastAPI veya Django) | Veri işleme ve optimizasyon algoritmaları |
| Optimizasyon | Google OR-Tools / OptaPlanner | Akıllı çizelgeleme |
| Veritabanı | PostgreSQL (veya Supabase) | Karmaşık ürün ağaçları ve stok hareketleri |

## 4. Geliştirme Yol Haritası

| Aşama | Odak Noktası | Çıktı |
|---|---|---|
| **1. Faz (MVP)** | Sipariş girişi, ürün ağacı (BOM) ve manuel bant planlama ekranı | Çalışan temel üretim takip sistemi |
| **2. Faz** | Bantlardan anlık veri toplama (tablet/barkod ile adet girişi) | Gerçek zamanlı verimlilik ve darboğaz tespiti |
| **3. Faz** | Yapay zeka tabanlı otomatik iş emri atama ve termin tahmini | Tam otonom akıllı planlama asistanı |

---

## 5. Veritabanı Şeması

Şema dosyası: [`tekstil_planlama_schema.sql`](./tekstil_planlama_schema.sql) (PostgreSQL, v1 taslak)

### Modüller

| # | Modül | Başlıca tablolar |
|---|---|---|
| 0 | Çekirdek | `tenant`, `app_user`, `unit_of_measure`, `business_partner`, `working_calendar`, `working_calendar_day` |
| 1 | Ürün / Varyant | `season`, `size_scale`, `size`, `color`, `style`, `style_variant` |
| 2 | Malzeme + BOM | `material`, `fabric_spec`, `bom`, `bom_line` |
| 3 | Rota / Operasyon / SMV | `department`, `routing`, `routing_step`, `operation` |
| 4 | Kapasite / Hat / Makine | `production_line`, `machine`, `operator`, `operator_skill`, `changeover_time` |
| 5 | Sipariş | `sales_order`, `order_line`, `order_line_qty` |
| 6 | Malzeme Tedarik / Stok / Lot | `purchase_order`, `purchase_order_line`, `material_lot`, `stock_movement`, `material_requirement` |
| 7 | Kesim / Pastal | `marker`, `marker_size_ratio`, `cutting_order` |
| 8 | Fason | `subcontract_capacity`, `subcontract_order`, `subcontract_shipment`, `subcontract_shipment_line` |
| 9 | Üretim Takibi | `work_order`, `work_order_variant_qty`, `production_log`, `downtime_log`, `line_balance` |
| 10 | Kalite | `defect_type`, `inspection`, `inspection_defect` |
| 11 | Planlama | `plan_scenario`, `plan_assignment` |
| 12 | AI / ML Destek | `efficiency_history`, `actual_waste_history`, `delivery_prediction`, `assistant_audit_log` |

### Tasarım Kararları

- **Varyant hiyerarşisi:** `season` → `style` (model) → `style_variant` (model × renk × beden = SKU). Renk-beden matrisi `order_line_qty` ve `work_order_variant_qty` tablolarında tutulur.
- **Versiyonlu BOM ve rota:** `bom` ve `routing` modele bağlıdır ve `version` / `status` alanlarına sahiptir. `bom_line` üzerindeki `applies_color_id` / `applies_size_id` alanları `NULL` ise satır tüm renk/bedenler için geçerlidir. Planlanan fire `waste_pct` ile tutulur.
- **SMV:** Departman seviyesindeki adım (`routing_step.total_smv`) ve dikim operasyonları (`operation.smv`, hat dengeleme için) ayrı tutulur.
- **Fason:** `routing_step.is_subcontractable` ile fasona gidebilen adımlar işaretlenir; `work_order.line_id` boş ise iş emri fasondadır. Sevk/dönüş irsaliyeleri ve dönüşteki hatalı adet `subcontract_shipment*` tablolarında izlenir.
- **Kumaş lot takibi:** `material_lot` üzerinde ton grubu, gerçek en/gramaj ve ölçülen çekme değerleri tutulur; kesim emirleri lota bağlanabilir.
- **Çevrimdışı veri toplama:** `production_log.client_uuid` (UNIQUE) tablet/barkod cihazlarının çevrimdışı kayıtlarında tekrar gönderimi engeller; `logged_at` (cihaz saati) ve `synced_at` ayrı tutulur.
- **Planlama senaryoları:** Çizelge çıktıları `plan_scenario` / `plan_assignment` altında tutulur (`manual`, `rule_based`, `ortools`). `btree_gist` eklentisi ve `EXCLUDE` kısıtı ile aynı senaryoda aynı hatta zaman çakışması veritabanı seviyesinde engellenir. `is_locked` ile planlamacı atamayı sabitleyebilir.
- **ML geri besleme:** `delivery_prediction.actual_finish` sonradan doldurularak model başarısı ölçülür; `efficiency_history` ve `actual_waste_history` modellerin eğitim verisini oluşturur.
- **LLM denetimi:** Asistan çağrıları ve araç kullanımları `assistant_audit_log` tablosunda kayıt altına alınır.
- **Çok kiracılık:** Ana tanım tabloları `tenant_id` taşır (SaaS veya tek kurulum).
- **ERP entegrasyonu:** `business_partner.erp_ref` ve `sales_order.erp_ref` alanları Logo/Netsis/SAP eşleştirmesi için ayrılmıştır.

### Kurulum

```bash
createdb tekstil
psql -d tekstil -f tekstil_planlama_schema.sql
```

> `btree_gist` eklentisini kurabilmek için ilgili veritabanında yeterli yetkiye sahip olunmalıdır.

### Bilinen Eksikler (v1 taslak)

- `routing.status`, `purchase_order.status`, `cutting_order.status`, `subcontract_order.status` alanlarında henüz `CHECK` kısıtı yok.
- Varyant ve sorgu performansı için ek indeksler (ör. `order_line(ship_date)`, `stock_movement(material_id, moved_at)`) gerçek veriyle ölçüm sonrası eklenecek.
- Migration aracı (Alembic vb.) henüz seçilmedi; şema şimdilik tek SQL dosyasıdır.

## 6. Yerel Web Arayüzü

Şemaya bağlı, yerel çalışan bir web arayüzü bulunur (FastAPI + tek sayfalık HTML/JavaScript). Arayüz tamamen Türkçedir.

- **Plan Panosu:** Hatlar için 14 günlük zaman çizelgesi; iş emirlerini hatlara ve zamana atama, aynı hatta çakışma kontrolü.
- **Veri:** Şemadaki tüm tablolar için Türkçe etiketli liste, kayıt ekleme ve silme.

### Çalıştırma

**Gereksinimler:** PostgreSQL 14+ ve Python 3.10–3.13 (Python 3.15 gibi çok yeni sürümlerde bazı paketler henüz derlenemeyebilir; 3.13 önerilir).

**Seçenek A – Docker ile**

```bash
docker compose up -d
cd app
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1   |   Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

**Seçenek B – Yerel PostgreSQL ile (Docker olmadan)**

```bash
createdb -U postgres tekstil
psql -U postgres -d tekstil -f tekstil_planlama_schema.sql -f db/seed.sql
cd app
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1   |   Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
# Windows PowerShell:  $env:DATABASE_URL = "postgresql://postgres:SIFRE@localhost:5432/tekstil"
# Linux/macOS:         export DATABASE_URL="postgresql://postgres:SIFRE@localhost:5432/tekstil"
python -m uvicorn main:app --reload
```

Ardından tarayıcıda `http://localhost:8000` adresini açın. Veritabanı bağlantısı `DATABASE_URL` ortam değişkeniyle verilir; şifreyi hiçbir dosyaya yazmayın. Varsayılan değer Docker kurulumuyla uyumludur (`tekstil:tekstil@localhost:5432/tekstil`).

### Sınırlamalar (v1)

Kullanıcı girişi yok; kayıt düzenleme yok (silip yeniden eklenir, iş emri planı hariç); bağlı alanlar numara olarak elle girilir; sürükle-bırak yok. Ayrıntılar için kılavuzlara bakın.

## 7. Depo Yapısı

```
Tekstil/
├── README.md
├── tekstil_planlama_schema.sql   # PostgreSQL şeması (v1 taslak)
├── docker-compose.yml            # PostgreSQL + şema + örnek veri
├── db/
│   └── seed.sql                  # Örnek veri
├── app/
│   ├── main.py                   # FastAPI arka uç
│   ├── requirements.txt
│   └── static/
│       ├── index.html            # Web arayüzü
│       └── labels.js             # Türkçe etiket sözlüğü
└── docs/
    ├── kullanici-kilavuzu.md     # Ekran ve kurulum kılavuzu
    └── musteri-kilavuzu.md       # Modüller ve süreç akışı
```

## 8. Dokümantasyon

- [Kullanıcı Kılavuzu](docs/kullanici-kilavuzu.md): uygulamayı başlatma, ekranların kullanımı, hata çözümleri, yedekleme.
- [Müşteri Kullanım Kılavuzu](docs/musteri-kilavuzu.md): modüllerin kısa açıklaması ve süreçlerin hangi sırayla kullanılacağı.

---

## Lisans

Henüz belirlenmedi.

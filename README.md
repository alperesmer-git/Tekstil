# Tekstil – Yerel Web Arayüzü

## Çalıştırma
1. Veritabanı (şema + örnek veri otomatik yüklenir):
   `docker compose up -d`
2. Arayüz ve API:
   ```
   cd app
   python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```
3. Tarayıcıda `http://localhost:8000` adresini açın.

Veritabanını sıfırlamak için: `docker compose down -v && docker compose up -d`

Docker kullanmıyorsanız: `createdb tekstil`, ardından `psql -d tekstil -f tekstil_planlama_schema.sql -f db/seed.sql`
ve `DATABASE_URL=postgresql://kullanici:sifre@localhost:5432/tekstil` ortam değişkenini ayarlayın.

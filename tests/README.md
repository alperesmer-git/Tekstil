# Tekstil Planlama – Test Sistemi

Testler **gerçek bir PostgreSQL** üzerinde çalışır. Canlı veritabanınıza (`tekstil`) dokunmaz; yalnızca
`tekstil_test` adlı ayrı bir veritabanını her çalıştırmada silip şema + örnek veriyle yeniden oluşturur.
Her testten önce tablolar boşaltılıp örnek veri yeniden yüklenir, yani testler birbirinden bağımsızdır.

## Kurulum (bir kez)

```powershell
cd C:\tekstil-web\tekstil-web
python -m venv .venv-test
.venv-test\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m playwright install chromium     # yalnızca arayüz (e2e) testleri için
```

## Çalıştırma

```powershell
$env:TEST_ADMIN_URL = "postgresql://postgres:SIFRENIZ@localhost:5432/postgres"

python -m pytest -m "not e2e"     # hızlı: şema + API testleri (tarayıcı gerekmez)
python -m pytest                  # hepsi (arayüz testleri dahil)
python -m pytest -m e2e           # yalnızca tarayıcı testleri
python -m pytest tests\test_api_plan.py -k cakisma    # tek dosya / anahtar kelime
```

`TEST_ADMIN_URL`, `postgres` yönetici veritabanına bağlanan adrestir; test veritabanını oluşturmak için
yetkili bir kullanıcı gerekir (ör. `postgres`). Şifrede `@ : /` gibi karakterler varsa URL kodlaması yapın.

## Senaryo matrisi

| Dosya | Neyi doğrular |
|---|---|
| `test_schema.py` | 54 tablo, örnek veri; rol/durum kısıtları; e-posta ve hat kodu benzersizliği; yabancı anahtarlar; varsayılan değerler; plan atamasında aynı hat/aynı zaman çakışma engeli, bitişik aralık, senaryo silince atamaların silinmesi |
| `test_enums_and_labels.py` | Seçim listesi ayrıştırması (text/varchar/kesme işaretli/liste olmayan kısıtlar); şemadaki **tüm** kısıtların API'de seçenek olarak gelmesi; **her** tablo, sütun, veri tipi ve seçenek değerinin Türkçe etiketi olması (şemaya yeni tablo/sütun eklenip etiket unutulursa test kırılır) |
| `test_api_data.py` | Tablo listesi ve form meta verisi; limit; sıralama; 6 rolle ekleme; boş alan = varsayılan; evet/hayır; bilinmeyen alan; Türkçe karakter/tırnak; tarih; tüm hata mesajları (boş kayıt, geçersiz değer, tekrar, bağlı kayıt, zorunlu alan, biçim, tarih); silme ve bağımlılık; kimliksiz tablo; bilinmeyen/kötü niyetli tablo adları ve SQL enjeksiyonu |
| `test_api_plan.py` | Pano verisi ve sıralaması; atama; çakışma (tam/kısmi/bitişik/kendi aralığı/iptal edilen iş emri); hatalı aralık; olmayan hat/iş emri; geçersiz tarih; plan kaldırma; art arda iş |
| `test_workflows.py` | Siparişten plana uçtan uca akış; iki siparişin aynı bantta sırayla planlanması; tekrarlı sipariş no; silme sırası; yeni model tanımlama sırası |
| `test_static_ui.py` | Ana sayfa ve statik dosyaların sunulması |
| `test_e2e_ui.py` | Tarayıcıda: sekmeler, pano, atama, çakışma uyarısı, plan kaldırma, tablo/alan Türkçe adları, Rol ve durum seçim listeleri, kayıt ekleme/silme/iptal, hata uyarıları, JavaScript hatası olmaması |

## Notlar

- Test sırasında bulunan bir davranış düzeltildi: var olmayan bir iş emrine atama yapmak artık `404` döndürür
  (önceden sessizce başarılı görünüyordu).
- Şemayı değiştirirseniz `tekstil_planlama_schema.sql` ve gerekirse `db/seed.sql` güncelleyin; tablo sayısı
  (`test_schema.py`, `test_api_data.py`, `test_e2e_ui.py`) ve örnek veri numaralarına bağlı testler de
  güncellenmelidir.
- Testler örnek verideki numaralara dayanır (hat 1-3, iş emri 1-3, model 1-2). `seed.sql` değişirse ilgili
  testleri uyarlayın.

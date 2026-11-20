# Tekstil Planlama – Kullanıcı Kılavuzu

Yerel web arayüzü · Sürüm 1

## 1. Genel Bakış

Tekstil Planlama; sipariş, model, ürün ağacı (BOM), rota, hat ve iş emri bilgilerini PostgreSQL veritabanında tutan ve iş emirlerini bantlara manuel olarak planlamanızı sağlayan bir web uygulamasıdır. Uygulama bilgisayarınızda yerel olarak çalışır; verileriniz yalnızca kendi PostgreSQL veritabanınızda saklanır.

Ekranın solunda süreçlere göre gruplanmış bir **menü** bulunur. Bir grubun başlığına tıklayınca altındaki ekranlar açılır:

| Bölüm | Gruplar |
|---|---|
| **Süreçler** | Planlama (Plan Panosu dahil), Sipariş, Depo ve Satın Alma, Kesim, Üretim, Fason, Kalite |
| **Tanımlar** | Ürün ve Model, Malzeme ve Ürün Ağacı, Rota ve Operasyon, Hat ve Kapasite, Temel Tanımlar |
| **Analiz** | Yapay Zeka ve Analiz |

**Plan Panosu** iş emirlerini hatlara atar ve zaman çizelgesinde gösterir. Diğer tüm menü öğeleri (ör. *Siparişler*, *Malzeme lotları*) ilgili tabloya kayıt ekler, listeler ve siler. Üstteki başlık, bulunduğunuz yeri gösterir (ör. *Sipariş › Siparişler*). Telefon ve dar ekranlarda menü ☰ düğmesiyle açılır.

## 2. Uygulamayı Başlatma

Önce PostgreSQL'in çalıştığından emin olun (Windows'ta kurulumdan sonra genellikle otomatik başlar). Ardından PowerShell'de:

```powershell
cd C:\tekstil-web\tekstil-web\app
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
$env:DATABASE_URL = "postgresql://postgres:SIFRENIZ@localhost:5432/tekstil"
python -m uvicorn main:app --reload
```

Terminalde `Uvicorn running on http://127.0.0.1:8000` satırını gördüğünüzde tarayıcıda **http://localhost:8000** adresini açın.

**Kapatmak için:** terminalde Ctrl+C. Her yeni terminal penceresinde etkinleştirme ve `DATABASE_URL` adımlarını yeniden yapmanız gerekir.

## 3. Plan Panosu

### 3.1 Zaman çizelgesi

Her üretim hattı (bant, kesim masası vb.) bir satırdır. Ekran **bugünden başlayarak 14 günü** gösterir. Hatta atanmış her iş emri, planlanan başlangıç ve bitişine göre mavi bir çubuk olarak çizilir; çubukta iş emri numarası ve model kodu yazar, üzerine geldiğinizde sipariş no, model ve adet görünür.

> 14 günlük aralığın dışında kalan planlar çizelgede görünmez, ancak aşağıdaki listede yer almaya devam eder.

### 3.2 İş emrini hatta atama

1. Bir çubuğa ya da aşağıdaki listede bir iş emri satırına tıklayın.
2. **Hat** listesinden hattı seçin.
3. **Başlangıç** ve **Bitiş** alanlarına tarih ve saat girin. Yeni bir iş emri seçtiğinizde başlangıç olarak o anki saat, bitiş olarak 8 saat sonrası önerilir.
4. **Kaydet** düğmesine basın.

### 3.3 Çakışma kontrolü

Seçtiğiniz hatta aynı zaman aralığına denk gelen başka bir iş emri varsa kayıt yapılmaz ve *"Hatta çakışma var: iş emri #3"* gibi bir uyarı çıkar. Başka bir saat aralığı ya da hat seçin. Bitiş zamanı başlangıçtan önce ya da eşitse de kayıt reddedilir.

### 3.4 Planı kaldırma

İş emrini seçip **Planı kaldır** düğmesine basarsanız hat, başlangıç ve bitiş bilgileri silinir; iş emri atanmamış duruma döner. İş emrinin kendisi silinmez.

### 3.5 İş emri listesi

Çizelgenin altındaki tablo iptal edilmemiş tüm iş emirlerini gösterir: iş emri no, sipariş, model, departman, adet, termin (yükleme tarihi), hat, planlanan başlangıç ve bitiş. Hatta atanmamış iş emirlerinde hat sütununda **—** görünür.

## 4. Kayıt Ekranları

### 4.1 Tablo seçme ve listeleme

Sol menüden grubu açıp ekranı seçin (ör. *Ürün ve Model › Modeller*, *Sipariş › Siparişler*, *Üretim › İş emirleri*). Liste en yeni kayıttan başlar ve en fazla **200 kayıt** gösterir.

### 4.2 Kayıt ekleme

1. Tabloyu seçin; o tabloya özel giriş formu belirir.
2. Alanları doldurun. Adının yanında **\*** bulunan alanlar zorunludur. Alanın içindeki gri ipucu beklenen türü gösterir.
3. **Ekle** düğmesine basın. Hata olursa formun üstünde kırmızı bir uyarı çıkar.

| Tür | Nasıl girilir |
|---|---|
| Tam sayı / sayı | Yalnızca rakam; ondalık için nokta (ör. `2.5`). |
| Tarih | `YYYY-AA-GG` (ör. `2026-12-31`). |
| Tarih-saat | Tarih ve saat birlikte (ör. `2026-12-01 08:00`). |
| Evet / hayır | Açılır listeden **Evet** ya da **Hayır**. |
| Seçim listesi | Rol, durum, tür gibi yalnızca belirli değerleri kabul eden alanlar açılır liste olarak gelir (ör. Rol: Yönetici, Planlamacı, Üretim müdürü…). Listeden seçin; veritabanına doğru değer otomatik gider. |
| Boş alan | Girilmeyen alanlar boş kaydedilir; yalnızca zorunlu olmayanlar boş bırakılabilir. |

> **Önemli:** Başka bir tabloya bağlı alanlar (adı "No" ile biten; *Model No*, *Renk No*, *Müşteri No* gibi) şimdilik **numara olarak elle** girilir. Doğru numarayı ilgili tabloyu açıp "No" sütunundan okuyabilirsiniz.

### 4.3 Kayıt silme

"No" sütunu olan tablolarda her satırın sonunda **Sil** düğmesi bulunur. Başka kayıtlar tarafından kullanılan bir kaydı (ör. siparişi olan bir modeli) silmeye çalışırsanız veritabanı izin vermez; önce bağlı kayıtları silmeniz gerekir. Tekil "No" sütunu olmayan tablolara (*Ölçü birimleri*, *Takvim günleri*, *Kumaş özellikleri*, *Sipariş renk-beden adetleri* vb.) kayıt eklenebilir ama arayüzden silinemez.

### 4.4 Kayıt düzenleme

Bu sürümde var olan bir kaydı düzenleme özelliği yoktur; hatalı kayıt silinip yeniden eklenir. İş emirlerinin hat ve zamanı bunun istisnasıdır, Plan Panosu'ndan değiştirilebilir.

## 5. Önerilen Veri Giriş Sırası

Tablolar birbirine bağlı olduğundan aşağıdaki sıra hata almanızı önler:

1. **Firmalar** ve **Ölçü birimleri**
2. **İş ortakları** (müşteri, tedarikçi, fason atölye)
3. **Departmanlar** (Kesim, Dikim, Baskı/Nakış, Yıkama, Ütü-Paket)
4. **Çalışma takvimleri** ve **Takvim günleri** (isteğe bağlı)
5. **Üretim hatları (bantlar)**
6. **Beden skalaları**, **Bedenler**, **Renkler**
7. **Sezonlar** (isteğe bağlı) ve **Modeller**
8. **Model varyantları** (renk × beden)
9. **Malzemeler** ve **Kumaş özellikleri**
10. **Ürün ağaçları (BOM)** ve **BOM satırları**
11. **Rotalar**, **Rota adımları** (SMV ile) ve **Operasyonlar**
12. **Siparişler**, **Sipariş satırları**, **Sipariş renk-beden adetleri**
13. **İş emirleri** (sipariş satırı ve rota adımı numaralarıyla)
14. İş emirlerini **Plan Panosu**'nda hatlara atayın

Kumaş, fason, kalite ve yapay zeka destek tabloları aynı mantıkla, ihtiyaç duyuldukça doldurulur.

## 6. Örnek: Bir Siparişi Bantta Planlamak

1. **Sipariş › Siparişler:** sipariş numarası ve müşteri numarası.
2. **Sipariş › Sipariş satırları:** sipariş numarası, model numarası, yükleme tarihi, rota numarası.
3. **Sipariş › Sipariş renk-beden adetleri:** her varyant için sipariş adedi.
4. **Üretim › İş emirleri:** sipariş satırı numarası, rota adımı numarası (ör. Dikim adımı), planlanan adet.
5. **Plan Panosu:** yeni iş emrine tıklayın, bandı ve zamanı seçip **Kaydet**'e basın.
6. Çubuğun doğru hatta ve günlerde göründüğünü, bitişinin yükleme tarihinden önce olduğunu listeden kontrol edin.

## 7. Sık Karşılaşılan Hatalar

| Mesaj / durum | Anlamı ve çözümü |
|---|---|
| *Bu kayıt zaten var* | Benzersiz olması gereken bir alan (kod, sipariş no vb.) daha önce girilmiş. Farklı bir değer girin. |
| *Zorunlu bir alan boş bırakıldı* | \* ile işaretli alanları doldurun. |
| *Bağlı kayıt bulunamadı ya da bu kayıt başka kayıtlarca kullanılıyor* | Girdiğiniz "No" değeri o tabloda yok ya da silmeye çalıştığınız kayıt başka bir yerde kullanılıyor. |
| *Girilen değer izin verilen aralığın dışında* | Alan için geçersiz bir değer girilmiş (ör. negatif adet). Seçim listesi olan alanlarda bu hata oluşmaz. |
| *Geçersiz değer biçimi* | Sayı alanına harf ya da tarih alanına yanlış biçim girilmiş olabilir. |
| *Hatta çakışma var* / *Zaman çakışması* | Seçilen hat o saatlerde dolu. Başka saat ya da hat seçin. |
| Sayfa açılmıyor | Terminalde sunucunun çalıştığını ve adresin `http://localhost:8000` olduğunu kontrol edin. |
| Sayfada eski görünüm kalıyor | Ctrl+F5 ile sayfayı tam yenileyin. |
| Kayıtlar gelmiyor | PostgreSQL servisinin çalıştığını ve `DATABASE_URL` şifresinin doğru olduğunu kontrol edin. |
| `pip install` derleme hatası verir | Python 3.15 gibi çok yeni bir sürüm olabilir; Python 3.13 ile sanal ortamı yeniden oluşturun. |

## 8. Yedekleme ve Sıfırlama

**Yedek almak:**

```powershell
pg_dump -U postgres -d tekstil -f yedek.sql
```

**Yedekten geri yüklemek:**

```powershell
createdb -U postgres tekstil_geri
psql -U postgres -d tekstil_geri -f yedek.sql
```

**Veritabanını sıfırlamak** (tüm kayıtlar silinir, örnek veri yeniden yüklenir):

```powershell
dropdb -U postgres tekstil
createdb -U postgres tekstil
psql -U postgres -d tekstil -f tekstil_planlama_schema.sql -f db\seed.sql
```

Sıfırlamadan önce mutlaka yedek alın; bu işlem geri alınamaz.

## 9. Bilinen Sınırlamalar (Sürüm 1)

- Kullanıcı girişi ve yetkilendirme yoktur; uygulama yalnızca kendi bilgisayarınızda kullanım için tasarlanmıştır.
- Kayıt düzenleme yoktur (iş emri planı hariç).
- Bağlı alanlar numara olarak elle girilir.
- Plan Panosu'nda sürükle-bırak yoktur; 14 günlük görünüm kaydırılamaz.
- Yapay zeka destekli otomatik atama, termin tahmini ve doğal dil asistanı bu sürümde yer almaz (3. Faz).
- Aynı anda tek kullanıcı için tasarlanmıştır.

# Tekstil Planlama – Müşteri Kullanım Kılavuzu

Modüller ve iş akışı · Sürüm 1

## 1. Bu Kılavuz Ne Anlatıyor?

Bu kılavuz, yazılımı günlük işinizde nasıl kullanacağınızı anlatır: sistemin hangi bölümlerden oluştuğunu, hangi işin hangi sırayla yapılması gerektiğini ve her gün hangi adımları izleyeceğinizi. Ekrandaki düğme ve alanların ayrıntılı kullanımı için [Kullanıcı Kılavuzu](kullanici-kilavuzu.md)'na bakın.

## 2. Sistem Nasıl Çalışır?

Yazılım, bir siparişin hazırlanmasından bantta planlanmasına kadar tüm bilgiyi tek yerde toplar. Çalışma mantığı üç aşamadadır:

1. **Tanımlar (bir kez yapılır):** Departmanlarınız, hatlarınız, renkleriniz, bedenleriniz, modelleriniz, ürün ağaçlarınız ve rotalarınız girilir. Bu bilgiler sonraki tüm siparişlerde yeniden kullanılır.
2. **Sipariş (her siparişte yapılır):** Müşteri siparişi, renk-beden adetleri ve yükleme tarihleriyle girilir; sipariş için iş emirleri oluşturulur.
3. **Planlama ve takip (günlük yapılır):** İş emirleri hatlara atanır, termine göre kontrol edilir; üretim, fason ve kalite bilgileri izlenir.

Tanımlar ne kadar eksiksiz ve doğruysa plan o kadar güvenilir olur. İlk kurulumda zaman ayırmak sonraki aylarda zaman kazandırır.

## 3. Modüllere Kısa Bakış

Sistem 13 modülden oluşur. Modüllerin tamamına **Veri** ekranından erişilir; iş emri planlaması için ayrıca **Plan Panosu** vardır.

| # | Modül | Ne işe yarar | Başlıca kayıtlar | Ne zaman kullanılır |
|---|---|---|---|---|
| 0 | **Temel tanımlar** | Firma, ölçü birimi, müşteri/tedarikçi/fason atölye ve çalışma takvimi | Firmalar, İş ortakları, Ölçü birimleri, Çalışma takvimleri | Kurulumda, sonra gerektikçe |
| 1 | **Ürün ve varyant** | Modelin renk ve beden yapısı; her renk-beden kombinasyonu ayrı bir ürün kodu (SKU) olur | Sezonlar, Beden skalaları, Bedenler, Renkler, Modeller, Model varyantları | Yeni model geldiğinde |
| 2 | **Malzeme ve ürün ağacı (BOM)** | Kumaş, iplik ve aksesuarlar; bir adet ürün için gereken miktar ve planlanan fire | Malzemeler, Kumaş özellikleri, Ürün ağaçları, BOM satırları | Yeni model geldiğinde |
| 3 | **Rota ve operasyon (SMV)** | Ürünün hangi departmanlardan hangi sırayla geçtiği ve her adımın standart dakikası | Departmanlar, Rotalar, Rota adımları, Operasyonlar | Kurulumda; yeni model geldiğinde |
| 4 | **Kapasite ve hatlar** | Bantlar, makineler, operatörler, operatör becerileri ve modeller arası değişim süreleri | Üretim hatları, Makineler, Operatörler, Operatör becerileri, Model değişim süreleri | Kurulumda; hat değiştikçe |
| 5 | **Sipariş** | Müşteri siparişi, sipariş satırları, renk-beden adetleri, yükleme tarihleri | Siparişler, Sipariş satırları, Sipariş renk-beden adetleri | Her yeni siparişte |
| 6 | **Malzeme tedarik ve stok** | Satın alma siparişleri, gelen kumaş/aksesuar lotları, stok hareketleri, malzeme ihtiyacı | Satın alma siparişleri, Malzeme lotları, Stok hareketleri, Malzeme ihtiyaçları | Malzeme sipariş edilip geldiğinde |
| 7 | **Kesim ve pastal** | Pastal planı (beden oranları, boy, verimlilik) ve kesim emirleri | Pastallar, Pastal beden oranları, Kesim emirleri | Kesim hazırlığında |
| 8 | **Fason** | Fason atölyelerin kapasitesi, fasona gönderilen işler, sevk ve dönüş irsaliyeleri | Fason kapasiteleri, Fason siparişleri, Fason sevkiyatları | İş fasona verildiğinde |
| 9 | **Üretim takibi** | İş emirleri, günlük üretim adetleri, duruşlar ve hat dengeleme | İş emirleri, Üretim kayıtları, Duruş kayıtları, Hat dengeleme | Her gün |
| 10 | **Kalite** | Hata türleri, kalite kontroller ve bulunan hatalar | Hata türleri, Kalite kontroller, Kalite kontrol hataları | Kontrol yapıldıkça |
| 11 | **Planlama** | İş emirlerinin hatlara ve tarihlere atanması (**Plan Panosu**) | Plan Panosu; Plan senaryoları, Plan atamaları | Her gün |
| 12 | **Yapay zeka desteği** | Geçmiş verilerden verimlilik, fire ve termin tahmini; otomatik atama | Verimlilik geçmişi, Gerçek fire geçmişi, Termin tahminleri | Sonraki sürümlerde (bkz. Bölüm 7) |

## 4. Süreç Akışı: Hangi İş, Hangi Sırayla?

### Aşama A – İlk kurulum (bir kez)

1. **Temel tanımlar:** Firma, ölçü birimleri (adet, metre, kg), müşteriler, tedarikçiler ve fason atölyeler.
2. **Departmanlar:** Kesim, Dikim, Baskı/Nakış, Yıkama, Ütü-Paket.
3. **Çalışma takvimi:** Resmi tatiller ve çalışma günleri (isteğe bağlı ama planlama için önerilir).
4. **Üretim hatları:** Her bant için departman, operatör sayısı ve varsayılan verimlilik.
5. **Beden skalaları, bedenler ve renkler:** Çalıştığınız bedenleri ve renk kodlarını bir düzene oturtun (örn. S–M–L–XL; BYZ = Beyaz).

### Aşama B – Yeni model tanımı (her yeni modelde)

1. **Model:** Model kodu, açıklama, ürün grubu ve beden skalası.
2. **Model varyantları:** Modelin renk × beden kombinasyonları.
3. **Malzemeler:** Kullanılan kumaş ve aksesuarlar (gramaj, en, çekme değerleri dahil).
4. **Ürün ağacı (BOM):** Bir adet ürün için hangi malzemeden ne kadar gerektiği ve planlanan fire yüzdesi.
5. **Rota ve rota adımları:** Ürünün geçeceği departmanlar, sıra ve standart dakika (SMV) değerleri.

Bir model bir kez tanımlandıktan sonra sonraki siparişlerde tekrar girilmez.

### Aşama C – Sipariş girişi (her siparişte)

1. **Sipariş:** Sipariş numarası ve müşteri.
2. **Sipariş satırı:** Model, yükleme tarihi (termin), öncelik, kullanılacak ürün ağacı ve rota.
3. **Renk-beden adetleri:** Her varyant için sipariş adedi ve tolerans.

### Aşama D – Malzeme hazırlığı (isteğe bağlı kayıt)

Malzemenin zamanında gelmesi terminin ön şartıdır. Bu adımları kullanıyorsanız:

1. **Malzeme ihtiyacı:** Sipariş için gereken net ve brüt miktar ile ihtiyaç tarihi.
2. **Satın alma siparişi ve satırları:** Tedarikçiye verilen sipariş ve söz verilen geliş tarihi.
3. **Malzeme lotu:** Kumaş geldiğinde lot numarası, ton grubu, top sayısı, gerçek en ve gramaj, ölçülen çekme.
4. **Stok hareketleri:** Giriş ve çıkışlar.
5. **Pastal ve kesim emri:** Beden oranları, kat sayısı, kesim tarihi.

### Aşama E – İş emri ve planlama (her gün)

1. **İş emri oluşturun:** Sipariş satırı ve rota adımı (örn. Dikim) ile planlanan adet. Bir siparişin her departman adımı için ayrı iş emri açılır.
2. **Plan Panosu'nu açın:** Hatta atanmamış iş emirleri listede **—** işaretiyle görünür.
3. **İş emrini hatta atayın:** Hat, başlangıç ve bitiş zamanını seçin. Aynı hatta çakışan atamayı sistem reddeder.
4. **Termini kontrol edin:** Listede her iş emrinin yükleme tarihi görünür; planlanan bitişi yükleme tarihiyle karşılaştırın.

### Aşama F – Üretim, fason ve kalite takibi

1. **Fason işler:** İş fasona gidecekse fason sipariş açın, giden ve dönen irsaliyeleri ve hatalı adetleri kaydedin.
2. **Üretim kayıtları:** Hatlardan gelen günlük adetler.
3. **Duruş kayıtları:** Makine arızası, malzeme bekleme gibi duruş nedenleri ve süreleri.
4. **Kalite kontrol:** Kontrol edilen adet ve bulunan hatalar.

> Bu kayıtlar bu sürümde Veri ekranından elle girilir. Tablet/barkodla anlık veri toplama sonraki sürümlerde planlanmıştır.

### Süreç özeti

| Süreç | Sıklık | Nerede yapılır | Öncesinde hazır olması gerekenler |
|---|---|---|---|
| İlk kurulum | Bir kez | Veri | Hat sayıları, bedenler, renk kodları, müşteri listesi |
| Yeni model tanımı | Her yeni modelde | Veri | Kurulum tamamlanmış olmalı |
| Sipariş girişi | Her siparişte | Veri | Model, varyantlar, BOM ve rota tanımlı olmalı |
| Malzeme ve kesim hazırlığı | Siparişe göre | Veri | Sipariş girilmiş olmalı |
| İş emri ve planlama | Günlük | Veri + Plan Panosu | Sipariş satırı ve rota adımı hazır olmalı |
| Üretim, fason, kalite takibi | Günlük | Veri | İş emri açılmış olmalı |

## 5. Önerilen Çalışma Rutini

**Her sabah**

1. Yeni gelen siparişleri girin (Aşama C).
2. Yeni açılan iş emirlerini kontrol edin.
3. Plan Panosu'nda atanmamış iş emirlerini hatlara yerleştirin.
4. Önceki günün üretim, duruş ve kalite kayıtlarını girin.

**Haftalık**

1. Termini yaklaşan siparişleri listeden gözden geçirin; gecikme riski olanların planını güncelleyin.
2. Hat kapasitesi, operatör sayısı veya çalışma takvimi değişmişse tanımları güncelleyin.
3. Veritabanının yedeğini alın.

## 6. Başarılı Kullanım İçin İpuçları

- **Kodlamayı baştan standartlaştırın.** Model, renk, malzeme ve sipariş kodlarında tutarlı bir düzen kullanın; sonradan değiştirmek zordur.
- **SMV değerlerini dikkatle girin.** Planlamanın ve ileride yapılacak tahminlerin temeli standart dakika değerleridir.
- **Fire yüzdesini gerçek verilerle güncelleyin.** Planlanan fire ile gerçekleşen fire arasındaki fark, malzeme ihtiyacı hesabının doğruluğunu belirler.
- **Sıraya uyun.** Bir kayıt başka bir kayda ihtiyaç duyar (örneğin sipariş satırı için model gerekir). Sistem eksik bağlantıyı reddeder; Bölüm 4'teki sırayı izlemek hata almayı önler.
- **Düzenli yedek alın.** Özellikle toplu veri girişinden önce ve sonra.

## 7. Bu Sürümde Neler Var, Neler Gelecek?

| Faz | Kapsam | Durum |
|---|---|---|
| **1. Faz** | Sipariş girişi, ürün ağacı, rota, hat tanımları ve manuel bant planlama (Plan Panosu) | **Bu sürümde mevcut** |
| **2. Faz** | Bantlardan tablet/barkod ile anlık adet girişi; gerçek zamanlı verimlilik ve darboğaz tespiti | Planlandı |
| **3. Faz** | Yapay zeka destekli otomatik iş emri atama, termin ve gecikme tahmini, doğal dil asistanı | Planlandı |

Bu sürümde kullanıcı girişi (şifre) ve çok kullanıcılı çalışma yoktur; uygulama tek bilgisayarda, tek kullanıcı için tasarlanmıştır. Kayıt düzenleme de yoktur: hatalı bir kayıt silinip yeniden girilir (iş emirlerinin hat ve zamanı Plan Panosu'ndan değiştirilebilir).

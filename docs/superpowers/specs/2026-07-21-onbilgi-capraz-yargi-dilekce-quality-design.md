# SocratLegal Ön Bilgi, Çapraz Yargı, Dilekçe ve Kalite Mimarisi

## Durum

Tasarım onay bekliyor. Bu belge yazılım uygulama planı değil; uygulama öncesi
mimari sözleşmedir. Bu belge onaylanmadan üretim koduna geçilmez.

## 1. Amaç ve değişmezler

Bu tasarım; süreç başlatan veya tetikleyen belge üzerinden ön bilgi toplama ve
strateji üretimini, çapraz yargı muhakemesini, genel dilekçe işlemlerini,
operasyonel bağlamı, kaynak/alıntı disiplinini, TIFF belge intake'ini ve Reklam
Kurulu corpus'unu aynı kalite mimarisine bağlar.

Değişmez kurallar:

1. Superpowers, SocratLegal hukukî muhakemesini, persona profillerini,
   çapraz yargı sorgusunu veya kaynak kurallarını değiştiremez ve override
   edemez; yalnızca bunların eksiksiz, tutarlı, ekonomik ve denetlenebilir
   uygulanmasına yardımcı olur.
2. Modelin kendi içindeki basit alan promptu SocratLegal personasının yerine
   geçemez. Örneğin “ceza hukukunda uzman danışman” ifadesi, tanımlı ceza
   personasının kıdemli avukat, Ceza Genel Kurulu başhakimi ve ceza/ceza
   muhakemesi profesörü bakışını daraltamaz.
3. Her sonuç analysis-only ve non-binding'dir. Kesin olmayan olgu, kaynak,
   alıntı, süre, görev veya yetki kesinmiş gibi sunulamaz.
4. Kullanıcı belgeleri ve kişisel veriler ham hâliyle Git, genel corpus,
   telemetry veya model eğitimi içine alınmaz. Dış çağrıdan önce yerel PII
   masking uygulanır.
5. Doğrudan hukukî otorite, analoji adayı, doktrin görüşü, operasyonel
   hipotez ve teknik çıkarım birbirinden ayrı etiketlenir.

## 2. Talimat ve kalite önceliği

Her host model ve server-side model için birleşik kalite bağlamı şu sırayla
oluşturulur:

1. Sistem, güvenlik, gizlilik ve veri sınırları
2. SocratLegal hukukî muhakeme adımları
3. İlgili birincil, destekleyici ve çapraz persona profilleri
4. Çapraz yargı/alt hukuk dalı sorgusu
5. Maddi olgu, hayatın olağan akışı, genel ispat, iş akışı, sektör, teamül,
   davranış ve teknik bağlam
6. Kaynak, künye, kısa alıntı ve atıf doğrulama sözleşmesi
7. Kullanıcının talebi, üslup ve uzunluk tercihi
8. Superpowers kalite kernel'i
9. Modelin genel üslup ve görev yönlendirmesi

Kalite kernel'i aşağıdaki işlemleri yapar: eksik başlık kontrolü, karşı görüş
kontrolü, belirsizlik kontrolü, kaynak kimliği kontrolü, tekrar azaltma, dilsel
netlik ve çıktı formatı doğrulaması. Yeni hukuk kuralı, persona veya sonuç
üretme yetkisi yoktur.

## 3. Ortak muhakeme katmanları

### 3.1 Çapraz yargı sorgusu

`cross_domain_inquiry` ortak katmanı her analiz, mütalaa, strateji,
sözleşme ve dilekçe akışında çalışır. Algılanan her yargı türü ve alt hukuk
dalı için şu matris hazırlanır:

| Alan | Lehe potansiyel etki | Aleyhe potansiyel etki | Kaynak ve doğrulama |
|---|---|---|---|
| Yargı türü/alt dalı | Somut olaya katkı | Risk veya çelişki | Norm/içtihat/doktrin |

Matriste ayrıca diğer süreçteki beyan, kabul, ödeme, başvuru, karar,
delil ve çelişkilerin sonraki süreçte kullanılabilirliği incelenir. Ceza,
hukuk, idare, vergi, icra, anayasa ve insan hakları boyutları yalnızca
semantik yakınlıkla değil, olayın hukukî etkisi bakımından tetiklenir.

### 3.2 Maddi hayat ve operasyonel bağlam

`operational_context` genişletilerek her alanda şu kartları üretebilir:

- aktörler ve rol dağılımı,
- normal iş akışı ve sektör teamülü,
- ekonomik/teknik teşvikler,
- davranış örüntüsü ve alternatif açıklamalar,
- yasa dışı eylem döngüsü ihtimalleri,
- beklenen dijital/fiziksel izler,
- doğrulama soruları ve delil kaynakları.

Her kart `kullanıcı beyanı`, `belgeyle doğrulanan olgu`, `genel hayat
deneyimi`, `sektörel bilgi`, `operasyonel hipotez`, `teknik hipotez` veya
`doğrulama gerekli` etiketi taşır. Bu kartlar hukukî sonucun yerine geçmez;
ilgili norm, unsur ve ispat bağlantısı kurulur.

### 3.3 Kanıt ve atıf kartı

Her önemli hukukî iddia için ortak bir evidence ledger kaydı hazırlanır:

- claim id ve iddia metni,
- hukukî sonuç,
- kaynak türü ve otorite seviyesi,
- tam künye ve belge kimliği,
- madde/paragraf/sayfa bilgisi,
- erişilmiş kısa alıntı,
- ratio/dictum veya karşı oy ayrımı,
- somut olaya bağlantı,
- temporal uygunluk,
- karşı kaynak ve karşı görüş,
- güven, varsayım ve eksik doğrulama.

Tam metin veya kısa alıntı erişilemiyorsa sonuçta bu açıkça belirtilir.
Atıf doğrulama, yalnızca `[ #id ]` biçimini değil, iddia-künye-alıntı
ilişkisini de denetler.

## 4. Süreç başlatan belge üzerinden ön bilgi ve strateji

Ana backend adı `PreActionIntakeStrategy` olacaktır. Kullanıcıya sunulan
araç adı:

```text
socratlegal_onbilgi_ve_strateji
```

Belge türleri tebligat, dava dilekçesi, ihtar, yazılı savunma talebi,
iddianame, kurum/kurul bildirimi, icra belgesi ve benzeri tetikleyici
belgeleri kapsar.

Akış:

1. Yerel belge intake, format/OCR ve PII sınırı
2. Belge türü, taraflar, iddialar, talepler, ekler ve kritik tarihler
3. Usulî durum, süre, görev, yetki, merci ve acil hak koruma taraması
4. Maddi olgu, operasyonel bağlam ve çapraz yargı matrisi
5. Mevcut delil ve delil boşluğu analizi
6. Dava, icra, kurum/kurul, ceza, arabuluculuk, sulh, feragat, 35/A,
   idari başvuru ve diğer yolların koşullu karşılaştırması
7. Eksik bilgi-belge-delil soru listesi
8. Bilgi toplandıktan sonra ayrıntılı strateji ve tercihe bağlı dilekçe

Kullanıcı iki çalışma şeklinden birini seçebilir:

- `triage`: hızlı ilk tarama, P0/P1 riskler ve kritik sorular,
- `full_intake`: geniş soru-belge-delil dosyası ve karar ağacı.

Kullanıcı tek promptla ikisini de isteyebilir; araç sonucu iki aşamayı
ayrı başlıklarla döndürür.

## 5. Ortak dilekçe backend'i ve kamuya açık araçlar

Tek backend işlemleri:

```text
draft
review
shorten
lengthen
```

Kullanıcıya keşfi kolaylaştıran ayrı MCP araçları:

```text
socratlegal_dilekce_incele
socratlegal_dilekce_hazirla
socratlegal_dilekce_kisalt
socratlegal_dilekce_uzat
socratlegal_uslup_profili
```

Tüm işlemler aynı persona, çapraz yargı, operasyonel bağlam, evidence
ledger ve Türk dili profesörü perspektifini kullanır.

### 5.1 Dilekçe hazırlama

Taslak üretim sırası; usulî konum, talep sonucu, maddi vakıa, kronoloji,
iddia-delil matrisi, hukukî sorun, norm, içtihat/doktrin, karşı taraf,
süre/görev/yetki ve son kontrol katmanlarından oluşur.

### 5.2 Dilekçe kısaltma

Metin doğrudan silinmez. Önce stratejik süzgeç uygulanır. Dava şartı,
görev, kesin yetki, süre, usul, delil, talep ve karşı argüman bölümleri
ayrıştırılır. Çıkartılabilecek veya riskli görülen kısımlar kullanıcıya
önerilir; kritik hukukî içerik kullanıcı onayı olmadan kaldırılmaz.

Çıktı, kısaltılmış taslağın yanında “korundu/önerildi/çıkarıldı ve riski”
matrisi içerir.

### 5.3 Dilekçe uzatma

Uzatma yalnızca uzunluk artırmaz. Eksik hukukî bağlantıları, içtihat ve
doktrin atıflarını, karşı argümanları, delil bağlantılarını, çapraz yargı
etkilerini ve olayın operasyonel bağlamını ekler. Ana vakıa ve talep
sonucundan uzaklaşma kontrolü yapılır.

### 5.4 Üslup profili

Kullanıcının sağladığı örnek mütalaa/dilekçelerden yerel üslup profili
çıkarılabilir. Profil; başlık düzeni, cümle yoğunluğu, atıf biçimi,
argüman sırası, ton ve açıklık tercihlerini içerir. Ham belgeler model
temel eğitimine, genel corpus'a veya Git'e aktarılmaz.

## 6. Türk dili profesörü perspektifi

Tüm dilekçe işlemlerinde ortak yazım lensi olarak çalışır. Hukukî anlamı
değiştirmeden sade Türkçe, tutarlı terim kullanımı, iddia-gerekçe geçişleri,
gereksiz tekrarların azaltılması ve talep sonucu ile gerekçenin dilsel
uyumu denetlenir. Bu lens hukukî persona veya maddi hukuk analizini
daraltamaz.

## 7. Belge formatı ve TIFF

Ortak belge intake `.tif` ve `.tiff` uzantılarını destekler. OCR eklentisi
ve işletim sistemi motoru yoksa `ocr_required` dönülür; okunmamış içerik
üzerinden hukukî veya teknik sonuç üretilmez. Host IDE TIFF'i sohbetten
geçiremiyorsa yerel `file_path` akışı kullanılabilir.

## 8. Reklam Kurulu corpus'u

Yeni kaynak id'si `reklam_kurulu` olacaktır. İlk kapsam kararlar, reklam ve
tüketici mevzuatı, kurul kararlarının künye/alıntıları ve mümkün olan resmî
site adapter'ıdır. Kaynak federasyonu yerel corpus ve resmî adapter'ı
paralel arar; kaynak provenance'ı korunur.

Persona bileşenleri:

- reklam hukukunda kıdemli avukat,
- tüketici hukukunda kıdemli avukat,
- Reklam Kurulu başkanı perspektifi,
- reklamcılık/pazarlama sektör uzmanı,
- olayın gerektirdiği hukuk, idare, ceza ve diğer destekleyici personalar.

Anti-damping şimdilik yalnızca ileri hukuk alanı/corpus/persona roadmap
notudur; bu tasarımda aktif kaynak veya persona değildir.

## 9. Görsel çıktı politikası

Görsel yalnızca ilişkiyi metinden daha anlaşılır kılıyorsa üretilir.
Öncelikli formatlar zaman çizelgesi, karar ağacı, delil matrisi, risk
haritası ve süreç şemasıdır. Server yapılandırılmış Mermaid/tablo/spec
üretir; host render edemiyorsa düz metin fallback'i kullanır.

## 10. Komut sözlüğü ve keşif

Yeni kaynak ve araçlar:

```text
socratlegal_komut_sozlugu
socratlegal://commands
```

Slash menüsünün görünmesi host istemcinin kararına bırakılır. Prompt
listesi, araç açıklamaları, resource ve doğal dil fallback'i bütün
istemcilerde ortak keşif yüzeyidir. `/` komutları IDE'ye özel kayıtlarla
eklenebilir, ancak protokol seviyesinde zorunlu tutulmaz.

## 11. Portable all-IDE kaydı

Portable çekirdek IDE'den bağımsızdır. İleride `--ide all` idempotent kayıt
modu eklenir. Bu mod yalnızca kurulu istemcileri algılar, ayarları yedekler,
mevcut SocratLegal kaydını çoğaltmaz ve bulunmayan istemcileri atlar.
Sonradan yeni IDE kuran kullanıcı aynı portable çekirdekte kayıt işlemini
yeniden çalıştırır; paketi tekrar indirmesi gerekmez.

## 12. Test ve kabul ölçütleri

- Superpowers kernel'i persona veya reasoning step metnini değiştiremez.
- Modelin basit alan promptu, tam persona metninin yerine geçemez.
- Her çapraz alan için lehe/aleyhe etki ve kaynak doğrulama alanı bulunur.
- Ön bilgi aracı P0/P1/P2/P3 soru-belge önceliği üretir.
- Kısaltma, kritik hukukî bölümü kullanıcı onayı olmadan silmez.
- Uzatma ana bağlamdan sapma ve atıf/alıntı kontrolünden geçer.
- Dilekçe çıktısında Türk dili perspektifi ve künye-alıntı kartları bulunur.
- TIFF intake ve OCR yokluğu açıkça test edilir.
- Reklam Kurulu kaynak kaydı ve persona rotası keşfedilebilir olur.
- Eski araç alias'ları korunur; upstream modüller doğrudan değiştirilmez.

## 13. Uygulama sırası

1. Kalite önceliği ve Superpowers non-override sözleşmesi
2. Çapraz yargı ve operasyonel bağlam kartları
3. Evidence ledger ve alıntı doğrulama
4. Ön bilgi/strateji intake
5. Ortak dilekçe backend'i ve dört işlem
6. Üslup profili ve Türk dili perspektifi
7. TIFF ortak intake
8. Reklam Kurulu corpus/adapter/persona
9. Komut sözlüğü, görsel spec ve portable all-IDE kaydı
10. Tam regresyon ve kabul testleri

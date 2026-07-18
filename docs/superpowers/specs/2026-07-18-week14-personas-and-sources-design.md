# Hafta 14 — Persona, Kurum Kaynakları ve Hukuki Muhakeme Tasarımı

## Durum ve amaç

Bu belge, LegalAI'nin belirli hukuk alanlarını ve kurum/kurul kaynaklarını birlikte değerlendirmesi için onaylanan tasarımı tanımlar. Tasarım; tek bir persona seçmek yerine olayda algılanan tüm ilgili hukuk alanlarını uzman lensleriyle birleştirir. Çıktılar her zaman kaynaklı, ihtimalli, analiz niteliğinde ve bağlayıcı olmayan görüş olarak sunulur.

Bu belge uygulama kodu değildir. Uygulama öncesi sözleşme, due diligence ve teknik bilirkişi raporu itirazı gibi daha sonraki özelliklerle uyumlu sınırlar bırakır.

## 1. Persona mimarisi

### 1.1 Ortak taban persona

Tüm profiller, mevcut çıktı kalitesinin altında bir vaat oluşturmayacak kıdemli hukukçu düzeyinde çalışır. Rol adları gerçek bir hâkim, avukat, akademisyen veya kurum başkanı kimliği iddiası değildir; uzmanlık bakışını ve analiz standardını tanımlar.

Ortak davranış kuralları:

- olay, iddia, delil ve varsayımı birbirinden ayır;
- mevzuatın olay, dava ve ilgili diğer tarihlerdeki yürürlük durumunu kontrol et;
- zamanaşımı, hak düşürücü süre, görev, yetki ve kurum/kurul başvurusunu ara;
- bağlayıcı hukuk kuralı, yargı kararı, kurum kararı, doktrin ve politika kaynağını ayrı etiketle;
- karşıt içtihat ve karşı görüşü gizleme;
- belirsizliği ve sonucu değiştirecek eksik bilgiyi açıkça göster;
- kullanıcıya yalnız dava değil, icra, idari başvuru, ceza şikâyeti, arabuluculuk, sulh, feragat, ibra, uzlaşma ve diğer hukuki yolları da olayla ilgisi ölçüsünde sun.

### 1.2 Çoklu alan seçimi

Tekil `jurisdiction_id` geriye dönük olarak korunur; yeni akış aşağıdaki çoklu yapıyı destekler:

```text
primary_jurisdiction
supporting_jurisdictions[]
expert_lenses[]
jurisdiction_conflicts[]
selection_confidence
```

Ana hukuki sonucu en çok belirleyen alan baş persona olur. Diğer alanlar yardımcı uzman persona olarak çalışır. Usul, süre, görev ve yetki konuları ortak denetim katmanından geçer. Alan belirlenemezse `diger` profili kullanılır; alan tespit edildiğinde `diger` ilgili uzmanları devreye sokar.

Kullanıcı, otomatik algılamayı şu şekilde sınırlandırabilir veya genişletebilir:

```text
Bu olayı hukuk, ceza, idare ve KVKK perspektifleriyle birlikte değerlendir.
```

## 2. Profil kapsamı

### 2.1 Hukuk profili

Hukuk profili; kıdemli özel hukuk avukatı, Yargıtay Hukuk Genel Kurulu perspektifi ve hukuk profesörü lenslerini birleştirir. Olayda algılanan alt alan için ayrıca uzman lens seçer.

İlk uzmanlık kataloğu:

- ticaret, iş, sözleşmeler, kira, genel tazminat;
- kişiler, eşya ve miras;
- fikri ve sınai haklar, marka ve patent;
- haksız rekabet;
- deniz ticareti;
- bilişim, tüketici, sağlık, sigorta, spor, enerji, inşaat ve diğer algılanan özel alanlar.

Haksız rekabet hukuku ile rekabet hukuku ayrı profillerdir. Marka ve patent, fikri ve sınai haklar altında ayrı uzmanlıklar olarak çalışır. Kira uyuşmazlığı; sözleşmeler, borçlar, eşya ve usul boyutlarıyla birlikte ele alınabilir.

Hukuk profili, olay ceza, idare, vergi, anayasa, insan hakları veya başka bir alana da giriyorsa ilgili profilleri birlikte çağırır.

### 2.2 Ceza, idare ve vergi profilleri

- `ceza`: kıdemli ceza avukatı, Ceza Genel Kurulu perspektifi, ceza ve ceza muhakemesi hukuku profesörü; alt dallarda ilgili ceza dairesi uzmanlığı.
- `idare`: idare hukuku kıdemli avukatı, İDDK perspektifi, idare ve idari yargılama usulü hukuku profesörü; ilgili Danıştay dairesinin alt alan uzmanlığı.
- `vergi`: vergi hukuku kıdemli avukatı, kıdemli YMM, VDDK perspektifi, vergi/idari-vergi yargılama usulü ve kamu maliyesi profesörü; hukuk analizi öncelikli, teknik mali değerlendirme destekleyici.

Bu üç profil gerektiğinde anayasa ve insan hakları profillerini de çağırır.

### 2.3 Rekabet, KVKK ve KİK profilleri

- `rekabet`: kıdemli rekabet hukukçusu, Rekabet Kurulu perspektifi, AB Komisyonu/DG COMP ve ABAD/Genel Mahkeme perspektifleri, ticaret/işletme/iktisat ve idare lensleri.
- `kvkk`: kıdemli KVKK ve bilişim hukuku avukatı, veri yönetişimi ve güvenlik uzmanı, idare ve ceza lensleri.
- `kik`: idare, sözleşme ve ticaret hukuku avukatları; KİK perspektifi ve olayın teknik alanındaki uzman.

Rekabet profilinde AB Komisyonu ve ABAD ayrı kaynak/uzmanlık katmanlarıdır. OECD kaynakları rekabet araştırma ve ekonomik/politika analizi için yardımcı kaynak olarak kullanılır; Türk mevzuatı veya bağlayıcı içtihat gibi sunulmaz.

### 2.4 Anayasa, insan hakları ve genel profil

- `anayasa`: AYM perspektifi ve anayasa hukuku profesörü.
- `insan_haklari`: AİHM perspektifi ve insan hakları hukuku profesörü.
- `diger`: kıdemli genel hukuk danışmanı, hukuk profesörü, issue-spotting ve hukuki araştırma uzmanı; belirli alan tespit edilemezse genel tarama ve uzman yönlendirmesi yapar.

Anayasa ve insan hakları profilleri otomatik olarak her soruya eklenmez. Temel hak, ölçülülük, kanunilik, eşitlik, mülkiyet, özel hayat, adil yargılanma veya etkili başvuru bağlantısı algılanırsa devreye girer.

## 3. Kurumsal profil ve öncelik sırası

Kurum profilleri ortak idare çekirdeği, kurum/kurul perspektifi, ilgili kıdemli hukukçu ve teknik uzman katmanlarından oluşur. Kararların hukuki ağırlığı ayrıca sınıflandırılır.

Uygulama sırası:

1. Ortak kurum kaynak ve karar şeması.
2. KİK.
3. Kamu Denetçiliği Kurumu.
4. TİHEK.
5. SPK.
6. BDDK.
7. BTK.
8. EPDK.
9. RTÜK.
10. KGK.

Her kurum kaydında kurum, karar türü, karar tarihi, yürürlük tarihi, mevzuat dayanağı, karar numarası, ilgili teknik alan, bağlayıcılık seviyesi, belge bağlantısı ve alıntılanabilir metin bulunur.

## 4. Kaynak ve doktrin katmanı

### 4.1 Kaynak sınıfları

Kaynaklar en az şu sınıflara ayrılır:

- mevzuat ve resmi mevzuat sürümleri;
- yüksek mahkeme, AYM, AİHM ve kurum/kurul kararları;
- açık erişimli akademik doktrin;
- baro dergileri ve Türkiye Barolar Birliği dergileri;
- DergiPark ve üniversite hukuk fakültesi dergileri;
- YÖK veritabanında kamuya açık hukuk yüksek lisans ve doktora tezleri;
- Rekabet Kurumu uzmanlık tezleri;
- Rekabet Dergisi makaleleri;
- OECD rekabet tavsiyeleri, yuvarlak masa çalışmaları, politika raporları, ülke incelemeleri ve rekabet değerlendirme kaynakları;
- kullanıcının yüklediği veya lisanslı olarak sağlanan doktrin.

Kamuya açık erişim, otomatik olarak sınırsız çoğaltma hakkı anlamına gelmez. Tam metin saklama ve alıntı kapsamı lisans/telif durumuna göre belirlenir. Uygun olmayan kaynaklarda yalnızca künye, özet, bağlantı ve izin verilen kısa alıntı tutulur.

Her doktrin kaydı şu alanları taşır:

```text
author, title, publication, year, volume, issue, pages,
doi_or_url, access_date, license, opinion_type, language,
relevant_topics, quoted_excerpt
```

Doktrin görüşü; baskın, azınlık, karşı görüş, eleştirel görüş veya uygulama görüşü olarak etiketlenir. Doktrin hiçbir zaman mevzuat veya bağlayıcı yargı kararı gibi sunulmaz.

### 4.2 OECD kapsamı

OECD katmanı birincil Türk hukuk kaynağı değildir. Rekabet hukukunda:

- pazar ve ekonomik analiz,
- kartel ve hâkim durum politikası,
- birleşme ve düzenleme,
- kamu ihalelerinde danışıklı teklif,
- dijital piyasalar,
- rekabetçi tarafsızlık,
- kurumlar arası uygulama karşılaştırması

gibi araştırma sorularında devreye girer. Başka bir hukuk alanında OECD kaynağı ancak konu ile gerçek ve doğrulanabilir bir kesişim varsa çağrılır.

## 5. Hukuki muhakeme akışı

Kaynak aramasından önce olay ve soru yapılandırılır. Analizin zorunlu muhakeme omurgası şöyledir:

1. **Hukuki sorun nedir?** Kullanıcının sorusu, hedefi ve derin analiz talebi somut hukuki sorunlara ayrılır.
2. **Teorik ve yasal altyapı nedir?** Sorunun unsurları, kavramları, mevzuat dayanakları ve varsa doktrindeki yaklaşımlar belirlenir.
3. **Somut olayın unsurlarla ilişkisi nedir?** Kullanıcının olayları, belgeleri, tarihler ve iddiaları her unsurla eşleştirilir; eksik veya tartışmalı olgular ayrılır.
4. **Cevap ve strateji nedir?** Her unsur bakımından olumlu/olumsuz ihtimaller, delil durumu, süreler, görev-yetki, başvuru yolları ve alternatif hukuki stratejiler ortaya konur.

Bu dört adımın üzerine Temporal Legal Context, karşıt görüş/karşıt içtihat taraması ve çoklu persona sentezi uygulanır. Sonuç tek bir kesin cümleye indirgenmez; varsayım, güven düzeyi ve alternatif senaryolar gösterilir.

## 6. Çıktı ve atıf kuralları

Her ilgili yüzeyde:

- kullanılan persona ve alt uzmanlıklar;
- olay ve dava tarihleri;
- yürürlükteki mevzuat ve değişiklikler;
- süre, görev ve yetki ihtimalleri;
- ilgili karar/doktrin kaynaklarının künyesi;
- kısa ve izin verilen alıntı;
- bağlayıcılık seviyesi;
- karşıt içtihat veya doktrin;
- belirsizlikler ve sonucu değiştirecek eksik bilgiler

gösterilir. Çıktı `analysis_only` ve `non_binding` niteliğini korur.

## 7. Kabul ölçütleri

- Hukuk profili, soru içindeki özel hukuk alt alanını bir veya daha fazla uzman lens olarak seçer.
- Haksız rekabet ve rekabet hukuku ayrı seçilir.
- Bir soru birden fazla alana giriyorsa baş ve yardımcı personalar birlikte çalışır.
- Ceza, idare ve vergi analizlerinde ilgili anayasa/insan hakları lensleri tetiklenebilir.
- Bilinmeyen alanlar `diger` profiline düşer ve özel profil eksikliği açıkça belirtilir.
- Doktrin kaynaklarında künye, görüş türü, telif/erişim durumu ve kısa alıntı sınırı tutulur.
- OECD kaynağı rekabet araştırmasında yardımcı kaynak olarak görünür; bağlayıcı hukuk gibi görünmez.
- Her analiz dört muhakeme adımını ve kaynaklı sonuç/strateji bölümünü içerir.


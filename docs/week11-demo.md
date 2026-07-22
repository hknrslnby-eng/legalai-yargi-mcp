# LegalAI Week 11: İlk Kullanım Demo Rehberi

Bu rehber yazılım bilmeyen kullanıcı için hazırlanmıştır. Ekranların adı Codex, Cursor, Claude, Antigravity veya VS Code'da değişebilir; aradığımız işlem aynıdır: yerel LegalAI MCP sunucusunu açmak ve sohbet alanından soru sormak.

İstemci ayarlarının karşılaştırmalı tablosu için [MCP istemci matrisi](mcp-client-matrix.md) belgesine bakın.

Bu sayfadaki ekranlar varsayımsaldır. Gerçek istemci ekranı gibi değerlendirilmemelidir.

## Başlamadan önce

1. LegalAI fork klasörünü IDE'de proje olarak açın.
2. MCP ayarlarında `legalai` sunucusunun proje klasöründen `uv run legalai-mcp` ile başlatıldığını doğrulayın.
3. Mevcut Cursor veya başka IDE ayarlarını silmeyin ve yeniden adlandırmayın.
4. Ayrı hosting veya ortak port gerekmez.

## IDE'de beş adım

### 1. Bağlantıyı kontrol edin

IDE'nin MCP araçları/Tools bölümünde `legalai_saglik_kontrolu` aracını bulun ve çalıştırın.

Beklenen sonuç:

```json
{
  "status": "ok",
  "version": "0.2.5",
  "external_calls": false
}
```

Bu sonuç LegalAI sürecinin çalıştığını gösterir. Dış hukuk veritabanına veya LLM'e istek göndermez.

### 2. Yardım menüsünü açın

`legalai_yardim` aracını çalıştırın. Araç size hangi talepte hangi yeteneği kullanabileceğinizi ve örnek cümleleri gösterir. İstemci resource paneli sunuyorsa `legalai://capabilities` kaynağını da açabilirsiniz.

### 3. Bir seviye seçin

- **Yalın:** Sadece soruyu yazın.
- **Yönlendirilmiş:** Tarih, taraf rolü, hukuk alanı veya istenen çıktı türünü ekleyin.
- **Rafine:** Süre, görev/yetki, karşıt içtihat, karşı taraf argümanı, temporal context ve dava dışı çözüm yollarını ayrıca isteyin.

### 4. Sohbet alanına cümleyi yazın

Araç adlarını bilmek zorunda değilsiniz. IDE'deki sohbet alanına normal bir insan gibi yazabilirsiniz. Host model, MCP açıklamalarına göre uygun aracı seçer.

### 5. Çıktıyı kontrol edin

İyi bir sonuçta şu başlıkları arayın:

- Kaynaklar ve künye bilgileri
- Kısa ilgili alıntılar
- Olay ve dava tarihleri
- Zamanaşımı/hak düşürücü süre riskleri
- Görevli/yetkili mahkeme, icra dairesi veya kurum adayları
- Karşıt görüşler ve karşı taraf argümanları
- Alternatif çözüm stratejileri
- Varsayımlar, eksik bilgiler ve güven seviyesi

LegalAI çıktısı `analysis_only` ve `non_binding` niteliğindedir. Kesin hukukî görüş veya garanti değildir.

## Üç kopyala-yapıştır örneği

### Örnek 1 — Yalın

```text
Bir kira uyuşmazlığında kiraya verenin hangi hukukî yollara başvurabileceğini kaynaklı ve ihtimalli biçimde açıkla.
```

Beklenen çıktı: ilgili içtihatlar, temel hukukî yollar ve eksik olay bilgilerinin kısa listesi.

### Örnek 2 — Yönlendirilmiş

```text
Kiracı 15.03.2024 tarihinde kira bedelini ödemedi. Kiraya veren 20.06.2024 tarihinde ihtar gönderdi. Tahliye ve alacak bakımından süreleri, görevli mahkeme ihtimalini ve gerekli ön şartları kaynaklı analiz et.
```

Beklenen çıktı: olay tarihleri, süre riskleri, görev/yetki adayları, ön şartlar ve kaynak künye/alıntıları.

### Örnek 3 — Rafine

```text
Bu alacağın tahsili için dava, icra, zorunlu veya ihtiyari arabuluculuk, Avukatlık Kanunu 35/A, sulh/ibra ve gerekiyorsa idareye veya ceza makamlarına başvuru seçeneklerini karşılaştır. Olay ve dava tarihinde yürürlükteki kuralları, zamanaşımı ve hak düşürücü süre ihtimallerini, karşı tarafın en güçlü argümanlarını, karşıt içtihatları ve her stratejinin delil etkisini ayrı başlıklarda göster. Tarih veya olgu eksikse ihtimalli cevap ver.
```

Beklenen çıktı: strateji seçenekleri tablosu, her seçenek için merci, süre, ön şart, delil etkisi, geri döndürülebilirlik, risk ve kaynaklar.

## Yetenekler ne işe yarar?

| Kullanıcı amacı | LegalAI yeteneği |
|---|---|
| Bir soruyu içtihat ve temporal context ile incelemek | `katmanli_analiz` |
| Karşı tarafın argümanlarını ve dava dışı yolları görmek | `agresif_karsi_taraf` |
| Karmaşık soruyu alt sorulara bölmek | `derin_arastirma` |
| Taslaktaki belge atıflarını kontrol etmek | `alinti_dogrula` |
| Dış çağrılardan önce kişisel veriyi korumak | `pii_maskele` ve otomatik outbound maskeleme |

## CLI yardımcı yolu

IDE kullanırken CLI gerekmez. Hızlı bir yerel kontrol veya otomasyon için proje klasöründe şu komut kullanılabilir:

```powershell
uv run legalai qa "Bu olay için görevli mahkeme ve süre risklerini kaynaklı analiz et"
```

Bu komut host model yerine geçmez; `synthesize=false` ile belge ve analiz paketini JSON olarak üretir. Nihai kaynaklı anlatımı yine IDE içindeki host model düzenler.

## Kişisel veri uyarısı

LegalAI'nin Bedesten, AYM, HUDOC veya dış LLM'e yaptığı çağrılardan önce PII yerelde maskelenir. Yine de host IDE'nin kullanıcı mesajını MCP'ye göndermeden önce görmesi istemci davranışına bağlıdır. Gerçek kişi adları, TCKN, adres ve dosya bilgileri yerine önce örnek/anonim veriyle deneme yapın.

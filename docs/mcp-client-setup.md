# SocratLegal MCP istemci kurulumu

Normal kullanıcı için [portable kullanıcı kurulum rehberini](socratlegal-user-install.md) izleyin. Bu sayfa, IDE ayarını elle yapmak isteyen veya mevcut checkout ile çalışan kullanıcı içindir.

LegalAI bu aşamada yerel STDIO MCP sunucusudur. Ayrı hosting, global daemon veya ortak TCP portu gerekmez. Her IDE kendi istemci kaydından bağımsız bir süreç başlatır; böylece Cursor kaydı ile Codex kaydı çakışmaz.

## Codex

Repo içindeki `.codex/config.toml` proje-scoped `legalai` kaydını içerir:

```toml
[mcp_servers.legalai]
command = "uv"
args = ["run", "legalai-mcp"]
cwd = "."
```

Projeyi güvenilir olarak açtıktan sonra Codex’i yeniden başlatın veya yeni bir task açın. Aynı yapılandırma Codex desktop, CLI ve IDE yüzeylerinde kullanılabilir.

### uv bulunamazsa: dogrudan Python fallback'i

Bir istemci `uv` komutunu baslatamiyorsa ayni sunucuyu proje ortamindaki Python ile calistirin. Windows ornegi:

```json
{
  "mcpServers": {
    "legalai": {
      "command": "C:\\\\Users\\\\hakan\\\\Desktop\\\\Yargi MCP Fork\\\\legalai-yargi-mcp\\\\.venv\\\\Scripts\\\\python.exe",
      "args": ["-m", "legalai.apps.mcp.server"],
      "cwd": "C:\\\\Users\\\\hakan\\\\Desktop\\\\Yargi MCP Fork\\\\legalai-yargi-mcp"
    }
  }
}
```

Baska Windows kullanicilari kendi mutlak yolunu yazmali. macOS/Linux karsiligi `.venv/bin/python -m legalai.apps.mcp.server` olur. Bu fallback ayni `pyproject.toml` ve `uv.lock` bagimliliklarini kullanir; ortak port veya ayri global Python kurulumu gerektirmez. Ilk kurulum proje kokunde `uv venv --python 3.12` ve `uv sync --frozen --dev` komutlariyla yapilir.

## Cursor

## Kullanici ozel modulleri nasil secer?

## Süreç başlatan belgeyle ön-bilgi toplama

Kullanıcı araç adını bilmek zorunda değildir. Tebligat, dava dilekçesi, ihtar, savunma talebi veya iddianame yükleyip “önce hangi bilgi-belge-delillere ihtiyacın olduğunu çıkar ve tüm çözüm yollarını karşılaştır” demesi yeterlidir. İstemci `socratlegal_onbilgi_ve_strateji` aracını çağırır; belirsiz belgelerde `mode=triage`, daha kapsamlı çalışmada `mode=full_intake` kullanılabilir.

Kullanicinin arac adlarini ezberlemesi gerekmez. Host model, MCP baglantisinda arac aciklamalarini ve parametre semalarini gorur; kullanicinin dogal dildeki talebini uygun araca yonlendirir. Kullanici isterse istemcinin Tools/Prompts panelinden `legalai_yardim` aracini veya `legalai://capabilities` kaynagini acarak yalin, yonlendirilmis ve rafine ornekleri secebilir.

Ornek dogal dil talepleri:

```text
Bu soruyu olay ve dava tarihlerini ayirarak, ictihat ve sure riskleriyle katmanli analiz et.

Benim pozisyonumu karsi taraf avukati gibi test et; en guclu karsi argumanlari ve karsit ictihatlari getir.

Bu olay icin dava, icra, arabuluculuk, idareye basvuru ve Avukatlik Kanunu 35/A dahil genis cozum stratejisi cikar.
```

Prompt menusu bulunan istemcilerde `agresif_karsi_taraf_promptu`, `cozum_stratejisi_promptu` ve `bilir_kisi_raporu_itirazi_promptu` gorulebilir. Bilirkisi raporu itirazi artik uretim akisidir; teknik bulgular, karsi teknik aciklamalar ve bunlarin ilgili hukuk kaynaklariyla baglantilari birlikte degerlendirilir.

## Privacy-first kurali

LegalAI'nin baslattigi Bedesten, AYM, HUDOC ve server-side LLM cagrilarinda PII, dis cagridan once yerel tenant store uzerinden maskelenir. Host modelin ilk kullanici mesajini almadan once MCP'yi cagirip cagiramayacagi istemcinin davranisina baglidir; bu nedenle host/IDE tarafinda privacy-first talimati kullanilmasi onerilir.

Mevcut `.cursor/mcp.json` korunur. Yeni Codex kaydı bu dosyayı değiştirmez ve mevcut `yargi-mcp-fork` kaydını yeniden adlandırmaz. Cursor’da proje MCP ayarlarını yeniden yüklemek yeterlidir.

## Claude, VS Code ve Antigravity

Bu istemcilerde standart yerel MCP/STDIO ayarına şu eşdeğer kaydı ekleyin:

```json
{
  "mcpServers": {
    "legalai": {
      "command": "uv",
      "args": ["run", "legalai-mcp"],
      "cwd": "."
    }
  }
}
```

Antigravity’de Gemini aboneliği host model tarafından kullanılır; LegalAI sunucusuna Gemini API anahtarı vermek zorunlu değildir. Claude ve VS Code’da da aynı host-first STDIO akışı geçerlidir.

## İsteğe bağlı sunucu sentezi

API anahtarı kullananlar `.env` dışında güvenli ortam değişkenleriyle seçim yapabilir:

```text
LEGALAI_LLM_PROVIDER=auto|gemini|openrouter|deepseek|groq
GEMINI_API_KEY=...
OPENROUTER_API_KEY=...
DEEPSEEK_API_KEY=...
GROQ_API_KEY=...
OPENROUTER_MODEL=...
DEEPSEEK_MODEL=...
```

Gerçek anahtarlar ve kullanıcıya özel mutlak yollar repoya yazılmamalıdır. OpenRouter/DeepSeek seçimi host aboneliğinin yerine geçmez; yalnızca sunucu-tarafı sentez açıkça istendiğinde kullanılır.

## Çakışmasız çalışma kuralı

`.codex/config.toml`, `.cursor/mcp.json` ve diğer istemci kayıtları ayrı dosyalardır. Aynı anda çalışmaları için global port, ortak daemon veya zorunlu global geçici dosya yoktur. İstemci ayarları değiştirilmeden önce mevcut dosya yedeklenmeli; bu repo kurulumu hiçbir kullanıcı ayarını üzerine yazmaz.

Bu sprint remote MCP/HTTP hosting kurmaz. Gelecekte remote transport eklenirse domain katmanı ve istemci sözleşmesi korunacaktır.

## Guncelleme ve veri korumasi

Portable surum guncellemeleri `app` katmanini checksum dogrulayarak degistirir; `data`, yerel corpus, belgeler, API anahtarlari ve IDE ayarlari korunur. Basarisiz baslangicta `app.previous` uzerinden rollback yapilabilir. Guncelleme kontrolu yalnizca surum metadata'sidir ve 24 saatlik onbellek araligi kullanir. Ayrintili komutlar icin [kullanici kurulum rehberine](socratlegal-user-install.md) bakin.

## Tek `legalai` kurulumu ile kapsam

Yalnızca `legalai` MCP kaydı kurulduğunda `katmanli_analiz`, soru için Bedesten karar backend’inden Yargıtay/Danıştay belgelerini getirir ve katmanlı analizden geçirir. `derin_arastirma` alt soruları aynı akışa yönlendirir. `agresif_karsi_taraf` ise soru belgelerini aldıktan sonra ürettiği karşı argümanları da aynı backend’de ayrıca arar; dönen karşıt içtihatları künye, belge kimliği ve kısa alıntıyla bağlar.

Bu akış için ayrı `yargi-mcp` server süreci veya hosting gerekmez. `yargi-mcp` yalnızca upstream’de bulunup henüz LegalAI araçlarına taşınmamış bağımsız araçları ayrıca kullanmak isteyenler için opsiyoneldir. Sözleşme inceleme mevcut üretim aracıdır: `socratlegal_sozlesme_incele` veya doğal dilde sözleşme inceleme talebi kullanılabilir. Due diligence ise yol haritasındaki ayrı bir ileri geliştirmedir ve bu kapsamda uygulanmış gibi sunulmaz.
## Komut sözlüğü ve görseller

İstemci `socratlegal_komut_sozlugu` aracını veya `socratlegal://commands` kaynağını okuyarak yetenekleri ve örnek doğal dil istemlerini gösterebilir. `/` menüsünün görünmesi IDE/host özelliğidir; sözlük her hostta kullanılabilir. Strateji yolları gibi ilişkilerde SocratLegal Mermaid ve tablo fallback'i sunabilir; grafik desteklemeyen hostta tablo/metin gösterilir.

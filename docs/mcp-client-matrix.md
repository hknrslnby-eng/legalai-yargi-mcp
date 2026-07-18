# LegalAI MCP istemci matrisi

Bu sayfa aynı LegalAI sunucusunun farklı yerel IDE ve CLI istemcilerinde nasıl kullanılacağını gösterir. İstemcilerin menü adları ve ayar dosyası konumları değişebilir; ortak nokta yerel STDIO MCP sunucusudur.

## Ortak komut

Her istemci için temel sunucu komutu:

```text
uv run --directory "<FORK_KLASORU>" legalai-mcp
```

`<FORK_KLASORU>` yerine kendi fork klasörünüzü yazın. Komut proje bağımlılıklarını `uv` ile çalıştırır; ortak port, global daemon veya hosting gerektirmez.

## İstemci karşılaştırması

| İstemci | Ayar biçimi | Kullanıcı ne yapar? |
|---|---|---|
| Codex | Proje veya kullanıcı TOML MCP ayarı | `legalai` kaydını açar, projeyi trusted olarak çalıştırır, yeni task veya yeniden başlatma sonrası tools listesini yeniler. |
| Cursor | Proje veya kullanıcı JSON MCP ayarı | Mevcut `legalai` kaydını korur; `yargi-mcp-fork` kaydı varsa silmez; MCP panelinden yeniden bağlanır. |
| Claude | MCP servers JSON/ayar ekranı | `legalai` için STDIO sunucusu ekler ve proje klasörünü çalışma dizini olarak seçer. |
| Antigravity | MCP servers ayar ekranı veya workspace ayarı | Gemini aboneliğini host model olarak kullanır; LegalAI için ayrıca Gemini API key gerekmez. |
| VS Code | MCP servers/Settings JSON veya eklenti ayarı | Workspace veya kullanıcı alanında aynı STDIO komutunu kaydeder. |

Örnek JSON biçimi kullanan istemciler için:

```json
{
  "mcpServers": {
    "legalai": {
      "command": "uv",
      "args": ["run", "--directory", "<FORK_KLASORU>", "legalai-mcp"]
    }
  }
}
```

Codex için biçim TOML'dur:

```toml
[mcp_servers.legalai]
command = "uv"
args = ["run", "--directory", "<FORK_KLASORU>", "legalai-mcp"]
```

Mevcut ayarları silmeyin, yeniden adlandırmayın veya üzerine yazmayın. Özellikle Cursor'daki mevcut `yargi-mcp-fork` kaydı LegalAI kaydından bağımsızdır.

## İlk bağlantı testi

Her istemcide aynı sırayı uygulayın:

1. Projeyi açın ve MCP ayarını yeniden yükleyin.
2. `legalai_saglik_kontrolu` aracını çalıştırın.
3. Şu sonucu arayın: `status=ok`, `external_calls=false`.
4. `legalai_yardim` aracını çalıştırın.
5. `legalai://capabilities` resource paneli varsa kaynağı açın.
6. Sohbete doğal dilde soru yazın; araç adlarını ezberlemeniz gerekmez.

Health-check dış API çağırmaz. Bu nedenle health-check başarılı olsa bile hukuk veritabanı erişimi ayrıca gerçek bir arama sorusuyla sınanır.

## İstemci aboneliği ve API key ayrımı

Codex/ChatGPT, Claude veya Antigravity/Gemini aboneliği host modelin cevabı yazmasını sağlar. LegalAI'nin Bedesten, AYM ve HUDOC aramalarını kullanmak için ayrıca upstream MCP server kurmanız gerekmez; LegalAI fork'u kendi backend akışını kullanır.

OpenRouter, DeepSeek veya başka server-side LLM sağlayıcıları yalnızca ilgili API key `.env` içinde yapılandırılırsa ve server-side synthesis seçilirse devreye girer. API key'leri config dosyasına yazmayın.

## Sorun giderme

- **`legalai` görünmüyor:** Proje klasörünün doğru açıldığını, `uv sync --frozen --dev` çalıştığını ve istemcinin MCP ayarını yeniden yüklediğinizi kontrol edin.
- **Health-check çağrılamıyor:** Komutun `<FORK_KLASORU>` değerini doğru aldığını ve `uv run --directory "<FORK_KLASORU>" legalai-mcp` komutunu terminalde çalıştırabildiğinizi kontrol edin.
- **Araç görünüyor ama sonuç boş:** Bu bağlantıdan farklı bir konudur; Bedesten/AYM/HUDOC erişimi, sorgu kapsamı veya eksik olay bilgileri trace ve assumptions alanlarında incelenmelidir.
- **Cursor bozuldu:** Mevcut `.cursor/mcp.json` içeriğini geri yüklemek yerine önce değişikliğin yalnızca `legalai` kaydında olup olmadığını kontrol edin; LegalAI kurulumu `yargi-mcp-fork` kaydını değiştirmemelidir.

Tüm çıktılar `analysis_only` ve `non_binding` niteliğindedir; kesin veya bağlayıcı hukukî görüş değildir.

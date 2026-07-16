# LegalAI MCP istemci kurulumu

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

## Tek `legalai` kurulumu ile kapsam

Yalnızca `legalai` MCP kaydı kurulduğunda `katmanli_analiz`, soru için Bedesten karar backend’inden Yargıtay/Danıştay belgelerini getirir ve katmanlı analizden geçirir. `derin_arastirma` alt soruları aynı akışa yönlendirir. `agresif_karsi_taraf` ise soru belgelerini aldıktan sonra ürettiği karşı argümanları da aynı backend’de ayrıca arar; dönen karşıt içtihatları künye, belge kimliği ve kısa alıntıyla bağlar.

Bu akış için ayrı `yargi-mcp` server süreci veya hosting gerekmez. `yargi-mcp` yalnızca upstream’de bulunup henüz LegalAI araçlarına taşınmamış bağımsız araçları ayrıca kullanmak isteyenler için opsiyoneldir. Sözleşme inceleme ve due diligence ise yol haritasındaki ileri geliştirme özellikleridir; mevcut kurulumda uygulanmış gibi sunulmaz.

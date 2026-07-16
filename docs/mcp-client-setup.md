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

# SocratLegal local setup

Normal kullanıcı için [portable kullanıcı kurulum rehberini](socratlegal-user-install.md) izleyin. Portable paket Python/uv kurulumu ve hosting gerektirmez; aşağıdaki checkout yolu geliştiriciler içindir.

SocratLegal is the public name of this fork. The local Python package can keep
the `legalai` name for compatibility, while new MCP clients should register
`socratlegal-mcp`.

```powershell
uv sync --frozen --dev
uv run socratlegal-mcp
```

The server is stdio/local and does not require hosting. The local database is
`.data/socratlegal_corpus.db` and is ignored by Git. It can contain selected
public decisions, regulations, official guides, sector reports, doctrine and
other permitted sources. `socratlegal_corpus_durum` reports its status and
`socratlegal_corpus_belge_ekle` ingests a normalized public document.

Retrieval is federated: local corpus and live official adapters are queried in
parallel. Bedesten remains a live branch even when no Yargıtay or Danıştay
documents have been downloaded. Rekabet and KİK live adapters are keyword
gated; KVKK is enabled only when `BRAVE_API_TOKEN` is explicitly configured.
Missing sources are reported as unavailable and do not erase other hits.

Active public tools include:

- `socratlegal_katmanli_analiz`
- `socratlegal_agresif_karsi_taraf`
- `socratlegal_derin_arastirma`
- `socratlegal_bilirkisi_raporu_analiz`
- `socratlegal_bilirkisi_raporu_dilekce`
- `socratlegal_onbilgi_ve_strateji`
- `socratlegal_dilekce_hazirla`, `socratlegal_dilekce_incele`, `socratlegal_dilekce_kisalt`, `socratlegal_dilekce_uzat`
- `socratlegal_komut_sozlugu` and resource `socratlegal://commands`
- `socratlegal_corpus_durum` and `socratlegal_corpus_belge_ekle`

The old `legalai_*` names remain aliases. In Cursor, rename only the visible
server key in the user-local MCP configuration if desired; keep its command,
arguments and working directory unchanged. Do not commit that local file.

All external calls must pass through local PII masking. Outputs are
analysis-only and non-binding; citations, temporal dates, technical claims and
missing evidence require qualified human review.

The KDK and TİHEK HTML collection adapters are keyword-gated and use official
public collection pages. They are availability-tolerant: a site layout change
is reported as a source failure rather than converted into invented evidence.

The Reklam Kurulu adapter uses the official Ministry of Trade decision collection,
is keyword-gated, and preserves decision title, citation, official URL and live
retrieval provenance. Tests inject HTML fixtures and do not require a live site.

Image reports are accepted. Expert-report analysis and petition generation are active production flows. For OCR, install the optional Python extra with
`uv sync --extra ocr`; Windows still needs a local Tesseract executable and
Turkish language data. Without an OCR engine the tool returns `ocr_required`
and does not pretend that the image was read.

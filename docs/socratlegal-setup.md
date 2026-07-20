# SocratLegal local setup

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
- `socratlegal_corpus_durum` and `socratlegal_corpus_belge_ekle`

The old `legalai_*` names remain aliases. In Cursor, rename only the visible
server key in the user-local MCP configuration if desired; keep its command,
arguments and working directory unchanged. Do not commit that local file.

All external calls must pass through local PII masking. Outputs are
analysis-only and non-binding; citations, temporal dates, technical claims and
missing evidence require qualified human review.

"""HudocClient — AİHM/HUDOC veritabanına erişim.

Bkz. FORK-KAPSAMLI-PLAN.md §4. HUDOC'un resmi/belgelenmiş bir REST API'si
yok; burada kullanılan `/app/query/results` (arama, JSON) ve
`/app/conversion/docx/html/body` (belge metni, HTML) endpoint'leri
HUDOC'un kendi web arayüzünün arka planında kullandığı, halka açık ama
belgelenmemiş endpoint'lerdir (doğrulama: 15 Temmuz 2026'da canlı olarak
test edildi). Bu yapı HUDOC tarafında haber verilmeden değişebilir; bu
yüzden `search()`/`get_document_html()` başarısız olursa çağıran taraf
bunu bir entegrasyon hatası olarak ele almalı.

Nezaket kuralları (§4.3):
- Varsayılan hız sınırı: saatte 60 istek (`RateLimiter`).
- Tanımlayıcı bir `User-Agent` gönderilir.
- `https://hudoc.echr.coe.int/robots.txt` bu yazının tarihinde açık bir
  `Disallow` kuralı içermiyor (SPA ana sayfasına yönleniyor); yine de
  agresif toplu indirme yapılmaz.
"""
from __future__ import annotations

from typing import Any

import httpx

from legalai.packages.aihm.parser import html_to_text
from legalai.packages.aihm.rate_limiter import RateLimiter
from legalai.packages.pii.outbound import mask_for_external

BASE_URL = "https://hudoc.echr.coe.int"
USER_AGENT = "LegalAI-Fork/0.1 (+github.com/hknrslnby-eng/legalai-yargi-mcp)"

SEARCH_SELECT_FIELDS = (
    "itemid,docname,doctype,appno,extractedappno,kpdate,kpdateAsText,article,"
    "importance,languageisocode,respondent,originatingbody,typedescription,"
    "documentcollectionid"
)


class HudocClient:
    def __init__(self, rate_limiter: RateLimiter | None = None, timeout: float = 20.0) -> None:
        self._rate_limiter = rate_limiter or RateLimiter(max_requests=60, period_seconds=3600.0)
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "HudocClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    def _build_query(
        self,
        query: str,
        respondent: str | None,
        article: str | None,
        importance: int | None,
        date_from: str | None,
        date_to: str | None,
        appno: str | None,
    ) -> str:
        clauses = ["contentsitename:ECHR", '(documentcollectionid:"JUDGMENTS")']
        if respondent:
            clauses.append(f'(respondent:"{respondent}")')
        if appno:
            clauses.append(f'(appno:"{appno}")')
        if article:
            clauses.append(f'(article:"{article}")')
        if importance:
            clauses.append(f"(importance:{int(importance)})")
        if date_from or date_to:
            lo = date_from or "1959-01-01"
            hi = date_to or "2100-01-01"
            clauses.append(f'(kpdate>="{lo}" AND kpdate<="{hi}")')
        if query:
            safe_query = query.replace('"', "'")
            clauses.append(f'("{safe_query}")')
        return " AND ".join(clauses)

    async def search(
        self,
        query: str = "",
        respondent: str | None = "TUR",
        article: str | None = None,
        importance: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        appno: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        query = await mask_for_external(query)
        params = {
            "query": self._build_query(query, respondent, article, importance, date_from, date_to, appno),
            "select": SEARCH_SELECT_FIELDS,
            "sort": "",
            "start": 0,
            "length": limit,
        }

        await self._rate_limiter.acquire()
        response = await self._client.get("/app/query/results", params=params)
        response.raise_for_status()
        data = response.json()
        return [item["columns"] for item in data.get("results", [])]

    async def get_document_html(self, itemid: str) -> str:
        await self._rate_limiter.acquire()
        response = await self._client.get(
            "/app/conversion/docx/html/body", params={"library": "ECHR", "id": itemid}
        )
        response.raise_for_status()
        return response.text

    async def get_document_text(self, itemid: str) -> str:
        html = await self.get_document_html(itemid)
        return html_to_text(html)

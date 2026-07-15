"""LegalAI MCP sunucusu — Hafta 2 iskeleti.

`katmanli_analiz` aracı bu aşamada gerçek belge getirme (retrieve) YAPMAZ;
FORK-KAPSAMLI-PLAN.md §10 Hafta 2 kabul kriterine göre sabit bir test
fixture'ı üzerinden Pipeline'ı çalıştırıp sonucu döner. Gerçek RAG
entegrasyonu Hafta 7'de (§5.3, VerifiedCitationCheck ile birlikte)
eklenecek.
"""
from __future__ import annotations

from fastmcp import FastMCP

from legalai.packages.aihm.service import aihm_karar_ara as _aihm_karar_ara
from legalai.packages.aihm.service import aihm_karar_getir as _aihm_karar_getir
from legalai.packages.layers.citation_transfer_filter import CitationTransferFilter
from legalai.packages.layers.dissent_detector import DissentDetector
from legalai.packages.layers.pipeline import Context, Pipeline
from legalai.packages.layers.ratio_dictum import RatioDictumFilter
from legalai.packages.shared.types import Document

app = FastMCP(name="LegalAI MCP Server", version="0.1.0")

_FIXTURE_DOCUMENT = Document(
    id="fixture-1",
    source="yargitay",
    citation="Yargıtay 3. HD, 2023/1234 E., 2023/5678 K. (test fixture)",
    body=(
        "Davacı vekili, müvekkilinin zararının tazminini talep etmiştir. "
        "Davalı, zararın oluşmadığını savunmuştur. "
        "İlk derece mahkemesi davayı kısmen kabul etmiştir. "
        "Bilirkişi raporunda zarar miktarı hesaplanmıştır. "
        "Dairemizce yapılan incelemede, yerleşik içtihat gereği zarar "
        "ile kusur arasında illiyet bağı bulunduğu görülmüştür. "
        "Sonuç olarak, ilk derece mahkemesi kararının onanmasına karar verilmiştir. "
        "Hemen ifade edelim ki, bu tür davalarda ispat yükü davacıdadır.\n\n"
        "KARŞI OY\n"
        "Sayın çoğunluğun görüşüne katılmıyorum; zarar miktarının yeniden "
        "hesaplanması için dosyanın bozulması gerektiği düşüncesindeyim."
    ),
)

_pipeline = Pipeline(layers=[RatioDictumFilter(), DissentDetector(), CitationTransferFilter()])


@app.tool(
    description=(
        "Bir hukuki soruyu, yargı türüne özgü katmanlardan (ratio/dictum "
        "ayrımı, karşı oy tespiti, taraf aktarım cümlesi filtreleme) "
        "geçirerek analiz eder. Hafta 2 iskeletinde gerçek belge getirme "
        "yerine sabit bir test fixture'ı kullanılır; sonuçlar gerçek "
        "hukuki tavsiye değildir."
    ),
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def katmanli_analiz(question: str, mode: str = "standard") -> dict:
    ctx = Context(
        tenant_id="local",
        question=question,
        mode=mode,
        documents=[
            Document(
                id=_FIXTURE_DOCUMENT.id,
                source=_FIXTURE_DOCUMENT.source,
                citation=_FIXTURE_DOCUMENT.citation,
                body=_FIXTURE_DOCUMENT.body,
            )
        ],
    )
    result = await _pipeline.run(ctx)
    return {
        "question": result.question,
        "mode": result.mode,
        "ratios": result.ratios,
        "dictums": result.dictums,
        "dissents": result.dissents,
        "trace": result.trace,
        "note": "Bu bir fixture cevabıdır; gerçek belge getirme Hafta 7'de eklenecek.",
    }


@app.tool(
    description=(
        "AİHM/HUDOC veritabanında karar arar (bkz. FORK-KAPSAMLI-PLAN.md §4.2). "
        "Varsayılan olarak Türkiye'ye karşı açılan davalarla sınırlıdır "
        "(respondent='TUR'); bunu değiştirebilir veya None geçerek kaldırabilirsiniz."
    ),
    annotations={"readOnlyHint": True, "openWorldHint": True, "idempotentHint": True},
)
async def aihm_karar_ara(
    query: str = "",
    respondent: str = "TUR",
    article: str | None = None,
    importance: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> list[dict]:
    return await _aihm_karar_ara(
        query=query,
        respondent=respondent,
        article=article,
        importance=importance,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


@app.tool(
    description=(
        "Bir AİHM başvuru numarasına (application_no, örn. '47533/99') karşılık "
        "gelen kararın tam metnini bölümlere ayrılmış olarak getirir (PROCEDURE, "
        "THE FACTS, THE LAW, operative, varsa ayrı görüş). Türkçe çeviri yoktur; "
        "EN veya FR döner. Sonuçlar 30 gün önbelleğe alınır."
    ),
    annotations={"readOnlyHint": True, "openWorldHint": True, "idempotentHint": True},
)
async def aihm_karar_getir(application_no: str, lang: str = "en") -> dict:
    return await _aihm_karar_getir(application_no=application_no, lang=lang)


def main() -> None:
    app.run()


if __name__ == "__main__":
    main()

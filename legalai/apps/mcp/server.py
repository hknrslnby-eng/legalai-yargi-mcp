"""LegalAI MCP sunucusu.

`katmanli_analiz` aracı, gerçek belge getirme (RetrieveDocuments →
Bedesten API) + rerank + tüm jurisdiction-aware katmanları çalıştırır
(bkz. FORK-KAPSAMLI-PLAN.md §5.3). ÖNEMLİ MİMARİ KARAR: bu araç kendi
başına bir LLM'e API çağrısı YAPMAZ (`synthesize=False`) — MCP sunucusu
bir LLM değildir, sadece veri/analiz sağlar; nihai kaynaklı cevabı bu
aracı çağıran HOST MODEL (Cursor/Claude Desktop/ChatGPT-Codex/
Antigravity içindeki, kullanıcının zaten sahip olduğu abonelikle çalışan
model) `assistant_instructions` talimatına göre yazar. Böylece hiçbir
ek API anahtarı gerekmez — sadece `legalai` MCP sunucusunun kurulu
olması yeterlidir (bkz. §13 Çoklu İstemci Uyumluluğu).

`POST /api/v1/analyze` HTTP endpoint'i ise (host model olmayan
senaryolar için, örn. gelecekteki web UI) aynı `run_pipeline`
fonksiyonunu `synthesize=True` ile çağırır — bu durumda `LLMRouter`
üzerinden gerçek bir LLM API anahtarı gerekir (bkz. §2.6).
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from legalai.packages.aihm.aym_bridge import aihm_aym_kopru as _aihm_aym_kopru
from legalai.packages.aihm.service import aihm_karar_ara as _aihm_karar_ara
from legalai.packages.aihm.service import aihm_karar_getir as _aihm_karar_getir
from legalai.packages.layers.analysis_pipeline import run_pipeline
from legalai.packages.layers.citation_validator import validate_citations
from legalai.packages.layers.deep_research import run_deep_research
from legalai.packages.layers.memorandum import MemorandumProfile, build_memorandum_instructions, memorandum_section_ids
from legalai.packages.layers.opposing import run_opposing
from legalai.packages.discovery.catalog import capability_catalog
from legalai.packages.pii.gateway import PiiGateway
from legalai.packages.shared.settings import settings
from legalai.packages.shared.tenant import TenantContext, set_tenant
from legalai.packages.bilirkisi.workflow import analyze_report, build_petition_draft
from legalai.packages.contracts.models import ContractReviewRequest
from legalai.packages.contracts.review import review_contract
from legalai.packages.corpus.models import CorpusDocument
from legalai.packages.installer.update import UpdateError, archive_download_url, check_remote_update
from legalai.packages.corpus.store import CorpusStore
from legalai.packages.corpus.sync import CorpusSyncService
from legalai.packages.corpus.sources.official import build_default_priority_adapters

# Süreç başlarken tenant bağlamı kurulur — bkz. FORK-KAPSAMLI-PLAN.md §2.2.
# Bugün her zaman "local"; sunucuya taşındığında bu satır middleware'e taşınır.
set_tenant(TenantContext(tenant_id=settings.tenant_id, tenant_name=settings.tenant_name))

app = FastMCP(name="SocratLegal MCP Server", version="0.1.0")
_pii_gateway = PiiGateway()

ApplicationNo = Annotated[str, Field(description="AİHM başvuru numarası; örn. 47533/99.")]
LanguageCode = Annotated[str, Field(description="Tam metin dili; 'en' veya 'fr'.")]
LegalQuestion = Annotated[str, Field(description="Araştırılacak hukuki soru veya uyuşmazlık.")]
JurisdictionHint = Annotated[str | None, Field(description="İsteğe bağlı yargı türü veya hukuk alanı ipucu.")]
DetailLevel = Annotated[str, Field(description="Çıktı ayrıntısı: brief, standard, deep veya exhaustive.")]


@app.tool(
    name="legalai_yardim",
    description=(
        "LegalAI'nin yalın kullanımdan rafine analize kadar tüm mevcut yeteneklerini, "
        "hangi talepte hangisinin seçileceğini ve kopyalanabilir örnek promptları listeler. "
        "Kullanıcı araç adlarını bilmiyorsa önce bu aracı çağır. PII ve non-binding sınırlarını da gösterir."
    ),
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def _legalai_yardim_tool() -> dict:
    return capability_catalog()


async def legalai_yardim() -> dict:
    """Directly awaitable Python facade; FastMCP registers the same tool."""
    return await _legalai_yardim_tool.fn()


@app.tool(
    name="legalai_saglik_kontrolu",
    description="LegalAI MCP bağlantısını dış API çağırmadan kontrol eder.",
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def _legalai_saglik_kontrolu_tool() -> dict[str, object]:
    return {"status": "ok", "version": app.version, "external_calls": False}


async def legalai_saglik_kontrolu() -> dict[str, object]:
    """Directly awaitable local health-check facade."""
    return await _legalai_saglik_kontrolu_tool.fn()


@app.resource(
    "legalai://capabilities",
    name="legalai_capabilities",
    description="LegalAI capability catalog, routing guidance and privacy policy.",
    mime_type="application/json",
)
def _legalai_capabilities_resource() -> str:
    return json.dumps(capability_catalog(), ensure_ascii=False, indent=2)


def legalai_capabilities_resource() -> str:
    """Directly callable facade for local tests and non-MCP integrations."""
    return _legalai_capabilities_resource.fn()


@app.prompt(
    name="agresif_karsi_taraf_promptu",
    description="Karşı taraf argümanları, karşıt içtihatlar ve geniş çözüm stratejisi için yönlendirilmiş prompt.",
)
def agresif_karsi_taraf_promptu() -> str:
    return (
        "Kullanıcının olayını ve pozisyonunu karşı taraf avukatı gibi test et. "
        "En güçlü karşı argümanları, zayıf noktaları, karşıt içtihatları ve dava dışı çözüm yollarını "
        "ayrı başlıklarda ver. Olay/dava tarihlerini, süreleri, görev-yetki ihtimallerini ve belirsizlikleri "
        "göster. Her kaynak için künye ve kısa ilgili alıntı kullan; sonuç analysis-only ve non-binding'dir."
    )


@app.prompt(
    name="cozum_stratejisi_promptu",
    description="Dava dışı ve dava içi tüm hukuki çözüm yollarını karşılaştırmak için yönlendirilmiş prompt.",
)
def cozum_stratejisi_promptu() -> str:
    return (
        "Sorunun çözümü için dava, icra, idare/kurul başvurusu, ceza süreci, arabuluculuk, "
        "Avukatlık Kanunu 35/A, sulh, feragat ve ibra ihtimallerini koşullu biçimde karşılaştır. "
        "Yetkili merci, süre, ön şart, delil etkisi, geri döndürülebilirlik ve riskleri kaynaklarla göster."
    )


@app.prompt(
    name="bilir_kisi_raporu_itirazi_promptu",
    description="Planlanan teknik bilirkişi raporu itiraz modülü için kullanıcıdan doğru girdileri toplar.",
)
def bilir_kisi_raporu_itirazi_promptu() -> str:
    return (
        "Bilirkişi raporunu yükle veya ilgili bölümleri belirt; rapor tarihi, olay/ölçüm tarihi, dava tarihi, "
        "uzmanlık alanı ve itiraz edilmek istenen sonuçları ekle. Üretim akışı teknik alanı rapordan çıkarmaya, "
        "teknik bulguları alternatif hipotezlerle sınamaya, karşı teknik argümanları ve ilgili esas hukuk bağlantılarını "
        "kurmaya çalışır; HMK m.266 ve m.279-281 usul çıpası olarak ayrıca değerlendirilir. Teknik sonuçlar uzman raporu "
        "değildir; eksik veri, belirsizlik, kaynak ve insan uzman/avukat incelemesi açıkça gösterilir."
    )


@app.tool(
    description=(
        "Bir hukuki soruyla ilgili GERÇEK Yargıtay/Danıştay kararlarını "
        "getirir (Bedesten API) ve katmanlı hukuki analizden geçirir: "
        "sözcük örtüşmesine göre rerank, yargı türü tespiti, ratio/dictum "
        "ayrımı, karşı oy tespiti, taraf aktarım cümlesi filtreleme, "
        "argüman gücü puanlama. BU ARAÇ NİHAİ CEVABI YAZMAZ — sen (bu "
        "aracı çağıran asistan), dönen `documents`/`ratios`/`dictums`/"
        "`dissents`/`argument_scores` alanlarını ve `assistant_instructions` "
        "talimatını kullanarak kullanıcıya [#belge_id] ile kaynaklı, "
        "kaynaksız iddia içermeyen bir cevap yaz. API anahtarı GEREKMEZ. "
        "Sonuçlar gerçek hukuki tavsiye değildir; kullanıcıya bunu belirt."
    ),
    annotations={"readOnlyHint": True, "openWorldHint": True, "idempotentHint": True},
)
async def katmanli_analiz(
    question: LegalQuestion,
    mode: Annotated[str, Field(description="Analiz modu; layered veya simple.")] = "layered",
    jurisdiction_hint: JurisdictionHint = None,
    quality_profile: Annotated[str, Field(description="Model kalite profili: auto, fast, balanced, frontier veya exhaustive.")] = "auto",
    model_hint: Annotated[str, Field(description="İsteğe bağlı model adı; kalite sözleşmesi için ipucudur.")] = "",
) -> dict:
    result = await run_pipeline(
        question=question,
        mode=mode,
        jurisdiction_hint=jurisdiction_hint,
        synthesize=False,
        quality_profile=quality_profile,
        model_hint=model_hint,
    )
    return result.to_dict()


@app.tool(
    name="agresif_karsi_taraf",
    description=(
        "Agresif karşı taraf ve geniş hukuki çözüm stratejisi analizi yapar: "
        "karşı argümanlar, karşıt kaynaklar, olay/dava tarihi ve yürürlük bağlamı, "
        "zamanaşımı/hak düşürücü süre riskleri, görev-yetki/kurum adayları ve "
        "dava dışı çözüm yollarını birlikte döndürür. Avukatlık Kanunu m.35/A, "
        "sulh/feragat/ibra, arabuluculuk, icra, idari başvuru ve somut suç sinyali "
        "varsa ceza yolu koşullu değerlendirilir. Bu araç nihai veya bağlayıcı "
        "hukuki görüş değildir; host model evidence künye ve kısa alıntıları "
        "kullanarak nonbinding bir araştırma taslağı yazmalıdır. API anahtarı "
        "olmayan Codex/ChatGPT, Claude, Cursor, VS Code ve Antigravity hostlarıyla "
        "çalışır; sunucu sentezi isteğe bağlıdır."
    ),
    annotations={"readOnlyHint": True, "openWorldHint": True, "idempotentHint": True},
)
async def _agresif_karsi_taraf_tool(
    question: LegalQuestion,
    position: Annotated[str, Field(description="Kullanıcının veya temsil edilen tarafın hukuki pozisyonu.")],
    role: Annotated[str, Field(description="Taraf rolü; varsayılan davacı.")] = "davacı",
    jurisdiction_hint: JurisdictionHint = None,
    source_scope: Annotated[str, Field(description="Kaynak kapsamı; targeted veya all.")] = "targeted",
    selected_source_ids: Annotated[list[str] | None, Field(description="İsteğe bağlı seçili kaynak kimlikleri.")] = None,
    quality_profile: Annotated[str, Field(description="Model kalite profili: auto, fast, balanced, frontier veya exhaustive.")] = "auto",
    model_hint: Annotated[str, Field(description="İsteğe bağlı model adı; kalite sözleşmesi için ipucudur.")] = "",
) -> dict:
    result = await run_opposing(
        question=question,
        position=position,
        role=role,
        jurisdiction_hint=jurisdiction_hint,
        source_scope=source_scope,
        selected_source_ids=selected_source_ids,
        synthesize=False,
        quality_profile=quality_profile,
        model_hint=model_hint,
    )
    return result.to_dict()


async def agresif_karsi_taraf(
    question: str,
    position: str,
    role: str = "davacı",
    jurisdiction_hint: str | None = None,
    source_scope: str = "targeted",
    selected_source_ids: list[str] | None = None,
    quality_profile: str = "auto",
    model_hint: str = "",
) -> dict:
    """Keep the Python API directly awaitable while FastMCP registers the tool."""
    return await _agresif_karsi_taraf_tool.fn(
        question=question,
        position=position,
        role=role,
        jurisdiction_hint=jurisdiction_hint,
        source_scope=source_scope,
        selected_source_ids=selected_source_ids,
        quality_profile=quality_profile,
        model_hint=model_hint,
    )


@app.tool(
    description=(
        "Karmaşık bir hukuki soruyu ALT SORULARA bölerek araştırır (bkz. "
        "FORK-KAPSAMLI-PLAN.md §5.2, Hafta 8). `.env`'de bir LLM anahtarı "
        "(GEMINI_API_KEY/GROQ_API_KEY/DEEPSEEK_API_KEY) YOKSA (varsayılan "
        "durum): sunucu kendi planlama yapmaz; `subquestions` (aday alt "
        "sorular) + `instructions` alanını döner — SEN (bu aracı çağıran "
        "asistan) bu alt soruların her biri için `katmanli_analiz`'i çağırıp "
        "kendi sentezini yaparsın (host-orkestrasyonlu mod, API anahtarı "
        "GEREKMEZ). Bir LLM anahtarı VARSA: sunucu Planner→Researcher→"
        "Critic→Editor döngüsünü kendi içinde tam otomatik yürütür ve "
        "`answer` alanında kaynaklı, hazır bir sentez döner. `depth` ve "
        "`detail_level` (brief/standard/deep/exhaustive) "
        "en fazla kaç alt soruya bölüneceğini sınırlar."
    ),
    annotations={"readOnlyHint": True, "openWorldHint": True, "idempotentHint": True},
)
async def derin_arastirma(
    question: LegalQuestion,
    depth: Annotated[int, Field(description="Alt soru derinliği; 1 ile 5 arasında.")] = 3,
    detail_level: DetailLevel = "deep",
) -> dict:
    if not settings.enable_deep_research:
        return {
            "question": question,
            "mode": "disabled",
            "answer": None,
            "citations": [],
            "note": "Derin araştırma özelliği .env'de ENABLE_DEEP_RESEARCH=false ile kapatılmış.",
        }
    result = await run_deep_research(question=question, depth=depth, detail_level=detail_level)
    return result.to_dict()


@app.tool(
    description=(
        "Saf doğrulama aracı — LLM ÇAĞIRMAZ, API anahtarı GEREKMEZ. Bir "
        "taslak cevap metnindeki `[#belge_id]` referanslarının, verdiğin "
        "gerçek belge kimlikleri listesinde (known_doc_ids — `katmanli_analiz` "
        "veya `derin_arastirma` çağrılarından topladığın id'ler) GERÇEKTEN "
        "bulunup bulunmadığını kontrol eder. Host-orkestrasyonlu (API "
        "anahtarsız) akışlarda, kendi yazdığın cevabı kullanıcıya sunmadan "
        "ÖNCE bu araçla kontrol et; `invalid_citations` boş değilse cevabını "
        "düzelt."
    ),
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def alinti_dogrula(
    answer: Annotated[str, Field(description="Belge kimlikleriyle atıflanmış taslak cevap metni.")],
    known_doc_ids: Annotated[list[str], Field(description="Arama araçlarından elde edilen geçerli belge kimlikleri.")],
) -> dict:
    return validate_citations(answer, known_doc_ids).to_dict()


@app.tool(
    description=(
        "AİHM/HUDOC veritabanında karar arar (bkz. FORK-KAPSAMLI-PLAN.md §4.2). "
        "Varsayılan olarak Türkiye'ye karşı açılan davalarla sınırlıdır "
        "(respondent='TUR'); bunu değiştirebilir veya None geçerek kaldırabilirsiniz."
    ),
    annotations={"readOnlyHint": True, "openWorldHint": True, "idempotentHint": True},
)
async def aihm_karar_ara(
    query: Annotated[str, Field(description="AİHM/HUDOC kararlarında aranacak ifade.")] = "",
    respondent: Annotated[str, Field(description="Başvurunun yöneldiği devlet kodu; varsayılan TUR.")] = "TUR",
    article: Annotated[str | None, Field(description="İsteğe bağlı AİHS madde numarası.")] = None,
    importance: Annotated[int | None, Field(description="İsteğe bağlı önem seviyesi filtresi.")] = None,
    date_from: Annotated[str | None, Field(description="Başlangıç tarihi; YYYY-MM-DD.")] = None,
    date_to: Annotated[str | None, Field(description="Bitiş tarihi; YYYY-MM-DD.")] = None,
    limit: Annotated[int, Field(description="Döndürülecek azami karar sayısı.")] = 20,
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
async def aihm_karar_getir(application_no: ApplicationNo, lang: LanguageCode = "en") -> dict:
    return await _aihm_karar_getir(application_no=application_no, lang=lang)


@app.tool(
    description=(
        "Bir AYM (Anayasa Mahkemesi) bireysel başvuru numarası için, aynı "
        "olayda AİHM'e (HUDOC) yapılmış olabilecek paralel başvuruları "
        "bulmayı dener (bkz. FORK-KAPSAMLI-PLAN.md §4.5). İsim eşleştirme + "
        "tarih penceresi kullanır; KESİN eşleştirme yapmaz, sadece "
        "\"muhtemel eşleşme\" adayları döner — kullanıcı her adayı "
        "`aihm_karar_getir` ile inceleyip kendisi teyit etmelidir."
    ),
    annotations={"readOnlyHint": True, "openWorldHint": True, "idempotentHint": True},
)
async def aihm_aym_kopru(
    aym_basvuru_no: Annotated[str, Field(description="Anayasa Mahkemesi bireysel başvuru numarası.")],
) -> dict:
    return await _aihm_aym_kopru(aym_basvuru_no=aym_basvuru_no)


@app.tool(
    description=(
        "Bir metindeki yapılandırılmış kişisel verileri (TCKN, telefon, "
        "e-posta, IBAN, plaka) geri döndürülebilir şekilde maskeler — "
        "FORK-KAPSAMLI-PLAN.md Hafta 6, aşama 1 (regex tabanlı; isim/kurum "
        "tanıma NER modeli henüz eklenmedi). Maskelenen değerler bu "
        "tenant için şifreli olarak SQLite'ta saklanır; `pii_ac` ile geri "
        "açılabilir."
    ),
    annotations={"readOnlyHint": False, "idempotentHint": True},
)
async def pii_maskele(
    metin: Annotated[str, Field(description="Dış aramadan önce yerelde maskelenecek metin.")],
) -> str:
    return await _pii_gateway.mask(metin)


@app.tool(
    description=(
        "`pii_maskele` ile maskelenmiş bir metindeki [TCKN_1], [IBAN_1] gibi "
        "yer tutucuları, bu tenant için saklanan şifreli değerlerden geri "
        "açar. Aynı oturumda çağrılan `pii_maskele` sonuçları için çalışır."
    ),
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def pii_ac(
    metin: Annotated[str, Field(description="Aynı yerel oturumda maskelenmiş yer tutucuları içeren metin.")],
) -> str:
    return await _pii_gateway.unmask(metin)


# Public SocratLegal names are additive aliases. The original LegalAI Python
# package and tool names remain registered so existing Cursor/Claude configs do
# not break during the branding transition.
@app.tool(name="socratlegal_yardim", description="SocratLegal yetenek kataloğu ve yönlendirme yardımı.")
async def _socratlegal_yardim_tool() -> dict:
    return capability_catalog()


async def socratlegal_yardim() -> dict:
    return await _socratlegal_yardim_tool.fn()


@app.tool(name="legalai_yardim", description="Geçiş uyumluluğu: SocratLegal yetenek kataloğu.")
async def _legacy_legalai_yardim_tool() -> dict:
    return capability_catalog()


@app.tool(name="socratlegal_saglik_kontrolu", description="SocratLegal yerel MCP sağlık kontrolü.")
async def _socratlegal_health_tool() -> dict[str, object]:
    return {"status": "ok", "version": app.version, "external_calls": False}


async def socratlegal_saglik_kontrolu() -> dict[str, object]:
    return await _socratlegal_health_tool.fn()


@app.tool(name="legalai_saglik_kontrolu", description="Geçiş uyumluluğu: SocratLegal sağlık kontrolü.")
async def _legacy_legalai_health_tool() -> dict[str, object]:
    return {"status": "ok", "version": app.version, "external_calls": False}


@app.tool(name="socratlegal_corpus_durum", description="Yerel SocratLegal corpus veritabanı ve kaynak kayıt durumunu gösterir.")
async def socratlegal_corpus_durum() -> dict:
    return await CorpusSyncService().status()


@app.tool(name="legalai_corpus_durum", description="Geçiş uyumluluğu: SocratLegal corpus durumunu gösterir.")
async def _legacy_legalai_corpus_durum() -> dict:
    return await socratlegal_corpus_durum()


@app.tool(name="socratlegal_corpus_belge_ekle", description="Maskelenmiş veya kamuya açık bir corpus belgesini yerel SocratLegal veritabanına ekler.")
async def socratlegal_corpus_belge_ekle(
    source_id: str,
    document_id: str,
    title: str,
    body: str,
    document_type: str = "decision",
    institution: str = "",
    url: str = "",
    citation: str = "",
    published_on: str | None = None,
    effective_from: str | None = None,
    effective_to: str | None = None,
) -> dict:
    from datetime import date

    document = CorpusDocument(
        document_id=document_id,
        source_id=source_id,
        title=title,
        document_type=document_type,
        institution=institution,
        body=body,
        url=url,
        citation=citation,
        published_on=date.fromisoformat(published_on) if published_on else None,
        effective_from=date.fromisoformat(effective_from) if effective_from else None,
        effective_to=date.fromisoformat(effective_to) if effective_to else None,
    )
    return await CorpusSyncService().ingest(source_id, [document])


@app.tool(name="legalai_corpus_belge_ekle", description="Geçiş uyumluluğu: SocratLegal yerel corpus belgesi ekleme.")
async def _legacy_legalai_corpus_belge_ekle(
    source_id: str, document_id: str, title: str, body: str, document_type: str = "decision", institution: str = "", url: str = "", citation: str = "", published_on: str | None = None, effective_from: str | None = None, effective_to: str | None = None
) -> dict:
    return await socratlegal_corpus_belge_ekle(source_id, document_id, title, body, document_type, institution, url, citation, published_on, effective_from, effective_to)


@app.tool(name="socratlegal_corpus_sync", description="Maskeli sorguyla yapılandırılmış resmi adapter'ı arar ve sonuçları yerel corpus'a kaydeder.")
async def socratlegal_corpus_sync(source_id: str, query: str, limit: int = 20) -> dict:
    adapters = {adapter.source_id: adapter for adapter in build_default_priority_adapters()}
    adapter = adapters.get(source_id)
    if adapter is None:
        return {"source_id": source_id, "status": "unavailable_or_not_configured", "documents_ingested": 0}
    return await CorpusSyncService().sync_from_adapter(source_id, adapter, query, limit)


@app.tool(name="legalai_corpus_sync", description="Geçiş uyumluluğu: SocratLegal resmi kaynak sync.")
async def _legacy_legalai_corpus_sync(source_id: str, query: str, limit: int = 20) -> dict:
    return await socratlegal_corpus_sync.fn(source_id, query, limit)


async def _analysis_alias(
    question: str,
    mode: str = "layered",
    jurisdiction_hint: str | None = None,
    quality_profile: str = "auto",
    model_hint: str = "",
) -> dict:
    return await katmanli_analiz(
        question=question,
        mode=mode,
        jurisdiction_hint=jurisdiction_hint,
        quality_profile=quality_profile,
        model_hint=model_hint,
    )


@app.tool(name="socratlegal_katmanli_analiz", description="SocratLegal katmanlı hukuki analiz.")
async def _socratlegal_layered_tool(
    question: LegalQuestion,
    mode: Annotated[str, Field(description="Analiz modu; layered veya simple.")] = "layered",
    jurisdiction_hint: JurisdictionHint = None,
    quality_profile: Annotated[str, Field(description="Model kalite profili: auto, fast, balanced, frontier veya exhaustive.")] = "auto",
    model_hint: Annotated[str, Field(description="İsteğe bağlı model adı; kalite sözleşmesi için ipucudur.")] = "",
) -> dict:
    return await _analysis_alias(question, mode, jurisdiction_hint, quality_profile, model_hint)


@app.tool(name="legalai_katmanli_analiz", description="Geçiş uyumluluğu: SocratLegal katmanlı analiz.")
async def _legacy_legalai_layered_tool(
    question: str,
    mode: str = "layered",
    jurisdiction_hint: str | None = None,
    quality_profile: str = "auto",
    model_hint: str = "",
) -> dict:
    return await _analysis_alias(question, mode, jurisdiction_hint, quality_profile, model_hint)


async def _opposing_alias(
    question: str,
    position: str,
    role: str = "davacı",
    jurisdiction_hint: str | None = None,
    source_scope: str = "targeted",
    selected_source_ids: list[str] | None = None,
    quality_profile: str = "auto",
    model_hint: str = "",
) -> dict:
    return await agresif_karsi_taraf(
        question,
        position,
        role,
        jurisdiction_hint,
        source_scope,
        selected_source_ids,
        quality_profile,
        model_hint,
    )


@app.tool(name="socratlegal_agresif_karsi_taraf", description="SocratLegal agresif karşı taraf ve çözüm stratejisi analizi.")
async def _socratlegal_opposing_tool(
    question: LegalQuestion,
    position: Annotated[str, Field(description="Kullanıcının veya temsil edilen tarafın hukuki pozisyonu.")],
    role: Annotated[str, Field(description="Taraf rolü; varsayılan davacı.")] = "davacı",
    jurisdiction_hint: JurisdictionHint = None,
    source_scope: Annotated[str, Field(description="Kaynak kapsamı; targeted veya all.")] = "targeted",
    selected_source_ids: Annotated[list[str] | None, Field(description="İsteğe bağlı seçili kaynak kimlikleri.")] = None,
    quality_profile: Annotated[str, Field(description="Model kalite profili: auto, fast, balanced, frontier veya exhaustive.")] = "auto",
    model_hint: Annotated[str, Field(description="İsteğe bağlı model adı; kalite sözleşmesi için ipucudur.")] = "",
) -> dict:
    return await _opposing_alias(
        question, position, role, jurisdiction_hint, source_scope, selected_source_ids, quality_profile, model_hint
    )


@app.tool(name="legalai_agresif_karsi_taraf", description="Geçiş uyumluluğu: SocratLegal agresif karşı taraf analizi.")
async def _legacy_legalai_opposing_tool(question: str, position: str, role: str = "davacı", jurisdiction_hint: str | None = None, source_scope: str = "targeted", selected_source_ids: list[str] | None = None) -> dict:
    return await _opposing_alias(question, position, role, jurisdiction_hint, source_scope, selected_source_ids)


@app.tool(name="socratlegal_derin_arastirma", description="SocratLegal derin hukuki araştırma.")
async def _socratlegal_deep_tool(
    question: LegalQuestion,
    depth: Annotated[int, Field(description="Alt soru derinliği; 1 ile 5 arasında.")] = 3,
    detail_level: DetailLevel = "deep",
) -> dict:
    return await derin_arastirma(question, depth, detail_level)


@app.tool(name="legalai_derin_arastirma", description="Geçiş uyumluluğu: SocratLegal derin araştırma.")
async def _legacy_legalai_deep_tool(
    question: LegalQuestion,
    depth: Annotated[int, Field(description="Alt soru derinliği; 1 ile 5 arasında.")] = 3,
    detail_level: DetailLevel = "deep",
) -> dict:
    return await derin_arastirma(question, depth, detail_level)


@app.tool(
    name="socratlegal_hukuki_mutalaa",
    description=(
        "Hukuki soruyu kaynaklı ve 13 bölümlü mütalaa formatında inceler: yönetici özeti, "
        "maddi vakıalar, normlar, deliller, içtihat/doktrin, karşı görüşler, temporal context, "
        "merci/süre, strateji, bütünleştirici değerlendirme, sonuç ve kaynakça/alintılar. "
        "Ayrıntı seviyesi brief/standard/deep/exhaustive olabilir. Sonuç analysis-only ve non-binding'dir."
    ),
    annotations={"readOnlyHint": True, "openWorldHint": True, "idempotentHint": True},
)
async def _socratlegal_legal_opinion_tool(
    question: LegalQuestion,
    detail_level: DetailLevel = "deep",
    jurisdiction_hint: JurisdictionHint = None,
    include_strategy: Annotated[bool, Field(description="Çözüm stratejileri 10. bölümde yer alsın mı?")] = True,
    max_source_quotes: Annotated[int, Field(description="Kaynakça bölümünde gösterilecek azami kısa alıntı sayısı.")] = 3,
    quality_profile: Annotated[str, Field(description="Model kalite profili: auto, fast, balanced, frontier veya exhaustive.")] = "auto",
    model_hint: Annotated[str, Field(description="İsteğe bağlı model adı; yalnızca kalite ayarı için ipucudur.")] = "",
    server_side_synthesis: Annotated[bool, Field(description="İsteğe bağlı API anahtarıyla sunucu sentezi çalışsın mı?")] = False,
) -> dict:
    profile = MemorandumProfile(
        detail_level=detail_level,
        include_strategy=include_strategy,
        max_source_quotes=max_source_quotes,
    )
    output_contract = build_memorandum_instructions(
        profile,
        quality_profile=quality_profile,
        model_hint=model_hint,
    )
    result = await run_pipeline(
        question=question,
        mode="layered",
        jurisdiction_hint=jurisdiction_hint,
        synthesize=server_side_synthesis,
        output_contract=output_contract,
    )
    payload = result.to_dict()
    payload["mode"] = "hukuki_mutalaa"
    payload["memorandum_sections"] = list(memorandum_section_ids())
    payload["memorandum_detail_level"] = profile.detail_level
    memo_instructions = build_memorandum_instructions(
        profile,
        source_ids=tuple(document["doc_id"] for document in payload.get("sources", [])),
        quality_profile=quality_profile,
        model_hint=model_hint,
    )
    payload["assistant_instructions"] = "\n\n".join(
        item for item in (payload.get("assistant_instructions"), memo_instructions) if item
    )
    return payload


@app.tool(
    name="legalai_hukuki_mutalaa",
    description="Geçiş uyumluluğu: SocratLegal 13 bölümlü hukukî mütalaa aracı.",
)
async def _legacy_legalai_legal_opinion_tool(
    question: str,
    detail_level: str = "deep",
    jurisdiction_hint: str | None = None,
    include_strategy: bool = True,
    max_source_quotes: int = 3,
    quality_profile: str = "auto",
    model_hint: str = "",
    server_side_synthesis: bool = False,
) -> dict:
    return await _socratlegal_legal_opinion_tool.fn(
        question=question,
        detail_level=detail_level,
        jurisdiction_hint=jurisdiction_hint,
        include_strategy=include_strategy,
        max_source_quotes=max_source_quotes,
        quality_profile=quality_profile,
        model_hint=model_hint,
        server_side_synthesis=server_side_synthesis,
    )


def _bilirkişi_payload(analysis) -> dict:
    return asdict(analysis)


async def _bilirkisi_legal_sources(question: str, technical_domain: str) -> list[dict]:
    """Ground the technical matrix in locally available corpus evidence."""
    try:
        hits = await CorpusStore(settings.corpus_db_path).search(question or technical_domain, 10)
    except Exception:
        return []
    return [
        {
            "id": hit.document.document_id,
            "source_id": hit.document.source_id,
            "title": hit.document.title,
            "citation": hit.document.citation,
            "source_url": hit.document.url,
            "quote": hit.chunk.text[:1000],
            "non_binding": hit.source.source_type in {"academic", "international_policy"},
        }
        for hit in hits
    ]


@app.tool(name="socratlegal_bilirkisi_raporu_analiz", description="Bilirkişi raporunu teknik karşı-argüman, hukuk bağlantısı ve temporal context ile analiz eder.")
async def _socratlegal_bilirkisi_analysis_tool(
    report_text: Annotated[str | None, Field(description="Yerel rapor metni; file_path ile birlikte verilmemelidir.")] = None,
    file_path: Annotated[str | None, Field(description="Yerel PDF/DOCX/TXT/görüntü raporu yolu; ham dosya dışarı gönderilmez.")] = None,
    question: Annotated[str, Field(description="Raporla ilgili hukuki/teknik itiraz talebi.")] = "",
    technical_domain: Annotated[str, Field(description="İsteğe bağlı teknik alan; boşsa rapor içinden çıkarım yapılır.")] = "",
    event_dates: Annotated[list[str] | None, Field(description="Olay veya ölçüm tarihleri.")] = None,
    case_date: Annotated[str | None, Field(description="Dava/başvuru tarihi.")] = None,
) -> dict:
    result = await analyze_report(text=report_text, file_path=file_path, question=question, technical_domain=technical_domain, event_dates=event_dates, case_date=case_date, legal_sources=await _bilirkisi_legal_sources(question, technical_domain))
    return _bilirkişi_payload(result)


@app.tool(name="legalai_bilirkisi_raporu_analiz", description="Geçiş uyumluluğu: SocratLegal bilirkişi raporu analizi.")
async def _legacy_legalai_bilirkisi_analysis_tool(
    report_text: str | None = None, file_path: str | None = None, question: str = "", technical_domain: str = "", event_dates: list[str] | None = None, case_date: str | None = None
) -> dict:
    return await _socratlegal_bilirkisi_analysis_tool(report_text, file_path, question, technical_domain, event_dates, case_date)


@app.tool(name="socratlegal_bilirkisi_raporu_dilekce", description="Bilirkişi raporu analizinden itiraz dilekçesi taslağı üretir.")
async def _socratlegal_bilirkisi_petition_tool(
    report_text: Annotated[str | None, Field(description="Yerel rapor metni; file_path ile birlikte verilmemelidir.")] = None,
    file_path: Annotated[str | None, Field(description="Yerel PDF/DOCX/TXT/görüntü raporu yolu; ham dosya dışarı gönderilmez.")] = None,
    question: Annotated[str, Field(description="İtiraz dilekçesinde cevaplanacak teknik ve hukuki soru.")] = "",
    technical_domain: Annotated[str, Field(description="İsteğe bağlı teknik alan; boşsa rapordan çıkarılır.")] = "",
    court: Annotated[str, Field(description="Dilekçe başlığında kullanılacak mahkeme veya merci.")] = "",
    event_dates: Annotated[list[str] | None, Field(description="Olay veya ölçüm tarihleri.")] = None,
    case_date: Annotated[str | None, Field(description="Dava/başvuru tarihi.")] = None,
) -> dict:
    analysis = await analyze_report(text=report_text, file_path=file_path, question=question, technical_domain=technical_domain, event_dates=event_dates, case_date=case_date, legal_sources=await _bilirkisi_legal_sources(question, technical_domain))
    return {"analysis": _bilirkişi_payload(analysis), "petition": asdict(build_petition_draft(analysis, court=court))}


@app.tool(name="legalai_bilirkisi_raporu_dilekce", description="Geçiş uyumluluğu: SocratLegal bilirkişi itiraz dilekçesi.")
async def _legacy_legalai_bilirkisi_petition_tool(
    report_text: str | None = None, file_path: str | None = None, question: str = "", technical_domain: str = "", court: str = "", event_dates: list[str] | None = None, case_date: str | None = None
) -> dict:
    return await _socratlegal_bilirkisi_petition_tool(report_text, file_path, question, technical_domain, court, event_dates, case_date)


@app.tool(
    name="socratlegal_sozlesme_incele",
    description=(
        "Yerel olarak sağlanan sözleşme metnini veya dosyasını PII'yi dışarı göndermeden "
        "inceler; hukuki nitelendirme, persona yönlendirmesi, madde/boşluk riskleri, "
        "operasyonel bağlam, temporal context ve kaynaklı araştırma talimatları döndürür. "
        "Sonuç analysis-only ve non-binding'dir. contract_text veya file_path'ten yalnızca "
        "biri verilmeli; due diligence bu aracın kapsamı dışındadır."
    ),
    annotations={"readOnlyHint": True, "openWorldHint": True, "idempotentHint": True},
)
async def _socratlegal_contract_review_tool(
    contract_text: Annotated[str | None, Field(description="Yerel sözleşme metni; file_path ile birlikte verilmemelidir.")] = None,
    file_path: Annotated[str | None, Field(description="Yerel DOCX/PDF/TXT sözleşme yolu; ham dosya dışarı gönderilmez.")] = None,
    purpose: Annotated[str, Field(description="İncelemenin amacı; örn. imza öncesi risk taraması veya revizyon.")] = "",
    position: Annotated[str, Field(description="Kullanıcının tarafı ve ticari/hukuki pozisyonu.")] = "",
    detail_level: Annotated[str, Field(description="Çıktı ayrıntısı; brief, standard, deep veya exhaustive.")] = "standard",
    event_dates: Annotated[list[str] | None, Field(description="Sözleşme, ifa, ihlal veya dava tarihleri.")] = None,
    jurisdiction_hint: JurisdictionHint = None,
    server_side_synthesis: Annotated[bool, Field(description="İsteğe bağlı API anahtarıyla sunucu sentezi çalışsın mı?")] = False,
) -> dict:
    request = ContractReviewRequest(
        contract_text=contract_text,
        file_path=file_path,
        purpose=purpose,
        position=position,
        detail_level=detail_level,
        event_dates=event_dates,
        jurisdiction_hint=jurisdiction_hint,
        server_side_synthesis=server_side_synthesis,
    )
    result = await review_contract(request)
    return result.to_dict()


@app.tool(
    name="legalai_sozlesme_incele",
    description="Geçiş uyumluluğu: SocratLegal sözleşme inceleme aracının aynı işlevli alias'ı.",
)
async def _legacy_legalai_contract_review_tool(
    contract_text: str | None = None,
    file_path: str | None = None,
    purpose: str = "",
    position: str = "",
    detail_level: str = "standard",
    event_dates: list[str] | None = None,
    jurisdiction_hint: str | None = None,
    server_side_synthesis: bool = False,
) -> dict:
    return await _socratlegal_contract_review_tool.fn(
        contract_text=contract_text,
        file_path=file_path,
        purpose=purpose,
        position=position,
        detail_level=detail_level,
        event_dates=event_dates,
        jurisdiction_hint=jurisdiction_hint,
        server_side_synthesis=server_side_synthesis,
    )


@app.tool(
    name="socratlegal_guncelleme_kontrol",
    description=(
        "GitHub Releases üzerinden yalnızca SocratLegal sürüm metadata'sını kontrol eder. "
        "Arşiv indirmez, otomatik kurmaz, IDE ayarlarını değiştirmez ve kullanıcı belgelerini göndermez."
    ),
    annotations={"readOnlyHint": True, "openWorldHint": True, "idempotentHint": True},
)
async def _socratlegal_update_check_tool(
    current_version: str = "0.2.2",
    platform_tag: str | None = None,
    manifest_url: str | None = None,
) -> dict:
    try:
        result = check_remote_update(
            current_version,
            platform_tag=platform_tag,
            manifest_url=manifest_url,
            state_path=Path(settings.storage_root) / "update-check.json",
        )
    except UpdateError as error:
        return {
            "status": "error",
            "error": str(error),
            "auto_apply": False,
            "archive_downloaded": False,
        }
    return {
        "status": "ok",
        "current_version": current_version,
        "available": result.available,
        "available_version": result.manifest.version if result.manifest else None,
        "channel": result.manifest.channel if result.manifest else None,
        "release_url": result.manifest.release_url if result.manifest else None,
        "archive_name": result.manifest.archive_name if result.manifest else None,
        "archive_url": archive_download_url(result.manifest) if result.manifest else None,
        "sha256": result.manifest.sha256 if result.manifest else None,
        "from_cache": result.from_cache,
        "checked_at": result.checked_at.isoformat(),
        "auto_apply": False,
        "archive_downloaded": False,
        "analysis_only": True,
        "non_binding": True,
    }


async def socratlegal_guncelleme_kontrol(
    current_version: str = "0.2.2",
    platform_tag: str | None = None,
    manifest_url: str | None = None,
) -> dict:
    """Directly awaitable facade for local tests and non-MCP integrations."""
    return await _socratlegal_update_check_tool.fn(current_version, platform_tag, manifest_url)


@app.tool(
    name="legalai_guncelleme_kontrol",
    description="Geçiş uyumluluğu: SocratLegal sürüm metadata kontrolü.",
)
async def _legacy_legalai_update_check(
    current_version: str = "0.2.2",
    platform_tag: str | None = None,
    manifest_url: str | None = None,
) -> dict:
    return await socratlegal_guncelleme_kontrol(current_version, platform_tag, manifest_url)


def main() -> None:
    app.run()


if __name__ == "__main__":
    main()

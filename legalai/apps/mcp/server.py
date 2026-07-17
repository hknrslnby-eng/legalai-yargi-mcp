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

from fastmcp import FastMCP

from legalai.packages.aihm.aym_bridge import aihm_aym_kopru as _aihm_aym_kopru
from legalai.packages.aihm.service import aihm_karar_ara as _aihm_karar_ara
from legalai.packages.aihm.service import aihm_karar_getir as _aihm_karar_getir
from legalai.packages.layers.analysis_pipeline import run_pipeline
from legalai.packages.layers.citation_validator import validate_citations
from legalai.packages.layers.deep_research import run_deep_research
from legalai.packages.layers.opposing import run_opposing
from legalai.packages.discovery.catalog import capability_catalog
from legalai.packages.pii.gateway import PiiGateway
from legalai.packages.shared.settings import settings
from legalai.packages.shared.tenant import TenantContext, set_tenant

# Süreç başlarken tenant bağlamı kurulur — bkz. FORK-KAPSAMLI-PLAN.md §2.2.
# Bugün her zaman "local"; sunucuya taşındığında bu satır middleware'e taşınır.
set_tenant(TenantContext(tenant_id=settings.tenant_id, tenant_name=settings.tenant_name))

app = FastMCP(name="LegalAI MCP Server", version="0.1.0")
_pii_gateway = PiiGateway()


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
        "uzmanlık alanı ve itiraz edilmek istenen sonuçları ekle. Bu prompt planlanan özelliktir; üretim modülü "
        "henüz etkin değil. Gelecekte teknik bulgu, teknik karşı-argüman, hukukî bağlantı ve temporal context "
        "ayrı katmanlarda üretilecek; insan uzman ve avukat incelemesi zorunlu olacaktır."
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
    question: str, mode: str = "layered", jurisdiction_hint: str | None = None
) -> dict:
    result = await run_pipeline(
        question=question, mode=mode, jurisdiction_hint=jurisdiction_hint, synthesize=False
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
    question: str,
    position: str,
    role: str = "davacı",
    jurisdiction_hint: str | None = None,
    source_scope: str = "targeted",
    selected_source_ids: list[str] | None = None,
) -> dict:
    result = await run_opposing(
        question=question,
        position=position,
        role=role,
        jurisdiction_hint=jurisdiction_hint,
        source_scope=source_scope,
        selected_source_ids=selected_source_ids,
        synthesize=False,
    )
    return result.to_dict()


async def agresif_karsi_taraf(
    question: str,
    position: str,
    role: str = "davacı",
    jurisdiction_hint: str | None = None,
    source_scope: str = "targeted",
    selected_source_ids: list[str] | None = None,
) -> dict:
    """Keep the Python API directly awaitable while FastMCP registers the tool."""
    return await _agresif_karsi_taraf_tool.fn(
        question=question,
        position=position,
        role=role,
        jurisdiction_hint=jurisdiction_hint,
        source_scope=source_scope,
        selected_source_ids=selected_source_ids,
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
        "`answer` alanında kaynaklı, hazır bir sentez döner. `depth` (1-5) "
        "en fazla kaç alt soruya bölüneceğini sınırlar."
    ),
    annotations={"readOnlyHint": True, "openWorldHint": True, "idempotentHint": True},
)
async def derin_arastirma(question: str, depth: int = 3) -> dict:
    if not settings.enable_deep_research:
        return {
            "question": question,
            "mode": "disabled",
            "answer": None,
            "citations": [],
            "note": "Derin araştırma özelliği .env'de ENABLE_DEEP_RESEARCH=false ile kapatılmış.",
        }
    result = await run_deep_research(question=question, depth=depth)
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
async def alinti_dogrula(answer: str, known_doc_ids: list[str]) -> dict:
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
async def aihm_aym_kopru(aym_basvuru_no: str) -> dict:
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
async def pii_maskele(metin: str) -> str:
    return await _pii_gateway.mask(metin)


@app.tool(
    description=(
        "`pii_maskele` ile maskelenmiş bir metindeki [TCKN_1], [IBAN_1] gibi "
        "yer tutucuları, bu tenant için saklanan şifreli değerlerden geri "
        "açar. Aynı oturumda çağrılan `pii_maskele` sonuçları için çalışır."
    ),
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def pii_ac(metin: str) -> str:
    return await _pii_gateway.unmask(metin)


def main() -> None:
    app.run()


if __name__ == "__main__":
    main()

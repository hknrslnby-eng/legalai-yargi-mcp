"""Deterministic contract classification, persona routing, and gap matrix."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from typing import Any, Awaitable, Callable

from .intake import extract_contract
from .models import (
    ContractClassification,
    ContractIntake,
    ContractIssue,
    ContractReviewRequest,
    ContractReviewResult,
    PersonaRouteDecision,
)
from .privacy import ContractPrivacyGate


def _has(text: str, *terms: str) -> bool:
    lowered = text.casefold()
    return any(term.casefold() in lowered for term in terms)


def classify_contract(intake: ContractIntake) -> ContractClassification:
    text = intake.text
    signals: list[str] = []
    distribution = _has(text, "distribution", "dağıtım", "exclusive territory", "münhasır bölge", "bayi")
    sale = _has(text, "sale", "satış", "purchase", "alım", "bedel")
    service = _has(text, "service", "hizmet", "consulting", "danışmanlık")
    lease = _has(text, "lease", "kira", "rent", "kiracı", "kiraya veren")
    employment = _has(text, "employment", "iş sözleşmesi", "employee", "işçi")
    insurance = _has(text, "insurance", "sigorta", "policy", "poliçe", "premium", "prim")

    if distribution and (
        sale or _has(text, "agreement", "sözleşme", "contract", "exclusive territory", "münhasır bölge")
    ):
        legal_nature = "mixed_distribution"
        method = "dominant_element"
        signals.append("Dağıtım ve satış/tedarik unsurları birlikte algılandı.")
    elif insurance:
        legal_nature, method = "insurance", "typical_contract"
        signals.append("Sigorta sözleşmesi sinyalleri algılandı.")
    elif lease:
        legal_nature, method = "lease", "typical_contract"
        signals.append("Kira sözleşmesi sinyalleri algılandı.")
    elif employment:
        legal_nature, method = "employment", "typical_contract"
        signals.append("İş sözleşmesi sinyalleri algılandı.")
    elif service:
        legal_nature, method = "service", "typical_contract"
        signals.append("Hizmet sözleşmesi sinyalleri algılandı.")
    elif sale:
        legal_nature, method = "sale", "typical_contract"
        signals.append("Satış sözleşmesi sinyalleri algılandı.")
    else:
        legal_nature, method = "atypical_or_unclassified", "content_based_uncertain"
        signals.append("Sözleşme türü metnin içeriğine göre kesin sınıflandırılamadı.")

    foreign = bool(intake.foreign_element_signals) or intake.language in {"foreign", "mixed"}
    return ContractClassification(
        legal_nature=legal_nature,
        classification_method=method,
        foreign_law_layer="mohuk_priority" if foreign else "not_triggered",
        confidence=0.78 if method == "typical_contract" else 0.70 if method == "dominant_element" else 0.35,
        signals=tuple(signals),
    )


def _route(
    persona_id: str,
    text: str,
    triggers: Iterable[str],
    reason_if_absent: str,
    priority: str = "supporting",
) -> PersonaRouteDecision:
    matched = tuple(trigger for trigger in triggers if _has(text, trigger))
    if matched:
        return PersonaRouteDecision(
            persona_id=persona_id,
            invoked=True,
            positive_triggers=matched,
            priority=priority,
            confidence=0.75,
        )
    return PersonaRouteDecision(
        persona_id=persona_id,
        invoked=False,
        negative_reason=reason_if_absent,
        priority=priority,
        confidence=0.55,
        verification_needed=(f"{persona_id} bakımından özel bir unsur varsa sözleşme metni ve ekleri doğrulanmalı.",),
    )


def route_personas(
    classification: ContractClassification, intake: ContractIntake
) -> tuple[PersonaRouteDecision, ...]:
    text = intake.text
    routes = [
        PersonaRouteDecision(
            persona_id="hukuk",
            invoked=True,
            positive_triggers=("Her sözleşmede temel özel hukuk ve sözleşmeler analizi gerekir.",),
            priority="primary",
            confidence=0.95,
        ),
        _route("idare", text, ("kamu", "idare", "government", "public authority"), "Kamu/idare tarafı veya idari işlem sinyali bulunmadı."),
        _route("ceza", text, ("fraud", "dolandır", "sahte", "forgery", "suç"), "Suç, hile veya sahtecilik sinyali bulunmadı."),
        _route("vergi", text, ("vergi", "tax", "vat", "kdv", "withholding"), "Vergi, KDV veya stopaj unsuru bulunmadı."),
        _route("rekabet", text, ("rekabet", "competition", "exclusive", "münhasır", "market", "pazar", "distribution", "dağıtım"), "Rekabet/pazar etkisi veya dağıtım kısıtı sinyali bulunmadı."),
        _route("kvkk", text, ("kişisel veri", "personal data", "privacy", "gdpr", "veri işleme", "data processing"), "Kişisel veri veya veri işleme sinyali bulunmadı."),
        _route("kik", text, ("kamu ihale", "public procurement", "tender", "ihale"), "Kamu ihale süreci veya ihale sözleşmesi sinyali bulunmadı."),
        _route("sigorta", text, ("sigorta", "insurance", "poliçe", "policy", "prim", "premium"), "Sigorta ürünü veya poliçe unsuru bulunmadı."),
        _route("anayasa", text, ("anayasa", "constitutional", "temel hak", "fundamental right"), "Anayasal hak müdahalesi sinyali bulunmadı."),
        _route("insan_haklari", text, ("insan hakkı", "human rights", "ayrımcılık", "discrimination"), "İnsan hakları veya ayrımcılık sinyali bulunmadı."),
        _route("tahkim", text, ("tahkim", "arbitration", "arbitrage", "icc", "lcia"), "Tahkim şartı veya tahkim kurumu sinyali bulunmadı."),
        _route("fikri_mulkiyet", text, ("marka", "patent", "copyright", "telif", "lisans", "license"), "Fikri mülkiyet veya lisans unsuru bulunmadı."),
        _route("is", text, ("işçi", "işveren", "employee", "employer", "employment"), "İş ilişkisi sinyali bulunmadı."),
        _route("tuketici", text, ("tüketici", "consumer", "mesafeli satış", "distance sale"), "Tüketici işlemi sinyali bulunmadı."),
        PersonaRouteDecision(
            persona_id="mohuk",
            invoked=classification.foreign_law_layer == "mohuk_priority",
            positive_triggers=("Yabancılık unsuru algılandı; MÖHUK ilk çerçeve katmanıdır.",) if classification.foreign_law_layer == "mohuk_priority" else (),
            negative_reason="Yabancılık unsuru algılanmadı; MÖHUK öncelik katmanı tetiklenmedi." if classification.foreign_law_layer != "mohuk_priority" else "",
            priority="framework",
            confidence=0.90 if classification.foreign_law_layer == "mohuk_priority" else 0.60,
        ),
    ]
    return tuple(routes)


def build_issue_matrix(
    intake: ContractIntake,
    classification: ContractClassification,
    routes: tuple[PersonaRouteDecision, ...],
) -> tuple[ContractIssue, ...]:
    active_personas = tuple(route.persona_id for route in routes if route.invoked)
    issues: list[ContractIssue] = []
    for clause in intake.clauses:
        issues.append(
            ContractIssue(
                issue_id=f"clause-{clause.number or clause.position}",
                clause_number=clause.number,
                finding=f"Madde {clause.number or clause.position} kapsamı ve hukuki niteliği doğrulanmalı.",
                risk_level="medium",
                legal_rationale="Madde metni, TBK m.19 kapsamında gerçek ortak irade ve edim dengesiyle birlikte yorumlanmalıdır.",
                operational_rationale="Maddenin iş akışındaki uygulanma biçimi ve ticari teamül somut belgeyle doğrulanmalıdır.",
                personas=active_personas or ("hukuk",),
                missing_facts=("Maddeye ilişkin ek belge, bildirim ve fiili uygulama kayıtları.",),
            )
        )

    checks = (
        ("termination", ("fesih", "termination", "cancellation"), "Fesih sebepleri, bildirim süresi ve sonuçları düzenlenmemiş olabilir."),
        ("dispute_resolution", ("yetki", "mahkeme", "tahkim", "arbitration", "dispute"), "Uyuşmazlık çözüm yolu ve yetkili merci açık olmayabilir."),
        ("governing_law", ("uygulanacak hukuk", "governing law", "applicable law"), "Uygulanacak hukuk hükmü bulunmayabilir; yabancılık unsurunda MÖHUK ayrıca incelenmelidir."),
        ("confidentiality", ("gizlilik", "confidentiality", "secret"), "Gizlilik ve ticari sır koruması düzenlenmemiş olabilir."),
        ("assignment", ("devir", "temlik", "assignment"), "Devir/temlik koşulları düzenlenmemiş olabilir."),
        ("force_majeure", ("mücbir", "force majeure"), "Mücbir sebep ve ifa engeli sonuçları düzenlenmemiş olabilir."),
    )
    for issue_id, terms, finding in checks:
        if not _has(intake.text, *terms):
            issues.append(
                ContractIssue(
                    issue_id=issue_id,
                    clause_number=None,
                    finding=finding,
                    risk_level="medium",
                    legal_rationale="Eksik hüküm, sözleşmenin yorumunu, ifasını ve uyuşmazlık riskini etkileyebilir.",
                    operational_rationale="Tarafların fiili iş akışı ve risk dağılımı ayrıca doğrulanmalıdır.",
                    personas=active_personas or ("hukuk",),
                    missing_facts=("Tarafların ticari amacı ve müzakere kayıtları.",),
                )
            )
    return tuple(issues)


def _classification_dict(value: ContractClassification) -> dict[str, Any]:
    return asdict(value)


def _build_masked_research_query(
    redacted_text: str,
    classification: ContractClassification,
    issues: tuple[ContractIssue, ...],
) -> str:
    issue_ids = ", ".join(issue.issue_id for issue in issues)
    return (
        "SocratLegal sözleşme incelemesi için yalnızca aşağıdaki maskelenmiş metin ve metadata ile kaynak araştırması yap. "
        "Hukuki iddiaları erişilen kaynakların gerçek künyelerine bağla; erişilmeyen kaynak veya alıntı uydurma.\n"
        f"Nitelendirme: {classification.legal_nature}; yöntem: {classification.classification_method}; "
        f"MÖHUK katmanı: {classification.foreign_law_layer}.\n"
        f"İncelenecek issue id'leri: {issue_ids or '(genel tarama)'}.\n"
        f"MASKELENMİŞ SÖZLEŞME METNİ:\n{redacted_text}"
    )


def _assistant_instructions(
    intake: ContractIntake,
    classification: ContractClassification,
    analysis_dict: dict[str, Any],
    request: ContractReviewRequest,
) -> str:
    instructions = (
        "Bu araç nihai hukuki görüş üretmez. Önce Yönetici özeti, sonra sözleşmenin gerçek hukuki niteliği, "
        "persona bulguları, madde bazlı riskler, boşluklar, karşı görüşler, varsayımlar ve kaynakça yaz. "
        "Her hukuki iddiayı yalnızca dönen kaynakların künye/belge id'siyle destekle; operational context'i hipotez olarak etiketle. "
        "Temporal context, uygulanacak hukuk, görev-yetki ve süre risklerini erişilen kaynaklarla kontrol et. "
        f"Kullanıcının rolü: {request.position or 'belirtilmedi'}. Çıktı ayrıntı seviyesi: {request.detail_level}."
    )
    if classification.foreign_law_layer == "mohuk_priority" or intake.language in {"foreign", "mixed"}:
        instructions += (
            " source_language_revision: Her revizyon önerisinde önce Türkçe hukuki açıklama, sonra kaynak dilinde "
            "hukuki terminolojiye uygun öneri hükmü, ardından Turkish counterpart başlığı altında Türkçe karşılık göster. "
            "Bu metin yeminli/sertifikalı çeviri değildir; dil veya anlam belirsizliğini açıkça belirt."
        )
    if analysis_dict.get("assistant_instructions"):
        instructions += "\nKaynak pipeline talimatı:\n" + str(analysis_dict["assistant_instructions"])
    return instructions


async def review_contract(
    request: ContractReviewRequest,
    pipeline_runner: Callable[..., Awaitable[Any]] | None = None,
) -> ContractReviewResult:
    """Review a local contract through the existing federated analysis pipeline."""
    intake = extract_contract(text=request.contract_text, file_path=request.file_path)
    redaction = ContractPrivacyGate().redact(intake.text)
    classification = classify_contract(intake)
    routes = route_personas(classification, intake)
    issues = build_issue_matrix(intake, classification, routes)
    query = _build_masked_research_query(redaction.text, classification, issues)

    if pipeline_runner is None:
        from legalai.packages.layers.analysis_pipeline import run_pipeline

        pipeline_runner = run_pipeline
    analysis = await pipeline_runner(
        question=query,
        mode="layered",
        jurisdiction_hint=request.jurisdiction_hint,
        synthesize=request.server_side_synthesis,
    )
    analysis_dict = analysis.to_dict() if hasattr(analysis, "to_dict") else dict(analysis)
    evidence = list(analysis_dict.get("evidence") or analysis_dict.get("sources") or [])
    executive_summary = (
        f"Sözleşme {classification.legal_nature} olarak ön sınıflandırıldı; güven düzeyi {classification.confidence:.2f}. "
        f"{len(issues)} madde/boşluk bulgusu ve {len(evidence)} kaynak sonucu incelenmelidir."
    )
    privacy = {
        "persisted": False,
        "external_raw_text_sent": False,
        "ocr_required": intake.ocr_required,
        "warnings": ["Taranmış PDF için yerel OCR gerekir."] if intake.ocr_required else [],
    }
    return ContractReviewResult(
        executive_summary=executive_summary,
        classification=_classification_dict(classification),
        persona_routes=[asdict(route) for route in routes],
        clause_findings=[asdict(issue) for issue in issues if issue.issue_id.startswith("clause-")],
        gap_findings=[asdict(issue) for issue in issues if not issue.issue_id.startswith("clause-")],
        evidence=evidence,
        temporal_context=analysis_dict.get("temporal_context"),
        operational_context=dict(analysis_dict.get("operational_context") or {}),
        assistant_instructions=_assistant_instructions(intake, classification, analysis_dict, request),
        privacy=privacy,
    )

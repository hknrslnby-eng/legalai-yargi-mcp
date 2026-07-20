"""Deterministic contract classification, persona routing, and gap matrix."""
from __future__ import annotations

from collections.abc import Iterable

from .models import (
    ContractClassification,
    ContractIntake,
    ContractIssue,
    PersonaRouteDecision,
)


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

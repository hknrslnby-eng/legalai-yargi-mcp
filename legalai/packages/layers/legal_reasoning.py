"""Shared, source-aware instructions for structured legal reasoning."""
from __future__ import annotations

from collections.abc import Sequence

from legalai.packages.layers.operational_context import OperationalContext
from legalai.packages.layers.quality_contract import build_quality_contract
from legalai.packages.layers.quality_policy import build_quality_context
from legalai.packages.layers.cross_domain_inquiry import build_cross_domain_inquiry
from legalai.packages.layers.reasoning_playbook import (
    REASONING_PLAYBOOK,
    ReasoningPlaybook,
)
from legalai.packages.sources.policy import policies_for_context


REASONING_STEPS: tuple[str, str, str, str] = (
    "1. Hukuki sorun nedir?",
    "2. Teorik ve yasal altyapı nedir?",
    "3. Somut olayın unsurlarla ilişkisi nedir?",
    "4. Cevap ve strateji nedir?",
)


def _unique(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def build_reasoning_instructions(
    jurisdiction_ids: Sequence[str] = (),
    source_context: str = "legal_analysis",
    *,
    expert_lenses: Sequence[str] = (),
    operational_context: OperationalContext | None = None,
    question: str = "",
    documents: Sequence[object] = (),
    playbook: ReasoningPlaybook = REASONING_PLAYBOOK,
    quality_profile: str = "auto",
    model_hint: str = "",
) -> str:
    """Build shared instructions without making a legal conclusion.

    ``source_context`` remains the second positional argument for compatibility
    with existing upstream callers. New optional context is keyword-only.
    """
    jurisdictions = ", ".join(_unique(jurisdiction_ids)) or "algılanan ilgili alan(lar)"
    lenses = ", ".join(_unique(expert_lenses))
    policies = policies_for_context(source_context)
    source_labels = ", ".join(policy.label for policy in policies) or "uygun kaynak politikası"
    source_authorities = ", ".join(
        f"{policy.label} ({policy.authority_level})" for policy in policies
    )
    source_ids = [getattr(document, "id", "") for document in documents]
    quality_context = build_quality_context(
        jurisdiction_ids,
        expert_lenses,
        source_ids,
        operational_context=operational_context,
        quality_profile=quality_profile,
        model_hint=model_hint,
    )
    cross_domain = build_cross_domain_inquiry(
        question,
        jurisdiction_ids,
        documents=documents,
    )
    context_lines = (
        "Operasyonel bağlam: somut vakıa yerine geçmeyen, açıkça etiketlenmiş hipotezler ve doğrulama ihtiyaçlarıdır."
        if operational_context is None
        else "Operasyonel bağlamı yalnızca `operasyonel hipotez`, `kullanıcı beyanı`, `belgeyle desteklenen olgu` veya `doğrulama gerekli` etiketiyle sun."
    )

    lines = [
        "Yapılandırılmış hukuki muhakeme talimatları:",
        f"İlgili hukuk alanları/personalar: {jurisdictions}.",
    ]
    if lenses:
        lines.append(f"İlgili uzman lensleri: {lenses}.")
    lines.extend(
        [
            "",
            REASONING_STEPS[0],
            "Soruyu, olayları, talepleri, delilleri, tarihleri ve açık/örtülü hukuki ihtimalleri ayır; belirsizliği görünür kıl.",
            "",
            REASONING_STEPS[1],
            "Uygulanabilir mevzuatı, unsurları, usul kurallarını, görev ve yetki ihtimallerini; olay, dava ve diğer kritik tarihler bakımından Temporal Legal Context ile incele.",
            "Özellikle zamanaşımı ve hak düşürücü süreleri; yürürlüğe girme/yürürlükten kalkma, iptal ve yürütmenin durdurulması etkilerini ayrıca kontrol et.",
            "",
            REASONING_STEPS[2],
            "Her vakıanın hukuki unsurla ilişkisini ve her belgenin ispat değerini açıkla; eksik veya belirsiz olgular için alternatif ihtimaller ve varsayımlar belirt.",
            "Lehe görüş yanında karşıt görüşü, karşı tarafın itirazlarını ve zayıf noktaları otomatik olarak ara; görüşleri kesin hüküm gibi sunma.",
            "",
            REASONING_STEPS[3],
            "Sonucu yalnızca dava olarak sınırlama: sulh, feragat, Avukatlık Kanunu 35/A, zorunlu/ihtiyari arabuluculuk, idari başvuru, icra, ceza şikâyeti, delil koruma ve diğer hukuki çözüm yollarını amaca göre karşılaştır.",
            "Her seçenek için amaç, ön koşul, süre, görev-yetki/merci, delil etkisi, risk, geri döndürülemezlik ve sonraki süreçte kullanılabilirliği belirt.",
            "",
            "Çıktı önce kısa bir Yönetici özeti, ardından ayrıntılı bulgular, karşı görüşler, varsayımlar, eksik vakıalar ve sonraki doğrulama adımlarını içersin.",
            context_lines,
            f"Kaynak bağlamı: {source_context}. Kullanılabilecek kaynak sınıfları: {source_labels}.",
            f"Kaynak otoritesi: {source_authorities or 'kaynak bulunamadı'}.",
            "İçtihat, mevzuat ve doktrin için tam künye ve doğrulanabilir atıf ver; yalnızca gerçekten erişilen metinden kısa ilgili alıntı kullan.",
            "Doktrin, yabancı kararlar ve OECD kaynakları non-binding yardımcı kaynaklardır; bağlayıcı hukuk kuralı gibi yazılamaz.",
            "Çıktı analysis-only ve non-binding bir değerlendirmedir; kesin görüş, garanti veya hukuki danışmanlık iddiası değildir.",
            "",
            quality_context,
            "",
            cross_domain.render(),
            "",
            playbook.render(),
            "",
            build_quality_contract(quality_profile, model_hint=model_hint),
        ]
    )
    return "\n".join(lines)

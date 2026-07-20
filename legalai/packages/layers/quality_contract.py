"""Model-neutral quality contracts for source-grounded legal reasoning.

The contract improves consistency across host and API-routed models without
claiming that prompting can make a smaller model equal a frontier model.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelQualityProfile:
    name: str
    detail_level: str
    max_subquestions: int
    critic_passes: int
    require_source_matrix: bool = True
    require_summary: bool = True


QUALITY_PROFILES: dict[str, ModelQualityProfile] = {
    "fast": ModelQualityProfile("fast", "brief", 3, 0),
    "balanced": ModelQualityProfile("balanced", "standard", 5, 1),
    "frontier": ModelQualityProfile("frontier", "deep", 8, 2),
    "exhaustive": ModelQualityProfile("exhaustive", "exhaustive", 10, 3),
}

_MODEL_ALIASES = {
    "claude": "frontier",
    "opus": "frontier",
    "sonnet": "frontier",
    "grok": "frontier",
    "deepseek": "frontier",
    "gemini pro": "frontier",
    "gemini flash": "balanced",
    "composer": "frontier",
    "codex": "frontier",
}


def resolve_quality_profile(profile: str = "auto", model_hint: str = "") -> ModelQualityProfile:
    """Resolve a conservative profile; model names are hints, not guarantees."""
    key = (profile or "auto").casefold().strip()
    if key == "auto":
        hint = (model_hint or "").casefold()
        for alias, resolved in _MODEL_ALIASES.items():
            if alias in hint:
                return QUALITY_PROFILES[resolved]
        return QUALITY_PROFILES["frontier"]
    if key not in QUALITY_PROFILES:
        raise ValueError("quality profile fast, balanced, frontier, exhaustive veya auto olmalıdır.")
    return QUALITY_PROFILES[key]


def build_quality_contract(
    profile: str = "auto",
    *,
    model_hint: str = "",
    source_ids: tuple[str, ...] = (),
) -> str:
    """Render an instruction contract without requesting hidden chain-of-thought."""
    selected = resolve_quality_profile(profile, model_hint)
    source_list = ", ".join(f"#{item}" for item in source_ids) or "(erişilen kaynak yok)"
    return (
        "SOCRATLEGAL KALİTE SÖZLEŞMESİ\n"
        f"Profil: {selected.name}; ayrıntı: {selected.detail_level}; azami alt soru: {selected.max_subquestions}; "
        f"eleştiri/doğrulama turu: {selected.critic_passes}.\n"
        "Ham düşünce zincirini isteme veya ifşa etme. Bunun yerine denetlenebilir bir muhakeme cetveli sun: "
        "sorun, norm, vakıa-delil bağlantısı, karşı görüş, varsayım, belirsizlik, kaynak ve sonuç.\n"
        "Önce kapsamlı araştırma planı kur; sonra doğrudan kaynakları, karşıt kaynakları ve kıyas adaylarını ayır. "
        "Her iddiayı erişilen belge kimliğiyle bağla; kaynak yoksa bunu açıkça belirt ve künye uydurma.\n"
        "Persona perspektifini akademik ve pratik bilgiyle birleştir; personayı bağlayıcı makam veya gerçek kişi gibi sunma. "
        "Teknik/operasyonel çıkarımları olgu, hipotez veya doğrulama gerekli etiketiyle ayır.\n"
        "Çelişki, kanunilik/kıyas sınırı, temporal context, süre, görev-yetki, merci ve uygulanabilir çözüm yollarını ayrıca test et.\n"
        f"Kaynak matrisi yalnızca şu kimlikleri kullanabilir: {source_list}.\n"
        "Sonuç metninde kısa yönetici özeti, ayrıntılı değerlendirme ve koşullu sonuç mutlaka bulunmalıdır. "
        "Çıktı analysis-only ve non-binding bir araştırma taslağıdır; kesin görüş veya garanti değildir."
    )

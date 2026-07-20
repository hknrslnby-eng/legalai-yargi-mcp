"""Structured output contract for source-grounded Turkish legal opinions."""
from __future__ import annotations

from dataclasses import dataclass

from legalai.packages.layers.quality_contract import build_quality_contract


MEMORANDUM_SECTIONS: tuple[str, ...] = (
    "1. Yönetici Özeti",
    "2. Talep, Kapsam ve Varsayımlar",
    "3. Maddi Vakıalar, Kronoloji ve Kritik Tarihler",
    "4. Hukuki Sorunlar",
    "5. Normatif ve Teorik Altyapı",
    "6. Somut Olayın Unsurlar, Deliller ve Usulle İlişkisi",
    "7. İçtihat, Doktrin ve Karşılaştırmalı Kaynaklar",
    "8. Karşı Görüşler ve Karşı Taraf Argümanları",
    "9. Temporal Legal Context, Süreler ve Yetkili Merci",
    "10. Çözüm Yolları ve Stratejik Seçenekler",
    "11. Bütünleştirici Ayrıntılı Değerlendirme",
    "12. Sonuç",
    "13. Kaynakça ve İlgili Kısa Alıntılar",
)


@dataclass(frozen=True)
class MemorandumProfile:
    detail_level: str = "deep"
    include_strategy: bool = True
    include_research_gaps: bool = True
    max_source_quotes: int = 3

    def __post_init__(self) -> None:
        if self.detail_level not in {"brief", "standard", "deep", "exhaustive"}:
            raise ValueError("detail_level brief, standard, deep veya exhaustive olmalıdır.")
        if self.max_source_quotes < 0:
            raise ValueError("max_source_quotes negatif olamaz.")


def build_memorandum_instructions(
    profile: MemorandumProfile | None = None,
    *,
    source_ids: tuple[str, ...] = (),
    quality_profile: str = "auto",
    model_hint: str = "",
) -> str:
    """Return a model-neutral, non-chain-of-thought output contract."""
    profile = profile or MemorandumProfile()
    headings = "\n".join(MEMORANDUM_SECTIONS)
    valid_ids = ", ".join(f"#{source_id}" for source_id in source_ids) or "(erişilen kaynak yok)"
    strategy = (
        "10. bölümde dava, icra, idari/kurul başvurusu, arabuluculuk, sulh, feragat, 35/A, ceza yolu ve diğer seçenekleri koşullu karşılaştır."
        if profile.include_strategy
        else "10. bölümde yalnızca soruyla doğrudan ilgili çözüm yollarını kısaca belirt."
    )
    gaps = (
        "Eksik vakıaları, alternatif varsayımları ve doğrulama gerektiren noktaları açıkça ayır."
        if profile.include_research_gaps
        else "Yalnızca kullanıcı tarafından verilen ve kaynaklarla doğrulanan vakıaları kullan."
    )
    return (
        "HUKUKİ MÜTALAA ÇIKTI SÖZLEŞMESİ\n"
        f"Ayrıntı seviyesi: {profile.detail_level}. Ham düşünce zincirini gösterme; bunun yerine "
        "denetlenebilir gerekçe, varsayım, kaynak ve belirsizlik cetveli sun.\n"
        "Önce yönetici özetini ver, ardından aşağıdaki 13 bölümü aynı sırayla tamamla:\n"
        f"{headings}\n"
        "11. bölüm, 2-10. bölümlerdeki bulguları bir araya getirerek çelişkileri çözen ayrıntılı değerlendirmedir. "
        "12. bölüm, bu bütünleştirici değerlendirmeden çıkan koşullu sonuçtur. "
        f"13. bölümde tam künye, belge kimliği ve en fazla {profile.max_source_quotes} kısa ilgili alıntı göster.\n"
        f"{strategy}\n"
        f"{gaps}\n"
        "Doğrudan içtihat bulunamazsa bunu açıkça söyle; benzer norm/unsur/amaç taşıyan kaynakları "
        "doğrudan kaynakla karıştırmadan kıyas adımları, benzerlikler, farklar ve kıyas sınırlarıyla sun. "
        "Ceza ve vergi hukukunda kanunilik ve kıyas sınırlamalarını; temel haklarda kanunilik, meşru amaç, "
        "ölçülülük ve etkili başvuru boyutlarını ayrıca kontrol et. Erişilmeyen kaynak veya alıntı uydurma.\n"
        f"Kullanılabilecek kaynak kimlikleri: {valid_ids}. Her hukuki iddiayı mümkün olduğunca bu kimliklerle bağla.\n"
        "Çıktı analysis-only ve non-binding bir araştırma/mütalaa taslağıdır; kesin hukuki görüş veya garanti değildir.\n"
        + build_quality_contract(quality_profile, model_hint=model_hint, source_ids=source_ids)
    )


def memorandum_section_ids() -> tuple[str, ...]:
    """Return a stable copy for catalogs, tests and client renderers."""
    return MEMORANDUM_SECTIONS

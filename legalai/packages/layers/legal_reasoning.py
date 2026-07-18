"""Shared, source-aware instructions for structured legal reasoning."""
from __future__ import annotations

from collections.abc import Sequence

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
) -> str:
    """Build deterministic instructions shared by server and host analyses.

    The helper describes an analysis method; it does not make a legal
    conclusion and does not elevate doctrine, foreign material, or policy
    references to binding domestic law.
    """
    jurisdictions = ", ".join(_unique(jurisdiction_ids)) or "algılanan ilgili alan(lar)"
    policies = policies_for_context(source_context)
    source_labels = ", ".join(policy.label for policy in policies) or "uygun kaynak politikası"
    source_authorities = ", ".join(
        f"{policy.label} ({policy.authority_level})" for policy in policies
    )

    return "\n".join(
        [
            "Yapılandırılmış hukuki muhakeme talimatları:",
            f"İlgili hukuk alanları/personalar: {jurisdictions}.",
            "",
            REASONING_STEPS[0],
            "Soruyu, olayları, talepleri, delilleri ve açık/örtülü hukuki ihtimalleri ayır;"
            " birden fazla yargı türü veya alt hukuk alanı varsa bunları birlikte göster.",
            "",
            REASONING_STEPS[1],
            "Uygulanabilir mevzuatı, unsurları, usul kurallarını, görev ve yetki ihtimallerini;"
            " olay, dava ve diğer kritik tarihler bakımından Temporal Legal Context ile incele.",
            "Özellikle zamanaşımı ve hak düşürücü süreleri; yürürlüğe girme/yürürlükten kalkma, iptal"
            " ve yürütmenin durdurulması etkilerini ayrıca kontrol et.",
            "",
            REASONING_STEPS[2],
            "Her vakıanın hukuki unsurla ilişkisini ve her belgenin ispat değerini açıkla;"
            " eksik veya belirsiz olgular için alternatif ihtimaller ve varsayımlar belirt.",
            "Lehe görüş yanında karşıt görüşü, karşı tarafın itirazlarını ve zayıf noktaları"
            " otomatik olarak ara; görüşleri kesin hüküm gibi sunma.",
            "",
            REASONING_STEPS[3],
            "Sonucu yalnızca dava olarak sınırlama: sulh, feragat, Avukatlık Kanunu 35/A,"
            " zorunlu/ihtiyari arabuluculuk, idari başvuru, icra, ceza şikayeti, delil koruma"
            " ve diğer hukuki çözüm yollarını olayın amacına göre karşılaştır.",
            "Her seçenek için amaç, ön koşul, süre, görev-yetki/merci, delil etkisi, risk,"
            " geri döndürülemezlik ve sonraki süreçte kullanılabilirliği belirt.",
            "",
            f"Kaynak bağlamı: {source_context}. Kullanılabilecek kaynak sınıfları: {source_labels}.",
            f"Kaynak otoritesi: {source_authorities or 'kaynak bulunamadı'}.",
            "İçtihat, mevzuat ve doktrin için tam künye ve doğrulanabilir atıf ver;"
            " yalnızca gerçekten erişilen metinden kısa ilgili alıntı kullan.",
            "Doktrin, yabancı kararlar ve OECD kaynakları non-binding yardımcı kaynaklardır;"
            " bağlayıcı hukuk kuralı gibi yazılamaz. Çıktı analysis-only ve non-binding bir"
            " değerlendirmedir; kesin görüş, garanti veya hukuki danışmanlık iddiası değildir.",
        ]
    )

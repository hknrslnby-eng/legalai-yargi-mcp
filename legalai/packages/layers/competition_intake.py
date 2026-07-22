"""Maximum-relevant, evidence-driven intake for competition analysis."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any


@dataclass(frozen=True)
class IntakeQuestion:
    key: str
    question: str
    rationale: str
    priority: str
    sensitive_data_warning: str | None = None


@dataclass(frozen=True)
class CompetitionIntake:
    detected_context: tuple[str, ...]
    requested_facts: tuple[IntakeQuestion, ...]
    source_families: tuple[str, ...]


def _normalize(value: str) -> str:
    return (
        value.casefold()
        .replace("ı", "i")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ç", "c")
    )


def _has(text: str, *terms: str) -> bool:
    return any(term in text for term in terms)


def build_competition_intake(
    *,
    question: str,
    known_facts: Mapping[str, Any] | None = None,
    period: str | None = None,
) -> CompetitionIntake:
    known = known_facts or {}
    text = _normalize(question)
    contexts: list[str] = []

    def context(name: str, *terms: str) -> None:
        if _has(text, *terms) and name not in contexts:
            contexts.append(name)

    context("merger", "birlesme", "devralma", "joint venture", "yoğunlaşma", "yoğunlasma")
    context("pricing", "fiyat", "marj", "iskonto", "indirim", "maliyet alti", "margin", "predatory", "yikici fiyat")
    context("distribution", "dagitim", "distrib", "bayi", "münhasır", "munhasir", "dikey", "resale", "yeniden satis", "exclusivity")
    if not contexts:
        contexts.append("general_competition")

    questions: list[IntakeQuestion] = []

    def ask(key: str, prompt: str, rationale: str, priority: str = "P1", warning: str | None = None) -> None:
        if key not in known or known.get(key) in (None, "", [], {}):
            questions.append(IntakeQuestion(key, prompt, rationale, priority, warning))

    ask("relevant_product_market", "İlgili ürün veya hizmet pazarı nasıl tanımlanıyor; ikame ürün/hizmetler ve talep ikamesi nelerdir?", "Pazar tanımı ve ikame analizi olmadan hukuki nitelendirme eksik kalır.", "P0")
    ask("relevant_geographic_market", "İlgili coğrafi pazar nedir; ulusal, bölgesel veya uluslararası sınırlar hangi ticari verilerle destekleniyor?", "Coğrafi rekabet koşulları ve pazar gücü ölçümü için gereklidir.", "P0")
    ask("period_and_timeline", "İncelenen dönem, olay kronolojisi, sözleşme/karar tarihleri ve varsa soruşturma veya bildirim aşamaları nelerdir?", "Pazarın dönemsel seyri ve uygulanacak normların zamanı ayrılmalıdır.", "P0")
    if period:
        ask("missing_periods", f"{period} dönemi içinde eksik kalan ay/yıl veya veri aralıkları var mı; varsa neden?", "Eksik dönemler trend ve nedensellik analizini bozabilir.", "P1")
    else:
        ask("missing_periods", "Hangi ay/yıl dönemleri için veri eksik; eksikliğin nedeni ve telafi edilebilecek kaynaklar nelerdir?", "Yıllar arası karşılaştırma ve olay öncesi/sonrası analizi için gereklidir.", "P1")
    ask("market_shares_by_year", "Algılanan pazarda teşebbüsün ve başlıca rakiplerin yıllara göre pazar payları nedir; hesap yöntemi ve payda nedir?", "Pazar gücü ve değişimin yönü yalnızca tek yıl verisiyle ölçülemez.", "P0")
    ask("sales_volume_by_year", "Yıllara göre satış adedi, kapasite, satış hacmi ve büyüme oranları nedir?", "Hacim verisi pazar payı ve fiyat davranışının ekonomik zeminini kurar.", "P1")
    ask("sales_revenue_by_year", "Yıllara göre satış cirosu, net/brüt gelir, indirim ve iade etkileri nedir?", "Ciro ve net fiyat ayrımı ekonomik etkiyi test eder.", "P1")
    ask("competitors", "En büyük ve en yakın rakipler kimler; ürün, kapasite, fiyat, kalite ve dağıtım bakımından nasıl karşılaştırılıyor?", "Rakiplerin fiili rekabet baskısı ve alternatifleri değerlendirilmelidir.", "P0", "Kişisel kimlik bilgisi değil, teşebbüs/kurum düzeyinde ticari veri sağlayın.")
    ask("suppliers", "En büyük tedarikçiler, kritik girdiler, tedarik yoğunlaşması ve alternatif tedarik imkanları nelerdir?", "Girdi piyasasındaki güç ve bağımlılık zincirleme etkileri belirler.", "P1")
    ask("customers", "En büyük müşteriler, müşteri yoğunlaşması, müşteri geçiş maliyeti ve pazarlık gücü nedir?", "Alıcı gücü ve müşteri bağımlılığı pazar gücünü dengeleyebilir.", "P1", "Kişisel müşteri verisi yerine anonimleştirilmiş ticari segment verisi sağlayın.")
    ask("value_chain_position", "Teşebbüs üretim-dağıtım-zincirinin hangi noktasında; girdiden son kullanıcıya kadar iş akışı ve kontrol ettiği aşamalar nelerdir?", "Dikey etkiler ve fiili darboğazlar zincirdeki konuma bağlıdır.", "P0")
    ask("entry_barriers", "Pazara giriş ve genişleme engelleri nelerdir: lisans, sermaye, teknoloji, ağ etkisi, marka, dağıtım, veri veya mevzuat?", "Kalıcılık ve potansiyel rekabet değerlendirmesi gerekir.", "P1")
    ask("pricing_and_costs", "Fiyat listeleri, net fiyat, maliyet kalemleri, marj, iskonto/prim/rebate ve fiyat değişikliklerinin gerekçesi nedir?", "Fiyatlama davranışının ekonomik ve hukuki testi için gereklidir.", "P0")
    ask("regulatory_constraints", "İlgili sektörde lisans, kota, kamu düzenlemesi, teknik standart, ithalat/ihracat veya başka hukuki kısıtlar var mı?", "Her pazar sonucu salt özel teşebbüs davranışıyla açıklanamayabilir.", "P1")
    ask("sector_reports", "Sektör raporları, resmi/yarı resmi pazar araştırmaları, kurum istatistikleri ve metodoloji notları hangileri?", "Raporlar bağlayıcı içtihat değil, ekonomik/olgusal destek olarak kullanılmalıdır.", "P1")

    if "merger" in contexts:
        ask("transaction_structure", "İşlem tarafları, kontrol değişikliği, işlem bedeli, ortak girişim yapısı ve bildirim eşikleri nedir?", "Yoğunlaşma incelemesinin işlem kapsamı ve kontrol analizine dayanır.", "P0")
        ask("horizontal_vertical_overlap", "Tarafların yatay, dikey veya komşu pazarlardaki örtüşmeleri ve alternatif tedarik/müşteri kanalları nelerdir?", "Rekabetçi endişe ve etkinlik savunması pazar örtüşmesine bağlıdır.", "P0")
    if "pricing" in contexts:
        ask("pricing_strategy", "Fiyat davranışı maliyet altı satış, dışlayıcı iskonto, bağlama, paketleme veya ayrımcı koşul iddiasıyla nasıl ilişkilendiriliyor?", "Nitelendirme için ticari mekanizma ile hukuki unsur eşleştirilmelidir.", "P0")
    if "distribution" in contexts:
        ask("distribution_terms", "Dağıtım sözleşmeleri, münhasırlık, bölge/müşteri kısıtları, yeniden satış fiyatı ve çevrim içi satış kuralları nelerdir?", "Dikey kısıtın kapsamı, süresi ve fiili etkisi birlikte incelenmelidir.", "P0")

    sources = (
        "rekabet_kurumu", "idare_mahkemeleri", "bam", "danistay",
        "oecd_competition", "dg_comp", "curia", "competition_reports",
    )
    return CompetitionIntake(tuple(contexts), tuple(questions), sources)

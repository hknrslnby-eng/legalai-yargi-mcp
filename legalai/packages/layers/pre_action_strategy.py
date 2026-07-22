"""Ön-bilgi toplama ve süreç başlatıcı belge strateji katmanı.

Bu katman karar vermez; belgeyi yerel olarak tasnif eder, eksik vakıa-belge-delil
matrisini çıkarır ve koşullu çözüm yollarını karşılaştırılabilir hale getirir.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import re
import unicodedata
from typing import Any

from legalai.packages.documents.intake import DocumentInput, extract_document
from legalai.packages.layers.operational_cards import build_operational_cards
from legalai.packages.layers.competition_intake import build_competition_intake
from legalai.packages.layers.operational_context import OperationalContextBuilder


@dataclass(frozen=True)
class PreActionRequest:
    document_text: str | None = None
    file_path: str | None = None
    mode: str = "triage"
    question: str = ""
    jurisdiction_hint: str | None = None
    event_dates: list[str] | None = None


@dataclass
class PreActionResult:
    trigger_type: str
    procedural_posture: str
    sender_recipient: dict[str, str]
    claims: list[str]
    dates: list[str]
    priorities: list[dict[str, Any]]
    questions: list[dict[str, Any]]
    requested_documents: list[dict[str, Any]]
    evidence_preservation: list[dict[str, Any]]
    strategy_options: list[dict[str, Any]]
    cross_domain_effects: list[dict[str, Any]]
    assumptions: list[str] = field(default_factory=list)
    missing_facts: list[str] = field(default_factory=list)
    operational_cards: list[dict[str, Any]] = field(default_factory=list)
    operational_context: dict[str, Any] = field(default_factory=dict)
    evidence_ledger: list[dict[str, Any]] = field(default_factory=list)
    source_name: str = "inline"
    warnings: list[str] = field(default_factory=list)
    analysis_only: bool = True
    non_binding: bool = True

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["analysis_only"] = True
        result["non_binding"] = True
        return result


def analyze_pre_action(request: PreActionRequest) -> PreActionResult:
    """Extract a cautious intake matrix without persisting the supplied document."""
    text, source_name, warnings = _extract(request)
    normalized = _normalize(text)
    trigger = _classify(normalized)
    dates = list(dict.fromkeys((request.event_dates or []) + _find_dates(text)))
    urgent = _has_any(normalized, ("tebligat", "sure", "gun icinde", "durusma", "tutuklama", "yakalama"))
    mode = (request.mode or "triage").casefold()
    full = mode in {"full_intake", "strategy", "tam", "derin"}

    missing = _missing_facts(trigger, dates, normalized, full)
    questions = _questions(trigger, full)
    if _is_competition_context(normalized, request.jurisdiction_hint):
        intake = build_competition_intake(question=request.question or text)
        missing.extend(f"[{item.key}] {item.question}" for item in intake.requested_facts)
        questions.extend({
            "id": f"COMP_{item.key}",
            "priority": item.priority,
            "question": item.question,
            "rationale": item.rationale,
            "sensitive_data_warning": item.sensitive_data_warning,
        } for item in intake.requested_facts)
    documents = _documents(trigger, full)
    preservation = _preservation(trigger, normalized)
    priorities = _priorities(urgent, trigger)
    routes = _routes(trigger, normalized, full)
    domains = _cross_domain(trigger, normalized, request.jurisdiction_hint)
    cards = build_operational_cards(
        request.question or text,
        [item["domain"] for item in domains],
        (text,),
    )
    operational_context = OperationalContextBuilder().build(request.question or text, [item["domain"] for item in domains])
    ledger = [
        {
            "claim_id": "document_text",
            "source_id": source_name,
            "source_type": "user_document",
            "full_citation": source_name,
            "short_quote": text[:300],
            "supported": bool(text.strip()),
            "analysis_only": True,
            "non_binding": True,
        }
    ] if text.strip() else []

    assumptions = [
        "Belgenin niteliği ve olay anlatımı yalnızca sağlanan metne göre ön sınıflandırılmıştır.",
        "Süre, görev, yetki, dava şartı ve maddi vakıalar resmi belge ve mevzuat üzerinden ayrıca doğrulanmalıdır.",
        "Belirtilmeyen olgular kurulmuş gerçekler değil, doğrulanması gereken eksiklerdir.",
    ]
    return PreActionResult(
        trigger_type=trigger,
        procedural_posture=_posture(trigger),
        sender_recipient=_sender_recipient(text),
        claims=_claims(text),
        dates=dates,
        priorities=priorities,
        questions=questions,
        requested_documents=documents,
        evidence_preservation=preservation,
        strategy_options=routes,
        cross_domain_effects=domains,
        assumptions=assumptions,
        missing_facts=missing,
        operational_cards=[asdict(card) for card in cards],
        operational_context=operational_context.to_dict(),
        evidence_ledger=ledger,
        source_name=source_name,
        warnings=list(warnings),
    )


def _extract(request: PreActionRequest) -> tuple[str, str, tuple[str, ...]]:
    if request.document_text is not None and request.file_path is not None:
        raise ValueError("document_text and file_path cannot be used together")
    if request.document_text is not None:
        extracted = extract_document(DocumentInput(text=request.document_text))
    elif request.file_path is not None:
        extracted = extract_document(DocumentInput(file_path=Path(request.file_path)))
    else:
        extracted = extract_document(DocumentInput(text=request.question or "Belge metni sağlanmadı."))
    return extracted.text, extracted.source_name, extracted.warnings


def _normalize(value: str) -> str:
    text = value
    for _ in range(2):
        try:
            repaired = text.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if repaired == text:
            break
        text = repaired
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _is_competition_context(text: str, hint: str | None) -> bool:
    normalized_hint = _normalize(hint or "")
    return normalized_hint == "rekabet" or _has_any(text, (
        "rekabet", "fiyatlama", "pazar payi", "hakim durum", "kartel", "dagitim zinciri", "birlesme devralma",
    ))


def _classify(text: str) -> str:
    if "iddianame" in text or "sanik" in text:
        return "iddianame"
    if "tebligat" in text or "dava dilekcesi" in text:
        return "tebligat veya dava dilekçesi"
    if "ihtar" in text or "fesih" in text:
        return "ihtar veya fesih bildirimi"
    if "savunma talebi" in text or "disiplin" in text:
        return "yazılı savunma talebi"
    if _has_any(text, ("kurul", "idari basvuru", "idareye basvuru", "resmi yazı")):
        return "idari/kurumsal bildirim"
    return "belirsiz süreç başlatıcı belge"


def _posture(trigger: str) -> str:
    return {
        "iddianame": "ceza soruşturması veya kovuşturması",
        "tebligat veya dava dilekçesi": "tebliğ edilmiş veya edilmek üzere olan yargısal süreç",
        "ihtar veya fesih bildirimi": "dava/icra öncesi uyuşmazlık bildirimi",
        "yazılı savunma talebi": "kurumsal, iş veya idari savunma aşaması",
        "idari/kurumsal bildirim": "idari veya kurul öncesi/yanıt aşaması",
    }.get(trigger, "usuli konum belirsiz")


def _sender_recipient(text: str) -> dict[str, str]:
    sender = "belgede tespit edilmedi"
    recipient = "belgede tespit edilmedi"
    sender_match = re.search(r"(?:gonderen|gönderen|from)\s*[:：]\s*([^\n]+)", text, re.I)
    recipient_match = re.search(r"(?:muhatap|alici|alıcı|to)\s*[:：]\s*([^\n]+)", text, re.I)
    if sender_match:
        sender = sender_match.group(1).strip()
    if recipient_match:
        recipient = recipient_match.group(1).strip()
    return {"sender": sender, "recipient": recipient}


def _claims(text: str) -> list[str]:
    signals = (("alacak", "alacak/ifa iddiası"), ("fesih", "fesih/temerrüt iddiası"), ("tazminat", "tazminat iddiası"), ("suç", "suç isnadı"), ("ayrim", "ayrımcılık iddiası"))
    found = [label for term, label in signals if term in _normalize(text)]
    return found or ["Belgedeki talep ve vakıaların ayrıştırılması gerekiyor."]


def _find_dates(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"\b(?:\d{1,2}[./]){2}\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b", text)))


def _missing_facts(trigger: str, dates: list[str], text: str, full: bool) -> list[str]:
    if full:
        return []
    missing = []
    if not dates:
        missing.append("Belgenin düzenlenme, tebliğ ve olay tarihleri")
    missing.extend(["Tarafların kimlik ve sıfatları", "Belgedeki talep, isnat veya yaptırımın tam kapsamı", "Ekler ve karşı tarafın dayandığı deliller"])
    if trigger in {"iddianame", "yazılı savunma talebi"}:
        missing.append("Savunma süresi, usulî aşama ve önceki beyanlar")
    if trigger == "belirsiz süreç başlatıcı belge":
        missing.append("Belgenin hangi kurum/merci tarafından gönderildiği")
    return missing


def _questions(trigger: str, full: bool) -> list[dict[str, Any]]:
    base = [
        {"id": "Q1", "priority": "P0", "question": "Belge ne zaman ve hangi yolla tebliğ edildi? Tebliğ mazbatası veya elektronik kayıt mevcut mu?"},
        {"id": "Q2", "priority": "P1", "question": "Belgedeki iddia/talep ve karşılanması istenen sonuç tam olarak nedir?"},
        {"id": "Q3", "priority": "P1", "question": "Olay kronolojisi ve daha önce yapılan başvuru, ödeme, görüşme veya beyanlar nelerdir?"},
    ]
    if trigger == "iddianame":
        base.append({"id": "Q4", "priority": "P0", "question": "İsnat edilen fiil, ifade tutanakları, arama/el koyma ve diğer soruşturma işlemleri nelerdir?"})
    if trigger in {"ihtar veya fesih bildirimi", "tebligat veya dava dilekçesi"}:
        base.append({"id": "Q5", "priority": "P1", "question": "Sözleşme, borç, temerrüt, fesih ve varsa arabuluculuk sürecinin belgeleri nelerdir?"})
    if full:
        base.extend([
            {"id": "Q6", "priority": "P2", "question": "Tanık, teknik uzman, kayıt/log, kamera, yazışma ve üçüncü kişi kaynakları hangileridir?"},
            {"id": "Q7", "priority": "P2", "question": "Müzakere, sulh, 35/A, arabuluculuk, idari/kurul başvurusu veya icra yolunda hedeflenen sonuç nedir?"},
        ])
    return base


def _documents(trigger: str, full: bool) -> list[dict[str, Any]]:
    docs = [
        {"priority": "P0", "item": "Belgenin tamamı, ekleri, tebliğ/teslim kayıtları ve zarf/metadata", "reason": "Süre ve kapsam kontrolü"},
        {"priority": "P1", "item": "Olay kronolojisini destekleyen sözleşme, yazışma, ödeme ve başvuru kayıtları", "reason": "Vakıa ve talep doğrulaması"},
    ]
    if trigger == "iddianame":
        docs.append({"priority": "P0", "item": "İfade tutanakları, yakalama/arama/el koyma belgeleri ve bilirkişi raporları", "reason": "Savunma ve delil hukuku incelemesi"})
    if full:
        docs.extend([
            {"priority": "P2", "item": "Tanık/uzman listesi, teknik kayıtlar, loglar, kamera ve cihaz imajları", "reason": "Delil koruma ve karşı açıklama"},
            {"priority": "P2", "item": "Sektörel iş akışı, prosedür, iç politika ve benzer işlem örnekleri", "reason": "Operasyonel bağlamın doğrulanması"},
        ])
    return docs


def _preservation(trigger: str, text: str) -> list[dict[str, Any]]:
    items = [
        {"priority": "P0", "action": "Belgenin aslı, ekleri, tebliğ kaydı ve dosya metadata'sını değişmeden koru.", "reason": "Süre ve bütünlük incelemesi"},
        {"priority": "P1", "action": "E-posta, mesajlaşma, log, kamera, ödeme ve elektronik kayıtlar için silinmeyi önleyici koruma talimatı oluştur.", "reason": "Geri döndürülemez delil kaybı riski"},
    ]
    if trigger == "iddianame" or _has_any(text, ("sahte", "dolandiricilik", "tehdit")):
        items.append({"priority": "P0", "action": "Cihaz ve dijital veriler üzerinde değişiklik yapmadan adli bilişim uzmanından koruma/inceleme görüşü al.", "reason": "Ceza delilinin bütünlüğü"})
    return items


def _priorities(urgent: bool, trigger: str) -> list[dict[str, Any]]:
    if trigger == "belirsiz süreç başlatıcı belge" and not urgent:
        return [
            {"id": "P1", "title": "Belgenin niteliğini ve kapsamını doğrulama", "action": "Gönderen, merci, tarih, ekler ve istenen işlem ilk olarak netleştirilmeli."},
            {"id": "P2", "title": "Eksik bilgi-belge matrisi", "action": "Taraf, talep, kronoloji, merci ve dayanaklar tamamlanmalı."},
            {"id": "P3", "title": "Koşullu çözüm yolları", "action": "Dava dışı ve dava içi seçenekler ancak doğrulanan vakıalara göre sıralanmalı."},
        ]
    p0 = "Tebliğ/süre veya geri döndürülemez delil riski derhal doğrulanmalı." if urgent or trigger == "iddianame" else "Belgenin kapsamı ve tebliğ durumu ilk olarak doğrulanmalı."
    return [
        {"id": "P0", "title": "Acil usul ve delil koruma", "action": p0},
        {"id": "P1", "title": "Eksik bilgi-belge matrisi", "action": "Taraf, talep, kronoloji, merci ve dayanaklar tamamlanmalı."},
        {"id": "P2", "title": "Çapraz hukuk ve operasyon araştırması", "action": "Norm, içtihat, kurum, sektör ve teknik akışların etkileri karşılaştırılmalı."},
        {"id": "P3", "title": "Seçim ve uygulama planı", "action": "Koşulları doğrulanan yolların maliyet, süre, delil ve geri döndürülebilirlik bakımından seçimi yapılmalı."},
    ]


def _routes(trigger: str, text: str, full: bool) -> list[dict[str, Any]]:
    routes = [
        {"route": "cevap/itiraz", "when": "Belgenin usulüne, vakıalarına veya hukuki nitelendirmesine itiraz edilebildiği doğrulanırsa", "benefit": "Süre içinde savunma ve kayıt oluşturma", "risk": "Süre, merci ve cevap kapsamı kaçırılabilir"},
        {"route": "sulh, feragat veya ibra", "when": "Tasarruf edilebilir hak ve temsil yetkisi varsa", "benefit": "Uyuşmazlığı hızlı ve kontrollü kapatma", "risk": "Geniş veya belirsiz metin hak kaybı doğurabilir"},
        {"route": "Avukatlık Kanunu 35/A", "when": "Koşulları, avukat yetkisi ve tutanak/ifa düzeni somut olayda sağlanıyorsa", "benefit": "Dava öncesi uzlaşma ve olası icra kabiliyeti", "risk": "Şekil, yetki ve icra edilebilirlik ayrıca doğrulanmalı"},
        {"route": "zorunlu veya ihtiyari arabuluculuk", "when": "Uyuşmazlık türü ve dava şartı kapsamı doğrulanırsa", "benefit": "Anlaşma veya dava şartının tamamlanması", "risk": "Yanlış başvuru yeri veya eksik anlaşma metni"},
        {"route": "icra veya ihtiyati koruma", "when": "Muaccel alacak, belge ve gecikme/kaçırma riski varsa", "benefit": "Tahsil veya mevcut durumun korunması", "risk": "Yetki, takip türü ve kötü niyet sonuçları"},
        {"route": "idare/kurul başvurusu", "when": "Özel idari veya kurul yolu, ret kararı ya da düzenleyici inceleme olanağı varsa", "benefit": "İdari çözüm ve sonraki sürece kayıt üretme", "risk": "Özel başvuru ve dava süreleri"},
        {"route": "ceza şikayeti ve delil koruma", "when": "Somut suç şüphesi ve hukuka uygun delil varsa", "benefit": "Yetkili soruşturma ve delil koruma ihtimali", "risk": "Şikayet delil toplama aracı olarak kötüye kullanılamaz; iftira riski"},
        {"route": "dava", "when": "Görev, yetki, dava şartı, süre ve ispat zemini doğrulanırsa", "benefit": "Bağlayıcı yargısal koruma istemi", "risk": "Süre, görev, yetki ve ispat eksikleri"},
    ]
    if trigger == "iddianame":
        routes.insert(0, {"route": "ceza savunması ve usul itirazları", "when": "İddianame, isnat, delil elde etme ve soruşturma işlemleri incelendiğinde", "benefit": "Savunma hakkı ve hukuka aykırı delil itirazlarının korunması", "risk": "Ceza muhakemesi süreleri ve aşama kaybı"})
    if not full:
        return routes
    return routes + [{"route": "stratejik sıralama", "when": "Tüm seçeneklerin maliyet, süre, delil, karşı taraf davranışı ve geri döndürülebilirliği karşılaştırıldığında", "benefit": "Dava dışı ve dava içi yolların birlikte planlanması", "risk": "Eksik olgular nedeniyle öncelik değişebilir"}]


def _cross_domain(trigger: str, text: str, hint: str | None) -> list[dict[str, Any]]:
    domains = ["hukuk", "ceza", "idare"]
    if trigger == "iddianame":
        domains = ["ceza", "hukuk", "anayasa", "insan hakları"]
    elif _has_any(text, ("vergi", "vergi dairesi")):
        domains.append("vergi")
    if hint:
        domains.insert(0, hint)
    result = []
    for domain in dict.fromkeys(domains):
        result.append({"domain": domain, "positive_effects": [f"{domain} alanındaki usul, norm ve içtihatların lehe etkileri araştırılmalı."], "negative_effects": [f"{domain} alanındaki süre, görev, yetki, delil ve çelişen nitelendirmeler aleyhe risk yaratabilir."], "status": "araştırma adayı; somut vakıa ve kaynakla doğrulanmalı"})
    return result

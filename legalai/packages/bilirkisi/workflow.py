"""Local-first processing boundary for expert-report objections.

The module deliberately separates technical hypotheses from legal conclusions.
It does not claim that a heuristic is an expert opinion; the host model and a
qualified human must review the returned matrix before it is used.
"""
from __future__ import annotations

import html
import re
import zipfile
from io import BytesIO
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable
from xml.etree import ElementTree

from legalai.packages.pii.outbound import mask_for_external
from legalai.packages.layers.quality_contract import build_quality_contract

_MAX_REPORT_BYTES = 20 * 1024 * 1024
_SUPPORTED = {".txt", ".md", ".html", ".htm", ".pdf", ".docx", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
_PII_PATTERNS = (
    (re.compile(r"\b\d{11}\b"), "[TCKN_MASKELENDI]"),
    (re.compile(r"\bTR\d{24}\b", re.IGNORECASE), "[IBAN_MASKELENDI]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[EPOSTA_MASKELENDI]"),
    (re.compile(r"(?<!\d)(?:\+?90\s?)?(?:5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2})(?!\d)"), "[TELEFON_MASKELENDI]"),
)


@dataclass(frozen=True)
class ExtractedReport:
    text: str
    external_text: str
    format: str
    source_name: str = "inline"
    ocr_required: bool = False
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class DomainInference:
    domain: str
    confidence: float
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class ReportClaim:
    claim_id: str
    excerpt: str
    technical_finding: str
    technical_counterargument: str
    legal_links: tuple[str, ...]
    temporal_effect: str
    missing_evidence: tuple[str, ...]
    technical_questions: tuple[str, ...] = ()
    alternative_hypotheses: tuple[str, ...] = ()
    legal_issue_links: tuple[str, ...] = ()
    research_instructions: tuple[str, ...] = ()


@dataclass(frozen=True)
class BilirKisiAnalysis:
    report: ExtractedReport
    question: str
    technical_domain: str
    claims: tuple[ReportClaim, ...]
    temporal_context: dict[str, Any]
    legal_sources: tuple[dict[str, Any], ...] = ()
    production_enabled: bool = True
    non_binding: bool = True
    assistant_instructions: str = ""


@dataclass(frozen=True)
class PetitionObjection:
    claim_id: str
    report_excerpt: str
    technical_basis: str
    legal_basis: tuple[str, ...]
    requested_action: str
    missing_evidence: tuple[str, ...]


@dataclass(frozen=True)
class PetitionDraft:
    title: str
    objections: tuple[PetitionObjection, ...]
    missing_evidence: tuple[str, ...]
    legal_sources: tuple[dict[str, Any], ...]
    non_binding: bool = True


def _mask_text(text: str) -> str:
    masked = text
    for pattern, replacement in _PII_PATTERNS:
        masked = pattern.sub(replacement, masked)
    return masked


def _xml_text(xml: bytes, tags: Iterable[str]) -> str:
    root = ElementTree.fromstring(xml)
    wanted = set(tags)
    values = [node.text or "" for node in root.iter() if node.tag.rsplit("}", 1)[-1] in wanted]
    return "\n".join(value.strip() for value in values if value.strip())


OcrProvider = Callable[[Path], str | None]


def _default_ocr_provider() -> OcrProvider | None:
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        return None

    def _extract(path: Path) -> str | None:
        if path.suffix.lower() == ".pdf":
            try:
                import fitz
            except ImportError:
                return None
            pages: list[str] = []
            with fitz.open(path) as document:
                for page in document:
                    png = page.get_pixmap(dpi=200, alpha=False).tobytes("png")
                    with Image.open(BytesIO(png)) as image:
                        pages.append(pytesseract.image_to_string(image, lang="tur+eng"))
            return "\n".join(pages)
        with Image.open(path) as image:
            return pytesseract.image_to_string(image, lang="tur+eng")

    return _extract


def _read_file(path: Path, ocr_provider: OcrProvider | None = None) -> tuple[str, bool, list[str]]:
    suffix = path.suffix.lower()
    if suffix not in _SUPPORTED:
        raise ValueError(f"Desteklenmeyen bilirkişi raporu formatı: {suffix or 'uzantısız'}")
    if not path.is_file():
        raise FileNotFoundError(str(path))
    if path.stat().st_size > _MAX_REPORT_BYTES:
        raise ValueError("Bilirkişi raporu 20 MB sınırını aşıyor.")

    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace"), False, []
    if suffix in {".html", ".htm"}:
        raw = path.read_text(encoding="utf-8", errors="replace")
        return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).strip(), False, []
    if suffix == ".docx":
        with zipfile.ZipFile(path) as archive:
            return _xml_text(archive.read("word/document.xml"), {"t"}), False, []
    if suffix == ".xlsx":
        with zipfile.ZipFile(path) as archive:
            shared = ""
            if "xl/sharedStrings.xml" in archive.namelist():
                shared = _xml_text(archive.read("xl/sharedStrings.xml"), {"t"})
            sheet_names = [name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")]
            sheets = [_xml_text(archive.read(name), {"v", "t"}) for name in sheet_names]
        return "\n".join(item for item in [shared, *sheets] if item), False, []
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        if extracted.strip():
            return extracted, False, []
        provider = ocr_provider or _default_ocr_provider()
        if provider is not None:
            try:
                ocr_text = provider(path) or ""
                if ocr_text.strip():
                    return ocr_text, False, []
            except Exception as exc:
                return "", True, [f"PDF OCR sağlayıcısı çalışmadı: {type(exc).__name__}"]
        return "", True, ["PDF metin çıkarmadı; yerel OCR motoru bulunamadı veya çalıştırılamadı."]
    provider = ocr_provider or _default_ocr_provider()
    if provider is not None:
        try:
            extracted = provider(path) or ""
            if extracted.strip():
                return extracted, False, []
        except Exception as exc:
            return "", True, [f"OCR sağlayıcısı çalışmadı: {type(exc).__name__}"]
    return "", True, ["Görüntü raporu için OCR gerekir; yerel OCR motoru bulunamadı."]


def extract_report_text(*, text: str | None = None, file_path: str | Path | None = None, ocr_provider: OcrProvider | None = None) -> ExtractedReport:
    if bool(text) == bool(file_path):
        raise ValueError("Tam olarak text veya file_path verilmelidir.")
    if text is not None:
        raw, fmt, source_name, ocr, warnings = text, "text", "inline", False, []
    else:
        path = Path(file_path)  # type: ignore[arg-type]
        raw, ocr, warnings = _read_file(path, ocr_provider)
        fmt, source_name = path.suffix.lower().lstrip("."), path.name
    return ExtractedReport(raw, _mask_text(raw), fmt, source_name, ocr, tuple(warnings))


def _claim_lines(text: str) -> list[str]:
    lines = [re.sub(r"\s+", " ", line).strip(" -•\t") for line in text.splitlines()]
    lines = [line for line in lines if len(line) >= 20]
    if not lines and text.strip():
        lines = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    return lines[:25] or ["Raporda değerlendirilmesi gereken belirli bir bulgu ayrıştırılamadı."]


def infer_technical_domain(report_text: str, supplied_domain: str = "") -> DomainInference:
    if supplied_domain.strip():
        return DomainInference(supplied_domain.strip(), 1.0, ("Kullanıcı tarafından teknik alan sağlandı.",))
    lowered = report_text.casefold()
    candidates = (
        ("fire_safety_engineering", ("yangın", "yangin", "yangın yükü", "duman", "sprinkler", "kalibrasyon")),
        ("structural_engineering", ("betonarme", "kolon", "kiriş", "deprem", "statik", "taşıyıcı")),
        ("accounting_finance", ("bilanço", "mizan", "muhasebe", "amortisman", "nakit akışı")),
        ("medical_forensic", ("tıbbi", "yaralanma", "maluliyet", "epikriz", "otopsi", "tedavi")),
        ("software_cybersecurity", ("yazılım", "sunucu", "log", "siber", "zararlı yazılım", "veritabanı")),
        ("environmental_engineering", ("emisyon", "atık", "çevre", "zemin", "kirlilik", "gürültü")),
    )
    scores = [(domain, tuple(term for term in terms if term in lowered)) for domain, terms in candidates]
    domain, evidence = max(scores, key=lambda item: len(item[1]), default=("unspecified", ()))
    if not evidence:
        return DomainInference("unspecified", 0.20, ("Teknik alan metinden güvenle çıkarılamadı.",))
    confidence = min(0.95, 0.55 + 0.12 * len(evidence))
    return DomainInference(domain, confidence, evidence)


def link_substantive_issues(question: str, domain: DomainInference) -> tuple[str, ...]:
    lowered = question.casefold()
    links = [
        "Teknik bulgunun ispat değeri, ilgili maddi hukuk unsuruna ve illiyet değerlendirmesine bağlanmalıdır.",
        "Teknik yöntem, raporun gerekçesi ve denetime elverişliliği HMK m.266 ve m.279-281 çerçevesinde ayrıca incelenmelidir.",
    ]
    if any(term in lowered for term in ("sigorta", "tazminat", "poliçe", "hasar")):
        links.append("Sigorta sözleşmesinin teminat kapsamı, hasar nedeni, illiyet ve eksper/rapor değerlendirmesiyle bağlantı kurulmalıdır.")
    if any(term in lowered for term in ("sözleşme", "bedel", "ifa", "fesih")):
        links.append("Teknik bulgunun sözleşmesel edim, ayıp, ifa ve zarar unsurlarına etkisi araştırılmalıdır.")
    if any(term in lowered for term in ("ceza", "suç", "soruşturma", "kast")):
        links.append("Teknik bulgunun suçun maddi unsuru, kast/taksir ve illiyet bakımından etkisi araştırılmalıdır.")
    links.append(f"{domain.domain} alanındaki teknik standart, ölçüm yöntemi ve alternatif hipotezler erişilebilir kaynaklarla doğrulanmalıdır.")
    return tuple(links)


def _research_brief(excerpt: str, domain: DomainInference, question: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    technical_questions = (
        "Yöntem tekrar üretilebilir ve denetlenebilir mi?",
        "Ham veri, ölçüm belirsizliği, kalibrasyon ve örnekleme kayıtları mevcut mu?",
        "Aynı bulguyu açıklayabilecek alternatif teknik hipotezler test edilmiş mi?",
    )
    alternatives = (
        f"{domain.domain} alanında kullanılan varsayım veya örnekleme değişirse sonuç değişebilir.",
        "Ham veri/kalibrasyon/ölçüm belirsizliği eksikliği, kesinlik iddiasını zayıflatabilir.",
    )
    materials = ("ham veri", "yöntem ve standardın sürümü", "kalibrasyon/numune kayıtları", "alternatif hipotez testleri")
    return technical_questions, alternatives, materials, link_substantive_issues(question, domain)


def _technical_counterargument(excerpt: str, domain: str) -> tuple[str, tuple[str, ...]]:
    lowered = excerpt.casefold()
    missing: list[str] = []
    if any(term in lowered for term in ("kesin", "kesinlikle", "ölçüm")):
        missing.extend(["ölçüm belirsizliği ve hata payı", "kalibrasyon kayıtları", "ham veri"])
        counter = f"{domain or 'Teknik'} açıdan kesinlik iddiası; yöntem, kalibrasyon, hata payı ve ham veri açıklanmadan doğrulanamaz."
    elif any(term in lowered for term in ("incelemeden", "açıklamadan", "varsay", "kabul")):
        missing.extend(["kullanılan yöntem ve varsayımlar", "alternatif hipotez testi"])
        counter = "Sonuç, açık yöntem ve test edilebilir varsayımlar gösterilmeden kurulmuşsa yeniden üretilebilir bir teknik çıkarım değildir."
    else:
        missing.extend(["ham veri ve kaynak kayıtları", "uzmanlık yöntemi ve ölçütleri"])
        counter = "Bulguyu destekleyen teknik veri, yöntem ve alternatif açıklamalar karşılaştırılmadan sonuç tek başına yeterli kabul edilemez."
    return counter, tuple(missing)


async def analyze_report(
    *,
    text: str | None = None,
    file_path: str | Path | None = None,
    question: str = "",
    technical_domain: str = "",
    event_dates: list[str] | None = None,
    case_date: str | None = None,
    legal_sources: list[dict[str, Any]] | None = None,
) -> BilirKisiAnalysis:
    report = extract_report_text(text=text, file_path=file_path)
    # Keep the mandatory async PII boundary in the path that feeds host models
    # or live corpus adapters, even though extraction already redacts common IDs.
    external_text = await mask_for_external(report.external_text)
    report = ExtractedReport(report.text, external_text, report.format, report.source_name, report.ocr_required, report.warnings)
    inference = infer_technical_domain(report.text, technical_domain)
    claims: list[ReportClaim] = []
    for index, excerpt in enumerate(_claim_lines(report.text), 1):
        counter, missing = _technical_counterargument(excerpt, inference.domain)
        technical_questions, alternatives, required_materials, legal_issue_links = _research_brief(
            excerpt, inference, question
        )
        claims.append(
            ReportClaim(
                claim_id=f"RAPOR-{index}",
                excerpt=excerpt,
                technical_finding="Rapor bulgusu yerel metinden ayrıştırıldı; uzman doğrulaması gerekir.",
                technical_counterargument=counter,
                legal_links=(
                    "HMK m.266 ve bilirkişi incelemesinin sınırları (güncel metin/veritabanı ile doğrulanmalı)",
                    "HMK m.279-281 kapsamında gerekçe, denetime elverişlilik ve itiraz değerlendirmesi",
                    *legal_issue_links,
                ),
                temporal_effect="Rapor, olay ve dava tarihleriyle birlikte olay tarihinde yürürlükteki teknik/hukuki çerçeveye göre ayrıca karşılaştırılmalıdır.",
                missing_evidence=tuple(dict.fromkeys((*missing, *required_materials))),
                technical_questions=technical_questions,
                alternative_hypotheses=alternatives,
                legal_issue_links=legal_issue_links,
                research_instructions=(
                    "Aynı teknik bilim dalında standart, yöntem, ham veri ve karşı hipotezleri derinlemesine araştır; "
                    "teknik sonucu kesin uzman görüşü gibi sunma.",
                ),
            )
        )
    temporal = {"event_dates": event_dates or [], "case_date": case_date, "status": "date-specific-pending-source-resolution"}
    instructions = (
        f"Teknik alan çıkarımı: {inference.domain} (güven {inference.confidence:.2f}). "
        "Teknik alan düşük güvenliyse bu alanı kesinleştirme; en az iki makul teknik alan/hipotez öner ve "
        "hangi bulgunun hangisine bağlı olduğunu göster. Her RAPOR-* iddiasını aynı teknik bilim dalında "
        "kapsamlı bir araştırma/tez hazırlığı gibi test et: bulgunun veri kökenini, ölçüm modelini, "
        "standart sürümünü, kalibrasyonunu, hata payını, örneklemesini, yeniden üretilebilirliğini, "
        "alternatif teknik açıklamalarını ve karşı deney/hesaplamaları ayrı ayrı değerlendir. "
        "Teknik eleştiriyi yalnızca 'eksik inceleme' demekle bırakma; rapor sonucunun hangi varsayım "
        "değişince ne ölçüde değişeceğini ve bilirkişiye yöneltilecek somut soruları yaz. "
        "Sonra her teknik karşı argümanı, konunun esasını düzenleyen tüm ilgili maddi hukuk unsurları, "
        "usul kuralları, teknik mevzuat/standartlar ve erişilmiş içtihatlarla bağla; HMK m.266 ve "
        "m.279-281 yalnızca usul çapasıdır. Her bağlantıda hukuk kuralı → teknik bulgu → itiraz sonucu "
        "zincirini kur. Kaynak yoksa kesin görüş yazma; teknik uzman görüşü değildir, non-binding analiz "
        "ve araştırma brifidir."
    )
    instructions += "\n\n" + build_quality_contract("auto")
    if report.ocr_required:
        instructions += " OCR gerekli veya başarısız: teknik sonuç üretmeden önce belge metni yerel OCR ya da kullanıcı doğrulamasıyla tamamlanmalıdır."
    return BilirKisiAnalysis(report, question, inference.domain, tuple(claims), temporal, tuple(legal_sources or ()), True, True, instructions)


def build_petition_draft(analysis: BilirKisiAnalysis, *, court: str = "") -> PetitionDraft:
    objections = tuple(
        PetitionObjection(
            claim_id=claim.claim_id,
            report_excerpt=claim.excerpt,
            technical_basis=claim.technical_counterargument,
            legal_basis=claim.legal_links,
            requested_action="İtirazın değerlendirilmesi; gerekirse ek rapor veya yeni bilirkişi incelemesi alınması.",
            missing_evidence=claim.missing_evidence,
        )
        for claim in analysis.claims
    )
    missing = tuple(dict.fromkeys(item for objection in objections for item in objection.missing_evidence))
    title = f"{court + ' - ' if court else ''}Bilirkişi raporuna itiraz taslağı"
    return PetitionDraft(title, objections, missing, analysis.legal_sources, True)

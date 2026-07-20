"""Local-first processing boundary for expert-report objections.

The module deliberately separates technical hypotheses from legal conclusions.
It does not claim that a heuristic is an expert opinion; the host model and a
qualified human must review the returned matrix before it is used.
"""
from __future__ import annotations

import html
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree

from legalai.packages.pii.outbound import mask_for_external

_MAX_REPORT_BYTES = 20 * 1024 * 1024
_SUPPORTED = {".txt", ".md", ".html", ".htm", ".pdf", ".docx", ".xlsx", ".xls", ".png", ".jpg", ".jpeg"}
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
class ReportClaim:
    claim_id: str
    excerpt: str
    technical_finding: str
    technical_counterargument: str
    legal_links: tuple[str, ...]
    temporal_effect: str
    missing_evidence: tuple[str, ...]


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


def _read_file(path: Path) -> tuple[str, bool, list[str]]:
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
        return "\n".join(page.extract_text() or "" for page in reader.pages), False, []
    return "", True, ["Görüntü raporu için OCR gerekir; OCR motoru bu yerel çekirdekte etkin değildir."]


def extract_report_text(*, text: str | None = None, file_path: str | Path | None = None) -> ExtractedReport:
    if bool(text) == bool(file_path):
        raise ValueError("Tam olarak text veya file_path verilmelidir.")
    if text is not None:
        raw, fmt, source_name, ocr, warnings = text, "text", "inline", False, []
    else:
        path = Path(file_path)  # type: ignore[arg-type]
        raw, ocr, warnings = _read_file(path)
        fmt, source_name = path.suffix.lower().lstrip("."), path.name
    return ExtractedReport(raw, _mask_text(raw), fmt, source_name, ocr, tuple(warnings))


def _claim_lines(text: str) -> list[str]:
    lines = [re.sub(r"\s+", " ", line).strip(" -•\t") for line in text.splitlines()]
    lines = [line for line in lines if len(line) >= 20]
    if not lines and text.strip():
        lines = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    return lines[:25] or ["Raporda değerlendirilmesi gereken belirli bir bulgu ayrıştırılamadı."]


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
    claims: list[ReportClaim] = []
    for index, excerpt in enumerate(_claim_lines(report.text), 1):
        counter, missing = _technical_counterargument(excerpt, technical_domain)
        claims.append(
            ReportClaim(
                claim_id=f"RAPOR-{index}",
                excerpt=excerpt,
                technical_finding="Rapor bulgusu yerel metinden ayrıştırıldı; uzman doğrulaması gerekir.",
                technical_counterargument=counter,
                legal_links=("HMK m.266 ve bilirkişi incelemesinin sınırları (güncel metin/veritabanı ile doğrulanmalı)", "HMK m.279-281 kapsamında gerekçe, denetime elverişlilik ve itiraz değerlendirmesi"),
                temporal_effect="Rapor, olay ve dava tarihleriyle birlikte olay tarihinde yürürlükteki teknik/hukuki çerçeveye göre ayrıca karşılaştırılmalıdır.",
                missing_evidence=missing,
            )
        )
    temporal = {"event_dates": event_dates or [], "case_date": case_date, "status": "date-specific-pending-source-resolution"}
    instructions = (
        "Her RAPOR-* iddiasını önce aynı teknik bilim dalında test et; sonra karşı teknik hipotezi, "
        "eksik veriyi ve yöntem sorununu ayır; ardından corpus kaynaklarıyla mevzuat/içtihat bağlantısını kur. "
        "Kaynak yoksa kesin görüş yazma; sonucu non-binding analiz olarak sun."
    )
    return BilirKisiAnalysis(report, question, technical_domain, tuple(claims), temporal, tuple(legal_sources or ()), True, True, instructions)


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

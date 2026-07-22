from legalai.packages.corpus.sources.registry import default_source_registry
from legalai.packages.layers.memorandum import MEMORANDUM_SECTIONS, MemorandumProfile, build_memorandum_instructions
from legalai.packages.layers.operational_context import OperationalContextBuilder
from legalai.packages.layers.source_routing import build_source_query_plan
from legalai.packages.layers.translation_contract import extract_immutable_citation_ids
from legalai.packages.jurisdictions.selection import guess_jurisdictions


def test_competition_plan_includes_domestic_courts_and_authoritative_report_families():
    plan = build_source_query_plan(
        question="Fiyatlama ve dağıtım uygulamasının pazar etkisi",
        jurisdiction_ids=("rekabet",),
        expert_lenses=("ekonomi", "sektor_analizi"),
    )
    selected = {item.source_id for item in plan.subqueries}

    assert {"rekabet_kurumu", "bam", "danistay", "idare_mahkemeleri"} <= selected
    assert {"oecd_competition", "dg_comp", "curia", "competition_reports"} <= selected
    assert "bim" in {item.source_id for item in plan.skipped}


def test_trade_defense_plan_is_explicit_about_domestic_and_comparative_sources():
    plan = build_source_query_plan(
        question="Damping marjı, sübvansiyon ve zarar incelemesi",
        jurisdiction_ids=("ticaret_savunmasi",),
        expert_lenses=("ticaret_savunmasi",),
    )
    selected = {item.source_id for item in plan.subqueries}

    assert {"bam", "danistay", "idare_mahkemeleri"} <= selected
    assert {
        "ticaret_bakanligi_ithalat", "wto_trade_remedy_agreements",
        "eu_trade_defense_regulations", "us_trade_remedy_determinations",
    } <= {item.source_id for item in plan.skipped}


def test_registry_exposes_report_authority_and_bim_verification_gate():
    registry = default_source_registry()

    reports = registry.get("competition_reports")
    bim = registry.get("bim")
    assert reports is not None and reports.authority_level == "non_binding_economic_reference"
    assert reports.metadata["precedential"] is False
    assert bim is not None and bim.status == "verification_pending" and bim.live_supported is False


def test_kvkk_related_lenses_and_operational_legal_impacts_are_contextual():
    selection = guess_jurisdictions(
        "Tedarikçi veri ihlali, çalışan erişimi, NIS-2 bildirimi ve idari başvuru sorunu."
    )
    assert selection.primary == "kvkk"
    assert {"nis_1", "nis_2", "siber_guvenlik", "idare", "sozlesmeler"} <= set(selection.related_law.supporting)

    context = OperationalContextBuilder().build(
        "Maden arama ruhsatı, saha izinleri ve teknik proje yürütümü",
        ("idare",),
    )
    assert context.findings
    assert any(finding.legal_impacts for finding in context.findings)


def test_opinion_contract_has_thirteen_sections_and_preserves_citation_ids():
    instructions = build_memorandum_instructions(
        MemorandumProfile(detail_level="deep", output_language="de"),
        source_ids=("ECLI:TR:ABC:2025:1",),
    )

    assert len(MEMORANDUM_SECTIONS) == 13
    assert "#ECLI:TR:ABC:2025:1" in instructions
    assert extract_immutable_citation_ids("ECLI:TR:ABC:2025:1 CELEX:32016R0679") == (
        "ECLI:TR:ABC:2025:1", "CELEX:32016R0679",
    )

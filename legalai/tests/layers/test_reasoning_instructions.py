from legalai.packages.layers.legal_reasoning import build_reasoning_instructions
from legalai.packages.layers.operational_context import OperationalContextBuilder
from legalai.packages.layers.reasoning_playbook import REASONING_PLAYBOOK


def test_reasoning_instructions_contain_four_ordered_steps():
    text = build_reasoning_instructions(["hukuk", "ceza"])
    positions = [text.index(marker) for marker in (
        "1. Hukuki sorun nedir?",
        "2. Teorik ve yasal altyapı nedir?",
        "3. Somut olayın unsurlarla ilişkisi nedir?",
        "4. Cevap ve strateji nedir?",
    )]
    assert positions == sorted(positions)
    assert "Temporal Legal Context" in text
    assert "karşıt görüş" in text


def test_reasoning_instructions_cover_procedural_and_source_boundaries():
    text = build_reasoning_instructions(["rekabet"], source_context="competition_research")

    assert "zamanaşımı" in text
    assert "hak düşürücü süre" in text
    assert "görev" in text and "yetki" in text
    assert "non-binding" in text
    assert "OECD" in text
    assert "analysis-only" in text


def test_operational_context_labels_crypto_as_hypothesis():
    context = OperationalContextBuilder().build("Kripto cüzdanına yönlendirildim", ["ceza"])

    assert context.domain == "crypto_asset_operations"
    assert "kesin olgu değildir" in context.safety_note


def test_reasoning_requires_summary_and_detailed_findings():
    text = build_reasoning_instructions(["hukuk"])

    assert "Yönetici özeti" in text
    assert "operasyonel bağlam" in text.lower()
    assert "hipotez" in text.lower()


def test_reasoning_playbook_contains_no_private_source_material():
    text = REASONING_PLAYBOOK.render()

    assert "private sample" not in text
    assert "party name" not in text
    assert "TCKN" not in text


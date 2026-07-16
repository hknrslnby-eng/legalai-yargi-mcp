from legalai.packages.layers.strategy_planner import StrategicPathPlanner
from legalai.packages.shared.temporal import TemporalLegalContext


def test_debt_problem_returns_non_litigation_and_litigation_paths() -> None:
    paths = StrategicPathPlanner().plan(
        "Ödenmeyen ticari alacağımı tahsil etmek istiyorum.",
        "alacaklı",
        TemporalLegalContext.from_question("Ödenmeyen ticari alacağımı tahsil etmek istiyorum."),
        [],
    )

    kinds = {path.kind for path in paths}
    assert {"enforcement", "mediation", "settlement_35a", "suit"}.issubset(kinds)
    assert all(path.confidence <= 1 for path in paths)
    assert all(path.assumptions or path.evidence for path in paths)


def test_administrative_problem_suggests_application_before_suit_conditionally() -> None:
    paths = StrategicPathPlanner().plan(
        "İdare işleminin iptali için ne yapabilirim?",
        "başvurucu",
        TemporalLegalContext.from_question("İdare işleminin iptali için ne yapabilirim?"),
        [],
    )

    assert "administrative_application" in {path.kind for path in paths}
    assert any("ret" in step.lower() for path in paths for step in path.steps)


def test_vague_complaint_for_evidence_does_not_create_criminal_route() -> None:
    paths = StrategicPathPlanner().plan(
        "Dava açmadan önce delil toplamak için karşı tarafı şikayet edebilir miyim?",
        "karşı_taraf",
        TemporalLegalContext.from_question("Dava açmadan önce delil toplamak için karşı tarafı şikayet edebilir miyim?"),
        [],
    )

    assert "criminal_complaint" not in {path.kind for path in paths}


def test_concrete_offence_signal_adds_cautious_criminal_route() -> None:
    paths = StrategicPathPlanner().plan(
        "Sahte belge kullanıldığına dair somut deliller var; hangi hukuki yollar mümkün?",
        "mağdur",
        TemporalLegalContext.from_question("Sahte belge kullanıldığına dair somut deliller var; hangi hukuki yollar mümkün?"),
        [],
    )

    criminal = next(path for path in paths if path.kind == "criminal_complaint")
    assert any("somut" in item.lower() or "kötüye" in item.lower() for item in criminal.risks)

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_readme_describes_active_capabilities_and_subskills() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8").lower()

    for marker in (
        "kaynak arama ve çapraz sorgu",
        "ön bilgi",
        "strateji",
        "hukuki mütalaa",
        "dilekçe işlemleri",
        "agresif karşı taraf",
        "derin araştırma",
        "bilirkişi akışı",
        "teknik lens",
        "iktisat ve işletme",
        "kvkk",
        "nis-1",
        "nis-2",
        "siber güvenlik",
        "çok dilli hukuk çıktısı",
        "anti-damping",
        "slash sözlüğü",
    ):
        assert marker in text


def test_readme_explains_setup_and_corpus_limits_without_deep_architecture() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8").lower()

    assert "kaynak kodla kurulum" in text
    assert "python 3.11" in text
    assert "repo kökündeki `.env`" in text
    assert "corpus" in text and "canlı" in text
    assert "upstream" in text and "otomatik" in text
    assert "analysis_only" in text and "non_binding" in text
    assert "said sürücü" in text

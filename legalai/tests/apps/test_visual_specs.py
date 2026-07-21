from legalai.packages.discovery.visuals import visual_spec


def test_strategy_visual_returns_mermaid_and_table_fallback():
    payload = visual_spec("strategy_paths", [{"title": "Arabuluculuk", "benefit": "Hızlı çözüm"}, {"title": "Dava", "benefit": "Bağlayıcı karar"}])
    assert payload["kind"] == "strategy_paths"
    assert payload["mermaid"].startswith("flowchart")
    assert payload["fallback"]["type"] == "table"
    assert payload["fallback"]["rows"]


def test_unknown_visual_kind_is_safe_text_fallback():
    payload = visual_spec("unknown", {"x": 1})
    assert payload["mermaid"] == ""
    assert payload["fallback"]["type"] == "text"
    assert payload["fallback"]["content"]

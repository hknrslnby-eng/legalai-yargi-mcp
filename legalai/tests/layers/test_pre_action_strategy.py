from legalai.packages.layers.pre_action_strategy import PreActionRequest, analyze_pre_action


def test_tebligat_returns_urgent_priorities_questions_and_nonbinding_routes():
    result = analyze_pre_action(PreActionRequest(document_text="TEBLİGAT: 7 gün içinde cevap veriniz. Dava dilekçesi ektedir.", question="Savunma ve çözüm yolları"))
    assert result.trigger_type == "tebligat veya dava dilekçesi"
    assert result.priorities[0]["id"] == "P0"
    assert result.questions and result.requested_documents and result.evidence_preservation
    assert any(item["route"] == "Avukatlık Kanunu 35/A" for item in result.strategy_options)
    assert result.analysis_only and result.non_binding


def test_indictment_and_administrative_notice_have_cross_domain_branches():
    indictment = analyze_pre_action(PreActionRequest(document_text="İDDİANAME: sanık hakkında suç isnadı."))
    administrative = analyze_pre_action(PreActionRequest(document_text="KURUL savunma talebi ve idari başvuru süresi."))
    assert indictment.trigger_type == "iddianame"
    assert administrative.trigger_type in {"yazılı savunma talebi", "idari/kurumsal bildirim"}
    assert all(branch["positive_effects"] and branch["negative_effects"] for branch in indictment.cross_domain_effects)


def test_unknown_trigger_is_cautious_and_full_intake_reduces_missing_facts():
    result = analyze_pre_action(PreActionRequest(document_text="Bir yazı aldım, ne yapmalıyım?", mode="full_intake"))
    assert result.trigger_type == "belirsiz süreç başlatıcı belge"
    assert result.missing_facts == []
    assert result.priorities[0]["id"] == "P1"
    assert all("kesin" not in str(item).casefold() for item in result.strategy_options)

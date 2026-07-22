from legalai.packages.layers.related_law_selection import select_related_law_domains


def test_security_incident_selects_only_factually_linked_supporting_domains():
    result = select_related_law_domains(
        question="Tedarikci veri sizintisi, calisan erisimi ve loglar; zarar iddiasi var.",
        primary_domain="kvkk",
        expert_lenses=["nis_1", "nis_2", "siber_guvenlik"],
    )

    assert {"nis_1", "nis_2", "siber_guvenlik", "sozlesmeler", "is_hukuku", "tazminat"} <= set(result.supporting)
    assert "ceza" not in result.supporting
    assert any("sözleşme" in reason.lower() for reason in result.reasons)


def test_criminal_and_admin_lenses_require_concrete_facts():
    result = select_related_law_domains(
        question="Kisisel veri saklama suresi ve aydinlatma metni",
        primary_domain="kvkk",
    )

    assert {"nis_1", "nis_2", "siber_guvenlik"} <= set(result.supporting)
    assert "idare" not in result.supporting
    assert "ceza" not in result.supporting


def test_unrelated_land_dispute_does_not_inject_kvkk_nis():
    result = select_related_law_domains(
        question="Tapu iptali ve kadastro siniri uyuşmazlığı",
        primary_domain="hukuk",
    )

    assert not ({"kvkk", "nis_1", "nis_2", "siber_guvenlik"} & set(result.supporting))
    assert {"kvkk", "nis_1", "nis_2", "siber_guvenlik"} <= set(result.excluded)

from legalai.packages.jurisdictions.base import JurisdictionProfile


def test_profile_reads_persona_and_lenses():
    profile = JurisdictionProfile.from_dict(
        {
            "id": "hukuk",
            "name": "Hukuk",
            "system_prompt_persona": "Kıdemli hukukçu perspektifi.",
            "response_tone": "resmi",
            "disclaimer_required": True,
            "expert_lenses": ["ticaret", "haksiz_rekabet"],
            "analysis_focus": ["gorev_yetki", "sureler"],
        }
    )

    assert profile.system_prompt_persona.startswith("Kıdemli")
    assert profile.expert_lenses == ["ticaret", "haksiz_rekabet"]
    assert profile.disclaimer_required is True
    assert profile.analysis_focus == ["gorev_yetki", "sureler"]


def test_profile_defaults_keep_legacy_yaml_compatible():
    profile = JurisdictionProfile.from_dict({"id": "legacy", "name": "Legacy"})

    assert profile.system_prompt_persona == ""
    assert profile.response_tone == ""
    assert profile.disclaimer_required is False
    assert profile.expert_lenses == []
    assert profile.analysis_focus == []

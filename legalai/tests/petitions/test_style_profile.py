import pytest

from legalai.packages.petitions.models import PetitionRequest
from legalai.packages.petitions.service import process_petition
from legalai.packages.petitions.style_profile import build_style_profile


def test_style_profile_keeps_structural_signals_but_not_examples_or_pii():
    profile = build_style_profile(
        [
            "SAYIN MAHKEME\nDavacı: Ayşe Yılmaz\nE-posta: ayse@example.com\n"
            "1. OLAYLAR\nYargıtay 3. HD, E.2020/1, K.2021/2 kararında...\nSONUÇ VE İSTEM",
            "AÇIKLAMALAR\nI. HUKUKİ NEDENLER\nDanıştay 5. D., E.2019/3, K.2020/4.\nSONUÇ VE İSTEM",
        ],
        profile_id="office-style",
    )
    payload = profile.to_dict()
    assert payload["profile_id"] == "office-style"
    assert payload["heading_signals"]
    assert payload["citation_signals"]
    assert payload["privacy"]["raw_examples_persisted"] is False
    assert "ayse@example.com" not in str(payload)
    assert "Ayşe Yılmaz" not in str(payload)
    assert "local-derived" in payload["privacy"]["training_boundary"]


def test_style_profile_rejects_empty_examples():
    with pytest.raises(ValueError):
        build_style_profile([])


def test_petition_requires_explicit_consent_before_using_style_profile():
    request = PetitionRequest(
        operation="draft",
        petition_text=None,
        question="Alacak davası dilekçesi",
        style_profile_id="office-style",
        use_style_profile=True,
        style_profile_consent=False,
    )
    with pytest.raises(PermissionError):
        process_petition(request)

    request = PetitionRequest(**{**request.__dict__, "style_profile_consent": True})
    result = process_petition(request)
    assert result.style_profile["profile_id"] == "office-style"
    assert result.style_profile["consent"] is True

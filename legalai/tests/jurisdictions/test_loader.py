import pytest

from legalai.packages.jurisdictions.loader import JurisdictionNotFoundError, load_profile


def test_load_profile_raises_for_unknown_jurisdiction():
    with pytest.raises(JurisdictionNotFoundError):
        load_profile("bilinmeyen_yargi_turu")

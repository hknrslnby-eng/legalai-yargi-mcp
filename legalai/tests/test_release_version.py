import pytest

from scripts.check_release_version import ReleaseVersionError, check_release_version


def test_validator_accepts_matching_tag() -> None:
    check_release_version("v0.2.5", "0.2.5")


def test_validator_rejects_mismatch() -> None:
    with pytest.raises(ReleaseVersionError):
        check_release_version("v0.2.4", "0.2.5")

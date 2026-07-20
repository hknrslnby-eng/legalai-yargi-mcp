"""Version comparison isolated from update transport and filesystem code."""

from packaging.version import InvalidVersion, Version


def compare_versions(left: str, right: str) -> int:
    try:
        left_version, right_version = Version(left), Version(right)
    except InvalidVersion as error:
        raise ValueError(f"Geçersiz sürüm: {error}") from error
    return (left_version > right_version) - (left_version < right_version)

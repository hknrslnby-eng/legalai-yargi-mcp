"""Reject release tags that do not match the application source version."""

from __future__ import annotations

import argparse
import re


class ReleaseVersionError(ValueError):
    """The release tag and source version do not form a valid pair."""


_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def _normalise_source_version(source_version: str) -> str:
    value = source_version.strip()
    if not _VERSION_RE.fullmatch(value):
        raise ReleaseVersionError(f"Geçersiz kaynak sürümü: {source_version!r}")
    return value


def check_release_version(tag: str, source_version: str) -> None:
    """Validate a v-prefixed Git tag against the application version."""

    tag_value = tag.strip()
    if not tag_value.startswith("v"):
        raise ReleaseVersionError("Release tag'i v ile başlamalıdır.")
    tag_version = _normalise_source_version(tag_value[1:])
    source_value = _normalise_source_version(source_version)
    if tag_version != source_value:
        raise ReleaseVersionError(
            f"Release sürümü eşleşmiyor: tag={tag_version}, kaynak={source_value}."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a release tag against the source version.")
    parser.add_argument("tag", help="v-prefixed Git release tag, for example v0.2.5")
    args = parser.parse_args()

    from legalai import __version__

    try:
        check_release_version(args.tag, __version__)
    except ReleaseVersionError as error:
        parser.error(str(error))
    print(f"Release sürümü doğrulandı: {args.tag} / {__version__}")


if __name__ == "__main__":
    main()

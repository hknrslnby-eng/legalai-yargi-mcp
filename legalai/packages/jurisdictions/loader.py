"""Profil loader — YAML dosyasını okur, varsa Python override sınıfıyla
zenginleştirir. Bkz. FORK-KAPSAMLI-PLAN.md §3.3."""
from __future__ import annotations

import importlib
import pathlib

import yaml

from legalai.packages.jurisdictions.base import JurisdictionProfile

CONFIGS_DIR = pathlib.Path(__file__).resolve().parents[2] / "configs" / "jurisdictions"


class JurisdictionNotFoundError(FileNotFoundError):
    """İstenen jurisdiction_id için configs/jurisdictions/ altında YAML bulunamadı."""


def load_profile(jid: str) -> JurisdictionProfile:
    yaml_path = CONFIGS_DIR / f"{jid}.yaml"
    if not yaml_path.exists():
        raise JurisdictionNotFoundError(f"Jurisdiction profile bulunamadı: '{jid}' ({yaml_path})")

    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    base = JurisdictionProfile.from_dict(data)

    try:
        mod = importlib.import_module(f"legalai.packages.jurisdictions.{jid}_override")
    except ModuleNotFoundError:
        return base

    override_cls = next(
        (
            candidate
            for candidate in mod.__dict__.values()
            if isinstance(candidate, type)
            and issubclass(candidate, JurisdictionProfile)
            and candidate is not JurisdictionProfile
        ),
        None,
    )
    return override_cls(base=base) if override_cls else base

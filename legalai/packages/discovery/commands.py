"""Stable, host-neutral command dictionary for SocratLegal users."""
from __future__ import annotations

from typing import Any


def command_dictionary() -> dict[str, Any]:
    commands = {
        "yardim": {
            "tool": "socratlegal_yardim",
            "aliases": ["legalai_yardim"],
            "example_prompt": "SocratLegal yeteneklerini ve her biri için örnek komutları göster.",
        },
        "onbilgi_ve_strateji": {
            "tool": "socratlegal_onbilgi_ve_strateji",
            "aliases": ["legalai_onbilgi_ve_strateji"],
            "example_prompt": "Bu tebligat için önce eksik bilgi-belge-delil listesini çıkar, sonra tüm çözüm yollarını karşılaştır.",
        },
        "dilekce_hazirla": {
            "tool": "socratlegal_dilekce_hazirla",
            "aliases": ["legalai_dilekce_hazirla"],
            "example_prompt": "Davacı pozisyonundan kaynaklı ve duru Türkçeyle dilekçe taslağı hazırla.",
        },
        "dilekce_incele": {
            "tool": "socratlegal_dilekce_incele",
            "aliases": ["legalai_dilekce_incele"],
            "example_prompt": "Bu dilekçeyi dava şartı, görev, yetki, süre, delil ve kaynak bağlantılarıyla incele.",
        },
        "dilekce_kisalt": {
            "tool": "socratlegal_dilekce_kisalt",
            "aliases": ["legalai_dilekce_kisalt"],
            "example_prompt": "Dilekçeyi kısalt; korunması gereken usul başlıklarını silme ve silme önerilerini onayıma sun.",
        },
        "dilekce_uzat": {
            "tool": "socratlegal_dilekce_uzat",
            "aliases": ["legalai_dilekce_uzat"],
            "example_prompt": "Bu dilekçeyi yeni vakıa eklemeden, verilen kaynakların kısa alıntı ve künyeleriyle geliştir.",
        },
        "bilirkisi_raporu_analiz": {
            "tool": "socratlegal_bilirkisi_raporu_analiz",
            "aliases": ["legalai_bilirkisi_raporu_analiz"],
            "example_prompt": "Bilirkişi raporunu teknik alanda derinlemesine sınayarak her bulguya teknik ve hukuki karşı argüman üret.",
        },
        "komut_sozlugu": {
            "tool": "socratlegal_komut_sozlugu",
            "aliases": ["legalai_komut_sozlugu"],
            "example_prompt": "Kullanılabilir SocratLegal komut sözlüğünü göster.",
        },
    }
    return {
        "brand": "SocratLegal",
        "commands": commands,
        "slash_command_note": "Bazı IDE/hostlar '/' komut menüsü gösterebilir; bu görünüm istemciye bağlıdır. Her hostta doğal dil örnekleri ve MCP tool adları kullanılabilir.",
        "analysis_only": True,
        "non_binding": True,
    }

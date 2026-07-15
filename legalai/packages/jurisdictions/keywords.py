"""Çok basit, sözlük tabanlı yargı türü sınıflandırması.

Bu, Hafta 3 iskeletinde `QualifyIssue` katmanının kullandığı geçici bir
heuristic'tir. İleride (Hafta 8+) bir LLM sınıflandırıcı veya embedding
tabanlı arama ile değiştirilmesi planlanıyor — bkz.
FORK-KAPSAMLI-PLAN.md §5.2, §5.3. Yeni bir jurisdiction profili eklerken
buraya da birkaç temsili kelime eklemeyi unutmayın.
"""
from __future__ import annotations

JURISDICTION_KEYWORDS: dict[str, list[str]] = {
    "hukuk": [
        "vekalet", "tazminat", "sözleşme", "miras", "boşanma", "nafaka",
        "kira", "alacak", "haciz", "icra", "velayet", "nişan", "evlilik",
        "mülkiyet", "kat mülkiyeti", "tapu",
    ],
    "ceza": [
        "ceza", "sanık", "suç", "hapis", "beraat", "mahkumiyet", "savcı",
        "iddianame", "tutuklama", "kasten", "taksir", "cinayet", "hırsızlık",
        "dolandırıcılık",
    ],
    "idare": [
        "idari işlem", "idare mahkemesi", "danıştay", "iptal davası",
        "yürütmeyi durdurma", "kamu personeli", "belediye", "imar", "ruhsat",
        "disiplin cezası", "memur",
    ],
}

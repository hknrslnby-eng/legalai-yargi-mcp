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
        "dolandırıcılık", "sahte belge", "sahtecilik",
    ],
    "idare": [
        "idari işlem", "idare mahkemesi", "danıştay", "iptal davası",
        "yürütmeyi durdurma", "kamu personeli", "belediye", "imar", "ruhsat",
        "disiplin cezası", "memur",
    ],
    "vergi": ["vergi", "tarhiyat", "uzlaşma", "VUK", "vergi mahkemesi"],
    "rekabet": ["rekabet kurulu", "hâkim durum", "kartel", "birleşme devralma"],
    "kvkk": ["KVKK", "kişisel veri", "veri sorumlusu", "veri işleyen"],
    "kik": ["kamu ihale", "itirazen şikâyet", "ihale sözleşmesi"],
    "reklam_kurulu": ["reklam kurulu", "ticari reklam", "aldatıcı reklam", "haksız ticari uygulama", "tüketici reklamı"],
    "ticaret_savunmasi": [
        "damping", "dampinge karşı", "anti-dumping", "sübvansiyon",
        "telafi edici vergi", "korunma tedbiri", "ithalatta haksız rekabet",
        "gtip", "ithalat soruşturması", "gözden geçirme soruşturması",
    ],
}

# Data/security incidents may be described without the literal "KVKK".
JURISDICTION_KEYWORDS["kvkk"].extend([
    "veri ihlali", "veri sızıntısı", "siber saldırı", "NIS-1", "NIS-2",
    "yetkisiz erişim", "fidye yazılımı", "kişisel veri güvenliği",
])

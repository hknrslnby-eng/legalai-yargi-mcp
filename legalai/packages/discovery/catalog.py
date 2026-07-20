"""User-facing capability catalog shared by the MCP tool and resource."""
from __future__ import annotations

from typing import Any


def capability_catalog() -> dict[str, Any]:
    return {
        "brand": "SocratLegal",
        "server_name": "SocratLegal MCP Server",
        "legacy_brand": "LegalAI",
        "active_public_tools": {
            "socratlegal_katmanli_analiz": "katmanli_analiz",
            "socratlegal_agresif_karsi_taraf": "agresif_karsi_taraf",
            "socratlegal_derin_arastirma": "derin_arastirma",
            "socratlegal_sozlesme_incele": "sozlesme_incele",
            "socratlegal_guncelleme_kontrol": "guncelleme_kontrol",
            "socratlegal_bilirkisi_raporu_analiz": "bilirkisi_raporu_analiz",
            "socratlegal_bilirkisi_raporu_dilekce": "bilirkisi_raporu_dilekce",
            "socratlegal_corpus_durum": "corpus_durum",
            "socratlegal_corpus_belge_ekle": "corpus_belge_ekle",
            "socratlegal_corpus_sync": "corpus_sync",
        },
        "capabilities": [
            {
                "id": "katmanli_analiz",
                "label": "Katmanlı hukuki analiz",
                "use_when": "Soru-cevap, içtihatlı araştırma, olay/tarih/süre ve görev-yetki değerlendirmesi istendiğinde.",
                "levels": ["yalın soru-cevap", "yönlendirilmiş analiz", "kaynak ve temporal ayrıntılı analiz"],
                "inputs": ["soru", "varsa olay/dava/başvuru tarihleri", "varsa kaynak kapsamı"],
                "output": "Belgeler, künye/kısa alıntı, ratio/dictum, karşı oy, temporal context, süre ve strateji adayları.",
                "example_prompt": "Olay ve dava tarihlerini ayırarak bu uyuşmazlığı içtihatlı ve süre riskleriyle analiz et.",
            },
            {
                "id": "agresif_karsi_taraf",
                "label": "Agresif karşı taraf + geniş çözüm stratejisi",
                "use_when": "Karşı tarafın en güçlü itirazları, karşıt içtihatlar veya dava dışı çözüm yolları istendiğinde.",
                "levels": ["yalın karşı argüman", "5 karşı argüman ve zayıf noktalar", "karşıt içtihat + strateji + forum/süre ayrıntısı"],
                "inputs": ["kullanıcının pozisyonu", "karşı taraf rolü", "varsa tarihler ve belgeler"],
                "output": "Karşı argümanlar, zayıf noktalar, rebutting kararlar, görev/yetki/süre ve geniş çözüm yolları.",
                "example_prompt": "Benim pozisyonumu karşı taraf avukatı gibi test et; 5 güçlü karşı argüman, karşıt içtihat ve dava dışı çözüm seçenekleri üret.",
            },
            {
                "id": "derin_arastirma",
                "label": "Derin araştırma",
                "use_when": "Karmaşık soruyu alt sorulara bölüp birden fazla kaynaklı araştırma akışı gerektiğinde.",
                "levels": ["aday alt sorular", "host-orchestrated araştırma", "API anahtarı varsa server-synthesized araştırma"],
                "inputs": ["ana soru", "derinlik 1-5"],
                "output": "Alt sorular, araştırma sonuçları, kaynak doğrulama talimatı ve sentez için host talimatları.",
                "example_prompt": "Bu karmaşık soruyu en fazla 4 alt soruya böl, her biri için kaynaklı araştırma yap ve çelişkileri göster.",
            },
            {
                "id": "sozlesme_incele",
                "label": "Sözleşme inceleme",
                "use_when": "Bir sözleşmenin hukuki niteliği, madde riskleri, eksikleri, yabancı unsur ve operasyonel etkileri inceleneceğinde.",
                "levels": ["yalın risk taraması", "madde bazlı inceleme", "kaynaklı ve temporal ayrıntılı inceleme"],
                "inputs": ["sözleşme metni veya yerel dosya yolu", "kullanıcının amacı ve pozisyonu", "varsa olay/tarih ve yetki bilgileri"],
                "output": "Hukuki nitelendirme, ilgili persona rotaları, madde/boşluk riskleri, kaynaklı araştırma talimatları ve yabancı dil revizyon biçimi.",
                "example_prompt": "Bu sözleşmeyi kiracı açısından madde madde incele; riskleri, eksikleri, uygulanacak hukuk ve kaynaklı revizyon önerilerini göster.",
            },
            {
                "id": "guncelleme_kontrol",
                "label": "Güncelleme kontrolü",
                "use_when": "SocratLegal'in GitHub Releases üzerinde yeni portable sürümü olup olmadığı kontrol edileceğinde.",
                "levels": ["metadata kontrolü"],
                "inputs": ["isteğe bağlı platform etiketi", "isteğe bağlı mevcut sürüm"],
                "output": "Yeni sürüm, kanal ve açık release bağlantısı; otomatik indirme/kurma yapılmaz.",
                "example_prompt": "SocratLegal için yeni sürüm kontrolü yap; yalnızca metadata göster, indirme veya kurma yapma.",
            },
            {
                "id": "alinti_dogrula",
                "label": "Kaynak/alinti doğrulama",
                "use_when": "Taslak cevapta kullanılan [#belge_id] atıflarının gerçekten mevcut belgelerde bulunup bulunmadığı kontrol edileceğinde.",
                "levels": ["yalın doğrulama"],
                "inputs": ["taslak cevap", "bilinen belge kimlikleri"],
                "output": "Geçerli ve geçersiz atıflar.",
                "example_prompt": "Bu taslağın belge atıflarını kontrol et; geçersiz atıfları ve düzeltilmesi gereken cümleleri göster.",
            },
            {
                "id": "pii_maskele",
                "label": "Yerel PII maskeleme",
                "use_when": "Bir metni dış kaynaklara göndermeden önce yerelde kişisel verileri maskelemek gerektiğinde.",
                "levels": ["yalın maskeleme", "geri açma yetkisi olan yerel oturum"],
                "inputs": ["metin"],
                "output": "Dışarı gönderilmeye uygun maskeli metin; eşleşmeler yerel tenant store'da tutulur.",
                "example_prompt": "Bu metni dış arama/LLM çağrısından önce yerelde maskele ve hangi veri türlerini yakaladığını belirt.",
            },
        ],
        "planned_capabilities": [
            "bilirkişi raporu teknik itiraz analizi ve itiraz dilekçesi (üretim aracı aktif)",
            "dilekçe şablonu ve kaynaklı dilekçe taslağı",
            "due diligence",
        ],
        "natural_language_routing": (
            "Kullanıcı araç adını bilmek zorunda değildir. Host model, kullanıcının doğal dildeki talebini "
            "uygun capability id'sine yönlendirmeli; belirsizse önce bu catalog'u ve eksik olguları açıklamalıdır."
        ),
        "privacy": {
            "outbound_masking": True,
            "policy": "LegalAI'nin başlattığı dış arama ve server-side LLM çağrılarında yerel PII maskesi zorunludur.",
            "host_boundary_note": "Host modelin ilk kullanıcı mesajını almadan önce MCP'nin müdahale edebilmesi istemciye bağlıdır; privacy-first istemci talimatı önerilir.",
        },
        "analysis_only": True,
        "non_binding": True,
        "disclaimer": "Tüm çıktılar analysis-only, non-binding araştırma yardımıdır; kesin hukuki görüş veya garanti değildir.",
    }

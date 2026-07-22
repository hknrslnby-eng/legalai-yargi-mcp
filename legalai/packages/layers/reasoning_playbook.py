"""Privacy-safe, abstract reasoning policy for SocratLegal outputs."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReasoningPlaybook:
    """A reusable method description with no private source material."""

    stages: tuple[str, ...] = (
        "Soruyu, kapsamı, talebi, olayları, tarihleri ve belirsizlikleri ayır.",
        "Kronolojiyi, maddi vakıaları ve delilleri birbirinden ayır; her iddianın dayanağını etiketle.",
        "Normu, unsurları, usulü, temporal context'i ve kaynak hiyerarşisini belirle.",
        "Somut olayları hukuki unsurlarla ve yalnızca ilgili operasyonel bağlam hipotezleriyle eşleştir.",
        "Lehe ve aleyhe görüşleri, karşı argümanları, alternatif sonuçları ve doğrulama ihtiyacını test et.",
        "Erişilen kaynaklarla künye/atıf bağlantısı kur; önce yönetici özeti, sonra ayrıntılı kaynaklı sentez ver.",
    )

    def render(self) -> str:
        return "\n".join(
            [
                "Gizlilik uyumlu muhakeme politikası:",
                *[f"{index}. {stage}" for index, stage in enumerate(self.stages, 1)],
                "Rekabet baglaminda hukuki incelemeyi pazar, pay-hacim-ciro, rakip/tedarikci/musteri, zincir, giris engeli, fiyatlama, duzenleme ve sektor raporu verileriyle birlikte test et; bilinmeyenleri veri talebi olarak goster.",
                "Operasyonel bağlamı kesin olgu değil, açıkça etiketlenmiş hipotez veya doğrulama ihtiyacı olarak sun.",
                "Erişilmeyen mevzuat, içtihat, doktrin veya alıntı için künye uydurma.",
            ]
        )


REASONING_PLAYBOOK = ReasoningPlaybook()

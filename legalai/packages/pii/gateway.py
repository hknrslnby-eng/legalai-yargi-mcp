"""PiiGateway — geri döndürülebilir (reversible) PII maskeleme.

Bkz. FORK-KAPSAMLI-PLAN.md Hafta 6 kabul kriteri:
    pii.mask("Ahmet Yılmaz TCKN 12345678901") -> "... [TCKN_1]"
    pii.unmask(...) -> orijinali geri verir

AŞAMA 1 (bu commit, "regex_first" kararı — 15 Temmuz 2026): sadece
örüntüyle yakalanan tanımlayıcılar (TCKN, telefon, e-posta, IBAN, plaka)
maskelenir. İsim/kurum (PERSON/ORG) maskeleme, `HUGGINGFACE_TOKEN` alınıp
NER modeli entegre edildiğinde AŞAMA 2 olarak eklenecek — bu dosyadaki
`merger.merge_matches()` çağrısına NER sonuçları eklenerek genişletilir,
mevcut arayüz (`mask`/`unmask`) DEĞİŞMEZ.

Her maskelenen değer, `current_tenant()` altında ayrı bir DEK ile
şifrelenip SQLite'a yazılır (bkz. crypto.py, store.py). Aynı tenant için
aynı orijinal değer tekrar maskelenirse AYNI token kullanılır (tutarlılık
için basit bir süreç-içi önbellek).
"""
from __future__ import annotations

import pathlib

from legalai.packages.pii import crypto
from legalai.packages.pii.merger import merge_matches
from legalai.packages.pii.patterns import find_all
from legalai.packages.shared.settings import settings
from legalai.packages.shared.tenant import current_tenant

# tenant_id -> {orijinal_değer: token} — aynı değeri hep aynı token'a eşler
_consistency_cache: dict[str, dict[str, str]] = {}


class PiiGateway:
    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        self._db_path = pathlib.Path(db_path or settings.pii_map_db_path)

    async def mask(self, text: str) -> str:
        matches = merge_matches(find_all(text))
        if not matches:
            return text

        tenant_id = current_tenant().tenant_id
        cache = _consistency_cache.setdefault(tenant_id, {})
        counters: dict[str, int] = {}

        result_parts: list[str] = []
        cursor = 0
        for m in matches:
            result_parts.append(text[cursor:m.start])

            if m.text in cache:
                placeholder = cache[m.text]
            else:
                counters[m.label] = counters.get(m.label, 0) + 1
                token_id = f"{m.label}_{counters[m.label]}"
                placeholder = f"[{token_id}]"
                cache[m.text] = placeholder
                await self._persist(tenant_id, token_id, m.text)

            result_parts.append(placeholder)
            cursor = m.end
        result_parts.append(text[cursor:])
        return "".join(result_parts)

    async def unmask(self, text: str) -> str:
        tenant_id = current_tenant().tenant_id
        cache = _consistency_cache.get(tenant_id, {})
        reverse = {token: original for original, token in cache.items()}

        import re

        def _replace(match: "re.Match[str]") -> str:
            token = match.group(0)
            if token in reverse:
                return reverse[token]
            # Süreç-içi önbellekte yoksa (örn. farklı süreç) SQLite'a düş
            return token

        return re.sub(r"\[[A-ZÇĞİÖŞÜ]+_\d+\]", _replace, text)

    async def _persist(self, tenant_id: str, token_id: str, original_value: str) -> None:
        dek = crypto.generate_dek()
        encrypted_value = crypto.encrypt_value(original_value, dek)
        wrapped_dek = crypto.wrap_dek(dek)
        from legalai.packages.pii.store import put_token

        await put_token(tenant_id, token_id, encrypted_value, wrapped_dek, self._db_path)

    async def unmask_from_store(self, text: str) -> str:
        """`unmask()`'in süreç-içi önbelleğe değil, doğrudan SQLite'a
        bakan sürümü — farklı bir süreçte/oturumda çağrılırsa kullanılır."""
        import re

        from legalai.packages.pii.store import get_token

        tenant_id = current_tenant().tenant_id
        tokens = set(re.findall(r"\[[A-ZÇĞİÖŞÜ]+_\d+\]", text))
        replacements: dict[str, str] = {}
        for token in tokens:
            row = await get_token(tenant_id, token.strip("[]"), self._db_path)
            if row is None:
                continue
            encrypted_value, wrapped_dek = row
            dek = crypto.unwrap_dek(wrapped_dek)
            replacements[token] = crypto.decrypt_value(encrypted_value, dek)

        for token, original in replacements.items():
            text = text.replace(token, original)
        return text

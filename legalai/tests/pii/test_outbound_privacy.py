import pytest

from legalai.packages.pii.outbound import mask_for_external
from legalai.packages.shared.tenant import TenantContext, tenant_scope


@pytest.mark.asyncio
async def test_external_text_never_contains_structured_tckn(tmp_path) -> None:
    from legalai.packages.pii.gateway import PiiGateway

    with tenant_scope(TenantContext("privacy-test", "Privacy Test")):
        masked = await mask_for_external(
            "Davacı TCKN 10000000146 için alacak araştırması.",
            gateway=PiiGateway(tmp_path / "pii_map.db"),
        )

    assert "10000000146" not in masked
    assert "[TCKN_1]" in masked


@pytest.mark.asyncio
async def test_external_mask_preserves_non_personal_legal_query(tmp_path) -> None:
    from legalai.packages.pii.gateway import PiiGateway

    with tenant_scope(TenantContext("privacy-test", "Privacy Test")):
        masked = await mask_for_external(
            "Zamanaşımı ve görevli mahkeme değerlendirmesi",
            gateway=PiiGateway(tmp_path / "pii_map.db"),
        )

    assert masked == "Zamanaşımı ve görevli mahkeme değerlendirmesi"


@pytest.mark.asyncio
async def test_external_text_masks_contextual_person_address_and_birth_date(tmp_path) -> None:
    from legalai.packages.pii.gateway import PiiGateway

    text = "Ad Soyad: Ahmet Yılmaz; Adres: İstanbul Kadıköy; Doğum tarihi: 01.02.1980"
    with tenant_scope(TenantContext("privacy-test-context", "Privacy Test")):
        masked = await mask_for_external(text, gateway=PiiGateway(tmp_path / "pii_map.db"))

    assert "Ahmet Yılmaz" not in masked
    assert "İstanbul Kadıköy" not in masked
    assert "01.02.1980" not in masked
    assert "[KISI_1]" in masked
    assert "[ADRES_1]" in masked
    assert "[DOGUM_TARIHI_1]" in masked


@pytest.mark.asyncio
async def test_external_text_masks_probable_two_word_person_name(tmp_path) -> None:
    from legalai.packages.pii.gateway import PiiGateway

    with tenant_scope(TenantContext("privacy-test-name", "Privacy Test")):
        masked = await mask_for_external(
            "Ahmet Yılmaz hakkında sözleşme uyuşmazlığı.",
            gateway=PiiGateway(tmp_path / "pii_map.db"),
        )

    assert "Ahmet Yılmaz" not in masked

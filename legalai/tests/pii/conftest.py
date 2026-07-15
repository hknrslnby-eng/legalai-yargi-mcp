import pytest

from legalai.packages.shared.tenant import TenantContext, set_tenant


@pytest.fixture(autouse=True)
def _tenant_context():
    set_tenant(TenantContext(tenant_id="test", tenant_name="Test Tenant"))
    yield
    # Testler arasında tutarlılık önbelleğinin sızmaması için temizle
    from legalai.packages.pii.gateway import _consistency_cache

    _consistency_cache.clear()

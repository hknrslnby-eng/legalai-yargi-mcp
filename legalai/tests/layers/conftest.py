import pytest

from legalai.packages.shared.tenant import TenantContext, set_tenant


@pytest.fixture(autouse=True)
def _tenant_context():
    set_tenant(TenantContext(tenant_id="test", tenant_name="Test Tenant"))
    yield

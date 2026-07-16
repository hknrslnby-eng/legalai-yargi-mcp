"""LegalAI FastAPI uygulaması — `POST /api/v1/analyze` gibi iç HTTP
endpoint'lerini sunar. Bkz. FORK-KAPSAMLI-PLAN.md §2.6.

Süreç başlarken tenant bağlamı kurulur (bugün her zaman "local"; sunucuya
taşındığında bu satır bir middleware'e taşınır — bkz. §7 tablosu).
"""
from __future__ import annotations

from fastapi import FastAPI

from legalai.apps.api.routes import router
from legalai.packages.shared.settings import settings
from legalai.packages.shared.tenant import TenantContext, set_tenant

set_tenant(TenantContext(tenant_id=settings.tenant_id, tenant_name=settings.tenant_name))

app = FastAPI(title="LegalAI API", version="0.1.0")
app.include_router(router)

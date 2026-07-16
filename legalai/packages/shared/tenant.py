"""TenantContext — her yerde birinci sınıf vatandaş.
Bkz. FORK-KAPSAMLI-PLAN.md §2.2."""
from __future__ import annotations

from contextvars import ContextVar
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    tenant_name: str
    tier: str = "free"
    features: frozenset[str] = field(default_factory=frozenset)


_current: ContextVar[TenantContext | None] = ContextVar("tenant", default=None)


def current_tenant() -> TenantContext:
    tenant = _current.get()
    if tenant is None:
        raise RuntimeError("TenantContext set edilmemiş — set_tenant() çağırın")
    return tenant


def set_tenant(ctx: TenantContext) -> None:
    _current.set(ctx)


@contextmanager
def tenant_scope(ctx: TenantContext) -> Iterator[None]:
    """Temporarily bind a tenant and restore the parent async context."""
    token = _current.set(ctx)
    try:
        yield
    finally:
        _current.reset(token)

"""Non-destructive MCP configuration merging for supported clients."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .models import InstallResult, McpLaunchSpec


class ConfigMergeError(ValueError):
    """The target configuration is invalid or has an unsupported shape."""


def _server_payload(spec: McpLaunchSpec) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "command": spec.command,
        "args": list(spec.args),
        "cwd": spec.cwd,
    }
    if spec.env:
        payload["env"] = dict(spec.env)
    return payload


def _backup_before_write(path: Path, backup_dir: Path | None) -> Path:
    target_dir = backup_dir or path.parent / ".socratlegal-backups"
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = target_dir / f"{path.name}.{stamp}.bak"
    backup_path.write_bytes(path.read_bytes())
    return backup_path


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _decode_json(path: Path, repair: bool) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {}, ""
    original = path.read_text(encoding="utf-8")
    try:
        value = json.loads(original)
    except json.JSONDecodeError as error:
        if not repair:
            raise ConfigMergeError(
                f"{path} geçerli tek bir JSON nesnesi değil; dosya değiştirilmedi. "
                "Ekrandaki iki bitişik JSON nesnesi için repair=True kullanın."
            ) from error
        decoder = json.JSONDecoder()
        try:
            first, offset = decoder.raw_decode(original.lstrip())
            remainder = original.lstrip()[offset:].strip()
            second, trailing = decoder.raw_decode(remainder)
            if trailing != len(remainder):
                raise ValueError("birden fazla onarım nesnesi")
        except (json.JSONDecodeError, ValueError) as repair_error:
            raise ConfigMergeError(f"{path} JSON onarımı başarısız; dosya değiştirilmedi.") from repair_error
        if not isinstance(first, dict) or not isinstance(second, dict):
            raise ConfigMergeError("JSON onarımı yalnızca iki kök nesneyi destekler.")
        merged = dict(first)
        for key, value in second.items():
            if key == "mcpServers" and isinstance(merged.get(key), dict) and isinstance(value, dict):
                merged[key] = {**merged[key], **value}
            elif key not in merged:
                merged[key] = value
            elif merged[key] != value:
                raise ConfigMergeError(f"JSON onarımında çakışan kök alan: {key}")
        return merged, original
    if not isinstance(value, dict):
        raise ConfigMergeError("MCP JSON kökü nesne olmalıdır; dosya değiştirilmedi.")
    return value, original


def _merge_json_document(
    path: Path,
    spec: McpLaunchSpec,
    *,
    container_key: str,
    server_key: str,
    repair: bool,
    backup_dir: Path | None,
    transform: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]] | None = None,
) -> InstallResult:
    document, original = _decode_json(path, repair)
    container = document.get(container_key)
    if container is None:
        container = {}
        document[container_key] = container
    if not isinstance(container, dict):
        raise ConfigMergeError(f"{container_key} alanı nesne olmalıdır; dosya değiştirilmedi.")
    payload = _server_payload(spec)
    if transform:
        payload = transform(payload, spec.__dict__)
    if container.get(server_key) == payload and not repair:
        return InstallResult(server_key, path, "unchanged", None, "SocratLegal zaten kayıtlı; değişiklik yapılmadı.")
    container[server_key] = payload
    content = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    backup = _backup_before_write(path, backup_dir) if path.exists() else None
    _atomic_write(path, content)
    return InstallResult(server_key, path, "installed", backup, "SocratLegal yapılandırmaya eklendi.")


def merge_json_config(
    path: Path,
    spec: McpLaunchSpec,
    *,
    backup_dir: Path | None = None,
    repair: bool = False,
) -> InstallResult:
    return _merge_json_document(
        Path(path), spec, container_key="mcpServers", server_key=spec.name,
        repair=repair, backup_dir=backup_dir,
    )


def merge_vscode_json_config(
    path: Path,
    spec: McpLaunchSpec,
    *,
    backup_dir: Path | None = None,
    repair: bool = False,
) -> InstallResult:
    def transform(payload: dict[str, Any], _: dict[str, Any]) -> dict[str, Any]:
        return {"type": "stdio", **payload}

    return _merge_json_document(
        Path(path), spec, container_key="servers", server_key=spec.name,
        repair=repair, backup_dir=backup_dir, transform=transform,
    )


def merge_codex_toml_config(
    path: Path,
    spec: McpLaunchSpec,
    *,
    backup_dir: Path | None = None,
) -> InstallResult:
    try:
        from tomlkit import array, document, dumps, load, table
    except ImportError as error:
        raise ConfigMergeError("Codex TOML kurulumu için tomlkit bağımlılığı gereklidir.") from error

    target = Path(path)
    if target.exists():
        with target.open("rb") as handle:
            parsed = load(handle)
    else:
        parsed = document()
    servers = parsed.get("mcp_servers")
    if servers is None:
        servers = table()
        parsed["mcp_servers"] = servers
    if not hasattr(servers, "get"):
        raise ConfigMergeError("mcp_servers TOML tablosu olmalıdır; dosya değiştirilmedi.")

    desired: dict[str, Any] = {"command": spec.command, "args": array(list(spec.args)), "cwd": spec.cwd}
    if spec.env:
        desired["env"] = dict(spec.env)
    existing = servers.get(spec.name)
    if existing is not None and dict(existing) == desired:
        return InstallResult(spec.name, target, "unchanged", None, "SocratLegal zaten Codex yapılandırmasında kayıtlı.")

    server_table = table()
    for key, value in desired.items():
        server_table[key] = value
    servers[spec.name] = server_table
    original_exists = target.exists()
    backup = _backup_before_write(target, backup_dir) if original_exists else None
    _atomic_write(target, dumps(parsed))
    return InstallResult(spec.name, target, "installed", backup, "SocratLegal Codex yapılandırmasına eklendi.")

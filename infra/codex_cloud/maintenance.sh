#!/usr/bin/env bash
# Maintenance script for Codex Cloud manual environments.
# Meant to be run on demand (e.g., via scheduled job or manual invocation).

set -euo pipefail

log() {
    printf '[maintenance] %s\n' "$*" >&2
}

require_uv() {
    if ! command -v uv >/dev/null 2>&1; then
        log "uv not detected; run setup.sh first."
        exit 1
    fi
}

refresh_background_job() {
    log "refreshing cached mcp-background-job package"
    uv cache prune --packages mcp-background-job || log "cache prune returned non-zero; continuing"
    uvx --with mcp-background-job python - <<'PY'
import importlib
module = importlib.import_module("mcp_background_job")
version = getattr(module, "__version__", "unknown")
print(f"mcp-background-job refreshed (version: {version})")
PY
}

health_check() {
    log "running smoke test for background job server"
    timeout 5s uvx mcp-background-job --help >/dev/null 2>&1 || {
        log "warning: unable to start mcp-background-job help output"
    }
}

check_codex_config() {
    local config_file="${HOME}/.codex/config.toml"
    if [[ ! -f "${config_file}" ]] || ! grep -q '^\[mcp_servers\.background_job\]' "${config_file}" >/dev/null 2>&1; then
        log "warning: background_job entry missing from ${config_file}; rerun setup.sh"
    fi
}

main() {
    require_uv
    refresh_background_job
    health_check
    check_codex_config
    log "maintenance complete"
}

main "$@"

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

find_codex_cli() {
    if [[ -n "${CODEX_BIN:-}" ]]; then
        if command -v "${CODEX_BIN}" >/dev/null 2>&1; then
            CODEX_BIN="$(command -v "${CODEX_BIN}")"
            return
        elif [[ -x "${CODEX_BIN}" ]]; then
            return
        fi
        log "specified CODEX_BIN '${CODEX_BIN}' is not executable"
        exit 1
    fi

    if command -v codex >/dev/null 2>&1; then
        CODEX_BIN="$(command -v codex)"
        return
    fi

    log "codex CLI not found on PATH; skipping registration check"
    CODEX_BIN=""
}

verify_registration() {
    [[ -z "${CODEX_BIN}" ]] && return
    if ! "${CODEX_BIN}" mcp get background_job >/dev/null 2>&1; then
        log "warning: background_job MCP server not registered; rerun setup.sh"
    fi
}

main() {
    require_uv
    refresh_background_job
    health_check
    find_codex_cli
    verify_registration
    log "maintenance complete"
}

main "$@"

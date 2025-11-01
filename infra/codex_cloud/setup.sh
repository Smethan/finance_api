#!/usr/bin/env bash
# Codex Cloud environment bootstrap script.
# According to the Codex Cloud environment setup guide, this script must be
# idempotent, non-interactive, and log progress to stdout/stderr.

set -euo pipefail

log() {
    printf '[setup] %s\n' "$*" >&2
}

ensure_paths() {
    mkdir -p "${HOME}/.local/bin"
    mkdir -p "${HOME}/.cache/codex"
}

ensure_local_bin_on_path() {
    case ":${PATH}:" in
        *":${HOME}/.local/bin:"*) ;;
        *) export PATH="${HOME}/.local/bin:${PATH}" ;;
    esac

    local profile="${HOME}/.profile"
    local export_line='export PATH="$HOME/.local/bin:$PATH"'

    if [[ -f "${profile}" ]]; then
        if ! grep -F "${export_line}" "${profile}" >/dev/null 2>&1; then
            printf '\n%s\n' "${export_line}" >> "${profile}"
        fi
    else
        printf '%s\n' "${export_line}" > "${profile}"
    fi
}

install_uv() {
    ensure_system_packages

    if command -v uv >/dev/null 2>&1; then
        log "uv already available at $(command -v uv)"
        return
    fi

    log "installing uv (docs specify manual environments must ship dependencies explicitly)"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="${HOME}/.local/bin:${PATH}"
    log "uv installed to ${HOME}/.local/bin"
}

prefetch_background_job() {
    log "prefetching mcp-background-job via uvx"
    uvx --with mcp-background-job python - <<'PY'
import importlib
module = importlib.import_module("mcp_background_job")
version = getattr(module, "__version__", "unknown")
print(f"mcp-background-job ready (version: {version})")
PY
}

find_codex_cli() {
    if [[ -n "${CODEX_BIN:-}" ]]; then
        if command -v "${CODEX_BIN}" >/dev/null 2>&1; then
            CODEX_BIN="$(command -v "${CODEX_BIN}")"
            log "using codex CLI from ${CODEX_BIN}"
            return
        elif [[ -x "${CODEX_BIN}" ]]; then
            log "using codex CLI from ${CODEX_BIN}"
            return
        fi
        log "specified CODEX_BIN '${CODEX_BIN}' is not executable"
        exit 1
    fi

    if command -v codex >/dev/null 2>&1; then
        CODEX_BIN="$(command -v codex)"
        log "codex CLI detected at ${CODEX_BIN}"
        return
    fi

    log "codex CLI not found on PATH. Install Codex CLI or set CODEX_BIN before running setup."
    exit 1
}

register_background_job_server() {
    local server_name="background_job"

    if "${CODEX_BIN}" mcp get "${server_name}" >/dev/null 2>&1; then
        log "existing MCP server '${server_name}' found; refreshing configuration"
        "${CODEX_BIN}" mcp remove "${server_name}"
    fi

    "${CODEX_BIN}" mcp add "${server_name}" uvx mcp-background-job
    log "registered '${server_name}' MCP server (command=uvx, args=[mcp-background-job])"
}

ensure_system_packages() {
    # The codex-universal base image (https://github.com/openai/codex-universal)
    # preinstalls many developer dependencies, but we ensure the essentials
    # needed for uv/uvx and the MCP server are present.
    local required_packages=(curl git jq build-essential pkg-config libssl-dev libffi-dev python3 python3-venv)

    if ! command -v apt-get >/dev/null 2>&1; then
        log "apt-get not available; skipping system package check"
        return
    fi

    local apt_cmd=(apt-get)
    if [[ "${EUID}" -ne 0 ]]; then
        if command -v sudo >/dev/null 2>&1; then
            apt_cmd=(sudo apt-get)
        else
            log "skipping system package installation (requires root privileges)"
            return
        fi
    fi

    log "installing required system packages: ${required_packages[*]}"
    "${apt_cmd[@]}" update
    "${apt_cmd[@]}" install -y --no-install-recommends "${required_packages[@]}"
    "${apt_cmd[@]}" clean
}

main() {
    log "starting Codex Cloud setup"
    ensure_paths
    ensure_local_bin_on_path
    install_uv
    prefetch_background_job
    find_codex_cli
    register_background_job_server
    log "setup complete"
}

main "$@"

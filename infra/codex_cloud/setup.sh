#!/usr/bin/env bash
# Codex Cloud environment bootstrap script.
# According to the Codex Cloud environment setup guide, this script must be
# idempotent, non-interactive, and log progress to stdout/stderr.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

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

ensure_codex_config() {
    local config_dir="${HOME}/.codex"
    local config_file="${config_dir}/config.toml"
    local server_block=$'[mcp_servers.background_job]\ncommand = "uvx"\nargs = ["mcp-background-job"]\ntransport = "stdio"\n'

    mkdir -p "${config_dir}"

    if [[ -f "${config_file}" ]] && grep -q '^\[mcp_servers\.background_job\]' "${config_file}"; then
        log "codex config already defines mcp_servers.background_job; skipping update"
        return
    fi

    if [[ -f "${config_file}" && -s "${config_file}" ]]; then
        printf '\n%s\n' "${server_block}" >> "${config_file}"
    else
        printf '%s\n' "${server_block}" > "${config_file}"
    fi

    log "appended mcp_servers.background_job entry to ${config_file}"
}

install_project_dependencies() {
    if [[ ! -f "${REPO_ROOT}/pyproject.toml" ]]; then
        log "pyproject.toml not found at ${REPO_ROOT}; skipping project dependency install"
        return
    fi

    log "installing Python project dependencies via uv (pyproject.toml)"
    UV_LINK_MODE=copy uv pip install --system "${REPO_ROOT}"
    log "project dependencies installed"
}

main() {
    log "starting Codex Cloud setup"
    ensure_paths
    ensure_local_bin_on_path
    install_uv
    prefetch_background_job
    ensure_codex_config
    install_project_dependencies
    log "setup complete"
}

main "$@"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_DIR="${REPO_ROOT}/infra/codex-cloud"
CONFIG_TEMPLATE="${CONFIG_DIR}/mcp-background-job.toml"

usage() {
    cat <<'EOF'
Usage: manage_codex_cloud.sh <command>

Commands:
  setup       Ensure uv is available, prefetch mcp-background-job via uvx, and write the Codex Cloud config template.
  refresh     Drop any cached build and re-prefetch the latest mcp-background-job package.
  status      Display versions for uv and mcp-background-job and point to the config template.
EOF
}

require_uv() {
    if ! command -v uv >/dev/null 2>&1; then
        cat <<'EOF' >&2
error: uv is not installed or not on PATH.
Install it from https://docs.astral.sh/uv/getting-started/installation/ and re-run this script.
EOF
        exit 1
    fi
}

prefetch_package() {
    require_uv
    uvx --with mcp-background-job python - <<'PY'
import importlib
mod = importlib.import_module("mcp_background_job")
print(f"mcp-background-job cached (version: {getattr(mod, '__version__', 'unknown')})")
PY
}

write_config_template() {
    mkdir -p "${CONFIG_DIR}"
    cat <<'EOF' > "${CONFIG_TEMPLATE}"
# Codex Cloud MCP server template for mcp-background-job.
# Copy this into the Codex Cloud MCP settings UI or merge it into an existing config.
[mcp_servers.background_job]
command = "uvx"
args = ["mcp-background-job"]
transport = "stdio"

# Optional environment overrides:
# env = {
#   MCP_BG_MAX_JOBS = "10",
#   MCP_BG_MAX_OUTPUT_SIZE = "20MB",
#   MCP_BG_WORKING_DIR = "/workspace"
# }
EOF
    echo "Wrote template ${CONFIG_TEMPLATE}"
}

setup() {
    prefetch_package
    write_config_template
    cat <<EOF

Next steps:
  1. Upload the template at ${CONFIG_TEMPLATE} to Codex Cloud (Settings → MCP Servers).
  2. In Codex Cloud, add a new server named "background_job" using those fields.
  3. When Codex spins up the server it will execute "uvx mcp-background-job" with stdio transport.
EOF
}

refresh() {
    require_uv
    uv cache prune --packages mcp-background-job >/dev/null 2>&1 || true
    prefetch_package
}

status() {
    require_uv
    uv --version
    uvx --with mcp-background-job python - <<'PY'
import importlib
mod = importlib.import_module("mcp_background_job")
print(f"mcp-background-job version: {getattr(mod, '__version__', 'unknown')}")
PY
    if [[ -f "${CONFIG_TEMPLATE}" ]]; then
        echo "Template available at ${CONFIG_TEMPLATE}"
    else
        echo "Template not found; run setup."
    fi
}

main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi

    case "$1" in
        setup)
            setup
            ;;
        refresh)
            refresh
            ;;
        status)
            status
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "error: unknown command '$1'" >&2
            usage
            exit 1
            ;;
    esac
}

main "$@"

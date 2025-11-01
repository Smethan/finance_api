# Codex Cloud Environment Setup

These scripts follow the manual environment guidance from the Codex Cloud environment setup documentation:

- **Setup scripts must be idempotent and non-interactive.**
- **All dependencies must be installed explicitly each time the environment spins up.**
- **State lives under `$HOME`; artifacts should not be written outside the workspace.**
- **Log actionable progress to stdout/stderr so Cloud run logs stay readable.**

## Files

- `setup.sh` – bootstraps the Codex Cloud workspace. It ensures the base system packages from the [codex-universal image](https://github.com/openai/codex-universal) that `uvx`/Python depend on are present (`curl`, `git`, `jq`, build tooling, etc.), installs `uv` when missing, prefetches the `mcp-background-job` package via `uvx`, and uses `codex mcp add background_job uvx mcp-background-job` to ensure the global Codex configuration includes the stdio server.
- `maintenance.sh` – refreshes the cached package, runs a `uvx mcp-background-job --help` smoke test, and warns if the MCP entry disappears.

## Usage

1. Upload `infra/codex_cloud/setup.sh` to Codex Cloud as your manual setup script. The platform runs it at the start of each session.
2. Optionally register `infra/codex_cloud/maintenance.sh` as a periodic maintenance script to keep the cached wheel fresh.

The scripts emit `mcp-background-job` version information so you can confirm the server binary Codex Cloud will launch. If `codex` is not on `PATH` in your environment, set `CODEX_BIN=/path/to/codex` before invoking either script.

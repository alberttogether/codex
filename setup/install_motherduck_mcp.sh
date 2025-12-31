#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="${HOME}/.codex"
CONFIG_FILE="${CONFIG_DIR}/config.toml"
SERVER_NAME="motherduck"

mkdir -p "${CONFIG_DIR}"

# Create file if it doesn't exist
if [[ ! -f "${CONFIG_FILE}" ]]; then
  cat > "${CONFIG_FILE}" <<'EOF'
# Project-local Codex configuration
EOF
fi

python3 <<'PY'
from pathlib import Path
import re

path = Path(".codex/config.toml")
text = path.read_text(encoding="utf-8")

# Ensure [features] rmcp_client = true
if re.search(r'(?m)^\[features\]', text):
    if not re.search(r'(?m)^\[features\][\s\S]*?^rmcp_client\s*=\s*true', text):
        text = re.sub(
            r'(?m)^\[features\][\s\S]*?(?=^\[|\Z)',
            lambda m: m.group(0).rstrip() + "\nrmcp_client = true\n",
            text
        )
else:
    text += "\n[features]\nrmcp_client = true\n"

# Remove any existing motherduck MCP block
text = re.sub(
    r'(?ms)^\[mcp_servers\.motherduck\]\n.*?(?=^\[|\Z)',
    "",
    text
).rstrip() + "\n"

# Append fresh MotherDuck HTTP MCP config
text += """
[mcp_servers.motherduck]
url = "https://api.motherduck.com/mcp"
bearer_token_env_var = "MOTHERDUCK_TOKEN"
"""

path.write_text(text, encoding="utf-8")
PY

echo "✅ MotherDuck HTTP MCP server configured in ${CONFIG_FILE}"
echo
echo "Next:"
echo "  export MOTHERDUCK_TOKEN=md_..."
echo "  codex   # run from this directory"



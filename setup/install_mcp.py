#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Iterable

import tomllib


MOTHERDUCK_CONFIG = {
    "url": "https://api.motherduck.com/mcp",
    "bearer_token_env_var": "MOTHERDUCK_TOKEN",
}
LINEAR_CONFIG = {
    "url": "https://mcp.linear.app/mcp",
    "bearer_token_env_var": "LINEAR_TOKEN",
}
NOTION_CONFIG = {
    "url": "https://mcp.notion.com/mcp",
    "bearer_token_env_var": "NOTION_TOKEN",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Motherduck and Linear MCP server config into ~/.codex/config.toml",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path.home() / ".codex" / "config.toml",
        help="Path to config.toml (default: ~/.codex/config.toml).",
    )
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config.toml root must be a table")
    return data


def is_bare_key(key: str) -> bool:
    return key.replace("_", "").replace("-", "").isalnum()


def quote_key(key: str) -> str:
    if is_bare_key(key):
        return key
    escaped = key.replace("\\", "\\\\").replace('"', '\\"')
    return f"\"{escaped}\""


def format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f"\"{escaped}\""
    if isinstance(value, list):
        inner = ", ".join(format_value(item) for item in value)
        return f"[{inner}]"
    raise TypeError(f"Unsupported TOML value type: {type(value).__name__}")


def write_table(
    lines: list[str],
    path: tuple[str, ...],
    table: dict[str, Any],
    is_root: bool,
) -> None:
    scalar_items: list[tuple[str, Any]] = []
    child_tables: list[tuple[str, dict[str, Any]]] = []
    for key, value in table.items():
        if isinstance(value, dict):
            child_tables.append((key, value))
        else:
            scalar_items.append((key, value))

    if not is_root and scalar_items:
        if lines and lines[-1] != "":
            lines.append("")
        header = ".".join(quote_key(segment) for segment in path)
        lines.append(f"[{header}]")
        for key, value in scalar_items:
            lines.append(f"{quote_key(key)} = {format_value(value)}")
    elif is_root and scalar_items:
        for key, value in scalar_items:
            lines.append(f"{quote_key(key)} = {format_value(value)}")

    for key, child in child_tables:
        write_table(lines, path + (key,), child, False)


def dump_config(config: dict[str, Any]) -> str:
    lines: list[str] = []
    write_table(lines, (), config, True)
    return "\n".join(lines).rstrip() + "\n"


def ensure_tables(config: dict[str, Any], *path: str) -> dict[str, Any]:
    current = config
    for key in path:
        value = current.get(key)
        if value is None:
            current[key] = {}
            value = current[key]
        if not isinstance(value, dict):
            raise ValueError(f"Expected table at {'.'.join(path)}")
        current = value
    return current


def main() -> int:
    args = parse_args()
    config_path = args.config
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config = load_config(config_path)
    features = ensure_tables(config, "features")
    features["rmcp_client"] = True

    mcp_servers = ensure_tables(config, "mcp_servers")
    mcp_servers["motherduck"] = MOTHERDUCK_CONFIG
    mcp_servers["linear"] = LINEAR_CONFIG
    mcp_servers["notion"] = NOTION_CONFIG

    config_path.write_text(dump_config(config), encoding="utf-8")

    print(f"Configured Motherduck and Linear MCP servers in {config_path}")
    print("Next:")
    print("  export MOTHERDUCK_TOKEN=md_...")
    print("  export LINEAR_TOKEN=lin_...")
    print("  export NOTION_TOKEN=ntn_...")
    print("  codex   # run from this directory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

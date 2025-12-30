#!/usr/bin/env bash
set -euo pipefail

if command -v gpushell >/dev/null 2>&1; then
  echo "gpushell is already installed at $(command -v gpushell)"
  exit 0
fi

if ! command -v go >/dev/null 2>&1; then
  echo "go is required to install gpushell" >&2
  exit 1
fi

export GOPRIVATE=github.com/alberttogether/*

go install github.com/alberttogether/k8s-gpu-shell/cmd/gpushell@latest

if command -v gpushell >/dev/null 2>&1; then
  echo "gpushell installed at $(command -v gpushell)"
else
  echo "gpushell install completed but binary not found in PATH" >&2
  exit 1
fi

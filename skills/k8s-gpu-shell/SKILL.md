---
name: k8s-gpu-shell
description: Run commands or open shells on Kubernetes GPU nodes using the internal gpushell CLI. Use when Codex needs temporary GPU access for tests, CUDA tooling, model profiling, or when a laptop lacks GPU hardware, including allocating GPU-backed pods, running one-off commands, port-forwarding services, copying files, listing allocations, or deleting/refreshing GPU shells.
---

# K8s Gpu Shell

## Overview

Provision temporary GPU-backed StatefulSets in Kubernetes and run interactive or one-off commands inside them. Use `gpushell` to allocate GPU pods, execute commands, copy files, port-forward, and clean up allocations.

## Quick start

- Install `gpushell` if needed:
  - `skills/k8s-gpu-shell/scripts/install.sh`

- Allocate a GPU shell:
  - `gpushell allocate --name <nickname> --gpu-count <n> [--node-count <n>] [--image cuda|vllm|sglang|<image>] [--cpu-per-gpu <cores>] [--memory-per-gpu <mem>] [--wait <duration>]`
- Run a command:
  - `gpushell run --name <nickname> -- <command>`
- Open an interactive shell:
  - `gpushell connect --name <nickname>`
- Tear down when done:
  - `gpushell delete --name <nickname> [--wait <duration>]`

## Workflow

1) Decide allocation parameters.
   - Choose a short nickname for `--name` (used in resource names and labels).
   - Decide GPU count per pod (`--gpu-count`) and how many pods (`--node-count`).
   - Choose an image shortcut (`cuda`, `vllm`, `sglang`) or pass a full image.
   - Optional overrides: `--cpu-per-gpu`, `--memory-per-gpu`, `--namespace`.

2) Allocate.
   - `gpushell allocate --name <nickname> --gpu-count <n> [--node-count <n>] [--image <image>]`
   - Waits for pods to be ready (default 10m).

3) Run commands or open a shell.
   - One-off command: `gpushell run --name <nickname> -- <command>`
   - Background command: `gpushell run --name <nickname> --background -- <command>`
   - Interactive shell: `gpushell connect --name <nickname>`

4) Copy files or port-forward if needed.
   - Copy: `gpushell copy --name <nickname> <src> <dst>`
   - Port-forward: `gpushell forward --name <nickname> --local <port> [--remote <port>]`

5) Refresh TTL or delete.
   - Extend TTL: `gpushell refresh --name <nickname> [--extend <duration>]`
   - Delete: `gpushell delete --name <nickname> [--wait <duration>]`

## Key behaviors and defaults

- Namespace: `--namespace` overrides; otherwise uses `GPUSHELL_NAMESPACE` or `default`.
- Image shortcuts: `cuda`, `vllm`, `sglang` map to predefined images; any other value is treated as a full image reference.
- GPU sizing: resource requests/limits scale with `--gpu-count`. Defaults: 4 CPU cores and 32Gi per GPU when overrides are not provided.
- Pods: allocation creates a StatefulSet with `shell` container and `/scratch` hostPath mounted at `/scratch`.
- TTL: allocations are protected by an expiration policy (default 24h); use `gpushell refresh` to extend TTL if needed.
## Install script

- `scripts/install.sh` installs `gpushell` via `go install` and verifies it is on `PATH`.

## Examples

- Run CUDA diagnostics on a single A100:
  - `gpushell allocate --name cuda-diag --gpu-count 1 --image cuda`
  - `gpushell run --name cuda-diag -- nvidia-smi`
  - `gpushell delete --name cuda-diag --wait 2m`

- Launch a vLLM dev shell with 2 GPUs:
  - `gpushell allocate --name vllm-dev --gpu-count 2 --image vllm`
  - `gpushell connect --name vllm-dev`

- Port-forward a service running in pod 0:
  - `gpushell forward --name vllm-dev --local 8000 --remote 8000`

## Operational notes

- Prefer `gpushell list` to discover existing allocations before creating new ones.
- Use `gpushell delete` when done to avoid quota waste.
- When a command needs files, use `gpushell copy` to upload/download artifacts.
- If you need multiple pods, use `--node-count` and select pods with `--node`.
- Rely on the current Kubernetes context set in `KUBECONFIG`; do not override it unless the user asks.

---

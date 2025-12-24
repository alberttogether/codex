---
name: kuberadar
description: Query and lightly update internal Kubernetes clusters via the KubeRadar CLI. Use when you need to list clusters, inspect resources/logs, find GPU capacity, or make limited updates through the KubeRadar API using the `kuberadar` command.
---

# Kuberadar

## Overview

Use the `kuberadar` CLI to query or perform limited updates to internal Kubernetes clusters. Prefer read-only commands unless the user explicitly confirms `--allow-writes`.

## Core workflow

- Use `kuberadar` for listing clusters, querying resources, streaming logs, or finding GPU availability.
- Always scope large responses with `--jmespath` to return only the needed fields.
- Before any command that includes `--allow-writes`, ask the user for explicit confirmation.
- Use the global flags as needed: `--server`, `--api-key`, `--timeout`, `--output`.

## Read operations (common)

- List clusters: `kuberadar clusters list`
- Get resource metadata: `kuberadar get <resource> [name]`
- Describe resources with events: `kuberadar describe <resource> [name]`
- Fetch raw objects: `kuberadar raw <resource> [name]`
- Stream pod logs: `kuberadar logs <pod> <container> -n <ns> -c <cluster> -f`
- Find available GPUs: `kuberadar find gpu [filters]`

## Write operations (explicit confirmation required)

All write operations require `--allow-writes`. Ask the user for explicit confirmation immediately before any command that includes `--allow-writes`.

Typical write actions include:
- Add/remove clusters
- Set/delete node annotations
- Scale Argo rollouts
- Edit HPAs

## JMESPath guidance

When requesting large amounts of information (e.g., all pods, large resource lists), use `--jmespath` to limit returned data to only the fields needed for the task. Prefer server-side filtering with `--jmespath` over client-side filtering.

## Examples

Find H100 GPUs across clusters:

```bash
kuberadar find gpu --sku NVIDIA-H100-80GB-HBM3 --count 4 -c prod-a -c prod-b
```

Use JMESPath to return pod names and phases:

```bash
kuberadar get pods -n kube-system -c majesticmoose --jmespath 'data[].{name: metadata.name, phase: value.phase}'
```

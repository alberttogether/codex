---
name: motherduck-analytics
description: Use for Motherduck-based inference analytics, request lifecycle tracking, and request_id investigations via the Motherduck MCP server. Trigger on analytics questions about inference edge/pop, TGL telemetry, dedicated endpoints, or Kuberadar telemetry, and when needing table/column details or request_id-specific lookup.
---

# Motherduck Analytics

## Overview

Use the Motherduck MCP server to answer inference analytics questions and trace individual requests by request_id across analytics tables. Focus on table discovery, schema inspection, and targeted queries to summarize request lifecycles.

## Quick start

1. List databases: `mcp__motherduck__list_databases`
2. List tables: `mcp__motherduck__list_tables` per database
3. Inspect schemas: `mcp__motherduck__list_columns`
4. Query data: `mcp__motherduck__query` with fully qualified names

## Request lifecycle lookup (request_id)

1. Identify the source table for request_id (often `inference-pop-service`, `inference-edge`, `tgl-perf-metrics`, or `tgl-perf-metrics-sink`).
2. Pull request timeline fields (timestamps, status, latency, tokens, routing) for the request_id.
3. Join or correlate across tables if needed (e.g., edge routing to pop service to TGL perf).

## Table overview (exclude flow_checkpoints_v1)

### inference-edge-analytics
- `inference-edge`: Cloudflare edge routing/forwarding telemetry with request/response timing, URL, status, geo/asn metadata, and datacenter selection details.

### inference-platform
- `inference-pop-service`: inference-pop request lifecycle telemetry—engine/model info, request/response timings, rate limiting, user/account context, pricing, and pod-IP routing details.

### inference-platform-analytics
- `inference-pop-monitoring`: synthetic probe/monitoring requests with connection/tls/dns timing, status, bytes, and request metadata.
- `inference-pop-service`: inference-pop lifecycle telemetry with routing/pricing/session fields.

### tgl-telemetry-analytics
- `tgl-perf-metrics`: per-request TGL performance metrics (tokens, latency, finish reason, pod/model/user, timestamps, request params).
- `tgl-perf-metrics-sink`: normalized TGL perf sink with extended timing breakdowns (queue/prefill/decode), throughput, spec-decode stats, and ingestion timestamps.

### dedicated-endpoint-analytics
- `dedicated-endpoint-events-sink`: dedicated endpoint events with endpoint/model/user identifiers, status, and ingestion timestamps.

### kuberadar-analytics
- `kuberadar-events`: Kubernetes event stream (cluster/namespace/object, reason/message, timestamps, counts).
- `kuberadar-hpa`: HPA metrics and replica targets (current/desired/min/max, metric names/values).
- `kuberadar-nodes-gpu`: GPU inventory per node (free/used counts, GPU type/SKU, taints).
- `kuberadar-pod-node-events-sink`: pod/node event sink with GPU, model, service, status, and lifecycle metadata.
- `kuberadar-pods-gpu`: GPU usage per pod (cluster, model/service, GPU type/count).
- `kuberadar-pods-status`: pod status snapshots with GPU info, restarts, priority, and phase.

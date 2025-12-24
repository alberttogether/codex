---
name: noma
description: Maintain nodes in internal Kubernetes inference clusters by authoring NodeMaintenance CRs with the k8s-noma CLI. Use when a user requests node maintenance (drain/reboot/run scripts/install software/free nodes/remove nodes) or explicitly asks to create a NodeMaintenance CR. This skill covers node selection, Linear ticket handling, YAML generation via `k8s-noma init`, and safe application via `kubectl apply -f` with explicit cluster context.
---

# Noma

## Overview

Create NodeMaintenance CRs for internal inference clusters using `k8s-noma init`, select nodes safely, and apply manifests with explicit cluster context after user approval.

## Install k8s-noma

Run these once to install the CLI:

```bash
go env -w GOPRIVATE=github.com/alberttogether/*
go install github.com/alberttogether/k8s-node-maintenance/cmd/k8s-noma@latest
```

## Workflow

1. Confirm the request details: node name(s) or selector, desired action(s), and whether nodes should return to service or remain cordoned/removed.
2. Resolve the target cluster (if not already specified) using KubeRadar.
3. Ensure a Linear ticket exists; if missing, create a new ticket summarizing the maintenance request and capture its ID.
4. Generate a NodeMaintenance YAML file with `k8s-noma init` (never `k8s-noma apply`).
5. Ask permission, then apply the YAML with `kubectl apply -f` using an explicit cluster context.

## Node/Cluster discovery

Use KubeRadar to map a node name to its cluster:

```bash
kuberadar get nodes -o yaml \
  --jmespath "data[].{name:value.name,cluster:value.cluster,gpu_sku:value.gpu.sku}" \
  --name "<node name>*"
```

Update the JMESPath if additional fields are required.

## Ticket handling

Always include `--ticket` when generating the CR.
If the user has not provided a ticket, create a new Linear ticket summarizing the user request, then use the new ticket ID in the manifest. If tooling/access is unavailable, ask the user to create the ticket and provide the ID before proceeding.

## Generate the manifest

Always use `k8s-noma init` to create the YAML file. Do not use `k8s-noma apply`.

### Node selection and drain options

- `--nodes node-a,node-b` to target specific hostnames (`kubernetes.io/hostname`).
- `--selector 'label=value'` or `-l` for label selection.
- `--node-count N` to pick the most available GPU nodes and label them for reuse.
- `--force-drain`, `--drain-timeout 30m`, `--drain-non-gpu-pods` to tune drain behavior.

### Single-action manifests (recommended when one follow-up action is needed)

Use an action subcommand to generate a CR with one follow-up action:

```bash
# Run a script on specific nodes
k8s-noma init script ./maintenance.sh \
  --name gpu-maintenance \
  --ticket ENG-1234 \
  --nodes gpu-01,gpu-02 \
  --image ghcr.io/alberttogether/maintenance-tools:latest \
  --output maintenance.yaml
```

```bash
# Reboot selected nodes (keep them cordoned afterward unless Complete is added)
k8s-noma init reboot \
  --name reboot-gpu \
  --ticket ENG-1234 \
  --selector 'together.ai/role=gpu' \
  --output maintenance.yaml
```

```bash
# Remove nodes from the cluster
k8s-noma init delete-node \
  --name remove-gpu \
  --ticket ENG-1234 \
  --nodes gpu-01,gpu-02 \
  --output maintenance.yaml
```

### Multi-action manifests (manual edit)

For multiple actions or custom ordering, generate a template and edit the `spec.actions` list:

```bash
k8s-noma init \
  --name multi-step \
  --ticket ENG-1234 \
  --selector 'together.ai/role=gpu' \
  --output maintenance.yaml
```

## Action guidance

- Use `delete-node` when the request is to remove nodes from the cluster.
- Omit `Complete` if the nodes should remain cordoned after maintenance. Add `Complete` only when nodes should return to service.
- Use `script` or `run` to install software or perform remediation steps on drained nodes.

## Inspect ongoing maintenance

List active or completed NodeMaintenance CRs to see ongoing work:

```bash
kubectl get noma -A
```

Use this to find the CR name, namespace, and quick status before deciding whether to create or update maintenance.

## NodeMaintenance CRD fields (summary)

From `k8s-node-maintenance` CRD definition:

- `spec.operationName` (string, required): logical name for the maintenance operation.
- `spec.nodeSelector` (string, required): selector expression used to choose target nodes.
- `spec.linearTicket` (string, required): Linear ticket ID for the request.
- `spec.options` (optional):
  - `forceDrain` (bool): force node drain.
  - `drainTimeout` (string): timeout for draining.
  - `drainNonGpuPods` (bool): allow draining non-GPU pods.
- `spec.actions` (array, required): ordered list of action objects.
  - `type` (string, required): action type.
  - `name` (string, optional): action label.
  - `notify` (optional): `channel`, `message`.
  - `run` (optional): `image`, `command[]`, `args[]`.
  - `script` (optional): `image`, `script`, `args[]`.
  - `interactiveShell` (optional): `image`, `tty`.
- `status.phase` (string): overall phase (e.g., Running/Completed).
- `status.currentActionIndex` (int32): index of the active action.
- `status.currentActionType` (string): active action type.
- `status.pendingJobs` (string[]): pending job names.
- `status.jobTimeoutAt` (date-time): when the current job times out.
- `status.conditions` (array): condition list with `type`, `status`, `reason`, `message`, `lastTransitionTime`, `observedGeneration`.
- `status.observedNodes` (string[]): nodes targeted by the controller.
- `status.lastAction` (string): most recent action name/type.
- `status.startedAt` / `status.completedAt` (date-time): timestamps for lifecycle.

## Apply the manifest (explicit approval required)

Before applying, ask the user for permission. When applying, explicitly specify the cluster context:

```bash
kubectl --context <cluster-name> apply -f maintenance.yaml
```

Never apply without user approval.

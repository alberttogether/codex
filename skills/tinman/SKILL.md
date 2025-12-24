---
name: tinman
description: Manage GitOps model bringups and takedowns for Together inference using Tinman config generation and appset edits. Use when creating or removing model configs under infra/charts/tinman, running tinman.py config create or tinman.py config huggingface, or preparing PRs for model lifecycle changes.
---

# Tinman

## Overview

Create, update, and retire model appsets in `infra/charts/tinman` using Tinman config generation and GitOps PRs. This skill is only for the GitOps flow (no direct install/uninstall in clusters).

## Workflow Decision

Use the bringup flow when a new model needs to be deployed via GitOps. Use the takedown flow when a model should be removed from serving.

## Bringup (GitOps)

1. Confirm inputs.
   - Model ID (e.g., Hugging Face repo name).
   - Deployment type (dedicated, serverless, vllm, etc.).
   - Target directory under `infra/charts/tinman`.
   - Prefix or naming conventions for the appset files.
2. Generate base config.
   - From Hugging Face: run `tinman.py config huggingface --model <model-id>` in the target directory.
   - From CLI: run `tinman.py config create --type <type> --file <model-yaml> --prefix <prefix>` in the target directory.
3. Edit generated files.
   - Update the model config file (e.g., `dedicated-*.yaml` or `serverless-*.yaml`) with required settings.
   - Ensure the appset file (e.g., `app-*.yaml` or `appset-*.yaml`) points at the model config and has correct metadata.
4. Validate structure.
   - Run `tinman.py config check --file <appset-file>` from `tools/model_install` if validation is needed.
5. Open PR.
   - Commit changes under `infra/charts/tinman/<model>/`.
   - Note that deployment happens from GitHub Actions after the PR is merged.

## Takedown (GitOps)

1. Create PR 1: drain clusters.
   - Edit the model appset to set the `clusters` field to an empty list.
   - Submit a PR and wait for it to merge/deploy.
2. Create PR 2: remove appset.
   - Remove the appset file from `infra/charts/tinman/<model>/`.
   - Submit a second PR for the deletion.

## Notes

- Operate inside `infra/charts/tinman` for config generation so files land in the right directory.
- Prefer `tinman.py config create` or `tinman.py config huggingface` for starting files; edit afterward to make them deployable.

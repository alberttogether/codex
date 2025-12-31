description: Steps to bring up a new serverless or dedicated model

First determine whether this is a new model or a new endpoint for a model that is already deployed. It is common for multiple customers to have MREs for the same model. An MRE
request must be specific about the model name and the endpoint name. A serverless endpoint typically has the same name as the underlying model. Check `charts/tinman` to see if there
is already a `model-*.yaml` file for the requested model.

## Prerequisites

The tinman tool is used throughout these instructions, ensure that it is installed as per instructions in the tinman skill. Invoke it from within the `infra/charts/tinman` directory so generated files land in the correct place.

Some automation uses AWS resources. Ensure AWS login is current and the AWS CLI works (run `aws sts get-caller-identity` and `aws sso login` if it fails).

Gather inputs up front:
- Hugging Face model ID
- Deployment type (serverless or dedicated/MRE)
- Engine (pulsar, vllm, sglang, etc)
- GPU type, count, and memory/link if relevant
- Target clusters
- Dedicated only: prefix and owner (user id or email)

If the requester does not specify whether this is serverless, MRE (dedicated), or self-serve dedicated endpoint, ask for clarification before proceeding.

Inputs checklist by flow:
- Serverless: model ID, engine, GPU type/count, target clusters
- MRE (dedicated): model ID, engine, GPU type/count, target clusters, prefix, owner
- Self-serve DE: model ID, engine, GPU type/count variants, variants file, target clusters (if any)

## Bringing up a new model

### Uploading to R2
The source of truth for all models is Hugging Face. The Hugging Face repo name is the canonical name for model weights. Before a model is deployed it must be copied to R2. Run the
`unified-pipeline.yml` action in the `unified-downloader` repo:

```bash
gh workflow run unified-pipeline.yml --ref main \
  -F source_type=hf \
  -F source_object_id=${MODEL_NAME} \
  -F destination_type=r2 \
  -F destination_object_id=${MODEL_NAME}
```

### Creating the YAML files
Since this is a GitOps flow, first create a new branch in the local `infra` repo.

### Use Tinman to create a basic model configuration file

```bash
# Tell Tinman to create a config based on information from Hugging Face.
# --private tells it to use the Together.ai Hugging Face key instead of your local
# key. It is not needed for public models
tinman config huggingface --private --model ${MODEL_NAME}
```

Help details (from `tinman config huggingface --help`):
- `--model` is required
- `--private` uses Together.ai credentials for private models

This command creates a new directory and config file called model.yaml. This file contains config shared by all endpoints serving the model. The command returns the path of the created file.

### Update the config file
Read the Hugging Face model page (`https://huggingface.co/${MODEL_NAME}`). Update the description portion of the generated file (`registry.description`) with a short summary. Then
look for VLLM or SGLang serving instructions (depending on which engine is used). If specific parameters are needed, update the YAML file. Look at the templates to find the correct
template parameters. Use `extraArgs` if no template parameters are available.


### Selecting a cluster

Use your kuberadar skill to find a cluster that has nodes with available GPUs of the required type.

### Use Tinman to create a serverless model configuration file

Run `tinman config create --help` to review available parameters. Use the information provided in the request. If GPU type, engine, or GPU count are not specified, ask the user.
Pass the base model config file (created in the previous step) with `--file`.

Help details (from `tinman config create --help`):
- Required inputs: `--type` and `--file`; `--model` is not required
- Cluster selection: `--cluster` (can be passed multiple times)
- Dedicated parameters: `--prefix`, `--owner`, `--replicas`
- Engine settings: `--engine`, `--engine-variant`, `--context_length`, `--max_capacity`
- GPU settings: `--gpu_type`, `--gpu_memory`, `--gpu_link`, `--gpu_count`
- Pulsar toggles: `--pagedkv`, `--torchcompile`, `--prompt-cache`
- Overrides: `--custom_config_file`, `--base_model`, `--lora`

This command will create an appset.yaml and endpoint.yaml file. The command will print the names of all files created.

### Edit the configuration files

Edit the appset file to add additional clusters and set replica counts per cluster. Commit changes to git in a new branch and create a PR. Ask the user to review the PR and trigger a
QA run.

Use `tinman config check` to check the config for errors.

Help details (from `tinman config check --help`):
- `--file` checks a single appset file
- `--all` checks all files
- `--cluster` scopes checks to a cluster

### Model check

Use `tinman model check` to run a set of checks on an existing model deployment if you need additional validation beyond config linting.

### MRE configs

The parameters are the same as for serverless, except `--type` is `dedicated` and `--prefix` and `--owner` are required. The prefix should be a short version of the customer name
(for example `salesforce` or `dippy`). The owner is the user id or email of the user that will be charged for the model (Tinman accepts either).

### Testing the config

Use `tinman run` for a quick check of single-node configs. This is useful for quick iteration on engine parameters, since it can reuse the same pod. It primarily tests engine startup.

`tinman install` can bring up the full manifest using helm without going through ArgoCD. Make sure to run `tinman uninstall` after testing is complete.

To test, `tinman probe` sends a single request. 




### Self-serve DE configs

To generate self-serve DE configs from a YAML file, use `tinman config upload` with the appset file.

```bash
tinman config upload --file <appset file> --variants <variants.yaml>
```

Help details (from `tinman config upload --help`):
- `--file` is required
- `--model` overrides the model name if it cannot be derived from the config
- `--override key=value` applies config overrides
- `--variants` supplies a multi-document variants file
- `--dryrun` runs without uploading
- `--test` triggers tests after upload

The variants file is a multi-document YAML file that has one document with overrides for each variant. This is used to specify different GPU counts and type, for example:
```yaml
togetherNode:
  modelGPUs: 1
---
togetherNode:
  modelGPUs: 2
---
togetherNode:
  modelGPUs: 4
---
togetherNode:
  modelGPUs: 1
nodeSelector:
  nvidia.com/gpu.product: NVIDIA-A100-SXM4-80GB
---
togetherNode:
  modelGPUs: 2
nodeSelector:
  nvidia.com/gpu.product: NVIDIA-A100-SXM4-80GB
```

Upload returns a config id. To trigger testing of the config id:
```bash
../../../tools/model_install/test_de_config.py --config-id <config id>
```

Once a config has been tested it can be copied from QA to prod:
```bash
tinman config sync-to-prod --config-id <config id>
```

Help details (from `tinman config sync-to-prod --help`):
- `--config-id` is required
- `--force` syncs even if tests have not completed

To find the config in prod and view registry data, use `tinman model describe`:
```bash
tinman model describe --model <model name>
```

Help details (from `tinman model describe --help`):
- `--model` is required

If you need to delete a config:
```bash
tinman config delete --config-id <config id>
```

Help details (from `tinman config delete --help`):
- `--config-id` deletes a single config
- `--model` deletes all configs for a model

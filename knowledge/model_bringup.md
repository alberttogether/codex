description: Steps to bringup a new serverless or dedicated model

The first step is to determine if this is an entirely new model or a new endpoint for a model that has already been deployed. It is common for multiple customers to have MREs for
the same model. An MRE request must be specific about the name of the model and the endpoint. A serverless endpoint typically has the same name as the underlying model. Look in the
charts/tinman directory if the there's alreay a model-XXX.yaml file for the the requested model.

## Prerequisites

The tinman tool is used throughout these instruction. It is located in the tools repo in model_install/tinman.py. The tool must be invoked from within the charts/tinman directory. For brevity the instruction use "tinman.py".

Some automation uses AWS resources. Ensure AWS login is current and aws CLI works by running (run "aws sts get-caller-identity" and "aws sso login" if it fails)

## Bringing up a new model

### Uploading to R2
The source of truth for all models is HuggingFace. The huggingface name is used as the canonical name for model weights.
Before a model is deployed it needs to be copied to R2. This is done via the unified-pipeline.yml action in the github unified-downloader repo
gh workflow run unified-pipeline.yml --ref main -F source_type=hf source_object_id=${MODEL_NAME} destination_type=r2 destination_object_id=${MODEL_NAME}

### Creating the YAML files
Since this is a gitops flow, first create a new branch in the local infra repo.

### Use Tinman to create a basic model configuration file

```bash
# Tell Tinman to create a config based on information from Huggingface
# --private tells is to use the Together.ai Huggingface key instead of your local
# key. It is not needed for public models
tinman.py config huggingface --private --model ${MODEL_NAME}
```

This command will create a new directory and config file in that is based on the model name but simplified using (model_string_to_service_name) and starts with "model-". This file
contains config that is share by all endpoints serving this model.

### Update the config file
Read the Huggingface model page (https://huggingface.co/${MODEL_NAME}. Update the description portion of the generated file (registry.description) with a short summary. Then look
for VLLM or SGLang serving instructions (depending on which is used). If specific parameters are needed, update the yaml file. Look at the templates to find the correct template
parameters. Use extraArgs if no template parameters are available.


### Selecting a cluster

Use your kuberadar skill to find a cluster that has nodes with available GPUs of the required type.

### Use Tinman to create a serverless model configuration file

Run tinman.py config create --help to see the available parameters. Run the command using the information provided to you in the request. If GPU type, engine, or GPU count are not specified,
ask the user. Pass the model base config file (created in the previous step) with the --file parameter.

This command will create an appset-xxx.yaml and either a dedicated-xxx.yaml or serverless-xxx.yaml file.

### Edit the configuration files

Edit the appset file to add additional clusters and set the replica counts per cluster and commit changes to git in a new branch and create a PR. Ask user to review the PR and trigger QA run.

Use "tinman config check" to check the config for errors.
Use "tinman config run" to try to start up the engine. This doesn't work for multi-node configs.

### MRE configs

The parameters are the same as for serverless, except for `type` which is now `dedicated,` a required `prefix`  and `owner` parameter. The prefix should be a short version of the customer name (for example “salesforce” or “dippy”). The owner is the user_id of the user that will be charged for the model. Use the admin panel to find the user id by email if you don’t have it.


### Self-serve DE configs

To generate self-serve DE configs from a YAML file, use tinman upload.

# use those charts to send config to config store
tinman config upload --file <appset file> --variants <variants.yaml>

The variants file is a multi-document YAML file that has one document with overrides for each variant. This is used to specify different GPU counts and type, for example:
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



Upload will return a config ID. To trigger testing of the config id.
# test that config in QA
../../../tools/model_install/test_de_config.py --config-id <config id>

Once a config has been tested it can be copied from QA to prod
../../../tools/model_install/tinman.py config sync-to-prod --config-id <config id>

# find the config you just sent over in prod and view its test_metadata
tinman config find --model-name <model name>

# if you realize you did this wrong, you should get {"message":"Config deleted successfully"}
tinman config delete --config-id <config id>


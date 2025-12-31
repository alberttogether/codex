## Context

Together.ai is a leading provider of GPU cluster and inference as a service, primarily for LLMs but also image and audio models. This document is an overview of the Together inference stack and internal terminology.

## Tech Stack
All code lives in github under https://github.com/togethercomputer/ unless othwerwise specified. All repo names refer to this base URL. repos are checked out under ${HOME}/git.
Production Helm charts live in the production-charts repo.

The preferred coding language for all new services is golang. Frontend and some older backend components are written in TypeScript.

Observability is provided using Loki and Prometheus with data collected in Grafana cloud. You can access it using the grafana tool.

## Inference Stack

Requests are typially sent to api.together.ai, which maps to a Cloudflare worker (repo: inference-edge). The worker use KV store to locate the correct inference cluster to route the request to. The  KV store is written by the Edge KV sync service (repo: inference-edge-kv-sync), which uses service from the model registry and Kuberadar.
The model registry is backed by MongoDB table and accessed via one of multiple libraries. TypeScript code for accessing the model registry is in repo together-backend.

Inside the cluster, the request is sent to inference pop via a regular ingress route that utilizes Traefik. Inference pop (aka I-Pop, repo: inference-pop) is a proprietary API server that is responsible for access control, traffic shaping, request recording, generating billing events, and request translation for different engines. Depending on the config settings, inference pop will send the request to a per-model service or directly to the model pod (the latter is known as podIp routing). podIp routing optimizes load based on expected prefill delay, requests in flight, and expected KV cache hits.

Models are deployed as either Argo rollouts, LeaderWorkerSets (for multi-node deployments) or K8s deployments. The model can be served by an in-house engined called Pulsar (repo: pulsar), VLLM, TRT-LLM, or SGLang. For SGLang, an in-house fork called TGL is used (repo: tgl). For engines other than Pulsar, the pod runs a proxy (repo: tproxy) as a side-car to normalize requests. Each engine also run a small downloader (repo: unified-downloader) that loads the model from Cloudflare R2 to a local scratch drive or shared drive (depending on the cluster). To limit scratch drive usage each cluster runs a daemonset service called modelpreload (repo: infra), which does LRU deletion of models. It can also be configured to preload models, but this is not currently used.

## Model management

There are currently multiple ways models can be deployed. The most common flow relies on github as source of truth and deploys using ArgoCD (gitops). This flow is also known as the tinman flow. Models for this flow are in the infra repo. Each model is represented by a set of YAML files in one of these paths:
charts/tinman: Default path
charts/multi-node: Multi-node (LWS) deployments
charts/nexus: Models created via the Nexus flow.
These are either serverless models (paid per token, publicly accessible) or monthly reserved endpoints (MRE, which are paid by GPU time on long-term contracts and set up by the customer success team).

Apart from the engine configuration, the YAML files also contain information that goes into the model registry (in the "registry" section of the YAML). The values are written to the model registry using a post-install hook (see model_install.py in the tools repo).

Use the tinman skill to manipulate models deployed using this flow.

Models can also be self-deployed by users via a UI or an API. This is implemented by a system known as Autoscale or MOP (repo: together-dedicated-endpoints). These models are known as self-serve dedicated endpoints (DE). Not that "dedicated endpoint" is slightly ambiguous and can refer to MREs or self-serve DEs. Ask for clarification if not clear from context.

The together-autoscale service has two components. A REST API server that runs in a central EKS cluster (website-cluster) and a small agent (MOP - Model Operator) that runs in each inference cluster. The MOP is not a true Kubernetes operator, it communicates with the REST server via a workqueue. The MOP uses engine configurations stored in a database, which is called ConfigStore (repo: together-configstore).

The tinman tool has helpers for creating configstore entries from tinman YAML files and for migrating self-serve DEs to a different cluster using an API.

Nexus is a new system that can directly create Configstore entries via a UI / API. It also runs automated tests on all Configstore entries.

## Other pieces

Hadron (repo: hadron) is an in-house workload orchestrator used for testing. It's a wrapper over Argo workflows.

Citadel - TODO

## Other services

Poe bot (repo: poe-bot) hosts Together's Poe server bot on poe.com. The service deploys to the website-cluster EKS context; see the repo README for release steps.


## Clusters

All code runs on Kubernetes clusters. The primary Together account is 598726163780 and most resources are un us-west-2. Control plane clusters live in AWS EKS clusters:
For production (use AWS prod account)
website-cluster:  The original control-plane cluster. Runs most of the control plane.
whq_prod_usw2: A newer cluster that runs ArgoCD and a few other services.

For QA (use AWS QA account)
together-qa_qa_usw2: QA environment control plane


You can use the in-house kuberadar service (repo: kuberadar) to get the name of all clusters and retrieve aggregate lists of Kubernetes resources. Use you kuberadar skill for this.

There are two types of clusters. Older clusters use the k3s distribution. Newer clusters use an in-house provision system called tcloud that runs inference clusters (aka tenant clusters) inside VMs that are provisioned using kubevirt on baremetal substrate clusters. You do not access substrate clusters directly. You do not SSH into nodes. When asked to to do any node maintenance use your noma skill, which uses a Kubernetes operator for safe maintenance operations.

Services are deployed into the cluster using ArgoCD. The preference is to use an application set with a cluster generator, but some services list clusters explicitly. Application sets are in the argo-apps directory in the infra repository. When deploying in-house services, prefer having a Helm chart in the service repo and refer to it from the application set. For 3rd party services, prefer official Helm charts from the service maintainer. If none are available, bitnami helm charts are acceptable.


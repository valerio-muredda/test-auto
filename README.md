VPA-Driven Resource Right-Sizing with EDA + AAP on OpenShift

Scenario: cluster-wide pod resource optimization using Vertical Pod Autoscaler (VPA) in "Inform" mode, surfacing recommendations as Prometheus alerts, triggering AAP Event-Driven Ansible (EDA) workflows, creating ServiceNow tickets for human-in-the-loop approval, and executing remediation via ArgoCD.

┌─────────────────────────────────────────────────────────────────────────┐
│ 	                                                                      │
│                                                                         │
│  		  	                     ┌──────────────────────────────────────┐   │
│  		                         │  OpenShift Cluster                   │   │
│  		                         │                                      │   │
│                              │  ┌──────────────┐  ┌─────────────┐   │   │
│  ┌──────────┐                │  │ Dummy App    │  │   VPA       │   │   │
│  │  ArgoCD  │ ─── GitOps ──► │  │ (+ Traffic   │  │ (Inform)    │   │   │
│  └──────────┘                │  │   Gen)       │  └──────┬──────┘   │   │
│                              │  └──────────────┘         │          │   │
│  ┌──────────┐                │  ┌──────────────────────┐ │          │   │
│  │   AAP    │                │  │ Prometheus / OCP     │◄┘          │   │
│  │  + EDA   │◄── Webhook ────│  │ Monitoring Stack     │            │   │
│  └────┬─────┘  (AlertMgr)    │  └──────────────────────┘            │   │
│       │                      └──────────────────────────────────────┘   │
│       │  ticket                                                         │
│       ▼                                                                 │
│  ┌──────────┐                                     			                |
│  │ServiceNow│                                                           │
│  └────┬─────┘                                                           │
│       │ Human approval                                                  │
│       ▼                                                                 │
│  ┌──────────┐  patch PR/CR                                              │
│  │  ArgoCD  │ ────────────► Git Repo (VPA policy / resource manifests)  │
│  └──────────┘                                                           │
└─────────────────────────────────────────────────────────────────────────┘




Design decisions:

- VPA runs in "Inform" mode only so it never mutates pods automatically
- Prometheus scrapes VPA recommender metrics to detect divergence from current requests
- AlertManager routes alerts to AAP EDA via webhook
- EDA opens a ServiceNow change requests for human review
- After approval, a remediation playbook opens a Git PR to update resource definitions, letting ArgoCD reconcile





⚠️ Disclaimer
Warning: This software is provided "AS-IS" without any warranties or guarantees of any kind. No QA or formal testing process has been performed.

By using this tool, you acknowledge that:

You are solely responsible for verifying and validating its functionality
You should test it in a non-production environment first before using it on production clusters
The authors are not liable for any damages or issues arising from its use



Prerequisites:

┌────────────────────────────────────────────────────────────────────────────────────────────────┐
| Component     | Version                       | Notes                                          |
|---------------|-------------------------------|------------------------------------------------|
| OpenShift     | 4.14+                         | OCP Monitoring Stack enabled                   |
| ACM           | 2.9+                          | Hub + managed clusters registered              |
| AAP           | 2.6+                          | Deployed as Operator in aap namespace          |
| EDA           | 2.4+                          | Part of AAP 2.6 Operator bundle                |
| ArgoCD/GitOps | OpenShift GitOps 1.12+        | Deployed on hub, managing spoke apps           |
| VPA Operator  | 4.x VerticalPodAutoscaler CRD | Installed via OCP OperatorHub                  |
| ServiceNow    | Any supported instance        | REST API accessible from OpenShift             |
| Prometheus    | Cluster Monitoring Operator   | Built-in OCP, user-workload monitoring enabled |
└────────────────────────────────────────────────────────────────────────────────────────────────┘

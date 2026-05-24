# `.claude/skills/` — Reusable Engineering Playbooks

Each file is a focused, low-token playbook for one engineering concern.
Load only the skill(s) relevant to the task at hand.

| Skill | When to load |
|---|---|
| [rag_engineering.md](rag_engineering.md) | RAG pipeline changes (chunking, retrieval, reranking, grounding) |
| [agent_orchestration.md](agent_orchestration.md) | LangGraph workflow changes; adding agents |
| [evaluation_pipeline.md](evaluation_pipeline.md) | Evaluation metrics, thresholds, RAGAS/DeepEval |
| [observability.md](observability.md) | Metrics, traces, MLflow, dashboards |
| [fastapi_patterns.md](fastapi_patterns.md) | Routes, schemas, middleware, dependencies |
| [docker_deployment.md](docker_deployment.md) | Docker / docker-compose |
| [kubernetes_patterns.md](kubernetes_patterns.md) | K8s manifests, Helm, HPA, PDB, NetworkPolicy |
| [llmops.md](llmops.md) | Prompts, providers, costs, releases |
| [governance_guardrails.md](governance_guardrails.md) | Guardrails, PII, policy |
| [hallucination_detection.md](hallucination_detection.md) | Grounding + hallucination scoring |
| [prompt_engineering.md](prompt_engineering.md) | Authoring + versioning prompts |
| [async_workflows.md](async_workflows.md) | Async Python patterns |
| [microservices_patterns.md](microservices_patterns.md) | Splitting services (only when warranted) |

## Update protocol

When changing a playbook:

1. Edit ONLY the relevant skill file.
2. If a hard rule or pattern changes, also update `REPO_STATE.md` §11 (Hard constraints).
3. Add a CHANGELOG entry only for significant rule changes (not for prose edits).

# Skill — Agent Orchestration

> Playbook for the LangGraph multi-agent workflow.

## When to load

- Adding / removing an agent
- Changing the agent execution order or fan-out
- Debugging "why did agent X get skipped?" issues

## Mental model

`WarrantyGraph` is a `StateGraph` with 6 nodes executing in sequence. If LangGraph
is unavailable, `_run_sequential` runs the same nodes in the same order — same
contract, different runtime. Tests use the sequential path.

```
retrieval → document_rag → root_cause → recommendation → executive_summary → evaluation
```

## Key files

| File | Role |
|---|---|
| `app/workflows/warranty_graph.py` | Graph construction + node functions + sequential fallback |
| `app/agents/base.py` | `BaseAgent` (metrics + structured logs + uniform error handling) |
| `app/agents/<name>_agent.py` | One file per specialist |

## Standard tasks

### 1. Add a new agent

```python
# 1) app/agents/<name>_agent.py
from app.agents.base import BaseAgent

class MyAgent(BaseAgent):
    name = "my_agent"
    async def _execute(self, **inputs):
        return {"my_result": ...}

# 2) app/agents/__init__.py — export it
# 3) app/workflows/warranty_graph.py
#    - self.my = MyAgent()
#    - _node_my(...) function
#    - g.add_node("my", self._node_my)
#    - g.add_edge("<prev>", "my")
#    - extend WarrantyState typed dict
# 4) Add unit test (tests/unit/test_<name>_agent.py)
```

### 2. Make a node optional / conditional

Use a router node:

```python
g.add_conditional_edges("retrieval", lambda s: "rag" if s.get("claims") else "skip", {
    "rag": "document_rag",
    "skip": "evaluation",
})
```

### 3. Parallelize independent agents

LangGraph supports fan-out by adding multiple edges from the same source.
For our current pipeline, retrieval and document_rag could run in parallel:

```python
g.add_edge("entry", "retrieval")
g.add_edge("entry", "document_rag")
g.add_edge("retrieval", "root_cause")
g.add_edge("document_rag", "root_cause")  # join
```

Remember to update the sequential fallback to mirror behavior (use `asyncio.gather`).

## Hard rules

- Every agent inherits from `BaseAgent`. Don't reimplement metrics/logging.
- Agent inputs/outputs are dicts; document them in the docstring.
- An agent failure must NOT crash the graph — `BaseAgent.run` already wraps `_execute`.
- Don't read settings inside `_execute`; cache them in `__init__`.

## Debugging

- Set `LOG_LEVEL=DEBUG`; `BaseAgent` logs `agent_run_start` and `agent_run_complete`
  with elapsed ms and truncated inputs.
- Check `warranty_agent_invocations_total{agent,status}` for skipped/failed agents.
- Inspect `state["errors"]` in the returned `WarrantyState`.

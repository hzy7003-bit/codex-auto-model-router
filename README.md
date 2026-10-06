# Codex Auto Model Router

[![Validate](https://github.com/orange-the-weak/codex-auto-model-router/actions/workflows/validate.yml/badge.svg)](https://github.com/orange-the-weak/codex-auto-model-router/actions/workflows/validate.yml)

**A lightweight GPT-6 Astra, GPT-6.1 Sol, and GPT-6 Luna reasoning router for OpenAI Codex.** It separates task lanes from model identities and provides switchable routing profiles, including explicit Plus and Pro policies. GPT-6 Sol, GPT-5.6 Terra/Luna, and GPT-5.5 remain unavailable for routing and readable in historical records; GPT-5.6 Sol is limited to the Pro strict-implementation lane.

[简体中文](README.zh-CN.md) · [Routing feedback](https://github.com/orange-the-weak/codex-auto-model-router/issues/new?template=routing-feedback.yml) · [Bug report](https://github.com/orange-the-weak/codex-auto-model-router/issues/new?template=bug-report.yml)

GPT-5.6 gave Codex many useful model and reasoning combinations. With GPT-6, routing directly to versioned model names would make the next generation harder to add, so task lanes now describe the work and a model catalog resolves those lanes.

Version 2 therefore uses a fail-open, benefit-gated default: choose quickly, keep bookkeeping out of the critical path, and create a bounded subagent automatically when model-switch benefit outweighs startup and aggregation cost. This is my first open-source project; practical feedback is genuinely welcome.

**Automatic model routing**

```text
Request
└─ Re-evaluate the task itself
   ├─ Mechanical, ordinary, scan, or deterministic deep work → GPT-6 Luna
   ├─ latency_priority compatibility lane → GPT-6 Luna/max (cost/value choice)
   ├─ Bounded complex work → GPT-6.1 Sol/low
   ├─ High ambiguity or coupling → GPT-6.1 Sol/medium
   ├─ High consequence → profile-selected route (Astra/high in quality)
   └─ Classified complex reasoning failure → profile-selected route (Astra/xhigh in quality)
      ↓
   Recommendation matches or switching does not pay → run locally
   Recommendation differs and route benefit clears overhead → use that model's leaf agent
```

**Low-overhead concurrency**

```text
Task
├─ Independent, safe tool/process calls → run concurrently in the coordinator
├─ Reasoning-dependent or conflicting work → run serially
└─ Independent reasoning with clear net route benefit → automatic agent mode
```

## Quick start

Ask Codex:

> Install the `codex-auto-model-router` Skill from `https://github.com/orange-the-weak/codex-auto-model-router`.

Or install manually:

```bash
git clone https://github.com/orange-the-weak/codex-auto-model-router.git
cd codex-auto-model-router
./install.sh
```

Restart Codex after installation.

## Exit for one project

Tell Codex “stop using this Skill in the current project,” or run:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-auto-model-router/scripts/router_lite.py" project-disable --repository .
```

This preserves unrelated settings and adds one managed `[[skills.config]]` entry to the project's `.codex/config.toml`. Router commands stop immediately; restart Codex before the next task so a trusted project can prevent normal Skill loading. The setting applies only to that project and does not change global `~/.codex/config.toml`.

Restore or inspect it with:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-auto-model-router/scripts/router_lite.py" project-enable --repository .
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-auto-model-router/scripts/router_lite.py" project-status --repository .
```

`--no-subagents` is different: it disables child agents for one Router command but does not exit the Skill. Project-scoped configuration follows Codex's official [`config.toml` behavior](https://developers.openai.com/codex/config-reference/).

## Routing profiles and overrides

The built-in `balanced` profile preserves the original table. `economy` favors Luna across every lane; `quality` keeps mechanical tasks on Luna, uses Sol for other work, and selects Astra/high or Astra/xhigh for high-consequence work and classified complex failures. The explicit `plus` and `pro` profiles apply the policy tables below. These profiles express model and effort preferences, not latency guarantees.

Save a default globally or for the current project, or select one for a single command:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-auto-model-router/scripts/router_lite.py" profile-set economy --scope global
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-auto-model-router/scripts/router_lite.py" profile-set quality --scope project --repository .
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-auto-model-router/scripts/router_lite.py" profile-show --repository .
python3 "${CODEX_HOME:-$HOME/.codex}/skills/codex-auto-model-router/scripts/router_lite.py" decide --profile balanced
```

Settings live in `${CODEX_HOME:-~/.codex}/router.toml` and `<repository>/.codex/router.toml`. Project selection overrides global selection; project lane overrides take precedence over global lane overrides. Each override supplies both model and effort:

```toml
schema_version = 1
profile = "quality"

[profiles.quality.routes.complex_uncertain]
model = "gpt-6.1-sol"
effort = "high"
```

Use `router_lite.py decide --profile quality ...` or `plan --profile economy ...` for a temporary choice. `profile-set` changes only the saved profile and preserves route overrides.

Choose `plus` or `pro` explicitly; Router does not inspect plan metadata or infer a subscription from model availability. Natural-language requests such as “use Pro routing” or “switch to Plus” should map to `profile-set pro|plus --scope global`. Ask `profile-show` to report the saved choice. The existing `balanced` default remains for users who have not selected a profile, preserving backward compatibility.

The `plus` policy starts ordinary work on Luna/xhigh, reserves Luna/high for light work, and routes complex work through Sol/high then Sol/xhigh. It never automatically selects Astra. The `pro` policy starts the same way; bounded strict implementation uses GPT-5.6 Sol/xhigh, uncertain or long-horizon agentic work uses GPT-6.1 Sol/xhigh, and Astra/xhigh is reserved for high-consequence work or a classified substantive Sol failure. A prior Luna failure selects the appropriate Sol route rather than jumping directly to Astra.

Executor service tiers are isolated in each executor preset: Luna omits `service_tier` so the user's Fast preference can apply, while GPT-6.1 Sol, GPT-5.6 Sol, and Astra set `service_tier = "default"`. No shared `/fast` state is toggled, so concurrent Luna and Sol agents have independent settings.

## How it works

Every applicable request follows one of three paths:

| Path | Behavior |
|---|---|
| Local | Recommend a route, then complete the work in the current coordinator. |
| Tool concurrency | Run independent safe tool or process calls together without creating child agents. |
| Benefit-gated subagents | Automatically delegate, reuse, or use multi-model reasoning when route benefit clearly exceeds bounded overhead. |

There is no model Restore, plan hash, cursor, environment guard, or blocking ledger on the default path. Routing or executor startup failure does not block ordinary work. The legacy strict state machine remains available only when the user explicitly requests strict auditing or replay protection.

Visible routing notices follow the language of the current request. English prompts receive English labels, Chinese prompts receive Chinese labels, and model, effort, and reason values remain unchanged.

When execution stays local despite a different recommendation, the notice gives the concise reason: `main conversation model is fixed; leaf startup cost exceeds expected benefit`. Delegated execution similarly labels the switch reason, so a recommendation is never confused with observed model use. The Skill stores only the English canonical template and translates it to the user's current language at runtime.

The recommendation does not switch the current task's model. A routed leaf is a separate task running the recommended model, not a change to the already-running coordinator. Direct tool concurrency shares the coordinator's model and reasoning effort; it creates no child-agent cards or independent reasoning streams.

Safe direct concurrency includes independent file reads, searches, metadata queries, and tests that do not share build state. Reasoning-dependent calls, overlapping writes, Git mutation, deployment, approvals, and shared simulator, device, or build resources remain serial.

Subagent mode is automatic when route-fit, quality, latency, or resource benefit clearly exceeds bounded startup and aggregation overhead; no additional user permission prompt is required. Users can explicitly disable it with `--no-subagents`. Delegated agents keep bounded lifecycle safeguards: `completed` is terminal, child `task_complete` overrides stale parent `running`, a timeout alone is not a stall, and reuse never crosses user requests.

Before the coordinator's final response, any subagent run stops new dispatch, disables reuse, clears the current-request reuse registry, refreshes the current task tree, interrupts every optional or otherwise unneeded child still genuinely `running`, and refreshes once more. The coordinator finalizes only after every child owned by that request is terminal. This can end current-task children, but Codex exposes no collaboration operation for deleting completed child-agent UI history; historical cards may remain visible and are never reported as cleared.

The CLI enables benefit-gated subagents by default. `--no-subagents` is the explicit opt-out. The legacy `--allow-subagents` flag remains accepted for wrapper compatibility but is not permission and is no longer required. Executor presets are selected automatically only after the benefit gate clears; they are never prewarmed or queued speculatively.

## What changed in v0.2

- The default path automatically uses a model-specific leaf when switching benefit clearly exceeds bounded overhead.
- Independent safe tools and processes may run concurrently without extra model contexts or child-agent UI entries.
- `--no-subagents` explicitly disables delegate, reuse, and agent-parallel plans; no permission prompt is otherwise required.
- Recommendations are clearly separated from the current task's observed model.
- Ultra remains opt-in. Luna may fall back to Sol at the same effort; Sol routes never downgrade to Luna. GPT-5.5 is not an availability fallback.

## Balanced model gradient

| Work | Default route |
|---|---|
| Deterministic mechanical work | GPT-6 Luna / medium |
| Ordinary bounded work | GPT-6 Luna / high |
| Large bounded scans or reviews | GPT-6 Luna / xhigh |
| Large deterministic deep work | GPT-6 Luna / max |
| `latency_priority` compatibility lane (cost/value choice) | GPT-6 Luna / max |
| Bounded complex work | GPT-6.1 Sol / low |
| High ambiguity or coupling | GPT-6.1 Sol / medium |
| High-consequence work | GPT-6.1 Sol / high in balanced; GPT-6 Astra / high in quality |
| Failed complex reasoning or verification | GPT-6.1 Sol / xhigh in balanced; GPT-6 Astra / xhigh in quality |

The `latency_priority` lane name is retained for compatibility; its Luna/max route in `balanced` is a cost/value choice, not a fastest-route claim. `sol` selects GPT-6.1 Sol and `astra` selects GPT-6 Astra. GPT-6 Sol, GPT-5.6 Terra/Luna, and GPT-5.5 are unavailable for routing; GPT-5.6 Sol/xhigh is reserved for Pro strict implementation. Historical execution records remain readable.

Ultra is never automatic. Explicit Ultra uses its native orchestration and disables Router-managed parallelism. Unknown model availability keeps the preferred route advisory. If Sol is unavailable, the router retains its recommendation and follows the local fail-open path.

## Evidence and history

The user-provided Artificial Analysis graph recorded 2026-10-02 estimates Luna from index 21 / $0.005 per task at low to index 37 / $0.068 at max, and Sol 6.1 from index 42 / $0.131 at low to index 52 / $0.724 at max. These are estimates read from chart coordinates; they support Luna for lower-cost bounded work and Sol for higher-capability work. The graph provides no latency data and does not measure Codex subscription costs.

The graph's full effort estimates and limitations are recorded in [benchmark evidence](references/benchmark-evidence.md). Historical GPT-5.6 benchmark snapshots remain separate and do not calibrate these model routes. Task evidence and supported model overrides remain primary.

See [benchmark evidence](references/benchmark-evidence.md) and the [machine-readable snapshot](references/benchmark-evidence.json). The snapshot is optional at runtime; missing, invalid, or stale evidence falls back to deterministic rules without blocking work.

Only observed execution is recorded; a recommendation is never written as actual model use. Before a spawn is acknowledged, routing notices label the leaf as the planned executor; `Execution: leaf agent` is shown only after successful creation or reuse. Before every single or parallel spawn, validate `task_name` against `^[a-z0-9][a-z0-9_]{0,47}$` (lowercase letters, digits, and underscores; for example, `pipeline_workflows`). The machine-readable spawn contract includes this naming rule and requires `fork_turns="none"`; a contract mismatch falls back locally without retry. History never becomes a prerequisite for the project result.

## Development

```bash
python3 -m unittest discover -s tests
python3 tests/validate_distribution.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for privacy-safe feedback and development guidance.

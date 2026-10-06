# Explicit custom-agent preset mapping

Use a model-specific leaf only when the automatic benefit gate clears and the interface accepts an agent type. Local decisions return no Apply agent type. The normal routable models are GPT-6 Astra, GPT-6.1 Sol, and GPT-6 Luna; GPT-5.6 Sol/xhigh has one additional Pro strict-implementation executor. Other retired GPT-6 Sol and GPT-5.x IDs cannot be selected.

## Assess and Retune (read-only router)

| Model | low | medium | high | xhigh | max |
|---|---|---|---|---|---|
| GPT-6.1 Sol | `codex_auto_model_router_gpt61_sol_low` | `codex_auto_model_router_gpt61_sol` | `codex_auto_model_router_gpt61_sol_high` | `codex_auto_model_router_gpt61_sol_xhigh` | `codex_auto_model_router_gpt61_sol_max` |
| GPT-6 Astra | `codex_auto_model_router_gpt6_astra_low` | `codex_auto_model_router_gpt6_astra` | `codex_auto_model_router_gpt6_astra_high` | `codex_auto_model_router_gpt6_astra_xhigh` | `codex_auto_model_router_gpt6_astra_max` |
| GPT-6 Luna | `codex_auto_model_router_gpt6_luna_low` | `codex_auto_model_router_gpt6_luna` | `codex_auto_model_router_gpt6_luna_high` | `codex_auto_model_router_gpt6_luna_xhigh` | `codex_auto_model_router_gpt6_luna_max` |

## Apply (workspace-write executor)

| Model | low | medium | high | xhigh | max |
|---|---|---|---|---|---|
| GPT-6.1 Sol | `codex_auto_model_executor_gpt61_sol_low` | `codex_auto_model_executor_gpt61_sol` | `codex_auto_model_executor_gpt61_sol_high` | `codex_auto_model_executor_gpt61_sol_xhigh` | `codex_auto_model_executor_gpt61_sol_max` |
| GPT-6 Astra | `codex_auto_model_executor_gpt6_astra_low` | `codex_auto_model_executor_gpt6_astra` | `codex_auto_model_executor_gpt6_astra_high` | `codex_auto_model_executor_gpt6_astra_xhigh` | `codex_auto_model_executor_gpt6_astra_max` |
| GPT-6 Luna | `codex_auto_model_executor_gpt6_luna_low` | `codex_auto_model_executor_gpt6_luna` | `codex_auto_model_executor_gpt6_luna_high` | `codex_auto_model_executor_gpt6_luna_xhigh` | `codex_auto_model_executor_gpt6_luna_max` |

The only GPT-5.6 executor is the explicit Pro strict-implementation route: GPT-5.6 Sol/xhigh → `codex_auto_model_executor_gpt56_sol_xhigh`. It uses Standard service tier.

The benefit-gated executor receives one bounded task and returns one final result. It reads applicable project instructions, performs only that task, and never delegates. In parallel plans, the Coordinator owns dependencies, write scopes, capacity, scheduling, failure handling, aggregation, and cleanup.

For executor isolation, Luna presets omit `service_tier` and inherit the user's Fast preference. Every GPT-6.1 Sol, GPT-5.6 Sol, and GPT-6 Astra executor preset sets `service_tier = "default"` locally. This does not mutate a global Fast setting and allows concurrent executor configurations to remain independent.

The installer replaces Router-owned presets and removes old Router/executor preset files in the target directory. It preserves unrelated custom agents and settings. Current-coordinator metadata and historical ledger entries may still name retired models; those names do not make them selectable routes.

Max is one normal reasoning route. Ultra has no Router preset; it requires explicit opt-in and disables Router-managed parallelism.

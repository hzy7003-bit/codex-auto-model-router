# Routing profiles

The profile workflow is adapted from David Soff's PR #6; the optional prompt hook comes from his PR #4. Integration preserves the reviewed catalog, explicit model pins, fallback dispatch safety, and the historical GPT-5.6 programmatic policy API.

## Commands and scope

Run commands from the installed Skill directory, or use absolute script paths:

```bash
python3 scripts/router_lite.py profile-show --repository /path/to/project
python3 scripts/router_lite.py profile-set economy --scope project --repository /path/to/project
python3 scripts/router_lite.py profile-set balanced --scope global --repository /path/to/project
python3 scripts/router_lite.py decide --profile quality --repository /path/to/project
```

Global configuration lives in `${CODEX_HOME:-$HOME/.codex}/router.toml`; project configuration lives in `<repository>/.codex/router.toml`. Profile selection is command-line > project > global > balanced. Route overrides for the selected profile are built-in < global < project. Explicit model/effort arguments override profile routes. A model-only argument does not authorize high Astra effort.

`profile-set` changes only the selected scope, preserves existing comments and route overrides, and uses atomic replacement. Invalid configuration is rejected without rewriting it. Lite routing fails open to local execution; strict CLI reports configuration errors. Lite and strict routing check project opt-out before loading profiles. Profile commands do not re-enable a disabled project.

## Built-in profiles

| Profile | Difference from balanced |
|---|---|
| balanced | Existing default routes: Luna for bounded work, Sol for bounded complexity, Astra for uncertainty/high consequence. |
| economy | Uses Luna/high for complex bounded and complex uncertain tasks; preserves the high-consequence and failure lanes. |
| quality | Uses Sol for ordinary work and deterministic scans; does not automatically increase Astra effort. |

All built-ins use Astra/low, with medium reserved for reasoning/verification failure escalation. Astra high, xhigh, or max requires an explicit effort argument or an explicit configured lane override. Available-model checks and fallback routing still apply; a configured lane is not proof that the model executed.

## Lane overrides

```toml
schema_version = 1
profile = "balanced"

[profiles.balanced.routes.complex_uncertain]
model = "gpt-6-astra"
effort = "low"
```

Valid lanes: `mechanical_default`, `ordinary_default`, `bounded_scan`, `bounded_deep_deterministic`, `latency_priority`, `complex_bounded`, `complex_uncertain`, `high_consequence`, `complex_failed_escalation`. Each override requires both `model` and `effort`; only reviewed catalog/legacy model IDs and low-through-max efforts are accepted. Unknown keys, profiles, lanes, or unsupported efforts are errors. Overrides do not edit the model catalog or executor presets.

Strict CLI uses the same resolved profile. Programmatic `route_policy` APIs retain legacy defaults unless passed a `routing_config` from `resolve_routing_config`. Linear and parallel plans capture the selected routes once; later config changes cannot mutate an existing plan. Historical benchmark tables remain unchanged.

## Optional prompt hook

Install with `./install.sh --install-hook` or `./install.ps1 -InstallHook`, review/trust with `/hooks`, and restart Codex. Ordinary installation does not enable it. The hook adds a short routing reminder only when the Skill is installed and the project has not opted out; it does not include the user's prompt in its output, change the active model, or spawn an executor itself. Unrelated hooks are preserved, reinstall is idempotent, and installer failure rolls back the hook configuration along with the Skill payload.

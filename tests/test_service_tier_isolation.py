import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "codex-agents"


def executor_presets():
    return {
        path.stem: tomllib.loads(path.read_text(encoding="utf-8"))
        for path in sorted(AGENTS.glob("codex-auto-model-executor-*.toml"))
    }


class ExecutorServiceTierIsolationTests(unittest.TestCase):
    def test_sol_and_astra_executors_use_standard(self):
        presets = executor_presets()
        isolated = {
            name: preset for name, preset in presets.items()
            if preset["model"] in ("gpt-6.1-sol", "gpt-6-astra")
        }
        self.assertEqual(len(isolated), 10)
        self.assertTrue(all(preset.get("service_tier") == "default" for preset in isolated.values()))

    def test_luna_executors_inherit_the_user_fast_preference(self):
        presets = executor_presets()
        luna = [preset for preset in presets.values() if preset["model"] == "gpt-6-luna"]
        self.assertEqual(len(luna), 5)
        self.assertTrue(all("service_tier" not in preset for preset in luna))

    def test_concurrent_luna_and_sol_have_independent_tier_configuration(self):
        presets = executor_presets()
        luna = presets["codex-auto-model-executor-gpt6-luna-xhigh"]
        sol = presets["codex-auto-model-executor-gpt61-sol-xhigh"]
        self.assertNotIn("service_tier", luna)
        self.assertEqual(sol["service_tier"], "default")
        self.assertEqual(luna["model_reasoning_effort"], "xhigh")
        self.assertEqual(sol["model_reasoning_effort"], "xhigh")

    def test_router_analysis_presets_follow_the_same_model_tier_isolation(self):
        presets = [
            tomllib.loads(path.read_text(encoding="utf-8"))
            for path in AGENTS.glob("codex-auto-model-router-*.toml")
        ]
        sol_and_astra = [
            preset for preset in presets
            if preset["model"] in ("gpt-6.1-sol", "gpt-6-astra")
        ]
        luna = [preset for preset in presets if preset["model"] == "gpt-6-luna"]
        self.assertEqual(len(sol_and_astra), 10)
        self.assertTrue(all(preset.get("service_tier") == "default" for preset in sol_and_astra))
        self.assertEqual(len(luna), 5)
        self.assertTrue(all("service_tier" not in preset for preset in luna))


if __name__ == "__main__":
    unittest.main()

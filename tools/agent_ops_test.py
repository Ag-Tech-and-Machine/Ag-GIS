"""Check that public agent guidance retains its basic safety instructions.

This checks documentation only; it does not exercise a private agent workflow.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AgentGuidanceTest(unittest.TestCase):
    def test_guidance_covers_safe_contribution_and_handoff(self):
        guidance = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "## Start every task here",
            "preserve unrelated edits",
            "never reset/bulk-commit a shared working tree",
            "Do not publish releases",
            "For a useful task handoff",
            "limitations and remaining work",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, guidance)

    def test_documented_portable_checks_exist(self):
        guidance = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for name in ("check_repository.py", "check_plugin.py", "build_plugin.py", "feedback_workflow_test.cjs"):
            with self.subTest(name=name):
                self.assertIn(name, guidance)
                self.assertTrue((ROOT / "tools" / name).is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)

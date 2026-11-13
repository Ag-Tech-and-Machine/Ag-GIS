"""Test agent decision workflow operations.

Tests that the agent workflow checks are properly implemented and follow
the expected patterns for task validation, handoff, and documentation.
"""
import unittest


class AgentOpsTest(unittest.TestCase):
    """Test agent operations and workflow validation."""

    def test_agent_workflow_exists(self):
        """Verify that agent workflow documentation exists."""
        # Check that AGENTS.md exists and contains expected sections
        with open('AGENTS.md', 'r') as f:
            content = f.read()
        
        # Should have key sections
        self.assertIn('## Start every task here', content)
        self.assertIn('## Purpose', content)
        self.assertIn('## Development priority', content)
        self.assertIn('Portable checks', content)

    def test_agent_instructions_present(self):
        """Verify agent instructions document is present."""
        # Check that AGENTS.md contains task instructions
        with open('AGENTS.md', 'r') as f:
            content = f.read()
        
        # Should have task management instructions
        self.assertIn('Hermes manages ongoing execution', content)
        self.assertIn('Act as the tooling manager', content)
        self.assertIn('docs/WORK_LOG.md', content)

    def test_workflow_checks_documented(self):
        """Verify that workflow checks are documented."""
        with open('AGENTS.md', 'r') as f:
            content = f.read()
        
        # Should mention key portable checks
        self.assertIn('check_repository.py', content)
        self.assertIn('check_plugin.py', content)
        self.assertIn('build_plugin.py', content)

    def test_agent_handoff_documentation(self):
        """Verify task handoff documentation requirements."""
        with open('AGENTS.md', 'r') as f:
            content = f.read()
        
        # Should have handoff instructions
        self.assertIn('For a useful task handoff', content)
        self.assertIn('files changed', content)
        self.assertIn('limitations', content)


if __name__ == '__main__':
    unittest.main(verbosity=2)

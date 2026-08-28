"""Tests for Prompt Engineering module."""

import unittest
from ai_gitgen.prompts import PromptBuilder
from ai_gitgen.git_collector import GitChanges, FileStatus


class TestPromptBuilder(unittest.TestCase):
    def test_commit_prompt_structure(self):
        builder = PromptBuilder(language="ko")
        changes = GitChanges(
            is_repo=True,
            branch="feature/test",
            changed_files=[FileStatus("M ", "main.py", True, False)],
            total_files_changed=1,
            total_diff_lines=10,
            has_changes=True
        )
        prompt = builder.build_commit_prompt(changes, "+ print('hello')")
        self.assertIn("Conventional Commits", prompt)
        self.assertIn("main.py", prompt)
        self.assertIn("+ print('hello')", prompt)

    def test_pr_prompt_structure(self):
        builder = PromptBuilder(language="ko")
        changes = GitChanges(
            is_repo=True,
            branch="feature/generator",
            changed_files=[FileStatus("M ", "cli.py", True, False)],
            total_files_changed=1,
            total_diff_lines=20,
            has_changes=True
        )
        prompt = builder.build_pr_prompt(changes, "+ def run(): pass")
        self.assertIn("feature/generator", prompt)
        self.assertIn("## Why", prompt)
        self.assertIn("## What", prompt)
        self.assertIn("## How to Test", prompt)


if __name__ == "__main__":
    unittest.main()

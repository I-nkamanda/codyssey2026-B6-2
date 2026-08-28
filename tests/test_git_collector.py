"""Tests for Git Collector module."""

import unittest
import tempfile
import subprocess
import os
import shutil
from ai_gitgen.git_collector import GitCollector


class TestGitCollector(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Initialize git repo in test_dir
        subprocess.run(["git", "init", "-b", "main"], cwd=self.test_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.test_dir, check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_repo_detection(self):
        collector = GitCollector(self.test_dir)
        self.assertTrue(collector.is_git_repo())

        collector_non_repo = GitCollector(tempfile.gettempdir())
        # /tmp might or might not be a git repo, but an empty subfolder is not
        empty_dir = tempfile.mkdtemp()
        try:
            self.assertFalse(GitCollector(empty_dir).is_git_repo())
        finally:
            shutil.rmtree(empty_dir, ignore_errors=True)

    def test_no_changes_initially(self):
        collector = GitCollector(self.test_dir)
        changes = collector.collect_changes()
        self.assertTrue(changes.is_repo)
        self.assertFalse(changes.has_changes)
        self.assertEqual(changes.total_files_changed, 0)

    def test_detect_changes_and_diff(self):
        # Create a sample file
        sample_file = os.path.join(self.test_dir, "sample.txt")
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write("Line 1\nLine 2\n")

        subprocess.run(["git", "add", "sample.txt"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.test_dir, check=True)

        # Modify sample file
        with open(sample_file, "a", encoding="utf-8") as f:
            f.write("Line 3 modified\n")

        collector = GitCollector(self.test_dir)
        changes = collector.collect_changes()
        self.assertTrue(changes.has_changes)
        self.assertEqual(changes.total_files_changed, 1)
        self.assertIn("Line 3 modified", changes.diff_text)


if __name__ == "__main__":
    unittest.main()

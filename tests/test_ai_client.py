"""Tests for AI Client module."""

import unittest
import os
from ai_gitgen.ai_client import (
    AIClient,
    MissingApiKeyError,
    AIResponse
)


class TestAIClient(unittest.TestCase):
    def test_missing_api_key(self):
        env_backup = {k: os.environ.pop(k, None) for k in ["AI_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"]}
        try:
            client = AIClient(api_key=None, mock_mode=False)
            with self.assertRaises(MissingApiKeyError):
                client.generate("Test prompt")
        finally:
            for k, v in env_backup.items():
                if v is not None:
                    os.environ[k] = v

    def test_mock_mode_commit(self):
        client = AIClient(api_key="mock", mock_mode=True)
        res = client.generate("Commit prompt", task_type="commit")
        self.assertIsInstance(res, AIResponse)
        self.assertEqual(res.call_count, 1)
        self.assertIn("feat:", res.content)

    def test_mock_mode_pr(self):
        client = AIClient(api_key="mock", mock_mode=True)
        res = client.generate("PR prompt", task_type="pr")
        self.assertIsInstance(res, AIResponse)
        self.assertEqual(res.call_count, 1)
        self.assertIn("TITLE:", res.content)
        self.assertIn("## Why", res.content)
        self.assertIn("## What", res.content)
        self.assertIn("## How to Test", res.content)


if __name__ == "__main__":
    unittest.main()

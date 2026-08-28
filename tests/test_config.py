"""Tests for Configuration module."""

import unittest
import tempfile
import os
from ai_gitgen.config import Config


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = Config()
        self.assertEqual(cfg.model, "gpt-4o-mini")
        self.assertEqual(cfg.temperature, 0.2)
        self.assertEqual(cfg.max_tokens, 1000)
        self.assertTrue(cfg.safe_mode)
        self.assertEqual(cfg.language, "ko")

    def test_load_from_yaml_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False) as f:
            f.write("""
model: gpt-4o
temperature: 0.5
max_tokens: 1500
safe_mode: false
language: en
convention: angular
""")
            temp_path = f.name

        try:
            cfg = Config.load(temp_path)
            self.assertEqual(cfg.model, "gpt-4o")
            self.assertEqual(cfg.temperature, 0.5)
            self.assertEqual(cfg.max_tokens, 1500)
            self.assertFalse(cfg.safe_mode)
            self.assertEqual(cfg.language, "en")
            self.assertEqual(cfg.convention, "angular")
        finally:
            os.remove(temp_path)

    def test_env_var_override(self):
        os.environ["AI_API_KEY"] = "test_key_123"
        os.environ["AI_MODEL"] = "claude-3-5-sonnet"
        try:
            cfg = Config.load()
            self.assertEqual(cfg.api_key, "test_key_123")
            self.assertEqual(cfg.model, "claude-3-5-sonnet")
        finally:
            os.environ.pop("AI_API_KEY", None)
            os.environ.pop("AI_MODEL", None)


if __name__ == "__main__":
    unittest.main()

"""Tests for Safety and Sensitive Data Masking module."""

import unittest
from ai_gitgen.safety import SafetyFilter


class TestSafetyFilter(unittest.TestCase):
    def setUp(self):
        self.filter = SafetyFilter(max_diff_files=5, max_diff_lines=50)

    def test_mask_openai_api_key(self):
        diff = "+ openai_key = 'sk-1234567890abcdefghijklmnopqrstuvwxyz123456'"
        sanitized, report = self.filter.sanitize_diff(diff, safe_mode=True)
        self.assertIn("[MASKED_OPENAI_KEY]", sanitized)
        self.assertNotIn("sk-1234567890abcdefghijklmnopqrstuvwxyz123456", sanitized)
        self.assertGreaterEqual(report.masked_items_count, 1)

    def test_mask_google_and_aws_keys(self):
        diff = """+ google_key = 'AIzaSyD-1234567890abcdefghijklmnopqrst'
+ aws_id = 'AKIAIOSFODNN7EXAMPLE'
+ aws_secret_access_key = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'"""
        sanitized, report = self.filter.sanitize_diff(diff, safe_mode=True)
        self.assertIn("[MASKED_GOOGLE_KEY]", sanitized)
        self.assertIn("[MASKED_AWS_ACCESS_KEY]", sanitized)
        self.assertIn("[MASKED_AWS_SECRET_KEY]", sanitized)

    def test_mask_email_and_phone(self):
        diff = "+ contact = 'dev.lead@example.com / 010-1234-5678'"
        sanitized, report = self.filter.sanitize_diff(diff, safe_mode=True)
        self.assertIn("[MASKED_EMAIL]", sanitized)
        self.assertIn("[MASKED_PHONE]", sanitized)
        self.assertNotIn("dev.lead@example.com", sanitized)

    def test_exclude_sensitive_files(self):
        diff = """diff --git a/.env b/.env
--- /dev/null
+++ b/.env
+DB_PASSWORD=supersecret
diff --git a/main.py b/main.py
--- a/main.py
+++ b/main.py
+print('hello')"""
        sanitized, report = self.filter.sanitize_diff(diff, safe_mode=True)
        self.assertIn(".env", report.excluded_files)
        self.assertIn("[SAFE_MODE] 파일 '.env'은 민감정보 또는 대용량 파일 규칙에 의해 전송에서 제외되었습니다.", sanitized)
        self.assertNotIn("DB_PASSWORD=supersecret", sanitized)

    def test_diff_line_truncation(self):
        diff_lines = [f"+ line {i}" for i in range(100)]
        diff = "\n".join(diff_lines)
        sanitized, report = self.filter.sanitize_diff(diff, safe_mode=True)
        self.assertTrue(report.is_truncated)
        self.assertIn("최대 전송 제한(50줄)을 초과하여", sanitized)

    def test_safe_mode_off(self):
        diff = "+ openai_key = 'sk-1234567890abcdefghijklmnopqrstuvwxyz123456'"
        sanitized, report = self.filter.sanitize_diff(diff, safe_mode=False)
        self.assertEqual(sanitized, diff)
        self.assertEqual(report.masked_items_count, 0)


if __name__ == "__main__":
    unittest.main()

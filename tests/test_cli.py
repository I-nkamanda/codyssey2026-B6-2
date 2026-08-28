"""Tests for CLI module."""

import unittest
import tempfile
import subprocess
import os
import shutil
import io
from contextlib import redirect_stdout, redirect_stderr

from ai_gitgen.cli import run_cli


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cli_outside_repo(self):
        buf_err = io.StringIO()
        with redirect_stderr(buf_err):
            code = run_cli(["commit"])
        self.assertEqual(code, 1)
        self.assertIn("Git이 초기화된 프로젝트 루트 디렉토리가 아닙니다", buf_err.getvalue())

    def test_cli_no_changes(self):
        subprocess.run(["git", "init", "-b", "main"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        buf_out = io.StringIO()
        with redirect_stdout(buf_out):
            code = run_cli(["commit"])
        self.assertEqual(code, 0)
        self.assertIn("변경 사항이 없습니다", buf_out.getvalue())

    def test_cli_missing_api_key(self):
        subprocess.run(["git", "init", "-b", "main"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Create a file
        with open("hello.py", "w") as f:
            f.write("print('test')\n")

        # Ensure AI_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY are unset
        env_backup = {
            k: os.environ.pop(k, None) for k in ["AI_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"]
        }
        try:
            buf_err = io.StringIO()
            with redirect_stderr(buf_err):
                code = run_cli(["commit"])
            self.assertEqual(code, 1)
            self.assertIn("AI_API_KEY 환경변수가 설정되지 않았습니다", buf_err.getvalue())
        finally:
            for k, v in env_backup.items():
                if v is not None:
                    os.environ[k] = v

    def test_cli_mock_commit(self):
        subprocess.run(["git", "init", "-b", "main"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open("hello.py", "w") as f:
            f.write("print('test')\n")

        buf_out = io.StringIO()
        with redirect_stdout(buf_out):
            code = run_cli(["commit", "--mock"])
        self.assertEqual(code, 0)
        out = buf_out.getvalue()
        self.assertIn("[INFO] Git status 수집 완료", out)
        self.assertIn("[INFO] AI API 요청 중...", out)
        self.assertIn("[DONE] 커밋 메시지 생성 완료", out)
        self.assertIn("-- Commit Message --", out)
        self.assertIn("feat:", out)

    def test_cli_mock_pr(self):
        subprocess.run(["git", "init", "-b", "feature/pr-test"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open("hello.py", "w") as f:
            f.write("print('test')\n")

        buf_out = io.StringIO()
        with redirect_stdout(buf_out):
            code = run_cli(["pr", "--mock"])
        self.assertEqual(code, 0)
        out = buf_out.getvalue()
        self.assertIn("[INFO] 현재 브랜치: feature/pr-test", out)
        self.assertIn("[DONE] PR 초안 생성 완료", out)
        self.assertIn("--- PR Title ---", out)
        self.assertIn("--- PR Body ---", out)
        self.assertIn("## Why", out)
        self.assertIn("## What", out)
        self.assertIn("## How to Test", out)


if __name__ == "__main__":
    unittest.main()

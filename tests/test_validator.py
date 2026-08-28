"""Tests for Output Validator module."""

import unittest
from ai_gitgen.validator import OutputValidator


class TestOutputValidator(unittest.TestCase):
    def setUp(self):
        self.validator = OutputValidator(commit_max_title=72, commit_rec_title=50, pr_max_title=80)

    def test_validate_commit_standard(self):
        raw = """feat: AI 기반 Git 커밋 및 PR 생성기 추가

- git status와 diff 정보를 수집하여 AI 입력으로 제공
- 안전 모드(Safe Mode)를 통한 민감정보 마스킹 처리"""
        validated = self.validator.validate_commit(raw)
        self.assertTrue(validated.is_valid)
        self.assertEqual(validated.title, "feat: AI 기반 Git 커밋 및 PR 생성기 추가")
        self.assertIn("- git status와 diff", validated.body)

    def test_validate_commit_long_title(self):
        long_title = "feat: " + "a" * 80
        raw = f"{long_title}\n\n- 내용"
        validated = self.validator.validate_commit(raw)
        self.assertLessEqual(len(validated.title), 72)
        self.assertTrue(validated.title.endswith("..."))

    def test_validate_commit_missing_prefix(self):
        raw = "Git 커밋 생성기 로직 구현\n\n- 로직 추가"
        validated = self.validator.validate_commit(raw)
        self.assertTrue(validated.title.startswith("feat: "))

    def test_validate_pr_structure(self):
        raw = """TITLE: feat: 커밋/PR 자동 생성 기능 추가
BODY:
## Why
- 팀 협업 시 커밋 메시지와 PR 설명 작성 시간을 단축하기 위함

## What
- Git status, diff 수집 로직 추가
- CLI 명령어 commit, pr 추가

## How to Test
- python main.py commit 실행 후 출력 결과 확인
- python main.py pr 실행 후 섹션 확인"""
        validated = self.validator.validate_pr(raw)
        self.assertTrue(validated.is_valid)
        self.assertEqual(validated.title, "feat: 커밋/PR 자동 생성 기능 추가")
        self.assertIn("## Why", validated.body)
        self.assertIn("## What", validated.body)
        self.assertIn("## How to Test", validated.body)
        self.assertGreaterEqual(len(validated.sections["Why"]), 1)
        self.assertGreaterEqual(len(validated.sections["What"]), 1)
        self.assertGreaterEqual(len(validated.sections["How to Test"]), 1)

    def test_validate_pr_missing_sections_auto_repair(self):
        raw = """TITLE: feat: 신규 기능 추가
BODY:
단순 내용만 작성된 불완전한 텍스트입니다."""
        validated = self.validator.validate_pr(raw)
        self.assertTrue(validated.is_valid)
        self.assertIn("## Why", validated.body)
        self.assertIn("## What", validated.body)
        self.assertIn("## How to Test", validated.body)


if __name__ == "__main__":
    unittest.main()

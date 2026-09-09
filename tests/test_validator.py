"""Tests for Output Validator module."""

import unittest
from ai_gitgen.validator import OutputValidator


class TestOutputValidator(unittest.TestCase): #validator (AI 생성 답변을 자동 수정 및 검사해주는 기능)가 제대로 동작해주는 지 체크해줌
    def setUp(self):
        self.validator = OutputValidator(commit_max_title=72, commit_rec_title=50, pr_max_title=80) #커밋 제목 권장 50자, 최대 72자, PR제목 최대 80자 설정

    def test_validate_commit_standard(self): #정상적인 커밋 메시지가 잘 파싱되는지 체크해주는 메소드
        raw = """feat: AI 기반 Git 커밋 및 PR 생성기 추가

- git status와 diff 정보를 수집하여 AI 입력으로 제공
- 안전 모드(Safe Mode)를 통한 민감정보 마스킹 처리"""
        validated = self.validator.validate_commit(raw)
        self.assertTrue(validated.is_valid)
        self.assertEqual(validated.title, "feat: AI 기반 Git 커밋 및 PR 생성기 추가")
        self.assertIn("- git status와 diff", validated.body)

    def test_validate_commit_long_title(self): #커밋 제목이 너무 길 때 제대로 잘라주는지 테스트
        long_title = "feat: " + "a" * 80 # feat= aaaaaa... (총 80자) 같은 기다란 제목을 만들어줌
        raw = f"{long_title}\n\n- 내용"
        validated = self.validator.validate_commit(raw) #raw 가 validator를 거치고 나서
        self.assertLessEqual(len(validated.title), 72) #72자를 안 넘는지 체크
        self.assertTrue(validated.title.endswith("...")) # ...로 잘 잘라놓은 표시가 있는지 검증

    def test_validate_commit_missing_prefix(self): # feat: 같은 prefix가 없으면 자동으로 붙는지
        raw = "Git 커밋 생성기 로직 구현\n\n- 로직 추가" #prefix가 없는 문구가
        validated = self.validator.validate_commit(raw) #validator를 거친 뒤에
        self.assertTrue(validated.title.startswith("feat: ")) #prefix가 달렸는지 체크

    def test_validate_pr_structure(self): #생성된 PR 메시지의 구조 검증
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
        self.assertIn("## How to Test", validated.body) #각각 항목 제목이 잘 들어가있는지 본다.
        self.assertGreaterEqual(len(validated.sections["Why"]), 1)
        self.assertGreaterEqual(len(validated.sections["What"]), 1)
        self.assertGreaterEqual(len(validated.sections["How to Test"]), 1) #각각 Why, What, How to Test 섹션 뒤에 한 글자라도 더 들어가 있는지 본다

    def test_validate_pr_missing_sections_auto_repair(self): #PR 섹션이 빠져 있어도 자동으로 복구가 되는지
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

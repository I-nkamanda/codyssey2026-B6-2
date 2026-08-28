"""Prompt generation and templating for Commit and PR generation."""

from typing import List, Optional
from ai_gitgen.git_collector import FileStatus, GitChanges


class PromptBuilder:
    def __init__(self, language: str = "ko", convention: str = "conventional_commits", custom_instructions: str = ""):
        self.language = language
        self.convention = convention
        self.custom_instructions = custom_instructions

    def build_commit_prompt(self, changes: GitChanges, sanitized_diff: str) -> str:
        files_summary = ", ".join([f.path for f in changes.changed_files[:5]])
        if len(changes.changed_files) > 5:
            files_summary += f" 외 {len(changes.changed_files) - 5}개 파일"

        lang_instruction = (
            "커밋 메시지는 명확하고 정결한 한국어로 작성하세요. (단, type 접두어 'feat:', 'fix:' 등은 영문 사용)"
            if self.language == "ko"
            else "Write the commit message in concise English."
        )

        convention_instruction = """[커밋 컨벤션 가이드]
- Conventional Commits 형식: `<type>: <제목>`
- 타입: feat(기능 추가), fix(버그 수정), docs(문서), style(포맷팅), refactor(리팩토링), test(테스트), chore(빌드/설정), perf(성능 개선)
- 제목(1번째 줄): 마침표(.)를 찍지 않고 명령형/개조식으로 50자 이내(최대 72자)로 간결하게 작성
- 제목과 본문 사이에는 반드시 빈 줄 1개 포함
- 본문(선택/권장):
  * 변경된 주요 파일/모듈(1~3개) 언급
  * 핵심 변경 사항을 2~4개의 불릿('- ')으로 요약"""

        custom_sec = f"[사용자 정의 규칙]\n{self.custom_instructions}\n" if self.custom_instructions else ""

        prompt = f"""당신은 숙련된 시니어 소프트웨어 엔지니어이자 코드 리뷰어입니다.
아래 제공된 Git 변경 사항(diff 및 파일 목록)을 분석하여 최적의 Git 커밋 메시지를 생성하세요.

{lang_instruction}

{convention_instruction}

{custom_sec}
[Git 변경 파일 목록 ({changes.total_files_changed}개)]
{files_summary}

[Git Diff 내용]
```diff
{sanitized_diff}
```

[출력 형식 규칙]
- 다른 불필요한 서론이나 인사말, 코드블록 기호(```) 없이 바로 커밋 메시지 원문만 출력하세요.
- 첫 줄은 반드시 `<type>: <제목>` 형태여야 합니다.
- 빈 줄 다음 불릿('- ') 목록으로 변경 내용을 요약하세요.
"""
        return prompt.strip()

    def build_pr_prompt(self, changes: GitChanges, sanitized_diff: str) -> str:
        files_summary = "\n".join([f"- {f.path} ({'Staged' if f.is_staged else 'Unstaged/Untracked'})" for f in changes.changed_files[:10]])
        if len(changes.changed_files) > 10:
            files_summary += f"\n- ...외 {len(changes.changed_files) - 10}개 파일"

        lang_instruction = (
            "PR 제목과 본문은 정중하고 명확한 한국어로 작성하세요."
            if self.language == "ko"
            else "Write the PR title and body in clear English."
        )

        custom_sec = f"[사용자 정의 규칙]\n{self.custom_instructions}\n" if self.custom_instructions else ""

        prompt = f"""당신은 오픈소스 프로젝트 및 엔터프라이즈 코드베이스의 테크 리드입니다.
아래 제공된 Git 브랜치 및 변경 사항을 바탕으로 깔끔하고 구조화된 Pull Request(PR) 제목과 본문을 생성하세요.

[현재 브랜치]
{changes.branch}

[변경된 파일 목록]
{files_summary}

[Git Diff 내용]
```diff
{sanitized_diff}
```

{lang_instruction}
{custom_sec}
[필수 요구사항 및 템플릿 구조]
1. PR 제목:
   - 첫 줄에 `<type>: <제목>` 형태로 1줄 작성 (최대 80자 이내)
2. PR 본문:
   - 반드시 아래 3개 섹션 헤더를 정확히 포함해야 합니다:
     ## Why
     ## What
     ## How to Test
   - 각 섹션에는 최소 1개 이상, 가급적 2~4개의 상세한 불릿('- ') 항목을 포함하세요.
   - ## Why: 이번 변경의 배경, 문제점, 도입 목적
   - ## What: 변경된 핵심 기능, 로직 수정, 아키텍처 변화
   - ## How to Test: 환경변수 설정, 실행 명령어, 기대 검증 결과 등 사용자가 직접 테스트해볼 수 있는 구체적 절차

[출력 형식]
반드시 다음 구조로만 출력하세요. 앞뒤 불필요한 메타 설명은 생략하세요:
TITLE: <PR 제목>
BODY:
## Why
- <배경 요약>

## What
- <핵심 변경사항 요약>

## How to Test
- <테스트 및 검증 방법>
"""
        return prompt.strip()

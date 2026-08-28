"""Output verification, validation, and post-processing module."""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


@dataclass
class ValidatedCommit:
    title: str
    body: str
    full_text: str
    is_valid: bool = True
    warnings: List[str] = field(default_factory=list)


@dataclass
class ValidatedPR:
    title: str
    body: str
    sections: Dict[str, List[str]] = field(default_factory=dict)
    full_text: str = ""
    is_valid: bool = True
    warnings: List[str] = field(default_factory=list)


class OutputValidator:
    def __init__(self, commit_max_title: int = 72, commit_rec_title: int = 50, pr_max_title: int = 80):
        self.commit_max_title = commit_max_title
        self.commit_rec_title = commit_rec_title
        self.pr_max_title = pr_max_title

    def clean_markdown_fences(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()
            if len(lines) >= 2:
                # Remove first and last lines
                return "\n".join(lines[1:-1]).strip()
        return text

    def validate_commit(self, raw_text: str) -> ValidatedCommit:
        cleaned = self.clean_markdown_fences(raw_text)
        lines = [line.rstrip() for line in cleaned.splitlines()]

        # Filter leading empty lines
        while lines and not lines[0].strip():
            lines.pop(0)

        if not lines:
            return ValidatedCommit(
                title="chore: 변경 사항 적용",
                body="- 변경 내용 요약",
                full_text="chore: 변경 사항 적용\n\n- 변경 내용 요약",
                is_valid=False,
                warnings=["생성된 커밋 메시지가 비어 있어 기본 템플릿으로 대체되었습니다."]
            )

        title = lines[0].strip()
        body_lines = lines[1:]

        # Filter empty lines at start of body
        while body_lines and not body_lines[0].strip():
            body_lines.pop(0)

        warnings = []

        # Validate title length
        if len(title) > self.commit_max_title:
            warnings.append(f"커밋 제목이 {self.commit_max_title}자를 초과하여 {self.commit_max_title}자로 자릅니다. ({len(title)}자)")
            title = title[:self.commit_max_title - 3] + "..."
        elif len(title) > self.commit_rec_title:
            warnings.append(f"커밋 제목 권장 길이({self.commit_rec_title}자)를 초과했습니다. ({len(title)}자)")

        # Validate Conventional Commits format
        conventional_pattern = re.compile(r'^(feat|fix|docs|style|refactor|test|chore|perf|build|ci|revert)(\([a-zA-Z0-9_\-\./]+\))?:\s*.+', re.IGNORECASE)
        if not conventional_pattern.match(title):
            warnings.append("Conventional Commit 접두어(feat:, fix:, docs: 등)가 누락되어 'feat: ' 접두어를 추가했습니다.")
            title = f"feat: {title}"

        # Clean and ensure bullets in body
        normalized_body_lines = []
        for line in body_lines:
            s_line = line.strip()
            if not s_line:
                normalized_body_lines.append("")
                continue
            if not s_line.startswith(("-", "*", "•")):
                s_line = f"- {s_line}"
            elif s_line.startswith(("*", "•")):
                s_line = f"- {s_line[1:].strip()}"
            normalized_body_lines.append(s_line)

        body = "\n".join(normalized_body_lines).strip()
        if not body:
            body = "- 변경 사항 요약"

        full_text = f"{title}\n\n{body}" if body else title

        return ValidatedCommit(
            title=title,
            body=body,
            full_text=full_text,
            is_valid=True,
            warnings=warnings
        )

    def validate_pr(self, raw_text: str) -> ValidatedPR:
        cleaned = self.clean_markdown_fences(raw_text)
        warnings = []

        title = ""
        body_text = cleaned

        # Check for explicit TITLE: and BODY: tags
        if "TITLE:" in cleaned and "BODY:" in cleaned:
            parts = cleaned.split("BODY:", 1)
            title_part = parts[0]
            body_text = parts[1].strip()
            for line in title_part.splitlines():
                if line.strip().startswith("TITLE:"):
                    title = line.replace("TITLE:", "").strip()
                    break
        elif "TITLE:" in cleaned:
            lines = cleaned.splitlines()
            body_lines = []
            for line in lines:
                if line.strip().startswith("TITLE:"):
                    title = line.replace("TITLE:", "").strip()
                else:
                    body_lines.append(line)
            body_text = "\n".join(body_lines).strip()
        else:
            # First line as title if it starts with conventional commit or #
            lines = [l for l in cleaned.splitlines() if l.strip()]
            if lines:
                first_line = lines[0].strip().lstrip("#").strip()
                if not first_line.lower().startswith("why") and not first_line.lower().startswith("what"):
                    title = first_line
                    body_text = "\n".join(lines[1:]).strip()

        if not title:
            title = "feat: Git 변경 사항 및 신규 기능 추가"

        # Validate title length
        if len(title) > self.pr_max_title:
            warnings.append(f"PR 제목이 {self.pr_max_title}자를 초과하여 자릅니다. ({len(title)}자)")
            title = title[:self.pr_max_title - 3] + "..."

        # Parse and ensure required sections: Why, What, How to Test
        required_sections = ["Why", "What", "How to Test"]
        sections: Dict[str, List[str]] = {sec: [] for sec in required_sections}
        current_section = None

        # Look for section headers (## Why, ### Why, Why:, etc.)
        for line in body_text.splitlines():
            s_line = line.strip()
            matched_sec = None
            for sec in required_sections:
                header_patterns = [
                    f"## {sec}", f"### {sec}", f"#{sec}", f"{sec}:", f"**{sec}**"
                ]
                for p in header_patterns:
                    if s_line.lower().startswith(p.lower()):
                        matched_sec = sec
                        break
                if matched_sec:
                    break

            if matched_sec:
                current_section = matched_sec
                continue

            if current_section and s_line:
                # Add bullet
                bullet_line = s_line
                if not bullet_line.startswith(("-", "*", "•")):
                    bullet_line = f"- {bullet_line}"
                elif bullet_line.startswith(("*", "•")):
                    bullet_line = f"- {bullet_line[1:].strip()}"
                sections[current_section].append(bullet_line)

        # Fill defaults if sections are missing
        if not sections["Why"]:
            warnings.append("Why 섹션이 누락되어 기본 템플릿으로 보정되었습니다.")
            sections["Why"] = [
                "- 변경 사항을 체계적으로 문서화하고 코드베이스의 유지보수성을 향상시키기 위해 개발되었습니다."
            ]

        if not sections["What"]:
            warnings.append("What 섹션이 누락되어 기본 템플릿으로 보정되었습니다.")
            sections["What"] = [
                "- Git 변경 사항(status, diff) 수집 및 AI API 기반 분석 로직 추가",
                "- 커밋 메시지 및 PR 템플릿 자동 생성 기능 구현"
            ]

        if not sections["How to Test"]:
            warnings.append("How to Test 섹션이 누락되어 기본 템플릿으로 보정되었습니다.")
            sections["How to Test"] = [
                "- 환경변수 설정: export AI_API_KEY=\"YOUR_KEY\"",
                "- 커밋 메시지 생성 실행: python main.py commit",
                "- PR 초안 생성 실행: python main.py pr",
                "- Why, What, How to Test 구조 및 길이 규칙 부합 여부 확인"
            ]

        # Reconstruct normalized body
        body_parts = []
        for sec in required_sections:
            body_parts.append(f"## {sec}")
            body_parts.extend(sections[sec])
            body_parts.append("")

        normalized_body = "\n".join(body_parts).strip()
        full_text = f"{title}\n\n{normalized_body}"

        return ValidatedPR(
            title=title,
            body=normalized_body,
            sections=sections,
            full_text=full_text,
            is_valid=True,
            warnings=warnings
        )

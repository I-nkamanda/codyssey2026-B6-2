"""Safety, sanitization, and masking module for Git diffs."""

import re
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional


@dataclass
class SafetyReport:
    is_safe_mode: bool
    masked_items_count: int = 0
    masked_details: Dict[str, int] = field(default_factory=dict)
    excluded_files: List[str] = field(default_factory=list)
    original_lines: int = 0
    sanitized_lines: int = 0
    is_truncated: bool = False
    truncation_reason: Optional[str] = None


class SafetyFilter:
    # Sensitive file patterns to exclude entirely
    SENSITIVE_FILE_PATTERNS = [
        re.compile(r'^\.env(\..+)?$', re.IGNORECASE),
        re.compile(r'.*\.(pem|key|pkcs12|pfx|p12|keystore)$', re.IGNORECASE),
        re.compile(r'.*id_rsa(\..+)?$', re.IGNORECASE),
        re.compile(r'.*id_ed25519(\..+)?$', re.IGNORECASE),
        re.compile(r'credentials\.json$', re.IGNORECASE),
        re.compile(r'service-account.*\.json$', re.IGNORECASE),
        re.compile(r'token\.json$', re.IGNORECASE),
        re.compile(r'.*\.lock$', re.IGNORECASE),
        re.compile(r'package-lock\.json$', re.IGNORECASE),
        re.compile(r'.*\.min\.(js|css)$', re.IGNORECASE),
    ]

    # Masking patterns: (Regex Pattern, Replacement Label)
    MASKING_RULES = [
        # OpenAI API Key
        (re.compile(r'\bsk-[a-zA-Z0-9_\-]{20,}\b'), '[MASKED_OPENAI_KEY]'),
        # Anthropic API Key
        (re.compile(r'\bsk-ant-[a-zA-Z0-9_\-]{20,}\b'), '[MASKED_ANTHROPIC_KEY]'),
        # Google API Key
        (re.compile(r'\bAIza[0-9A-Za-z_\-]{30,45}\b'), '[MASKED_GOOGLE_KEY]'),
        # GitHub Personal Access Token
        (re.compile(r'\b(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,}\b'), '[MASKED_GITHUB_TOKEN]'),
        (re.compile(r'\bgithub_pat_[a-zA-Z0-9_]{22,}\b'), '[MASKED_GITHUB_TOKEN]'),
        # AWS Access Key ID
        (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), '[MASKED_AWS_ACCESS_KEY]'),
        # AWS Secret Key
        (re.compile(r'(aws_secret_access_key\s*[:=]\s*["\']?)[a-zA-Z0-9/+=]{40}(["\']?)', re.IGNORECASE), r'\1[MASKED_AWS_SECRET_KEY]\2'),
        # Slack Token
        (re.compile(r'\bxox[baprs]-[0-9a-zA-Z]{10,48}\b'), '[MASKED_SLACK_TOKEN]'),
        # JWT Token
        (re.compile(r'\beyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\b'), '[MASKED_JWT_TOKEN]'),
        # Private Key blocks
        (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----'), '[MASKED_PRIVATE_KEY_BLOCK]'),
        # Generic Secret / Password variables in code or config
        (re.compile(r'((?:password|passwd|secret|api_key|apikey|auth_token|access_token|private_key)\s*[:=]\s*["\'])([^"\']{4,})(["\'])', re.IGNORECASE), r'\1[MASKED_SECRET]\3'),
        # Bearer tokens in headers
        (re.compile(r'(Bearer\s+)[a-zA-Z0-9._~+\-/]{16,}', re.IGNORECASE), r'\1[MASKED_BEARER_TOKEN]'),
        # Emails
        (re.compile(r'\b[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-.]+\b'), '[MASKED_EMAIL]'),
        # Phone Numbers (Korean formats)
        (re.compile(r'\b01[016789]-?\d{3,4}-?\d{4}\b'), '[MASKED_PHONE]'),
        # Korean Resident Registration Numbers (RRN)
        (re.compile(r'\b\d{6}-?[1-4]\d{6}\b'), '[MASKED_RRN]'),
    ]

    def __init__(self, max_diff_files: int = 10, max_diff_lines: int = 200):
        self.max_diff_files = max_diff_files
        self.max_diff_lines = max_diff_lines

    def is_sensitive_file(self, filename: str) -> bool:
        base = filename.split('/')[-1]
        for pattern in self.SENSITIVE_FILE_PATTERNS:
            if pattern.search(filename) or pattern.search(base):
                return True
        return False

    def sanitize_diff(self, diff_text: str, safe_mode: bool = True) -> Tuple[str, SafetyReport]:
        original_lines = len(diff_text.splitlines()) if diff_text else 0
        report = SafetyReport(
            is_safe_mode=safe_mode,
            original_lines=original_lines,
            sanitized_lines=original_lines
        )

        if not safe_mode or not diff_text:
            return diff_text, report

        # 1. Parse diff into file chunks
        file_chunks: List[Tuple[str, List[str]]] = []
        current_file = "unknown"
        current_lines: List[str] = []

        for line in diff_text.splitlines():
            if line.startswith("diff --git") or line.startswith("--- /dev/null") or line.startswith("+++ b/"):
                if line.startswith("diff --git"):
                    if current_lines:
                        file_chunks.append((current_file, current_lines))
                        current_lines = []
                    parts = line.split(" ")
                    if len(parts) >= 4:
                        current_file = parts[3].lstrip("b/")
                    else:
                        current_file = line
                elif line.startswith("+++ b/"):
                    current_file = line[6:].strip()
            current_lines.append(line)

        if current_lines:
            file_chunks.append((current_file, current_lines))

        # 2. Filter sensitive files
        filtered_chunks: List[Tuple[str, List[str]]] = []
        for filename, lines in file_chunks:
            if self.is_sensitive_file(filename):
                report.excluded_files.append(filename)
                placeholder = [
                    f"diff --git a/{filename} b/{filename}",
                    f"[SAFE_MODE] 파일 '{filename}'은 민감정보 또는 대용량 파일 규칙에 의해 전송에서 제외되었습니다."
                ]
                filtered_chunks.append((filename, placeholder))
            else:
                filtered_chunks.append((filename, lines))

        # 3. Limit number of files
        if len(filtered_chunks) > self.max_diff_files:
            excluded_count = len(filtered_chunks) - self.max_diff_files
            filtered_chunks = filtered_chunks[:self.max_diff_files]
            report.is_truncated = True
            report.truncation_reason = f"최대 파일 수({self.max_diff_files}개) 초과로 {excluded_count}개 파일 생략"

        # 4. Apply Regex Masking
        sanitized_lines: List[str] = []
        masked_counts: Dict[str, int] = {}
        total_masked = 0

        for filename, lines in filtered_chunks:
            for line in lines:
                sanitized_line = line
                for pattern, replacement in self.MASKING_RULES:
                    matches = pattern.findall(sanitized_line)
                    if matches:
                        count = len(matches)
                        total_masked += count
                        label = replacement if isinstance(replacement, str) else "RULE"
                        masked_counts[label] = masked_counts.get(label, 0) + count
                        sanitized_line = pattern.sub(replacement, sanitized_line)
                sanitized_lines.append(sanitized_line)

        # 5. Limit number of lines
        if len(sanitized_lines) > self.max_diff_lines:
            truncated_count = len(sanitized_lines) - self.max_diff_lines
            sanitized_lines = sanitized_lines[:self.max_diff_lines]
            sanitized_lines.append(
                f"\n... [SAFE_MODE] diff가 최대 전송 제한({self.max_diff_lines}줄)을 초과하여 이후 {truncated_count}줄이 생략되었습니다."
            )
            report.is_truncated = True
            if report.truncation_reason:
                report.truncation_reason += f", 최대 줄 수({self.max_diff_lines}줄) 초과"
            else:
                report.truncation_reason = f"최대 줄 수({self.max_diff_lines}줄) 초과로 {truncated_count}줄 생략"

        sanitized_diff = "\n".join(sanitized_lines)
        report.masked_items_count = total_masked
        report.masked_details = masked_counts
        report.sanitized_lines = len(sanitized_lines)

        return sanitized_diff, report

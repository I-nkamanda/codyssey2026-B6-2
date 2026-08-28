"""Command Line Interface (CLI) entrypoint for AI Git Generator."""

import argparse
import sys
import os
from typing import Optional, List

from ai_gitgen.config import Config
from ai_gitgen.git_collector import GitCollector
from ai_gitgen.safety import SafetyFilter
from ai_gitgen.prompts import PromptBuilder
from ai_gitgen.validator import OutputValidator
from ai_gitgen.ai_client import (
    AIClient,
    AIClientError,
    MissingApiKeyError,
    AuthenticationError,
    RateLimitError
)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-gitgen",
        description="AI 기반 Git 커밋 메시지 및 Pull Request(PR) 초안 자동 생성 CLI 도구"
    )

    # Subparsers for commands: commit, pr
    subparsers = parser.add_subparsers(dest="command", help="실행할 명령어 (commit 또는 pr)")

    # Common arguments for subcommands
    def add_common_args(sub):
        sub.add_argument("--model", type=str, default=None, help="사용할 AI 모델명 (기본값: gpt-4o-mini)")
        sub.add_argument("--temperature", type=float, default=None, help="생성 다양성 (기본값: 0.2)")
        sub.add_argument("--max-tokens", "--max_tokens", dest="max_tokens", type=int, default=None, help="최대 생성 토큰 수 (기본값: 1000)")
        
        # Safe mode flags
        safe_group = sub.add_mutually_exclusive_group()
        safe_group.add_argument("--safe-mode", dest="safe_mode", action="store_true", default=None, help="안전 모드 활성화 (민감정보 마스킹, diff 제한)")
        safe_group.add_argument("--no-safe-mode", dest="safe_mode", action="store_false", help="안전 모드 비활성화")
        
        sub.add_argument("--language", "-l", type=str, default=None, choices=["ko", "en"], help="출력 언어 (기본값: ko)")
        sub.add_argument("--convention", type=str, default=None, help="커밋/PR 컨벤션 규칙")
        sub.add_argument("--config", type=str, default=None, help="설정 파일 경로 (.ai-gitgen.yml)")
        sub.add_argument("--dry-run", "--mock", dest="mock_mode", action="store_true", help="API 호출 없이 모의(Mock) 데이터로 테스트 실행")

    # Commit command
    commit_parser = subparsers.add_parser("commit", help="Git 변경 사항을 기반으로 커밋 메시지 생성")
    add_common_args(commit_parser)

    # PR command
    pr_parser = subparsers.add_parser("pr", help="Git 변경 사항을 기반으로 PR 제목 및 본문 초안 생성")
    add_common_args(pr_parser)

    return parser


def run_cli(args: Optional[List[str]] = None) -> int:
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 0

    # 1. Load Configuration
    config = Config.load(config_path=parsed_args.config)
    if parsed_args.model:
        config.model = parsed_args.model
    if parsed_args.temperature is not None:
        config.temperature = parsed_args.temperature
    if parsed_args.max_tokens is not None:
        config.max_tokens = parsed_args.max_tokens
    if parsed_args.safe_mode is not None:
        config.safe_mode = parsed_args.safe_mode
    if parsed_args.language:
        config.language = parsed_args.language
    if parsed_args.convention:
        config.convention = parsed_args.convention

    # 2. Collect Git Changes
    collector = GitCollector()
    changes = collector.collect_changes()

    if not changes.is_repo:
        print(f"[ERROR] {changes.error_message}", file=sys.stderr)
        return 1

    if not changes.has_changes:
        cmd_korean = "커밋 메시지를" if parsed_args.command == "commit" else "PR 초안을"
        print(f"[INFO] 변경 사항이 없습니다. {cmd_korean} 생성하지 않고 종료합니다.")
        return 0

    # Show branch info for PR
    if parsed_args.command == "pr":
        print(f"[INFO] 현재 브랜치: {changes.branch}")

    print(f"[INFO] Git status 수집 완료: {changes.total_files_changed}개 파일 변경 감지")
    print(f"[INFO] Git diff 수집 완료: {changes.total_diff_lines}줄")

    # 3. Apply Safety Filter
    safety_filter = SafetyFilter(
        max_diff_files=config.max_diff_files,
        max_diff_lines=config.max_diff_lines
    )
    sanitized_diff, safety_report = safety_filter.sanitize_diff(
        changes.diff_text,
        safe_mode=config.safe_mode
    )

    if config.safe_mode and safety_report.masked_items_count > 0:
        print(f"[INFO] [SAFE_MODE] 민감정보 {safety_report.masked_items_count}건 마스킹 처리 완료")
    if config.safe_mode and safety_report.excluded_files:
        print(f"[INFO] [SAFE_MODE] 민감 파일 {len(safety_report.excluded_files)}개 전송 제외 ({', '.join(safety_report.excluded_files)})")
    if config.safe_mode and safety_report.is_truncated:
        print(f"[INFO] [SAFE_MODE] diff 제한 적용: {safety_report.truncation_reason}")

    # 4. Build Prompt
    prompt_builder = PromptBuilder(
        language=config.language,
        convention=config.convention,
        custom_instructions=config.custom_instructions
    )

    if parsed_args.command == "commit":
        prompt = prompt_builder.build_commit_prompt(changes, sanitized_diff)
        task_type = "commit"
    else:
        prompt = prompt_builder.build_pr_prompt(changes, sanitized_diff)
        task_type = "pr"

    # 5. AI API Call
    ai_client = AIClient(
        api_key=config.api_key,
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        provider=config.provider,
        api_base_url=config.api_base_url,
        mock_mode=parsed_args.mock_mode
    )

    print("[INFO] AI API 요청 중...")
    try:
        response = ai_client.generate(prompt, task_type=task_type)
    except MissingApiKeyError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    except AuthenticationError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    except RateLimitError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    except AIClientError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] 예기치 못한 시스템 오류: {str(e)}", file=sys.stderr)
        return 1

    # 6. Validate and Format Output
    validator = OutputValidator(
        commit_max_title=config.commit_max_title_len,
        commit_rec_title=config.commit_rec_title_len,
        pr_max_title=config.pr_max_title_len
    )

    if parsed_args.command == "commit":
        validated_commit = validator.validate_commit(response.content)
        print("[DONE] 커밋 메시지 생성 완료\n")
        print("-- Commit Message --")
        print(validated_commit.title)
        if validated_commit.body:
            print()
            print(validated_commit.body)
    else:
        validated_pr = validator.validate_pr(response.content)
        print("[DONE] PR 초안 생성 완료\n")
        print("--- PR Title ---")
        print(validated_pr.title)
        print("\n--- PR Body ---")
        print(validated_pr.body)

    return 0


def main():
    sys.exit(run_cli())


if __name__ == "__main__":
    main()

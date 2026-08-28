"""AI API Client supporting OpenAI-compatible endpoints, Google Gemini REST API, and offline mock."""

import json
import os
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional, Dict, Any


class AIClientError(Exception):
    """Base exception for AI Client errors."""
    pass


class MissingApiKeyError(AIClientError):
    """Raised when API Key is not configured."""
    pass


class AuthenticationError(AIClientError):
    """Raised when API Key is invalid or expired."""
    pass


class RateLimitError(AIClientError):
    """Raised when API rate limit or quota is exceeded."""
    pass


@dataclass
class AIResponse:
    content: str
    model: str
    tokens_used: Optional[int] = None
    call_count: int = 1


class AIClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        max_tokens: int = 1000,
        provider: str = "openai",
        api_base_url: Optional[str] = None,
        mock_mode: bool = False
    ):
        self.api_key = api_key or os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.provider = provider.lower()
        self.api_base_url = api_base_url
        self.mock_mode = mock_mode or (self.api_key in ("mock", "test", "dummy"))
        self.call_count = 0

    def generate(self, prompt: str, task_type: str = "commit") -> AIResponse:
        """Generates AI completion for the given prompt."""
        self.call_count += 1

        if self.mock_mode:
            return self._generate_mock(prompt, task_type)

        if not self.api_key:
            raise MissingApiKeyError(
                "AI_API_KEY 환경변수가 설정되지 않았습니다.\n# 예) export AI_API_KEY=\"YOUR_KEY\""
            )

        if self.provider == "gemini" or (self.api_key.startswith("AIza") and not self.api_base_url):
            return self._call_gemini_api(prompt)
        else:
            return self._call_openai_api(prompt)

    def _call_openai_api(self, prompt: str) -> AIResponse:
        base_url = (self.api_base_url or "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "AI-Git-Generator/1.0"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a professional software engineer specialized in Git workflows and code reviews."},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                content = res_json["choices"][0]["message"]["content"].strip()
                tokens = res_json.get("usage", {}).get("total_tokens")
                return AIResponse(
                    content=content,
                    model=self.model,
                    tokens_used=tokens,
                    call_count=self.call_count
                )
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            if e.code in (401, 403):
                raise AuthenticationError(f"AI API 인증 실패 (HTTP {e.code}): API Key가 유효한지 확인하세요. [{error_body}]")
            elif e.code == 429:
                raise RateLimitError(f"AI API 요청 제한 초과 (HTTP 429): 사용량 한도(Quota) 또는 Rate Limit을 확인하세요. [{error_body}]")
            else:
                raise AIClientError(f"AI API 서버 오류 (HTTP {e.code}): {error_body}")
        except urllib.error.URLError as e:
            raise AIClientError(f"네트워크 연결 오류: {e.reason}")
        except Exception as e:
            raise AIClientError(f"API 요청 중 예기치 못한 오류 발생: {str(e)}")

    def _call_gemini_api(self, prompt: str) -> AIResponse:
        model_name = self.model if self.model.startswith("gemini") else "gemini-1.5-flash"
        base_url = (self.api_base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        url = f"{base_url}/models/{model_name}:generateContent?key={self.api_key}"

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens
            }
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                candidate = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                tokens = res_json.get("usageMetadata", {}).get("totalTokenCount")
                return AIResponse(
                    content=candidate,
                    model=model_name,
                    tokens_used=tokens,
                    call_count=self.call_count
                )
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            if e.code in (401, 403):
                raise AuthenticationError(f"Gemini API 인증 실패 (HTTP {e.code}): API Key가 유효한지 확인하세요. [{error_body}]")
            elif e.code == 429:
                raise RateLimitError(f"Gemini API 요청 제한 초과 (HTTP 429): Quota 제한을 확인하세요. [{error_body}]")
            else:
                raise AIClientError(f"Gemini API 서버 오류 (HTTP {e.code}): {error_body}")
        except urllib.error.URLError as e:
            raise AIClientError(f"네트워크 연결 오류: {e.reason}")
        except Exception as e:
            raise AIClientError(f"Gemini API 요청 중 오류 발생: {str(e)}")

    def _generate_mock(self, prompt: str, task_type: str) -> AIResponse:
        """Generates a realistic mock completion for offline testing/verification."""
        if task_type == "commit":
            mock_content = """feat: Git 변경 사항 기반 커밋 메시지 자동 생성 기능 추가

- git diff 결과를 수집해 AI 입력 컨텍스트로 전달하도록 구현
- 커밋 메시지 템플릿(feat/fix 등) 생성 규칙 적용
- API Key 미설정 시 안내 메시지 및 에러 처리 개선"""
        else:
            mock_content = """TITLE: feat: 커밋/PR 자동 생성 기능 추가
BODY:
## Why
- 팀 협업 시 커밋 메시지와 PR 설명 작성에 시간이 소요되어 자동 생성 도구가 필요했습니다.
- Git 변경 사항을 기반으로 일관된 형식의 요약 텍스트를 생성해 리뷰 효율을 높이고자 했습니다.

## What
- git status, git diff 결과를 수집해 AI 입력 컨텍스트로 전달하는 로직 추가
- 커밋 메시지 자동 생성 기능(python main.py commit) 구현
- PR 제목/본문 자동 생성 기능(python main.py pr) 및 템플릿 적용
- API Key 누락/요청 실패 시 에러 메시지 및 예외 처리 개선

## How to Test
- 환경변수 설정: export AI_API_KEY="YOUR_KEY"
- 커밋 메시지 생성: python main.py commit
- PR 초안 생성: python main.py pr
- 결과로 출력된 PR 본문이 Why/What/How to Test 구조와 길이 규칙을 만족하는지 확인"""

        return AIResponse(
            content=mock_content,
            model=f"{self.model}-mock",
            tokens_used=150,
            call_count=self.call_count
        )

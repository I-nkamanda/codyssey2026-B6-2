"""Tests for AI Client module."""

import unittest #unittest 를 불러온다.
import os
from ai_gitgen.ai_client import (
    AIClient,
    MissingApiKeyError,
    AIResponse
)


class TestAIClient(unittest.TestCase):
    def test_missing_api_key(self): #API 키가 없는 경우를 테스트하는 함수
        env_backup = {k: os.environ.pop(k, None) for k in ["AI_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"]} #API 키 환경 변수를 제거하고 백업
        try:
            client = AIClient(api_key=None, mock_mode=False) #AIClient를 생성할 때 api_key를 None으로 설정 & 실제 상황
            with self.assertRaises(MissingApiKeyError): #API 키가 없는 경우 MissingApiKeyError가 발생해야 함
                client.generate("Test prompt") # "Test prompt"를 사용하여 generate 메서드를 호출
        finally:
            for k, v in env_backup.items(): #k는 환경 변수 이름, v는 백업된 값
                if v is not None:
                    os.environ[k] = v #백업한 환경 변수를 복원

    def test_mock_mode_commit(self): #mock mode에서 commit 테스트
        client = AIClient(api_key="mock", mock_mode=True) #mock 모드에서 api_key="mock"으로 설정한 채로 AIClient를 생성
        res = client.generate("Commit prompt", task_type="commit") # "Commit prompt"를 사용하여 generate 메서드를 호출
        self.assertIsInstance(res, AIResponse) #그렇게 나온 res가 AIResponse 인스턴스인지 확인
        self.assertEqual(res.call_count, 1) #호출 횟수가 1인지 확인한다. 왜 그러냐면 mock 모드에서는 실제 API 호출이 일어나지 않기 때문에, 호출 횟수가 1이어야 함 (실제 상황처럼 반복 호출 및 timeout 같은 게 없다는 의미)
        self.assertIn("feat:", res.content) #response content에 "feat:"가 포함되어 있는지 확인

    def test_mock_mode_pr(self): #mock mode에서 Pull request 테스트함
        client = AIClient(api_key="mock", mock_mode=True) #mock 모드에서 api_key="mock"으로 설정한 채로 AIClient를 생성
        res = client.generate("PR prompt", task_type="pr") # "PR prompt"를 사용하여 generate 메서드를 호출
        self.assertIsInstance(res, AIResponse) 
        self.assertEqual(res.call_count, 1) 
        self.assertIn("TITLE:", res.content) #response content에 "TITLE:"가 포함되어 있는지 확인
        self.assertIn("## Why", res.content) #response content에 "## Why"가 포함되어 있는지 확인
        self.assertIn("## What", res.content) #response content에 "## What"가 포함되어 있는지 확인₩
        self.assertIn("## How to Test", res.content)


if __name__ == "__main__":
    unittest.main()

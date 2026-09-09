"""Tests for CLI module."""

import unittest
import tempfile
import subprocess
import os
import shutil
import io
from contextlib import redirect_stdout, redirect_stderr

from ai_gitgen.cli import run_cli


class TestCLI(unittest.TestCase): #TestCLI 클래스는 unittest.TestCase를 상속받아 CLI 모듈의 테스트를 수행하는 클래스입니다.
    def setUp(self): #셋업 메서드는 각 테스트 메서드가 실행되기 전에 호출되며, 테스트 환경을 설정한다. 여기서는 임시 디렉토리를 생성하고 현재 작업 디렉토리를 변경한다.
        self.test_dir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd() #현재 작업 디렉토리를 저장한다. cwd는 "current working directory"의 약자.
        os.chdir(self.test_dir) #위에 생성산 디렉토리로 change directory

    def tearDown(self): #테스트를 마친 뒤에 테스트 환경을 정리하는 메서드
        os.chdir(self.orig_cwd) #원레 디렉토리로 돌아가고
        shutil.rmtree(self.test_dir, ignore_errors=True) #tree self.test_dir를 제거하고, 수반되는 에러 메시지는 무시한다.

    def test_cli_outside_repo(self): #Git 저장소 외부에서 CLI를 실행할 때의 동작을 테스트하는 메서드
        buf_err = io.StringIO() #버퍼 에러를 저장할 StringIO 객체를 생성
        with redirect_stderr(buf_err): #redirect_stderr 컨텍스트 매니저를 사용하여 표준 에러 출력을 buf_err로 리디렉션한다.
            code = run_cli(["commit"]) #run_cli 함수를 호출하여 "commit" 명령을 실행하고, 반환된 종료 코드를 code 변수에 저장한다.
        self.assertEqual(code, 1) #종료 코드가 1인지 확인.
        self.assertIn("Git이 초기화된 프로젝트 루트 디렉토리가 아닙니다", buf_err.getvalue()) # buf_err에 저장된 에러 메시지에 "Git이 초기화된 프로젝트 루트 디렉토리가 아닙니다"가 포함되어 있는지 확인한다.

    def test_cli_no_changes(self): #Git 저장소 내에서 변경 사항이 없는 상태에서 CLI를 실행할 때의 동작을 테스트하는 메서드
        subprocess.run(["git", "init", "-b", "main"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) #subprocess.run을 사용하여 Git 저장소를 초기화하고, 출력은 DEVNULL로 무시한다.
        buf_out = io.StringIO() #아웃 버퍼 객체를 만들고
        with redirect_stdout(buf_out): #redirect_stdout 컨텍스트 매니저를 사용하여 표준 출력을 buf_out로 리디렉션한다.
            code = run_cli(["commit"]) #commit을 실행하고 종료 코드를 code에 저장한다.
        self.assertEqual(code, 0) #종료 코드가 0인지 확인
        self.assertIn("변경 사항이 없습니다", buf_out.getvalue()) #buf_out에 저장된 출력 메시지에 문자열 "변경 사항이 없습니다"가 포함되어 있는지 확인

    def test_cli_missing_api_key(self): #API 키 미설정시 CLI 동작을 테스트하는 메서드
        subprocess.run(["git", "init", "-b", "main"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) #Git 저장소를 초기화하고, 출력은 DEVNULL로 무시한다.
        # Create a file
        with open("hello.py", "w") as f: #print("test")\n 이라는 내용을 가진 hello.py 파일을 생성한다.
            f.write("print('test')\n")

        # Ensure AI_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY are unset
        env_backup = {
            k: os.environ.pop(k, None) for k in ["AI_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"]
        } #백업 환경변수를 미리 .pop()으로 env_backup에 저장하고, 환경변수에서 제거한다. (즉, API 키 환경 변수를 제거하고 백업)
        try:
            buf_err = io.StringIO() #에러 버퍼 객체를 만들고
            with redirect_stderr(buf_err):
                code = run_cli(["commit"]) #CLI에서 commit 명령 실행 후에
            self.assertEqual(code, 1) #종료 코드가 1인지 확인 후에
            self.assertIn("AI_API_KEY 환경변수가 설정되지 않았습니다", buf_err.getvalue()) #buf_err에 저장된 출력 메시지에 문자열 "AI_API_KEY 환경변수가 설정되지 않았습니다"가 포함되어 있는지 확인
        finally: #위의 일들을 다 마치고
            for k, v in env_backup.items():
                if v is not None:
                    os.environ[k] = v #API 키 환경 변수를 복원한다.

    def test_cli_mock_commit(self): #mock 모드에서 commit 테스트
        subprocess.run(["git", "init", "-b", "main"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) #Git 저장소를 초기화하고, 출력은 DEVNULL로 무시한다.
        with open("hello.py", "w") as f: #또 hello.py 파일을 생성하고
            f.write("print('test')\n")

        buf_out = io.StringIO()
        with redirect_stdout(buf_out):
            code = run_cli(["commit", "--mock"]) #이번에는 commit 명령을 mock 모드에서 실행하고 종료 코드를 code에 저장한다.
        self.assertEqual(code, 0) #성공 체크
        out = buf_out.getvalue() #buf_out에 저장된 출력 메시지를 out 변수에 저장한다.
        self.assertIn("[INFO] Git status 수집 완료", out)
        self.assertIn("[INFO] AI API 요청 중...", out)
        self.assertIn("[DONE] 커밋 메시지 생성 완료", out)
        self.assertIn("-- Commit Message --", out)
        self.assertIn("feat:", out)
            # 생성된 커밋 메세지에 원래 나오기로 예정되어 있는 문자엳들이 잘 들어가있는지 체크한다.
    def test_cli_mock_pr(self): #mock 모드에서 Pull request 테스트
        subprocess.run(["git", "init", "-b", "feature/pr-test"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open("hello.py", "w") as f: #또 hello.py 파일을 생성하고
            f.write("print('test')\n")

        buf_out = io.StringIO()
        with redirect_stdout(buf_out):
            code = run_cli(["pr", "--mock"]) #이제는 mock 모드에서 pr 생성
        self.assertEqual(code, 0) #성공을 확인 후에
        out = buf_out.getvalue()
        self.assertIn("[INFO] 현재 브랜치: feature/pr-test", out)
        self.assertIn("[DONE] PR 초안 생성 완료", out)
        self.assertIn("--- PR Title ---", out)
        self.assertIn("--- PR Body ---", out)
        self.assertIn("## Why", out)
        self.assertIn("## What", out)
        self.assertIn("## How to Test", out)
        #PR 메시지에 나오기로 예정되어 있는 문자엳들이 잘 들어가있는지 체크한다. 

if __name__ == "__main__": #직접 이 파일을 실행 시에... 
    unittest.main() #유닛 테스트.main 실행

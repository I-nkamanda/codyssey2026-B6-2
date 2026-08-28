# AI-GitGen 사용 설명서

## 1. 프로그램 소개

AI-GitGen은 현재 Git 저장소의 변경 사항을 분석하여 다음 결과를 생성하는 Python 기반 CLI 도구입니다.

- Conventional Commits 형식의 커밋 메시지
- `Why`, `What`, `How to Test` 구조의 Pull Request(PR) 제목과 본문

프로그램은 Git을 직접 커밋하거나 PR을 생성하지 않습니다. 수집한 변경 사항을 AI에 전달하고, 생성된 문서를 터미널에 출력합니다.

## 2. 요구사항

- Python 3.10 이상
- Git 2.20 이상
- AI API를 사용할 경우 해당 provider의 API 키

OpenAI 호환 API를 사용할 때는 별도의 Python AI SDK가 필요하지 않습니다. HTTP 요청은 Python 표준 라이브러리로 처리합니다.

## 3. 설치

프로젝트 디렉토리로 이동합니다.

```bash
cd B6-2
```

선택적으로 가상환경을 만들고 테스트 의존성을 설치할 수 있습니다.

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 4. API 키 설정

### OpenAI 또는 OpenAI 호환 API

PowerShell에서는 다음과 같이 설정합니다.

```powershell
$env:AI_API_KEY = "your-api-key"
```

명령 프롬프트에서는 다음과 같이 설정합니다.

```cmd
set AI_API_KEY=your-api-key
```

macOS/Linux에서는 다음과 같이 설정합니다.

```bash
export AI_API_KEY="your-api-key"
```

다음 환경변수도 사용할 수 있습니다.

| 환경변수 | 용도 |
| --- | --- |
| `AI_API_KEY` | 기본 API 키 |
| `OPENAI_API_KEY` | OpenAI API 키 |
| `GEMINI_API_KEY` | Gemini API 키 |
| `AI_PROVIDER` | provider 지정 (`openai`, `gemini`) |
| `AI_API_BASE_URL` | OpenAI 호환 API의 기본 URL |
| `AI_MODEL` | 사용할 모델명 |

API 키는 코드에 직접 입력하지 마십시오. API 키 없이 실행하려면 [Mock 모드](#8-mock-모드)를 사용합니다.

### Gemini

```powershell
$env:AI_API_KEY = "your-gemini-api-key"
$env:AI_PROVIDER = "gemini"
```

또는 `GEMINI_API_KEY`를 설정하면 Gemini 키를 기준으로 동작합니다.

### 로컬 또는 OpenAI 호환 서버

```powershell
$env:AI_API_KEY = "local-key"
$env:AI_API_BASE_URL = "http://localhost:11434/v1"
$env:AI_MODEL = "llama3"
```

## 5. 기본 사용법

명령은 반드시 Git 저장소 안에서 실행해야 합니다.

### 커밋 메시지 생성

```bash
python main.py commit
```

출력 결과는 일반적으로 다음과 같은 형식입니다.

```text
feat: 사용자 인증 오류 처리 개선

- 인증 실패 상황의 오류 응답을 정리
- 관련 테스트 케이스 추가
```

커밋 메시지를 생성할 뿐 실제 `git commit`은 실행하지 않습니다.

### PR 초안 생성

```bash
python main.py pr
```

출력 결과에는 PR 제목과 다음 세 섹션으로 구성된 본문이 포함됩니다.

```text
--- PR Title ---
feat: 사용자 인증 개선

--- PR Body ---
## Why
- 변경 목적

## What
- 주요 변경 내용

## How to Test
- 테스트 방법
```

## 6. 실행 옵션

`commit`과 `pr` 명령 모두 다음 옵션을 사용할 수 있습니다.

| 옵션 | 설명 | 기본값 |
| --- | --- | --- |
| `--model` | 사용할 AI 모델명 | `gpt-4o-mini` |
| `--temperature` | 생성 다양성, `0.0`부터 `1.0` 사이 권장 | `0.2` |
| `--max-tokens`, `--max_tokens` | AI 응답의 최대 토큰 수 | `1000` |
| `--safe-mode` | Safe Mode 활성화 | 기본 활성화 |
| `--no-safe-mode` | Safe Mode 비활성화 | 사용하지 않음 |
| `--language`, `-l` | 출력 언어 (`ko` 또는 `en`) | `ko` |
| `--convention` | 사용할 커밋/PR 컨벤션 이름 | `conventional_commits` |
| `--config` | 설정 파일 경로 | `.ai-gitgen.yml` |
| `--dry-run`, `--mock` | API를 호출하지 않고 Mock 결과 사용 | 비활성화 |

예시:

```bash
python main.py commit --language en --model gpt-4o-mini
python main.py pr --temperature 0.4 --max-tokens 1200
python main.py commit --no-safe-mode
python main.py pr --config .ai-gitgen.yml
```

Safe Mode를 끄면 민감정보가 외부 API로 전송될 수 있으므로 꼭 필요한 경우에만 사용하십시오.

## 7. 설정 파일

프로젝트 루트에 `.ai-gitgen.yml` 또는 `.ai-gitgen.yaml`을 만들 수 있습니다.

```yaml
provider: openai
model: gpt-4o-mini
temperature: 0.2
max_tokens: 1000
safe_mode: true
max_diff_files: 10
max_diff_lines: 200
language: ko
convention: conventional_commits
custom_instructions: "제목은 간결하게 작성하고 테스트 내용을 포함하세요."
```

설정값의 적용 우선순위는 다음과 같습니다.

1. 프로그램 기본값
2. 설정 파일
3. 환경변수
4. 명령줄 옵션

현재 구현에서 환경변수로 직접 지원되는 주요 항목은 API 키, API 기본 URL, provider, 모델입니다. 그 밖의 값은 설정 파일 또는 CLI 옵션을 사용하십시오.

## 8. Mock 모드

Mock 모드는 API 키와 네트워크 없이 실행할 수 있는 오프라인 테스트 모드입니다. `--mock`와 `--dry-run`은 같은 기능을 가리킵니다.

```bash
python main.py commit --mock
python main.py pr --dry-run
```

Mock 모드에서도 현재 Git 저장소의 변경 사항은 확인합니다. 따라서 변경 사항이 없는 저장소에서는 결과를 생성하지 않고 종료합니다.

## 9. 프로그램 처리 과정

프로그램은 다음 순서로 동작합니다.

1. CLI 명령과 옵션을 읽습니다.
2. 설정 파일, 환경변수, 명령줄 옵션에서 설정을 구성합니다.
3. 현재 Git 저장소인지 확인합니다.
4. 현재 브랜치, `git status --porcelain`, staged/unstaged diff를 수집합니다.
5. 작은 untracked 텍스트 파일의 앞부분을 변경 내용에 포함합니다.
6. Safe Mode가 켜져 있으면 민감 파일을 제외하고 비밀값을 마스킹합니다.
7. 커밋 또는 PR 생성용 프롬프트를 만듭니다.
8. AI API를 한 번 호출하거나 Mock 응답을 사용합니다.
9. 생성 결과의 형식과 길이를 검사하고 부족한 부분을 보정합니다.
10. 최종 결과를 터미널에 출력합니다.

## 10. Safe Mode

Safe Mode는 기본적으로 켜져 있습니다. AI API로 전송하기 전 diff를 다음 규칙에 따라 정리합니다.

### 민감 파일 제외

다음과 같은 파일은 전송 대상에서 제외되거나 placeholder로 대체됩니다.

- `.env`, `.env.*`
- `.pem`, `.key`, `.pfx`, `.p12`, `.keystore`
- `id_rsa`, `id_ed25519`
- `credentials.json`, `service-account*.json`, `token.json`
- lock 파일
- `package-lock.json`
- `*.min.js`, `*.min.css`

### 민감정보 마스킹

diff 안에서 다음 유형의 값을 찾아 대체 문자열로 바꿉니다.

- OpenAI, Anthropic, Google, GitHub, AWS, Slack API 키와 토큰
- JWT 및 Bearer 토큰
- Private Key 블록
- 비밀번호, secret, api key 등의 설정값
- 이메일 주소
- 한국 전화번호
- 주민등록번호

### 전송량 제한

기본 제한은 다음과 같습니다.

- 최대 10개 파일
- 최대 200줄

제한을 초과하면 이후 내용은 생략되고 실행 중 안내 메시지가 표시됩니다. 제한값은 설정 파일에서 `max_diff_files`와 `max_diff_lines`로 조정할 수 있습니다.

### Safe Mode 비활성화

```bash
python main.py commit --no-safe-mode
```

Safe Mode를 끄면 원본 diff가 AI API로 전송될 수 있습니다. 운영 저장소에서는 가급적 기본 설정을 유지하십시오.

## 11. 생성 결과 보정

### 커밋 메시지

- Conventional Commits 접두어가 없으면 `feat:`를 추가합니다.
- 제목의 최대 길이는 기본 72자입니다.
- 제목 50자는 권장 길이이며, 초과해도 생성은 계속됩니다.
- 제목이 최대 길이를 넘으면 뒤를 줄여 `...`로 표시합니다.
- 본문 항목은 불릿 형식으로 정리합니다.

### PR 초안

- 제목의 최대 길이는 기본 80자입니다.
- `Why`, `What`, `How to Test` 섹션이 없으면 기본 내용으로 보완합니다.
- Markdown 코드 펜스가 응답을 감싸고 있으면 제거합니다.

## 12. 오류와 해결 방법

### Git 저장소가 아닌 경우

다음과 같은 오류가 표시되면 Git 저장소 안에서 실행하거나 저장소를 초기화하십시오.

```bash
git init
```

### 변경 사항이 없는 경우

커밋 또는 PR을 생성할 변경 사항이 없으면 AI 호출 없이 종료합니다. 파일을 수정하거나 staging한 뒤 다시 실행하십시오.

```bash
git status
```

### API 키가 없는 경우

`AI_API_KEY` 또는 provider에 맞는 API 키 환경변수를 설정하십시오. API를 사용하지 않으려면 다음과 같이 실행합니다.

```bash
python main.py commit --mock
```

### 인증 실패 또는 요청 제한

- API 키가 올바르고 만료되지 않았는지 확인합니다.
- provider와 API 기본 URL이 올바른지 확인합니다.
- HTTP 429가 표시되면 사용량 한도나 Rate Limit을 확인한 뒤 다시 요청합니다.

### 네트워크 오류

인터넷 연결, 방화벽, proxy, API 기본 URL을 확인하십시오. 로컬 서버를 사용할 때는 해당 서버가 실행 중인지 확인합니다.

## 13. 테스트 실행

개발 의존성을 설치한 뒤 프로젝트 루트에서 실행합니다.

```bash
pytest
```

특정 테스트 파일만 실행하려면 다음과 같이 합니다.

```bash
pytest tests/test_safety.py
pytest tests/test_cli.py
```

CLI 도움말은 다음 명령으로 확인할 수 있습니다.

```bash
python main.py --help
python main.py commit --help
python main.py pr --help
```

## 14. 제한사항 및 주의사항

- 이 도구는 커밋이나 PR을 자동으로 GitHub에 등록하지 않습니다.
- 생성된 결과는 AI 응답이므로 실제 커밋 또는 PR에 사용하기 전에 검토해야 합니다.
- Safe Mode는 정규식 기반 보호 기능이므로 모든 비밀정보를 완벽하게 탐지한다고 보장할 수 없습니다.
- staged diff와 unstaged diff가 단순히 결합되므로 같은 파일의 내용이 중복으로 표시될 수 있습니다.
- untracked 파일은 50KB 미만인 텍스트 파일만 최대 100줄까지 미리 봅니다.
- 설정 파일에서 `commit_max_title_len`과 `pr_max_title_len`을 지정해도 현재 구현에서는 적용되지 않습니다. 제목 길이를 조정할 때는 CLI 옵션으로 직접 제공되지 않으므로 기본값을 사용해야 합니다.
- `--convention` 값은 설정에 저장되지만 현재 프롬프트의 기본 Conventional Commits 지침 자체를 변경하지는 않습니다.

## 15. 권장 사용 순서

```bash
# 1. 변경 사항 확인
git status

# 2. API 없이 결과 형식 확인
python main.py commit --mock
python main.py pr --mock

# 3. 실제 API 사용 전 Safe Mode를 유지한 채 실행
python main.py commit
python main.py pr

# 4. 결과를 검토한 뒤 직접 커밋 또는 PR 작성
```

# AI 기반 Git 커밋 & PR 자동 생성기 (AI-GitGen)

`ai-gitgen`은 Git 변경 사항(`git status`, `git diff`)을 분석하여 Conventional Commits 규칙에 부합하는 **커밋 메시지**와 구조화된 **Pull Request(PR) 초안**을 자동으로 생성하는 Python 기반 CLI 도구입니다.

단순한 AI API 호출에 그치지 않고, 프롬프트 엔지니어링, 출력 길이/형식 검증 및 후처리, 민감정보 마스킹(Safe Mode), 비용 최적화(단일 호출 원칙) 및 팀 컨벤션 커스터마이징 기능을 제공합니다.

---

## 📌 목차
1. [주요 기능](#-주요-기능)
2. [프로젝트 구조](#-프로젝트-구조)
3. [설치 및 요구사항](#-설치-및-요구사항)
4. [환경변수(API Key) 설정](#-환경변수api-key-설정)
5. [사용 방법 및 CLI 옵션](#-사용-방법-및-cli-옵션)
6. [실행 및 출력 예시](#-실행-및-출력-예시)
7. [보안 및 민감정보 보호 (Safe Mode)](#-보안-및-민감정보-보호-safe-mode)
8. [비용 및 API 호출 최적화](#-비용-및-api-호출-최적화)
9. [템플릿 및 컨벤션 커스터마이징](#-템플릿-및-컨벤션-커스터마이징)
10. [테스트 및 검증](#-테스트-및-검증)

---

## 🚀 주요 기능

- **Git 상태 및 변경 사항 자동 수집**: `git status`와 `git diff`(Staged, Unstaged, Untracked 파일 포함)를 정확하게 수집.
- **표준 커밋 메시지 생성 (`commit`)**:
  - Conventional Commits 형식(`feat:`, `fix:`, `docs:` 등) 준수
  - 1줄 제목(권장 50자, 최대 72자) 및 변경 파일/핵심 변경사항 불릿 요약 본문
- **구조화된 PR 제목/본문 생성 (`pr`)**:
  - PR 제목(최대 80자)
  - 필수 템플릿 섹션 자동 구성 (`## Why`, `## What`, `## How to Test`) 및 각 섹션별 불릿 리스트
- **출력 검증 및 자동 보정(Post-processing)**: 누락된 섹션이나 글자 수 초과 시 자동 다듬기 및 구조 복원.
- **강력한 안전 모드(Safe Mode)**: API Key, 비밀번호, 이메일, 전화번호, 주민등록번호, `.env`, `.pem` 등 민감정보 마스킹 및 전송 제한(최대 10개 파일, 200줄).
- **멀티 AI 백엔드 지원**: OpenAI API, Google Gemini API, 로컬 LLM(Ollama, Groq, vLLM) 및 오프라인 모의(Mock) 모드 지원.
- **외부 종속성 최소화**: Python 표준 라이브러리(`urllib`, `json`, `argparse` 등)만으로 구동 가능.

---

## 📂 프로젝트 구조

```
ai-git-generator/
├── ai_gitgen/
│   ├── __init__.py           # 패키지 메타데이터
│   ├── cli.py                # CLI 명령어 파서 및 실행 흐름 제어
│   ├── config.py             # 설정 파일(.ai-gitgen.yml) 및 환경변수 로더
│   ├── git_collector.py      # Git 상태(status, diff, branch) 수집 모듈
│   ├── ai_client.py          # OpenAI / Gemini / Mock REST API 클라이언트
│   ├── prompts.py            # 커밋 및 PR 프롬프트 템플릿 엔지니어링
│   ├── safety.py             # 민감정보 정규식 마스킹 및 diff 필터링(Safe Mode)
│   └── validator.py          # 출력 길이/형식 검증 및 후처리(Validator)
├── tests/
│   ├── test_ai_client.py     # API 클라이언트 및 예외 처리 테스트
│   ├── test_cli.py           # CLI 명령어 및 동작 플로우 테스트
│   ├── test_config.py        # 설정 로딩 테스트
│   ├── test_git_collector.py # Git 변경사항 수집 테스트
│   ├── test_prompts.py       # 프롬프트 빌더 테스트
│   ├── test_safety.py        # 민감정보 마스킹 및 diff 제한 테스트
│   └── test_validator.py     # 출력 검증 및 자동 보정 테스트
├── main.py                   # 실행 진입점 (Launcher)
├── .ai-gitgen.yml.example    # 설정 파일 예시
├── .gitignore                # Git 제외 파일 설정
├── requirements.txt          # 개발/테스트 의존성 목록
└── README.md                 # 프로젝트 문서
```

---

## 🛠 설치 및 요구사항

### 시스템 요구사항
- **Python**: 3.10 이상
- **Git**: Git 2.20 이상

### 설치
별도의 외부 라이브러리 설치 없이 기본 Python 환경에서 바로 실행할 수 있습니다. (선택적으로 YAML 설정 파싱 및 테스트를 위해 아래 패키지 설치 가능)

```bash
# 저장소 복제 (또는 프로젝트 디렉토리로 이동)
cd ai-git-generator

# (선택) 가상환경 생성 및 의존성 설치
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 🔑 환경변수(API Key) 설정

AI API Key를 환경변수에 등록하여 사용합니다. (코드 내 하드코딩 금지)

### 1. OpenAI 또는 호환 API 사용 시
```bash
export AI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# 또는
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 2. Google Gemini API 사용 시
```bash
export AI_API_KEY="AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export AI_PROVIDER="gemini"
# 또는
export GEMINI_API_KEY="AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 3. 로컬 LLM (Ollama / vLLM / LocalAI) 사용 시
```bash
export AI_API_KEY="local-key"
export AI_API_BASE_URL="http://localhost:11434/v1"
export AI_MODEL="llama3"
```

---

## 💻 사용 방법 및 CLI 옵션

### 기본 명령어

1. **커밋 메시지 자동 생성**:
   ```bash
   python main.py commit
   ```

2. **Pull Request(PR) 제목 및 본문 초안 생성**:
   ```bash
   python main.py pr
   ```

3. **API Key 없이 오프라인/테스트 모드로 실행 (Mock Mode)**:
   ```bash
   python main.py commit --mock
   python main.py pr --mock
   ```

### 주요 CLI 옵션

| 옵션 | 설명 | 기본값 |
| :--- | :--- | :--- |
| `--model` | 호출할 AI 모델명 | `gpt-4o-mini` |
| `--temperature` | 생성 다양성/창의성 조절 (0.0 ~ 1.0) | `0.2` |
| `--max-tokens` | 최대 생성 토큰 수 | `1000` |
| `--safe-mode` / `--no-safe-mode` | 안전 모드(민감정보 마스킹 및 전송 제한) 활성화/비활성화 | `True` (기본 활성화) |
| `-l`, `--language` | 생성 언어 선택 (`ko`, `en`) | `ko` |
| `--convention` | 적용할 커밋/PR 컨벤션 규칙명 | `conventional_commits` |
| `--config` | 커스텀 설정 파일 경로 지정 | `.ai-gitgen.yml` |
| `--mock`, `--dry-run` | API 호출 없이 시뮬레이션 데이터로 실행 | `False` |

---

## 📋 실행 및 출력 예시

### 1. 커밋 메시지 자동 생성 (`commit`)
```bash
$ python main.py commit
[INFO] Git status 수집 완료: 3개 파일 변경 감지
[INFO] Git diff 수집 완료: 128줄
[INFO] AI API 요청 중...
[DONE] 커밋 메시지 생성 완료

-- Commit Message --
feat: Git 변경 사항 기반 커밋 메시지 자동 생성 기능 추가

- git diff 결과를 수집해 AI 입력 컨텍스트로 전달하도록 구현
- 커밋 메시지 템플릿(feat/fix 등) 생성 규칙 적용
- API Key 미설정 시 안내 메시지 및 에러 처리 개선
```

### 2. PR 제목/본문 자동 생성 (`pr`)
```bash
$ python main.py pr
[INFO] 현재 브랜치: feature/commit-pr-generator
[INFO] Git status 수집 완료: 3개 파일 변경 감지
[INFO] Git diff 수집 완료: 128줄
[INFO] AI API 요청 중...
[DONE] PR 초안 생성 완료

--- PR Title ---
feat: 커밋/PR 자동 생성 기능 추가

--- PR Body ---
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
- 결과로 출력된 PR 본문이 Why/What/How to Test 구조와 길이 규칙을 만족하는지 확인
```

### 3. API Key 미설정 시
```bash
$ python main.py commit
[ERROR] AI_API_KEY 환경변수가 설정되지 않았습니다.
# 예) export AI_API_KEY="YOUR_KEY"
```

### 4. 변경 사항이 없는 경우
```bash
$ python main.py commit
[INFO] 변경 사항이 없습니다. 커밋 메시지를 생성하지 않고 종료합니다.
```

---

## 🔒 보안 및 민감정보 보호 (Safe Mode)

`ai-gitgen`은 소스 코드 내 민감정보가 외부 AI API로 유출되는 것을 원천 차단하기 위해 **Safe Mode**를 기본 활성화하고 있습니다.

### 1. 자동 마스킹 규칙
정규표현식을 통해 diff 내에 포함된 아래 패턴을 자동 감지하여 마스킹합니다:
- **API Key & Secret**: OpenAI(`sk-...`), Anthropic(`sk-ant-...`), Google(`AIza...`), GitHub PAT(`ghp_...`), AWS Access/Secret Key, Slack Token, JWT Token, Private Key 블록
- **개인정보**: 이메일 주소, 휴대폰 번호(010-XXXX-XXXX), 주민등록번호(RRN)
- **비밀번호/토큰 변수**: `password = "..."`, `secret = "..."` 등

### 2. 파일 제외 및 Diff 크기 제한 정책
- **민감 파일 자동 제외**: `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa`, `credentials.json`, `token.json`, `package-lock.json`, `*.min.js` 등
- **전송 용량 제한**:
  - 최대 파일 수: 기본 **10개** (초과 시 요약 처리)
  - 최대 diff 줄 수: 기본 **200줄** (초과 시 절삭 및 경고 메시지 부착)

### Safe Mode ON/OFF 비교 예시

| 변경 내용 | Safe Mode ON (기본) | Safe Mode OFF (`--no-safe-mode`) |
| :--- | :--- | :--- |
| `openai_key = "sk-abc12345..."` | `openai_key = "[MASKED_OPENAI_KEY]"` | 원본 API Key 그대로 전송 (위험) |
| `email = "dev@company.com"` | `email = "[MASKED_EMAIL]"` | 원본 이메일 전송 |
| `.env` 파일 변경 | 파일 내용 제외 및 플레이스홀더 대체 | `.env` 내부 비밀번호/시크릿 노출 위험 |
| 500줄 대량 diff | 상위 200줄까지만 전송 후 요약 안내 | 500줄 전체 전송 (비용 증가/토큰 낭비) |

---

## 💰 비용 및 API 호출 최적화

- **단일 호출 원칙 (1 Call per Execution)**:
  - 1회 실행(`commit` 또는 `pr`) 당 단 1회의 AI API 요청만 수행하여 불필요한 토큰 과금 및 비용 낭비를 방지합니다.
- **경량화 모델 기본값**:
  - 빠르고 경제적인 `gpt-4o-mini` 또는 `gemini-1.5-flash`를 기본 모델로 권장 및 설정.
- **Diff 압축 및 토큰 절약**:
  - 변경이 없는 공백 라인 및 바이너리/빌드 산출물을 제외하고 필수 diff만 선별 전송.

---

## ⚙️ 템플릿 및 컨벤션 커스터마이징

프로젝트 루트에 `.ai-gitgen.yml` 설정 파일을 생성하여 팀의 코딩 컨벤션과 프롬프트를 자유롭게 맞춤 설정할 수 있습니다.

```yaml
# .ai-gitgen.yml
model: gpt-4o-mini
temperature: 0.2
max_tokens: 1000
language: ko
safe_mode: true
max_diff_lines: 200

# 사용자 정의 커밋/PR 규칙 추가
custom_instructions: |
  - JIRA 티켓 번호(예: [PROJ-123])가 브랜치명에 포함되어 있다면 커밋 제목 앞에 붙일 것
  - 성능 개선 사항은 perf: 대신 feat(perf): 형식을 사용할 것
```

---

## 🧪 테스트 및 검증

프로젝트의 안정성과 예외 처리를 검증하는 27개의 단위/통합 테스트가 포함되어 있습니다:

```bash
# 전체 테스트 실행
python3 -m unittest discover tests
```

### 테스트 항목
- `test_git_collector.py`: Git 저장소 판별, status 파싱, staged/unstaged/untracked diff 수집 검증
- `test_safety.py`: API Key, 비밀번호, 이메일, 전화번호, 주민번호 마스킹 및 민감 파일 제외 검증
- `test_validator.py`: 커밋 제목 50/72자 제한, Conventional prefix 강제, PR 3대 필수 섹션 자동 보정 검증
- `test_prompts.py`: 언어별(ko/en), 컨벤션별 프롬프트 구조화 검증
- `test_cli.py`: 저장소 외부 실행 에러, 변경사항 없음 처리, API Key 미설정 처리, Mock 모드 E2E 실행 검증
- `test_ai_client.py`: API 호출 에러 핸들링(401, 429, Timeout) 및 Mock 응답 검증
- `test_config.py`: YAML 설정 파일 및 환경변수 우선순위 오버라이드 검증

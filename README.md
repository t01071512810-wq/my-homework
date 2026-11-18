# 공시 알림 (GitHub Actions)

코스피·코스닥 상장사의 새 공시 중 **[중요] 종류만** 내 텔레그램 봇으로 보내 줍니다.

## 운영 노트

> 키·토큰 **값**은 이 파일에 절대 적지 않습니다. 어디에 넣는지만 적습니다.

### 지금 무엇이 언제 도는지

| 무엇 | 언제 | 하는 일 |
|---|---|---|
| cron-job.org 작업 "공시 알림" | 평일 **09:07~19:37, 30분마다**(하루 22번, `Asia/Seoul`) | GitHub에 `dart-alert` 워크플로 실행(Run workflow) 요청을 보냅니다. |
| GitHub Actions `dart-alert` | cron-job.org가 부를 때마다 | `dart_alert.py`가 DART에서 새 공시를 받아 [중요] 공시만 텔레그램으로 보내고, `sent.json`을 저장소에 저장합니다. 실패하면 텔레그램으로 `실패`와 실행 기록 링크를 보냅니다. |

- 19:37 뒤에 나온 공시는 다음 평일 09:07에 갑니다. 11월 16~18일 기준으로 19:37 뒤에 나온 [중요] 공시는 약 2%였습니다.
- GitHub 자체 예약(`schedule`)은 몇 시간씩 늦게 돌 때가 많아서 쓰지 않습니다.
- 별개 프로그램: `C:\workspace\dartproject`(자사주 취득 알림)는 Oracle 서버에서 따로 돌고 있습니다. 이 저장소와는 상관이 없습니다.

### 멈췄을 때 다시 켜는 순서

평일인데 하루 종일 알림이 없으면 아래 순서로 확인합니다.

1. **cron-job.org 작업 켜기:** [console.cron-job.org](https://console.cron-job.org) → Cronjobs → "공시 알림"이 꺼져 있으면 켭니다. 실패가 계속되면 cron-job.org가 작업을 스스로 끄기도 합니다. 작업 기록(History)에서 응답 번호가 `401`이면 GitHub 토큰이 만료된 것입니다(아래 "키·토큰을 바꾸는 곳").
2. **Actions 워크플로 켜기:** 저장소 [Actions → dart-alert](https://github.com/t01071512810-wq/my-homework/actions/workflows/dart-alert.yml)에 "This workflow was disabled"가 보이면 **Enable workflow**를 누릅니다. 저장소 **Settings → Actions → General**에서 Actions가 꺼져 있지 않은지도 봅니다.
3. **Run workflow로 한 번 돌리기:** 같은 화면에서 **Run workflow → Run workflow**를 누르고, 초록색 체크가 뜨는지 봅니다(아래 "한 번 돌려서 확인하는 법").

### 키·토큰을 바꾸는 곳

| 무엇 | 바꾸는 곳 |
|---|---|
| 텔레그램 봇 토큰 | 저장소 Settings → Secrets and variables → Actions → `TELEGRAM_BOT_TOKEN` → Update |
| 텔레그램 대화방 번호 | 같은 곳의 `TELEGRAM_CHAT_ID` |
| OpenDART 인증키 | 같은 곳의 `DART_API_KEY` |
| GitHub 토큰(cron-job.org가 버튼을 누를 때 씀) | 새로 만든 뒤(아래 "GitHub 토큰 만들기") cron-job.org 작업 → ADVANCED → Headers의 `Authorization` 값을 `Bearer 새토큰`으로 바꿉니다. 옛 토큰은 GitHub Settings → Developer settings → Fine-grained tokens에서 삭제합니다. |

**GitHub 토큰 만료일:** `____년 __월 __일` ← 만료 2주 전에 새 토큰으로 바꾸세요. 만료되면 알림이 멈춥니다.

### 완전히 끄는 법

1. cron-job.org에서 "공시 알림" 작업을 끄거나 삭제합니다. 이것만 해도 더 이상 돌지 않습니다.
2. 저장소 Actions → dart-alert → 오른쪽 위 `…` → **Disable workflow**.
3. (선택) GitHub Settings → Developer settings → Fine-grained tokens에서 이 작업용 토큰을 삭제합니다.

다시 켤 때는 "멈췄을 때 다시 켜는 순서"를 따릅니다.

### 한 달 무료 사용량

- 하루 22번 × 한 달 평일 20~23일 = **440~506번** 실행합니다.
- GitHub는 실행마다 쓴 시간을 1분 단위로 올려서 셉니다. 11월 16~18일 실제 실행 42번 중 38번이 1분 안에 끝났고, 공시가 몰린 아침 실행 등 4번이 2분이었습니다.
- 그래서 한 달 약 **480~550분**으로, 무료 계정 비공개 저장소 한도 **2,000분**의 약 24~28%입니다. 모든 실행이 2분이 되는 최악의 경우에도 1,012분(51%)입니다.
- 2,000분은 내 계정의 **모든 비공개 저장소가 함께** 씁니다(예: `gongmo-bot`). 사용량은 GitHub **Settings → Billing and licensing**에서 봅니다.

### 한 번 돌려서 확인하는 법

1. [Actions → dart-alert](https://github.com/t01071512810-wq/my-homework/actions/workflows/dart-alert.yml) → 오른쪽 **Run workflow** → 초록 **Run workflow** 버튼을 누릅니다.
2. 10초쯤 뒤 목록 맨 위에 새 실행이 생깁니다. 1~2분 뒤 **초록색 체크**가 되면 성공, 빨간 X면 실패입니다(텔레그램에도 `실패`가 옵니다).
3. 실행을 눌러 `alert` → **새 공시 보내기**를 펼치면 아래 줄이 보입니다.
   - `보낼 공시 N건, 건너뜀 M건(받지않을종류.txt A건, 중요 아님 B건)`
   - 보낸 공시마다 `보냄: 접수번호 회사 공시이름`
4. 새 공시가 없으면 `보낼 공시 0건`이고 텔레그램도 조용합니다. 정상입니다.

## 파일

| 파일 | 하는 일 |
|---|---|
| `dart_alert.py` | 새 공시를 찾아 텔레그램으로 보냅니다. 파이썬 기본 기능만 씁니다. |
| `받지않을종류.txt` | **받지 않을 공시 종류**를 한 줄에 하나씩 적는 설정 파일입니다. 이 파일만 고쳐서 더하고 뺍니다. |
| `.github/workflows/dart-alert.yml` | 버튼을 누르면 실행되는 Actions 설정입니다. |
| `sent.json` | **이미 확인한 공시 기록**입니다. 보낸 공시와, 보내지 않고 넘긴 공시의 접수번호(`rcept_no`)를 모두 적습니다. 실행이 끝날 때마다 Actions가 저장소에 다시 저장하고, 최근 14일 치만 남깁니다. |
| `send_hello.py` | 1주차 연습용 "안녕" 보내기입니다. 이것만 내 PC의 `.env`를 읽습니다(`.env`는 GitHub에 올라가지 않습니다). |

## 동작 방식

1. cron-job.org가 GitHub에 "워크플로 실행" 요청을 보냅니다.
2. Actions가 저장소를 받고 `dart_alert.py`를 실행합니다.
3. DART에서 코스피(`Y`)·코스닥(`K`) 공시 목록을 받아 `sent.json`에 없는 것만 골라냅니다.
   - `받지않을종류.txt`에 있는 종류와 중요하지 않은 공시는 보내지 않고 `sent.json`에 '확인함'으로만 적습니다.
   - [중요] 공시는 오래된 순서로 보내고, 한 건 보낼 때마다 `sent.json`에 적습니다.
4. 실행이 성공하든 실패하든 끝나면 `sent.json`을 저장소에 커밋합니다.
5. 중간에 하나라도 실패하면 텔레그램으로 `실패` 한 줄과 그 실행 기록 링크를 보냅니다.

- **처음 실행:** 최근 3일 치 공시는 보내지 않고 기록만 한 뒤, "공시 알림을 시작합니다" 한 줄을 보냅니다.
- **조회 범위:** 마지막으로 본 공시 날짜의 하루 전부터 오늘까지입니다(최대 10일). 그래서 밤이나 주말에 나온 공시도 다음 실행에서 보냅니다.
- **두 실행이 겹칠 때:** 워크플로가 `concurrency`로 한 번에 하나만 돌게 합니다. 다음 실행은 앞 실행이 저장한 최신 `sent.json`을 받아서 시작하므로 같은 공시를 두 번 보내지 않습니다.
- **보내다 실패한 공시:** 기록되지 않으므로 다음 실행 때 다시 보냅니다.

## 받지 않을 종류 (`받지않을종류.txt`)

- 공시 제목(띄어쓰기를 뺀 것)에 이 파일의 줄이 들어 있으면 **[중요]여도 보내지 않습니다.**
- 한 줄에 하나씩 적고, `#`로 시작하는 줄은 메모입니다. 줄 앞에 `#`를 붙이면 잠깐 끌 수 있습니다.
- GitHub 저장소에서 파일을 열고 연필(Edit) 버튼 → 고치기 → **Commit changes**를 누르면 다음 실행부터 적용됩니다.
- 지금 들어 있는 것: `[기재정정]`, `[첨부정정]`, `[첨부추가]`. 11월 16~18일에 보낸 153건 중 63건이 정정 공시였습니다.

## [중요]로 표시하는 공시

공시 제목(띄어쓰기를 뺀 것)에 아래 단어가 들어 있는 공시**만** 보내고, 메시지 맨 앞에 `[중요]`를 붙입니다.

- 종류를 바꾸려면 `dart_alert.py`의 `IMPORTANT` 목록과 이 표를 함께 고치세요. 빼기만 할 때는 `받지않을종류.txt`에 적는 편이 쉽습니다.
- 모든 공시를 다시 받으려면 `dart_alert.py`의 `ONLY_IMPORTANT = True`를 `False`로 바꾸세요. 하루 600~800건이 옵니다.

| 종류 | 제목에 이 단어가 있으면 |
|---|---|
| 실적 | `실적`, `매출액또는손익구조` (예: 영업(잠정)실적, 매출액또는손익구조30%변경) |
| 유상증자 | `유상증자` |
| 무상증자 | `무상증자` |
| 전환사채 | `전환사채` |
| 신주인수권부사채 | `신주인수권부사채` |
| 교환사채 | `교환사채` |
| 최대주주 변경 | `최대주주변경` |
| 감자 | `감자결정` |
| 합병·분할 | `합병결정`, `분할결정`, `분할합병결정` |
| 자사주 취득 | `자기주식취득결정`, `자기주식취득신탁계약체결결정` |
| 공급계약 | `단일판매ㆍ공급계약` |
| 거래정지·상장폐지 | `매매거래정지`, `상장폐지` |
| 관리종목·상장적격성 | `관리종목`, `상장적격성`, `매출액미달` (2026-11-18 추가) |
| 회생·파산 | `회생절차`, `파산` |
| 횡령·배임 | `횡령`, `배임` |
| 주식 소각 | `주식소각결정` (2026-11-18 추가) |
| 투자판단 주요경영사항 | `투자판단관련주요경영사항` (예: 임상 승인, 2026-11-18 추가) |
| 타법인 주식 취득 | `타법인주식및출자증권취득결정` (2026-11-18 추가) |
| 소송 | `소송등의제기` (2026-11-18 추가) |
| 풍문·조회공시 | `풍문또는보도에대한해명`, `조회공시요구` (2026-11-18 추가) |

## 저장소 Secrets

저장소 **Settings → Secrets and variables → Actions → New repository secret**에서 아래 이름 그대로 넣습니다.

| 이름 | 넣을 값 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather가 준 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 내 대화방 번호(chat_id) |
| `DART_API_KEY` | OpenDART 인증키(40자리) |

## cron-job.org 설정

| 항목 | 값 |
|---|---|
| 주소(URL) | `https://api.github.com/repos/t01071512810-wq/my-homework/actions/workflows/dart-alert.yml/dispatches` |
| 요청 방법 | `POST` |
| 헤더 | `Accept: application/vnd.github+json`<br>`Authorization: Bearer <GitHub 토큰>`<br>`X-GitHub-Api-Version: 2022-11-28`<br>`Content-Type: application/json` |
| 본문 | `{"ref":"main"}` |
| 실행 시각 | Custom: 분 `7`, `37` / 시 `9`~`19` / 요일 월~금 / 날짜·월은 전체 → 09:07, 09:37, …, 19:07, 19:37 (하루 22번) |
| 시간대 | `Asia/Seoul` |

성공하면 GitHub가 `204`(또는 `200`)으로 응답합니다. `401`이면 토큰이 틀렸거나 만료된 것이고, `403`이면 토큰에 Actions 권한이 없는 것이고, `404`면 토큰에 이 저장소 권한이 없는 것입니다.

## GitHub 토큰 (fine-grained) 만들기

1. GitHub 오른쪽 위 프로필 사진 → **Settings** → 왼쪽 맨 아래 **Developer settings**
2. **Personal access tokens → Fine-grained tokens → Generate new token**
3. **Token name**은 `cron-job.org dart-alert`처럼 짓고, **Expiration**을 고릅니다. 만료일을 위 "GitHub 토큰 만료일" 칸에 적어 두세요.
4. **Resource owner**는 내 계정(`t01071512810-wq`)입니다.
5. **Repository access**는 **Only select repositories**를 고르고 `my-homework` 하나만 선택합니다.
6. **Permissions → Repository permissions → Actions**를 **Read and write**로 바꿉니다. 다른 권한은 건드리지 않습니다. (`Metadata: Read-only`는 GitHub가 자동으로 넣는 필수 권한입니다.)
7. **Generate token**을 누르고, 나온 값을 바로 cron-job.org의 `Authorization` 헤더에 `Bearer ` 뒤로 붙여 넣습니다. 이 화면을 닫으면 다시 볼 수 없습니다.

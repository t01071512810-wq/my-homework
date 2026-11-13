# 공시 알림 (GitHub Actions)

코스피·코스닥 상장사의 새 공시 중 **[중요] 종류만** 내 텔레그램 봇으로 보내 줍니다(아래 표 참고).
평일 09:07~15:37(한국 시간)에 30분마다 한 번씩 돌고, 그 사이에 나온 공시를 한꺼번에 보냅니다.

- 실행: GitHub Actions의 **Run workflow** 버튼(`workflow_dispatch`)으로만 돕니다. GitHub 자체 예약(`schedule`)은 몇 시간씩 늦게 돌 때가 많아서 쓰지 않습니다.
- 정해진 시각에 버튼을 누르는 일은 [cron-job.org](https://cron-job.org)가 대신 합니다.
- 비밀 값(봇 토큰, 대화방 번호, DART 인증키)은 코드나 `.env`가 아니라 **저장소 Secrets**에서만 읽습니다.

## 파일

| 파일 | 하는 일 |
|---|---|
| `dart_alert.py` | 새 공시를 찾아 텔레그램으로 보냅니다. 파이썬 기본 기능만 씁니다. |
| `.github/workflows/dart-alert.yml` | 버튼을 누르면 실행되는 Actions 설정입니다. |
| `sent.json` | **이미 확인한 공시 기록**입니다. 보낸 공시와, 중요하지 않아 건너뛴 공시의 접수번호(`rcept_no`)를 모두 적습니다. 실행이 끝날 때마다 Actions가 저장소에 다시 저장합니다. 첫 실행 때 생기고, 최근 14일 치만 남깁니다. |
| `send_hello.py` | 1주차 연습용 "안녕" 보내기입니다. 이것만 내 PC의 `.env`를 읽습니다(`.env`는 GitHub에 올라가지 않습니다). |

## 동작 방식

1. cron-job.org가 GitHub에 "워크플로 실행" 요청을 보냅니다.
2. Actions가 저장소를 받고 `dart_alert.py`를 실행합니다.
3. DART에서 코스피(`Y`)·코스닥(`K`) 공시 목록을 받아 `sent.json`에 없는 것만 골라냅니다.
   - 중요하지 않은 공시는 보내지 않고 `sent.json`에 '확인함'으로만 적습니다.
   - [중요] 공시는 오래된 순서로 보내고, 한 건 보낼 때마다 `sent.json`에 적습니다.
4. 실행이 성공하든 실패하든 끝나면 `sent.json`을 저장소에 커밋합니다.
5. 중간에 하나라도 실패하면 텔레그램으로 `실패` 한 줄과 그 실행 기록 링크를 보냅니다.

- **처음 실행:** 최근 3일 치 공시는 보내지 않고 기록만 한 뒤, "공시 알림을 시작합니다" 한 줄을 보냅니다. 다음 실행부터 새 공시를 보냅니다.
- **조회 범위:** 마지막으로 본 공시 날짜의 하루 전부터 오늘까지입니다(최대 10일). 그래서 장 마감 뒤나 주말에 나온 공시도 다음 실행에서 보냅니다.
- **두 실행이 겹칠 때:** 워크플로가 `concurrency`로 한 번에 하나만 돌게 합니다. 다음 실행은 앞 실행이 저장한 최신 `sent.json`을 받아서 시작하므로 같은 공시를 두 번 보내지 않습니다.
- **보내다 실패한 공시:** 기록되지 않으므로 다음 실행 때 다시 보냅니다.

## [중요]로 표시하는 공시

공시 제목(띄어쓰기를 뺀 것)에 아래 단어가 들어 있는 공시**만** 보내고, 메시지 맨 앞에 `[중요]`를 붙입니다.

- 종류를 바꾸려면 `dart_alert.py`의 `IMPORTANT` 목록과 이 표를 함께 고치세요.
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
| 회생·파산 | `회생절차`, `파산` |
| 횡령·배임 | `횡령`, `배임` |

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
| 실행 시각 | 사용자 지정: 분 `7`, `37` / 시 `9`~`15` / 요일 월~금 / 일·월은 매일·매월 → 09:07, 09:37, …, 15:07, 15:37 (하루 14번) |
| 시간대 | `Asia/Seoul` |

성공하면 GitHub가 `204`(또는 `200`)으로 응답합니다. `401`이면 토큰이 틀렸거나 만료된 것이고, `404`면 토큰에 이 저장소 권한이 없는 것입니다.

## GitHub 토큰 (fine-grained) 만들기

1. GitHub 오른쪽 위 프로필 사진 → **Settings** → 왼쪽 맨 아래 **Developer settings**
2. **Personal access tokens → Fine-grained tokens → Generate new token**
3. **Token name**은 `cron-job.org dart-alert`처럼 짓고, **Expiration**을 고릅니다. 만료일을 달력에 적어 두세요. 만료되면 알림이 멈춥니다.
4. **Resource owner**는 내 계정(`t01071512810-wq`)입니다.
5. **Repository access**는 **Only select repositories**를 고르고 `my-homework` 하나만 선택합니다.
6. **Permissions → Repository permissions → Actions**를 **Read and write**로 바꿉니다. 다른 권한은 건드리지 않습니다. (`Metadata: Read-only`는 GitHub가 자동으로 넣는 필수 권한입니다.)
7. **Generate token**을 누르고, 나온 값을 바로 cron-job.org의 `Authorization` 헤더에 `Bearer ` 뒤로 붙여 넣습니다. 이 화면을 닫으면 다시 볼 수 없습니다.

## GitHub 무료 시간

- 하루 14번 × 한 달 평일 20~23일 = 한 달 **280~322번** 실행합니다.
- GitHub는 실행마다 쓴 시간을 **1분 단위로 올려서** 셉니다.
- 실제로 돌려 보니 보낼 공시가 0건이어도 DART 목록(2~3일 치, 약 2천 건)을 받는 데만 약 1분(58초)이 걸렸습니다. 그래서 한 번 실행은 1~2분으로 셉니다.
- 한 달 약 **280~644분**입니다. 무료 계정의 비공개 저장소 한도 **한 달 2,000분**의 약 14~32%예요. 넉넉하게 잡으면 2분 × 322번 = 644분입니다.
- 2,000분은 내 계정의 **모든 비공개 저장소가 함께** 씁니다(예: `gongmo-bot`). 사용량은 GitHub **Settings → Billing and licensing**에서 볼 수 있습니다.

"""코스피·코스닥 새 공시를 내 텔레그램으로 보낸다.

GitHub Actions에서 한 번 실행되고 끝나는 프로그램이다(계속 켜 두지 않는다).
비밀 값은 코드나 .env가 아니라 환경 변수에서만 읽는다. Actions가 저장소 Secrets를 넣어 준다.
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DART_API_KEY

[중요] 종류(IMPORTANT)의 공시만 보낸다(ONLY_IMPORTANT).
확인한 공시(보낸 것 + 중요하지 않아 건너뛴 것)는 sent.json에 접수번호로 적고,
워크플로가 실행이 끝날 때마다 저장소에 저장한다.
파이썬 기본 기능만 사용한다(추가 설치 없음).
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
SENT_FILE = Path(__file__).with_name("sent.json")

MARKETS = {"Y": "코스피", "K": "코스닥"}
FIRST_LOOKBACK_DAYS = 3   # 처음 실행할 때 '이미 나온 공시'로 보고 건너뛸 기간
MAX_LOOKBACK_DAYS = 10    # 오래 쉬었다가 다시 돌아도 이 기간까지만 거슬러 올라간다
KEEP_DAYS = 14            # sent.json에 남겨 둘 기간. MAX_LOOKBACK_DAYS보다 길어야 중복이 안 생긴다
SEND_GAP = 1.1            # 한 대화방에는 1초에 한 통 정도로 보내야 텔레그램이 막지 않는다
ONLY_IMPORTANT = True     # True면 아래 IMPORTANT에 해당하는 공시만 보낸다(하루 600~800건 → 수십 건)
HTTP_TIMEOUT = 60         # 1주차에 텔레그램 첫 응답이 36초 걸린 적이 있다

# 메시지 맨 앞에 [중요]를 붙일 공시 종류. 공시 제목(띄어쓰기 제거)에 단어가 들어 있으면 중요로 본다.
# 바꾸면 README.md의 표도 같이 고친다.
IMPORTANT = [
    ("실적", ("실적", "매출액또는손익구조")),
    ("유상증자", ("유상증자",)),
    ("무상증자", ("무상증자",)),
    ("전환사채", ("전환사채",)),
    ("신주인수권부사채", ("신주인수권부사채",)),
    ("교환사채", ("교환사채",)),
    ("최대주주 변경", ("최대주주변경",)),
    ("감자", ("감자결정",)),
    ("합병·분할", ("합병결정", "분할결정", "분할합병결정")),
    ("자사주 취득", ("자기주식취득결정", "자기주식취득신탁계약체결결정")),
    ("공급계약", ("단일판매ㆍ공급계약", "단일판매·공급계약")),
    ("거래정지·상장폐지", ("매매거래정지", "상장폐지")),
    ("회생·파산", ("회생절차", "파산")),
    ("횡령·배임", ("횡령", "배임")),
]


class AlertError(Exception):
    """실행을 실패로 끝내야 하는 오류. 메시지에 토큰이나 인증키를 넣지 않는다."""


def need_env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise AlertError(f"{name} 값이 없습니다. GitHub 저장소 Settings → Secrets에 넣어 주세요.")
    return value


def http_post(url, params):
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(url, data=data, timeout=HTTP_TIMEOUT) as response:
        return json.load(response)


def http_get(url, params, tries=3):
    full = url + "?" + urllib.parse.urlencode(params)
    for attempt in range(1, tries + 1):
        try:
            with urllib.request.urlopen(full, timeout=HTTP_TIMEOUT) as response:
                return json.load(response)
        except (OSError, ValueError) as error:
            if attempt == tries:
                reason = getattr(error, "reason", None) or type(error).__name__
                raise AlertError(f"DART에 연결하지 못했습니다: {reason}") from None
            time.sleep(5 * attempt)


# ---------------------------------------------------------------- DART
DART_ERRORS = {
    "010": "등록되지 않은 인증키입니다. DART_API_KEY Secret을 확인해 주세요.",
    "011": "사용할 수 없는 인증키입니다.",
    "012": "접근할 수 없는 IP입니다.",
    "020": "오늘 DART 요청 한도(약 2만 회)를 넘었습니다.",
    "800": "DART 시스템 점검 중입니다.",
    "901": "인증키 사용 기간이 끝났습니다. OpenDART에서 연장해 주세요.",
}


def fetch_filings(api_key, start, end):
    """start~end 사이에 나온 코스피·코스닥 공시를 모두 받아 온다."""
    items = []
    for corp_cls in MARKETS:
        page = 1
        while True:
            body = http_get(
                "https://opendart.fss.or.kr/api/list.json",
                {
                    "crtfc_key": api_key,
                    "bgn_de": start.strftime("%Y%m%d"),
                    "end_de": end.strftime("%Y%m%d"),
                    "corp_cls": corp_cls,
                    "page_no": page,
                    "page_count": 100,
                },
            )
            status = body.get("status")
            if status == "013":  # 조회된 데이터 없음
                break
            if status != "000":
                help_text = DART_ERRORS.get(status, body.get("message", ""))
                raise AlertError(f"DART 오류 {status}: {help_text}")
            items.extend(body.get("list", []))
            if page >= int(body.get("total_page", 1)):
                break
            page += 1
    return items


# ---------------------------------------------------------------- 텔레그램
class Telegram:
    def __init__(self, token, chat_id):
        self.url = f"https://api.telegram.org/bot{token}/sendMessage"
        self.chat_id = chat_id

    def send(self, text):
        params = {"chat_id": self.chat_id, "text": text, "disable_web_page_preview": "true"}
        for attempt in range(1, 4):
            try:
                body = http_post(self.url, params)
            except urllib.error.HTTPError as error:
                try:
                    body = json.load(error)
                except ValueError:
                    body = {"ok": False, "error_code": error.code, "description": f"HTTP {error.code}"}
            except OSError as error:
                body = {"ok": False, "description": str(getattr(error, "reason", None) or type(error).__name__)}
            if body.get("ok"):
                return
            retry_after = body.get("parameters", {}).get("retry_after")
            if retry_after and attempt < 3:  # 너무 빨리 보냈다며 기다리라고 할 때
                time.sleep(int(retry_after) + 1)
                continue
            if body.get("error_code") in (401, 404):
                raise AlertError("텔레그램 봇 토큰이 올바르지 않습니다. TELEGRAM_BOT_TOKEN Secret을 확인해 주세요.")
            raise AlertError(f"텔레그램 전송 실패: {body.get('description')}")


def important_label(report_nm):
    name = report_nm.replace(" ", "")
    for label, words in IMPORTANT:
        if any(word in name for word in words):
            return label
    return None


def format_message(item):
    report = " ".join(item.get("report_nm", "").split())
    market = MARKETS.get(item.get("corp_cls"), "")
    d = item.get("rcept_dt", "")
    when = f"{d[:4]}-{d[4:6]}-{d[6:]}" if len(d) == 8 else d
    head = f"{item.get('corp_name', '')} ({market})"
    if important_label(report):
        head = "[중요] " + head
    return "\n".join(
        [
            head,
            report,
            f"{when} · 제출인 {item.get('flr_nm', '')}",
            f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item['rcept_no']}",
        ]
    )


# ---------------------------------------------------------------- 보낸 공시 기록
def load_sent():
    """보낸 공시 접수번호 집합. 파일이 없으면 None(= 처음 실행)."""
    if not SENT_FILE.exists():
        return None
    return set(json.loads(SENT_FILE.read_text(encoding="utf-8")))


def save_sent(sent, today):
    keep_from = (today - timedelta(days=KEEP_DAYS)).strftime("%Y%m%d")
    kept = sorted(r for r in sent if r[:8] >= keep_from)
    SENT_FILE.write_text(json.dumps(kept, indent=0) + "\n", encoding="utf-8")


def start_date(sent, today):
    """어디서부터 조회할지. 마지막으로 본 공시 날짜의 하루 전부터(놓친 공시를 다시 잡으려고)."""
    oldest_allowed = today - timedelta(days=MAX_LOOKBACK_DAYS)
    if not sent:
        return max(today - timedelta(days=FIRST_LOOKBACK_DAYS), oldest_allowed)
    newest = max(sent)[:8]
    last_seen = date(int(newest[:4]), int(newest[4:6]), int(newest[6:]))
    return min(max(last_seen - timedelta(days=1), oldest_allowed), today)


# ---------------------------------------------------------------- 실행
def main():
    telegram = Telegram(need_env("TELEGRAM_BOT_TOKEN"), need_env("TELEGRAM_CHAT_ID"))
    api_key = need_env("DART_API_KEY")
    today = datetime.now(KST).date()

    loaded = load_sent()
    first_run = loaded is None
    sent = loaded or set()
    start = start_date(sent, today)
    items = fetch_filings(api_key, start, today)
    new = sorted(
        {it["rcept_no"]: it for it in items if it.get("rcept_no") and it["rcept_no"] not in sent}.values(),
        key=lambda it: it["rcept_no"],
    )
    print(f"조회 기간 {start} ~ {today}, 받은 공시 {len(items)}건, 새 공시 {len(new)}건")

    if first_run:
        # 처음에는 이미 나온 공시를 한꺼번에 보내지 않고 기록만 해 둔다.
        sent.update(it["rcept_no"] for it in new)
        save_sent(sent, today)
        telegram.send(f"공시 알림을 시작합니다. 이미 나온 공시 {len(new)}건은 건너뛰고, 다음 실행부터 새 공시를 보냅니다.")
        print("처음 실행: 기록만 하고 시작 알림을 보냈습니다.")
        return 0

    to_send = []
    for item in new:
        if ONLY_IMPORTANT and not important_label(item.get("report_nm", "")):
            sent.add(item["rcept_no"])  # 중요하지 않은 공시는 보내지 않고 '확인함'으로만 적는다
        else:
            to_send.append(item)
    save_sent(sent, today)
    print(f"보낼 공시 {len(to_send)}건, 중요하지 않아 건너뜀 {len(new) - len(to_send)}건")

    failed = 0
    for i, item in enumerate(to_send):
        if i:
            time.sleep(SEND_GAP)
        try:
            telegram.send(format_message(item))
        except AlertError as error:
            failed += 1
            print(f"전송 실패 ({item['rcept_no']}): {error}", file=sys.stderr)
            if failed >= 3:
                print("3건 연속 실패해서 이번 실행은 여기서 멈춥니다. 남은 공시는 다음 실행 때 보냅니다.", file=sys.stderr)
                break
            continue
        failed = 0
        sent.add(item["rcept_no"])
        save_sent(sent, today)  # 한 건 보낼 때마다 적어 둔다. 중간에 멈춰도 보낸 것은 다시 안 보낸다.

    unsent = sum(1 for it in to_send if it["rcept_no"] not in sent)
    print(f"보냄 {len(to_send) - unsent}건, 못 보냄 {unsent}건")
    return 1 if unsent else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AlertError as error:
        print(f"실패: {error}", file=sys.stderr)
        sys.exit(1)

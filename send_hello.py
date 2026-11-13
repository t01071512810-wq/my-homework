"""내 텔레그램 봇이 나에게 "안녕" 한 줄을 보낸다.

실행: python send_hello.py
준비: .env의 TELEGRAM_BOT_TOKEN에 토큰을 넣고, 텔레그램에서 내 봇에게 /start를 보낸다.
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENV_PATH = Path(__file__).with_name(".env")
MESSAGE = "안녕"


class BotError(Exception):
    """사용자에게 그대로 보여줄 오류. 토큰을 메시지에 넣지 않는다."""


def read_env(path):
    values = {}
    if not path.exists():
        return values
    # 메모장이 붙이는 BOM까지 처리하려고 utf-8-sig로 읽는다.
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def call_api(token, method, params=None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(params or {}).encode()
    try:
        # 첫 요청에 30초 넘게 걸린 적이 있어 넉넉하게 기다린다.
        with urllib.request.urlopen(url, data=data, timeout=60) as response:
            body = json.load(response)
    except urllib.error.HTTPError as error:
        # 텔레그램은 실패 이유를 JSON 본문에 담아 돌려준다.
        try:
            body = json.load(error)
        except ValueError:
            raise BotError(f"텔레그램 응답 오류 (HTTP {error.code})") from None
    except OSError as error:
        reason = getattr(error, "reason", error)
        raise BotError(f"텔레그램에 연결하지 못했습니다: {reason}") from None

    if not body.get("ok"):
        code = body.get("error_code")
        if code in (401, 404):
            raise BotError("토큰이 올바르지 않습니다. .env의 값을 BotFather가 준 토큰과 비교해 주세요.")
        raise BotError(f"텔레그램 오류 {code}: {body.get('description')}")
    return body["result"]


def find_chat_id(token):
    """봇에게 말을 건 개인 대화를 찾아 chat_id를 돌려준다."""
    chats = {}
    for update in call_api(token, "getUpdates"):
        chat = update.get("message", {}).get("chat", {})
        if chat.get("type") == "private":
            chats[chat["id"]] = chat.get("first_name", "(이름 없음)")

    if not chats:
        raise BotError("봇이 받은 메시지가 없습니다. 텔레그램에서 내 봇에게 /start를 보낸 뒤 다시 실행해 주세요.")
    if len(chats) > 1:
        listing = ", ".join(f"{name}={chat_id}" for chat_id, name in chats.items())
        raise BotError(
            f"여러 사람이 봇에게 말을 걸었습니다 ({listing}). "
            "내 번호를 .env의 TELEGRAM_CHAT_ID에 넣어 주세요."
        )
    return next(iter(chats))


def main():
    env = read_env(ENV_PATH)
    token = env.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise BotError(".env의 TELEGRAM_BOT_TOKEN= 뒤에 봇 토큰을 넣어 주세요.")

    chat_id = env.get("TELEGRAM_CHAT_ID")
    if not chat_id:
        chat_id = find_chat_id(token)
        print(f"내 chat_id: {chat_id}")
        print("이 번호를 .env의 TELEGRAM_CHAT_ID= 뒤에 넣어 두면 다음부터 수신자가 고정됩니다.")

    call_api(token, "sendMessage", {"chat_id": chat_id, "text": MESSAGE})
    print(f'보냈습니다: "{MESSAGE}"')


if __name__ == "__main__":
    try:
        main()
    except BotError as error:
        print(f"실패: {error}", file=sys.stderr)
        sys.exit(1)

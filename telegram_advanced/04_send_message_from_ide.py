import sys
from pathlib import Path


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from telegram_advanced.telegram_client import (
    TelegramApiError,
    call_telegram,
    default_chat_id,
)


# 1. 아래 MESSAGE 안의 문장을 원하는 내용으로 바꿉니다.
# 2. 저장한 뒤 터미널에서 python 04_send_message_from_ide.py 를 실행합니다.
# 3. .env의 TELEGRAM_CHAT_ID로 메시지가 전송됩니다.
MESSAGE = """
안녕하세요.
IDE에서 직접 수정한 메시지를 Telegram으로 보내는 실습입니다.
정말 입력한 대로 보내지는지 볼까요?
""".strip()


def main() -> None:
    if not MESSAGE:
        raise SystemExit("MESSAGE가 비어 있습니다. 보낼 메시지를 입력하세요.")

    payload = {
        "chat_id": default_chat_id(),
        "text": MESSAGE,
    }

    try:
        data = call_telegram("sendMessage", payload)
    except TelegramApiError as exc:
        raise SystemExit(exc) from exc

    message = data["result"]
    print("IDE 입력 메시지 전송 성공")
    print(f"message_id: {message['message_id']}")
    print("보낸 메시지:")
    print(MESSAGE)


if __name__ == "__main__":
    main()

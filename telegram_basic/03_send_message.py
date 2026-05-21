import argparse

from telegram_client import TelegramApiError, call_telegram, default_chat_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram 메시지 보내기 실습")
    parser.add_argument(
        "text",
        nargs="?",
        default="Python에서 보낸 Telegram 실습 메시지입니다.",
        help="보낼 메시지",
    )
    args = parser.parse_args()

    payload = {
        "chat_id": default_chat_id(),
        "text": args.text,
    }

    try:
        data = call_telegram("sendMessage", payload)
    except TelegramApiError as exc:
        raise SystemExit(exc) from exc

    message = data["result"]
    print("메시지 전송 성공")
    print(f"message_id: {message['message_id']}")
    print(f"chat_id: {message['chat']['id']}")


if __name__ == "__main__":
    main()

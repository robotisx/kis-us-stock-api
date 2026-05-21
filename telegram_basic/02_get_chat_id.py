from typing import Any

from telegram_client import TelegramApiError, call_telegram


CHAT_EVENT_KEYS = (
    "message",
    "edited_message",
    "channel_post",
    "edited_channel_post",
    "my_chat_member",
)


def find_chat(update: dict[str, Any]) -> dict[str, Any] | None:
    for key in CHAT_EVENT_KEYS:
        event = update.get(key)
        if not event:
            continue

        if key == "my_chat_member":
            return event.get("chat")

        return event.get("chat")

    return None


def main() -> None:
    try:
        data = call_telegram("getUpdates")
    except TelegramApiError as exc:
        raise SystemExit(exc) from exc

    updates = data["result"]
    if not updates:
        print("업데이트가 없습니다.")
        print("Telegram에서 봇에게 /start 또는 아무 메시지나 보낸 뒤 다시 실행하세요.")
        return

    print("chat_id 후보:")
    seen_chat_ids = set()

    for update in updates:
        chat = find_chat(update)
        if not chat:
            continue

        chat_id = chat["id"]
        if chat_id in seen_chat_ids:
            continue

        seen_chat_ids.add(chat_id)
        title = chat.get("title") or chat.get("first_name") or chat.get("username") or "(이름 없음)"
        chat_type = chat.get("type", "unknown")
        print(f"- chat_id: {chat_id} | type: {chat_type} | name: {title}")

    if not seen_chat_ids:
        print("chat 정보를 찾지 못했습니다. 봇에게 새 메시지를 보낸 뒤 다시 실행하세요.")


if __name__ == "__main__":
    main()

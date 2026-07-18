"""
실행:
  python telegram_advanced/simple_telegram_trading_bot.py

Telegram 명령:
  /help
  /price AAPL [NAS]
  /balance
  /buy AAPL 1 50.00 [NASD] [00]
  /sell AAPL 1 500.00 [NASD] [00]
  /modify 31372145 AAPL 1 55.00 [NASD]
  /cancel 31372145 AAPL 1 [NASD]

기본값은 DRY-RUN입니다.
실제 주문까지 보내려면 .env 또는 config.yaml에 TELEGRAM_TRADING_LIVE=true 를 넣으세요.
"""

from __future__ import annotations

import io
import os
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Callable

import requests
from dotenv import load_dotenv

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from telegram_advanced import simple_telegram_commands
from chapter1_token import get_access_token
from chapter2_price import get_stock_price
from chapter3_balance import get_my_stocks
from chapter4_buy import send_buy_order
from chapter5_sell import send_sell_order
from chapter8_amend_cancel import amend_cancel_order
from config import TELEGRAM_CHAT_ID, TELEGRAM_TOKEN, load_config


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


load_dotenv()
CONFIG = load_config() or {}

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/{method}"
POLL_TIMEOUT_SECONDS = 20
MAX_MESSAGE_LENGTH = 3900

CommandHandler = Callable[[list[str], str, str | None], str]

BOT_COMMANDS = [
    {"command": "help", "description": "명령어 도움말"},
    {"command": "price", "description": "현재가 조회"},
    {"command": "balance", "description": "잔고 조회"},
    {"command": "buy", "description": "매수 주문"},
    {"command": "sell", "description": "매도 주문"},
    {"command": "modify", "description": "주문 정정"},
    {"command": "cancel", "description": "주문 취소"},
]


def _telegram_context():
    return sys.modules[__name__]


def telegram_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN") or TELEGRAM_TOKEN
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN 또는 TELEGRAM_TOKEN 설정이 필요합니다.")
    return token.strip()


def allowed_chat_id() -> str:
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or TELEGRAM_CHAT_ID
    if not chat_id:
        raise SystemExit("TELEGRAM_CHAT_ID 설정이 필요합니다.")
    return str(chat_id).strip()


def live_trading() -> bool:
    value = os.getenv("TELEGRAM_TRADING_LIVE") or CONFIG.get("TELEGRAM_TRADING_LIVE", "false")
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def call_telegram(method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = TELEGRAM_API_BASE.format(token=telegram_token(), method=method)
    response = requests.post(url, json=payload or {}, timeout=POLL_TIMEOUT_SECONDS + 5)
    data = response.json()

    if not response.ok or not data.get("ok"):
        raise RuntimeError(data.get("description", response.text))

    return data


def send_message(chat_id: str, text: str) -> None:
    chunks = [
        text[i : i + MAX_MESSAGE_LENGTH]
        for i in range(0, len(text), MAX_MESSAGE_LENGTH)
    ] or [""]

    for chunk in chunks:
        call_telegram(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": chunk,
                "link_preview_options": {"is_disabled": True},
            },
        )


def capture_output(func: Callable[..., Any], *args: Any) -> tuple[Any, str]:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        result = func(*args)
    return result, buffer.getvalue().strip()


def get_token_or_fail() -> str:
    token = get_access_token()
    if not token:
        raise RuntimeError("KIS access token 발급에 실패했습니다. config.yaml을 확인하세요.")
    return token


def parse_positive_int(value: str, name: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise ValueError(f"{name}은 정수로 입력하세요: {value}") from exc

    if number <= 0:
        raise ValueError(f"{name}은 1 이상이어야 합니다.")
    return number


def parse_positive_price(value: str) -> float:
    try:
        price = float(value)
    except ValueError as exc:
        raise ValueError(f"가격은 숫자로 입력하세요: {value}") from exc

    if price <= 0:
        raise ValueError("가격은 0보다 커야 합니다.")
    return round(price, 2)


def normalize_symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not symbol.isalnum():
        raise ValueError("종목코드는 영문/숫자만 입력하세요.")
    return symbol


def dry_run_message(title: str) -> str:
    return (
        "DRY-RUN 모드입니다.\n"
        "실제 주문은 전송하지 않았습니다.\n\n"
        f"{title}\n\n"
        "실제 주문을 보내려면 TELEGRAM_TRADING_LIVE=true 로 바꾼 뒤 다시 실행하세요."
    )


def _handle_help(parts: list[str], chat_id: str, token: str | None) -> str:
    return simple_telegram_commands.handle_help(_telegram_context(), parts, chat_id, token)


def _handle_balance(parts: list[str], chat_id: str, token: str | None) -> str:
    return simple_telegram_commands.handle_balance(_telegram_context(), parts, chat_id, token)


def _handle_price(parts: list[str], chat_id: str, token: str | None) -> str:
    return simple_telegram_commands.handle_price(_telegram_context(), parts, chat_id, token)


def _handle_buy(parts: list[str], chat_id: str, token: str | None) -> str:
    return simple_telegram_commands.handle_buy(_telegram_context(), parts, chat_id, token)


def _handle_sell(parts: list[str], chat_id: str, token: str | None) -> str:
    return simple_telegram_commands.handle_sell(_telegram_context(), parts, chat_id, token)


def _handle_modify(parts: list[str], chat_id: str, token: str | None) -> str:
    return simple_telegram_commands.handle_modify(_telegram_context(), parts, chat_id, token)


def _handle_cancel(parts: list[str], chat_id: str, token: str | None) -> str:
    return simple_telegram_commands.handle_cancel(_telegram_context(), parts, chat_id, token)


COMMANDS: dict[str, CommandHandler] = {
    "/start": _handle_help,
    "/help": _handle_help,
    "/price": _handle_price,
    "/balance": _handle_balance,
    "/buy": _handle_buy,
    "/sell": _handle_sell,
    "/modify": _handle_modify,
    "/cancel": _handle_cancel,
}


def help_text() -> str:
    return simple_telegram_commands.build_help_text(_telegram_context())


def normalize_command(value: str) -> str:
    return "/" + value.lstrip("/").split("@")[0].lower()


def _dispatch_command(command: str, parts: list[str], chat_id: str, token: str | None) -> str | None:
    handler = COMMANDS.get(command)
    if handler is None:
        return None

    try:
        return handler(parts, chat_id, token)
    except Exception as exc:
        return f"명령 처리 중 오류가 발생했습니다.\n{exc}"


def handle_command(text: str, chat_id: str = "") -> str:
    parts = text.strip().split()
    if not parts:
        return help_text()

    command = normalize_command(parts[0])
    reply = _dispatch_command(command, parts, chat_id, token=None)
    if reply is not None:
        return reply

    return f"알 수 없는 명령입니다: {command}\n\n{help_text()}"


def poll_updates(offset: int | None) -> list[dict[str, Any]]:
    payload: dict[str, Any] = {
        "timeout": POLL_TIMEOUT_SECONDS,
        "allowed_updates": ["message"],
    }
    if offset is not None:
        payload["offset"] = offset
    return call_telegram("getUpdates", payload)["result"]


def delete_webhook_for_polling() -> None:
    call_telegram("deleteWebhook", {"drop_pending_updates": False})


def sync_bot_commands() -> None:
    call_telegram("setMyCommands", {"commands": BOT_COMMANDS})


def latest_update_offset() -> int | None:
    updates = call_telegram(
        "getUpdates",
        {"timeout": 0, "allowed_updates": ["message"]},
    )["result"]
    if not updates:
        return None
    return updates[-1]["update_id"] + 1


def startup_message() -> str:
    mode = "LIVE" if live_trading() else "DRY-RUN"
    return (
        "Simple Telegram bot started.\n"
        f"현재 실행 모드: {mode}\n\n"
        "명령어 도움말: /help"
    )


def run_bot() -> None:
    my_chat_id = allowed_chat_id()

    try:
        delete_webhook_for_polling()
        sync_bot_commands()
    except Exception as exc:
        print(f"Startup setup warning: {exc}")

    offset = latest_update_offset()
    print(f"Simple Telegram bot started. mode={'LIVE' if live_trading() else 'DRY-RUN'}")
    print("Ctrl+C로 종료합니다.")

    try:
        send_message(my_chat_id, startup_message())
    except Exception as exc:
        print(f"Startup notification warning: {exc}")

    while True:
        try:
            for update in poll_updates(offset):
                offset = update["update_id"] + 1
                message = update.get("message") or {}
                chat_id = str((message.get("chat") or {}).get("id", ""))
                text = message.get("text", "")

                if not text:
                    continue

                if chat_id != my_chat_id:
                    send_message(chat_id, "허용되지 않은 chat_id입니다.")
                    continue

                reply = handle_command(text, chat_id)
                send_message(chat_id, reply)
        except KeyboardInterrupt:
            print("Simple Telegram bot stopped.")
            break
        except Exception as exc:
            print(f"Polling error: {exc}")
            time.sleep(3)


if __name__ == "__main__":
    run_bot()

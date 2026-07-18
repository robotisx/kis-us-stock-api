import os
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()

API_BASE_URL = "https://api.telegram.org/bot{token}/{method}"


class TelegramApiError(RuntimeError):
    pass


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"{name} 환경 변수가 비어 있습니다. .env 파일을 확인하세요.")
    return value.strip()


def bot_token() -> str:
    return require_env("TELEGRAM_BOT_TOKEN")


def default_chat_id() -> str:
    return require_env("TELEGRAM_CHAT_ID")


def call_telegram(method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    token = bot_token()
    url = API_BASE_URL.format(token=token, method=method)

    try:
        response = requests.post(url, json=payload or {}, timeout=15)
    except requests.RequestException as exc:
        raise TelegramApiError(f"Telegram API 요청 실패: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise TelegramApiError(f"JSON 응답 파싱 실패: {response.text}") from exc

    if not response.ok or not data.get("ok"):
        description = data.get("description", response.text)
        raise TelegramApiError(f"{method} 실패: {description}")

    return data

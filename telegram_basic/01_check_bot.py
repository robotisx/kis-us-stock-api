# 강의용 .env 파일 만들기
#
# GitHub에는 실제 .env 파일을 올리지 않습니다.
# 수강생은 프로젝트 폴더에 .env 파일을 직접 만들고, 아래 내용을 복사해서 넣습니다.
#
# TELEGRAM_BOT_TOKEN=put-your-bot-token-here
# TELEGRAM_CHAT_ID=
#
# TELEGRAM_BOT_TOKEN에는 BotFather에서 받은 봇 토큰을 넣습니다.
# TELEGRAM_CHAT_ID는 02_get_chat_id.py 실행 후 확인한 값을 넣습니다.

from telegram_client import TelegramApiError, call_telegram


def main() -> None:
    try:
        data = call_telegram("getMe")
    except TelegramApiError as exc:
        raise SystemExit(exc) from exc

    bot = data["result"]
    print("봇 토큰 확인 성공")
    print(f"id: {bot['id']}")
    print(f"first_name: {bot['first_name']}")
    print(f"username: @{bot['username']}")


if __name__ == "__main__":
    main()

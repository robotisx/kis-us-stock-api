"""
Chapter 1: 토큰 발급 및 재사용 (OAuth Authentication)

💡 [실습 0단계: 환경 설정]
아래 코드를 실행하기 전, 반드시 같은 폴더 안에 `config.yaml` 이라는 이름의
설정 파일을 직접 생성하시고, 본인이 발급받은 실제 정보를 기입하셔야 합니다.

----- [아래 내용을 복사하여 config.yaml 파일에 붙여넣고 수정하세요] -----
APP_KEY: '이곳에_본인의_API_키를_입력하세요'
APP_SECRET: '이곳에_본인의_API_시크릿을_입력하세요'

htsid: '이곳에_본인의_HTS_ID를_입력하세요'
custtype: 'P'  # 개인은 P, 법인은 B
is_paper_trading: False  # 모의투자 시 True로 변경

# API 호출 기본 URL (실전투자)
URL_BASE: "https://openapi.koreainvestment.com:9443"

# 모의투자인 경우 위 두 줄을 주석(#) 처리하고 아래 주석을 해제하세요.
# URL_BASE: "https://openapivts.koreainvestment.com:29443"

# 본인의 10자리 계좌번호를 앞 8자리와 뒤 2자리로 나누어 입력
CANO: '12345678'
ACNT_PRDT_CD: '01'
--------------------------------------------------------------------------

🎯 강의 목표:
   한국투자증권(KIS) API 플랫폼과 통신하기 위한 보안 인증 과정,
   즉 '접근 토큰(Access Token)'을 발급받는 방법을 실습합니다.

📌 핵심 포인트:
   1. 모든 API 호출의 필수 조건: [토큰 발급] → [HTTP 헤더에 포함] → [API 호출]
   2. 한 번 발급된 토큰은 24시간 동안 유효합니다.
   3. 매번 요청 시마다 새로 발급받지 않도록, 'token.json' 파일에 저장하고 재사용하는 구조를 권장합니다.
   4. 대부분의 KIS API는 헤더(Header)에 인증 정보를 넣지만, [토큰 발급 API]만 유일하게 본문(Body)에 키 데이터를 전송합니다.
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
import requests
from config import APP_KEY, APP_SECRET, URL_BASE

TOKEN_FILE = "token.json"
KST = timezone(timedelta(hours=9))


def _parse_token_expiry(value):
    """KST 만료 시각 문자열을 timestamp(초)로 바꿉니다."""
    if value in (None, ""):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    try:
        parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        return parsed.replace(tzinfo=KST).timestamp()
    except ValueError:
        return None


def _get_saved_token_expiry(saved_token):
    """저장된 토큰 정보에서 만료 시각을 꺼냅니다."""
    expires_at = _parse_token_expiry(saved_token.get("access_token_token_expired"))
    if expires_at is not None:
        return expires_at

    return _parse_token_expiry(saved_token.get("expires_at"))


def _format_expiry(expires_at):
    """timestamp를 읽기 쉬운 KST 시각 문자열로 바꿉니다."""
    if expires_at is None:
        return "알 수 없음"
    return datetime.fromtimestamp(expires_at, KST).strftime("%Y-%m-%d %H:%M:%S KST")


def _format_token_expiry_raw(expires_at):
    if expires_at is None:
        return None
    return datetime.fromtimestamp(expires_at, KST).strftime("%Y-%m-%d %H:%M:%S")


def _get_expiry_roundtrip_info(raw_value, expires_at):
    restored_expiry_text = _format_token_expiry_raw(expires_at)
    expiry_roundtrip_matches = (
        str(raw_value).strip() == restored_expiry_text
        if raw_value not in (None, "")
        else False
    )
    return restored_expiry_text, expiry_roundtrip_matches


def get_access_token():
    """저장된 토큰을 재사용하고, 없거나 만료되면 새로 발급합니다."""
    if not APP_KEY or not APP_SECRET:
        print("config.yaml에서 APP_KEY 또는 APP_SECRET을 찾을 수 없습니다.")
        return None

    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                saved_token = json.load(f)

            saved_token_expired_time = saved_token.get("access_token_token_expired")
            expires_at = _get_saved_token_expiry(saved_token)
            restored_expiry_text, expiry_roundtrip_matches = _get_expiry_roundtrip_info(
                saved_token_expired_time, expires_at
            )
            now = time.time()

            # 만료 60초 전까지는 저장된 토큰을 그대로 사용합니다.
            if expires_at is not None and now < expires_at - 60:
                print("저장된 유효한 토큰을 재사용합니다.")
                print(f"만료 시각: {_format_expiry(expires_at)}")
                # print(f"남은 시간: {int(expires_at - now)}초")
                # print(f"저장된 만료 시각(원본): {saved_token_expired_time}")
                # print(f"저장된 만료 시각(복원): {restored_expiry_text}")
                # print(f"저장된 만료 시각 왕복 검증: {expiry_roundtrip_matches}")
                return saved_token.get("access_token")

            print("저장된 토큰이 만료되었거나 만료 시각을 확인할 수 없어 새 토큰을 발급합니다.")
        except Exception as e:
            print(f"저장된 토큰 파일을 읽는 중 문제가 발생했습니다: {e}")

    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }

    print(f"한국투자증권 서버에 새 토큰을 요청합니다... ({URL_BASE})")

    try:
        res = requests.post(
            f"{URL_BASE}/oauth2/tokenP",
            # headers=headers,
            data=json.dumps(body),
            timeout=10,
        )

        if res.status_code != 200:
            print(f"토큰 발급에 실패했습니다. HTTP 상태 코드: {res.status_code}")
            print(res.text)
            return None

        data = res.json()
        access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 0))
        token_expired_time = data.get("access_token_token_expired")

        expires_at = _parse_token_expiry(token_expired_time)
        restored_expiry_text, expiry_roundtrip_matches = _get_expiry_roundtrip_info(
            token_expired_time, expires_at
        )
        # 실제 만료 시각이 없을 때만 expires_in으로 만료 시간을 계산합니다.
        if expires_at is None and expires_in > 0:
            expires_at = time.time() + expires_in

        print("새 토큰이 성공적으로 발급되었습니다.")
        print(f"발급된 토큰(앞 20자리): {access_token[:20]}...")
        print(f"API 응답 만료값(expires_in): {expires_in}초")
        print(f"실제 만료 시각(원본): {token_expired_time}")
        # print(f"실제 만료 시각: {_format_expiry(expires_at)}")
        # print(f"실제 만료 시각(복원): {restored_expiry_text}")
        # print(f"만료 시각 왕복 검증: {expiry_roundtrip_matches}")

        token_data = {
            "access_token": access_token,
            "access_token_token_expired": token_expired_time,
            "expires_at": expires_at,
        }

        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(token_data, f, ensure_ascii=False, indent=2)

        print(f"토큰을 {TOKEN_FILE} 파일에 저장했습니다.")
        return access_token
    except Exception as e:
        print(f"토큰 요청 중 오류가 발생했습니다: {e}")
        return None


if __name__ == "__main__":
    get_access_token()

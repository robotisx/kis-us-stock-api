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

import requests
import json
import time
import os
from config import APP_KEY, APP_SECRET, URL_BASE

TOKEN_FILE = 'token.json'

def get_access_token():
    """앱키와 앱시크릿을 이용하여 24시간 유효한 접근 토큰을 발급받거나 기존 토큰을 재사용합니다."""
    
    # API 키 누락 확인
    if not APP_KEY or not APP_SECRET:
        print("❌ config.yaml에서 APP_KEY 또는 APP_SECRET을 찾을 수 없습니다.")
        return None

    # Step 1: 디스크에 저장된 기존 토큰 재사용 (API 호출 횟수 절약 및 차단 방지)
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                saved_token = json.load(f)
            
            # 토큰 유효기간 확인 (재발급 기준: 만료 60초 전까지는 기존 토큰 사용)
            expires_at = saved_token.get('expires_at', 0)
            now = time.time()
            
            if now < expires_at - 60:
                print("✅ 24시간이 지나지 않은 유효한 토큰이 발견되어 이를 재사용합니다.")
                print(f"만료까지 남은 시간: {int(expires_at - now)}초")
                return saved_token.get('access_token')
            else:
                print("⚠️ 저장된 토큰의 유효기간이 만료되었습니다. 새 토큰 발급이 필요합니다.")
        except Exception as e:
            print(f"⚠️ 토큰 파일을 읽는 중 문제가 발생했습니다: {e}")

    # Step 2: 새 인증 토큰 발급 요청
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET
    }
    
    print(f"🔑 한국투자증권 서버에 새 토큰을 요청합니다... ({URL_BASE})")
    try:
        res = requests.post(f"{URL_BASE}/oauth2/tokenP", 
                           headers=headers, 
                           data=json.dumps(body))
        
        if res.status_code == 200:
            data = res.json()
            access_token = data['access_token']
            expires_in = int(data['expires_in'])
            
            print("✅ 새 토큰이 성공적으로 발급되었습니다!")
            print(f"발급된 토큰 (보안상 앞부분만): {access_token[:20]}...")
            print(f"만료시간: {expires_in}초 (약 {expires_in/3600:.1f}시간)")
            
            # Step 3: 발급받은 토큰을 로컬 파일에 저장
            token_data = {
                "access_token": access_token,
                "expires_at": time.time() + expires_in
            }
            
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(token_data, f)
            print(f"💾 향후 재활용을 위해 토큰을 저장했습니다: {TOKEN_FILE}")
            
            return access_token
        else:
            print(f"❌ 토큰 발급에 실패했습니다. (HTTP 상태 코드: {res.status_code})")
            print(res.text)
            return None
    except Exception as e:
        print(f"❌ API 서버 연결 중 오류가 발생했습니다: {e}")
        return None

if __name__ == "__main__":
    # 스크립트 직접 실행 시 테스트해볼 수 있습니다.
    token = get_access_token()

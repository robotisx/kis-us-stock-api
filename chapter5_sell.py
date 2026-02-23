"""
Chapter 5: 해외주식 매도 주문

🎯 강의 목표:
   보유하고 있는 해외 주식을 매도하는 API 사용법을 마스터합니다.
   매수 주문(Chapter 4)과 비교하여 TR_ID가 어떻게 다르게 쓰이는지 살펴봅니다.

📌 핵심 포인트:
   1. 매도(Sell) 요청에 쓰이는 TR_ID는 매수(Buy)와 코드가 다릅니다.
      - 주간 매도: TTTS6037U (주간 매수는 TTTS6036U 이었음)
      - 정규장 매도: TTTT1006U (정규장 매수는 TTTT1002U 이었음)
   2. 주문 유형은 매수와 동일하게 "00"(지정가), "34"(LOC) 
      혹은 심지어 시장가를 의미하는 "33"(MOC), "31"(MOO) 등도 활용 가능합니다.
   3. 장 마감 지정가(LOC) 등의 조건부 주문은 정규장(호가제출시간 포함) 내에서 전송해야 합니다.
"""

import requests
import json
import datetime
from config import APP_KEY, APP_SECRET, URL_BASE, CANO, ACNT_PRDT_CD
from chapter1_token import get_access_token
from chapter4_buy import hashkey

def send_sell_order(token, symbol, qty, price, market="NASD", order_type="00"):
    """
    해외주식 매도 주문 전송
    """
    try:
        qty_int = int(qty)
        round_price = round(float(price), 2)
    except:
        print("❌ 매도 수량 또는 단가의 형식이 올바르지 않습니다.")
        return None

    now = datetime.datetime.now()
    is_daytime = 10 <= now.hour < 18

    # 1. TR_ID 세팅 (매수와 코드가 구별됨을 주의하세요!)
    if is_daytime:
        tr_id = "TTTS6037U"  # 데이 마켓 매도
        url = f"{URL_BASE}/uapi/overseas-stock/v1/trading/daytime-order"
        print("☀️ 주간거래 기반으로 매도 주문을 넣습니다.")
    else:
        # 모의투자와 실전투자 TR_ID 자동 매핑 분기
        if "openapivts" in URL_BASE:
            tr_id = "VTTS1001U"
        else:
            tr_id = "TTTT1006U"  # 정규장 실전 매도
        url = f"{URL_BASE}/uapi/overseas-stock/v1/trading/order"
        print("🌙 정규장/야간 기반으로 매도 주문을 넣습니다.")

    # 2. 페이로드 바디 데이터 조립
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": market,
        "PDNO": symbol,
        "ORD_DVSN": order_type,
        "ORD_QTY": str(qty_int),
        "OVRS_ORD_UNPR": f"{round_price}",
        "ORD_SVR_DVSN_CD": "0"
    }

    # 3. HTTP 헤더 조립
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appKey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P"
    }

    # 4. 해시키 생성 (권장)
    if tr_id == "TTTT1006U":
        print("🔑 매도 요청 데이터를 해시키 변환하여 안전하게 암호화합니다.")
        headers["hashkey"] = hashkey(data)

    print(f"🚀 매도 주문 발송: [{symbol}] {qty_int}주 @ ${round_price}")
    res = requests.post(url, headers=headers, data=json.dumps(data), timeout=15)

    if res.status_code == 200:
        ret = res.json()
        if ret['rt_cd'] == '0':
            order_no = ret['output']['ODNO']
            print(f"✅ 매도 주문 접수 성공! (부여된 주문번호: {order_no})")
            return order_no
        else:
            error_msg = ret['msg1']
            print(f"❌ 매도 실패 사유: {error_msg}")

            # 부가 팁: 미국 휴장일에 요청하면 휴장 관련 에러 메시지가 리턴됩니다.
            # "영업일" 휴장" 등의 키워드가 포함될 수 있습니다.
    else:
        print(f"❌ 매도 주문 시 통신 에러 발생. 상태 코드: {res.status_code}")
        print(res.text)

    return None

if __name__ == "__main__":
    print("💼 주식 매도 주문 실습 (Chapter 5)\n")
    print("⚠️ (주의) 본 코드를 바로 돌리면 매도 주문이 접수될 수 있습니다.")
    print("보유 잔고가 없다면 '주문수량 초과' 등의 에러가 발생하며 테스트로 적합하기도 합니다.\n")

    token = get_access_token()
    if token:
        # 안전한 테스트를 위해 현재 시장가보다 한참 높은 말도 안되는 매수가를 입력해 봅니다.
        test_symbol = "TSLA"
        test_qty = 1
        test_price = 500.00  # 보유중이더라도 지정가가 너무 높아서 체결되지 않습니다.

        print("=== 지정가 매도 트라이 ===")
        send_sell_order(token, test_symbol, test_qty, test_price)

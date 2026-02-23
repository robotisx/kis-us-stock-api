"""
Chapter 4: 해외주식 매수 주문 (지정가 및 LOC 장마감지정가)

🎯 강의 목표:
   한국투자증권 API를 호출하여 해외 주식을 매수하는 구체적인 방법을 실습합니다.
   시장가나 흔히 쓰는 지정가(LIMIT) 형태뿐 아니라, 미국 주식에서 활용도가 높은
   LOC(장마감지정가) 주문의 개념과 차이를 이해합니다.

📌 핵심 포인트:
   1. 시간대에 따른 TR_ID 구분:
      미국 주식 시장은 주간/프리마켓/정규장/애프터마켓 등 세션이 나뉘며,
      호출하는 TR_ID가 주간거래와 정규장에 따라 다릅니다.
   2. 주문 유형 (ORD_DVSN): 
      - "00": 일반 지정가 (LIMIT)
      - "34": LOC (Limit On Close) - 장 마감 시점에 지정한 가격 혹은 더 유리한 가격으로 체결됩니다.
   3. ⭐️ 주의사항:
      - 모의투자 환경(VTTT1002U)에서는 현재 "00"(지정가) 주문만 지원합니다.

📌 미국 주식 세션 시간 (한국시간 KST 기준):
   ┌──────────┬──────────────────┬──────────────────┐
   │  세션명  │  서머타임(Summer)│  표준시(Winter)  │
   ├──────────┼──────────────────┼──────────────────┤
   │ 주간거래 │  10:00 ~ 17:00   │  10:00 ~ 18:00   │
   │ 프리마켓 │  17:00 ~ 22:30   │  18:00 ~ 23:30   │
   │ 정규장   │  22:30 ~ 05:00   │  23:30 ~ 06:00   │
   │ 애프터마켓
     (연장시)  │  05:00 ~ 09:00   │  06:00 ~ 09:00   │
   └──────────┴──────────────────┴──────────────────┘
"""

import requests
import json
import datetime
from config import APP_KEY, APP_SECRET, URL_BASE, CANO, ACNT_PRDT_CD
from chapter1_token import get_access_token

def hashkey(datas):
    """
    정규장 주문 시 보안을 위해 필요한 해시키(Hashkey) 생성 함수입니다.
    Body 데이터를 암호화하여 요청 헤더에 포함합니다. (실전 투자 시 권장됨)
    """
    headers = {
        "content-type": "application/json",
        "appKey": APP_KEY,
        "appsecret": APP_SECRET
    }
    res = requests.post(f"{URL_BASE}/uapi/hashkey", headers=headers, data=json.dumps(datas))
    if res.status_code == 200:
        return res.json()["HASH"]
    else:
        print("❌ 해시키 발급에 실패했습니다.")
        return ""

def send_buy_order(token, symbol, qty, price, market="NASD", order_type="00"):
    """
    해외주식 매수 주문을 서버로 전송합니다.

    Args:
        token (str): 발급받은 접근 토큰
        symbol (str): 주문할 종목코드 (예: AAPL)
        qty (int): 주문 수량
        price (float): 주문 단가 (지정가 기준 달러)
        market (str): 시장 구분 (NASD, NYSE, AMEX)
        order_type (str): 주문 유형 ("00": 지정가, "34": LOC 등)
    """
    try:
        qty_int = int(qty)
        round_price = round(float(price), 2)
    except:
        print("❌ 수량 또는 가격 숫자로 변환하는 데 실패했습니다.")
        return None

    now = datetime.datetime.now()
    is_daytime = 10 <= now.hour < 18  # KST 기준 대략적인 주간거래 시간

    if is_daytime:
        tr_id = "TTTS6036U"
        url = f"{URL_BASE}/uapi/overseas-stock/v1/trading/daytime-order"
        print("☀️ [시간감지] 주간거래(데이타임) 매수 주문으로 진행합니다.")
        
        # ⚠️ 주간거래 시간대에는 LOC 주문이 불가능하므로 강제로 지정가로 변경
        if order_type in ["34", "33", "32", "31"]:
            print(f"   ⚠️ 주간거래에서는 LOC/MOC가 불가능하여 지정가(LIMIT)로 자동 변경합니다.")
            order_type = "00"
    else:
        # 야간(정규장) 주문 TR ID (실전투자 기준코드)
        tr_id = "TTTT1002U"
        url = f"{URL_BASE}/uapi/overseas-stock/v1/trading/order"
        print("🌙 [시간감지] 정규장/미국야간 매수 주문으로 진행합니다.")

    order_type_names = {
        "00": "지정가(LIMIT)",
        "34": "LOC(장마감지정가)",
        "33": "MOC(장마감시장가)",
        "32": "LOO(장시작지정가)",
        "31": "MOO(장시작시장가)"
    }
    order_type_name = order_type_names.get(order_type, f"알 수 없는 유형({order_type})")
    print(f"📋 주문 유형: {order_type_name}")

    # 요청 매개변수 조립
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

    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appKey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P"
    }

    # 정규장 실전투자 매수일 경우 해시키 추가 적용
    if tr_id == "TTTT1002U":
        print("🔑 해시키 암호화 적용 중...")
        headers["hashkey"] = hashkey(data)

    print(f"🚀 실서버 주문 전송: [{symbol}] {qty_int}주 @ ${round_price} ({order_type_name})")
    res = requests.post(url, headers=headers, data=json.dumps(data), timeout=15)

    if res.status_code == 200:
        output = res.json()
        if output['rt_cd'] == '0':
            order_no = output['output']['ODNO']
            print(f"✅ 매수 주문 성공! 🥳 (부여된 주문번호: {order_no})")
            if order_type == "34":
                print(f"   ⏰ LOC 주문 특성상 장 마감 시간인 새벽(KST 06:00경) 직후 체결 여부가 확정됩니다.")
            return order_no
        else:
            print(f"❌ 매수 요청 실패 (API 서버 응답): {output['msg1']}")
    else:
        print(f"❌ 매수 요청 실패 (HTTP 에러 통신): {res.status_code}")
        print(res.text)

    return None

def explain_order_types():
    """초보자를 위한 주요 주문 유형 설명 테이블 출력"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                  📋 매수 주문 유형 요약 가이드             ║
╠═══════════╦══════╦═════════════════════════════════════════╣
║   유형    ║ 코드 ║                주요 특징                ║
╠═══════════╬══════╬═════════════════════════════════════════╣
║  LIMIT    ║  00  ║ 지정가 (일반) 지정 단가 도달 시 체결    ║
║  LOO      ║  32  ║ 장시작지정가 (장 개장 순간에만 판단)    ║
║  LOC      ║  34  ║ 장마감지정가 (장 마감 순간 종가로 판단) ║
╚═══════════╩══════╩═════════════════════════════════════════╝
💡 KIS API 모의투자에서는 현재 지정가(00) 주문만 허용됩니다.
    """)

if __name__ == "__main__":
    explain_order_types()

    token = get_access_token()
    if token:
        # [주의] 이 스크립트를 직접 실행하면 실제로 주문이 들어갑니다!
        # 실습을 위해 안전한 가격인 초저가로 테스트합니다.
        test_symbol = "AAPL"
        test_qty = 1
        test_price = 50.00  # 비현실적으로 낮은 가격을 주어 미체결에 남게 만듭니다.

        print(f"\n===== 🛒 지정가 (LIMIT) 매수 예제 ({test_symbol}) =====")
        send_buy_order(token, test_symbol, test_qty, test_price, order_type="00")

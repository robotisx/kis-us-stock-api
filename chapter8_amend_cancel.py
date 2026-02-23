"""
Chapter 8: 해외주식 주문 정정 및 취소

🎯 강의 목표:
   이미 계좌에 전송되어 활성화(미체결)된 주문의 가격/수량을 수정(정정)하거나 
   아예 파기(취소)하는 API의 호출 방법을 배웁니다.

📌 핵심 포인트:
   1. 정정/취소는 주문 번호의 연계성이 매우 중요합니다.
      - 본 API를 호출할 때는 무조건 원래 발생했던 **'원주문번호(ORGN_ODNO)'**가 필수 파라미터로 요구됩니다.
   2. 요청 구분 파라미터 (`RVSE_CNCL_DVSN_CD`):
      - "01": 정정 (주문의 단가나 수량을 수정)
      - "02": 취소 (주문을 즉시 파기)
   3. 정정 시 새로운 주문번호 부여:
      - 증권사 시스템 상, 정정을 요청하면 기존 주문번호가 아니라 '새로운 주문번호'가 발급되어 되돌아옵니다.
      - 따라서 정정 이후 미체결 추적 시 새로운 번호로 모니터링해야 합니다.
"""

import requests
import json
import datetime
from config import APP_KEY, APP_SECRET, URL_BASE, CANO, ACNT_PRDT_CD
from chapter1_token import get_access_token
from chapter4_buy import hashkey


def amend_cancel_order(token, org_order_no, symbol, qty, price, type="CANCEL", market="NASD"):
    """
    주문 정정 또는 취소 통합 함수입니다.

    Args:
        token (str): 발급받은 API 토큰
        org_order_no (str): 수정/취소하고자 하는 대상의 원래 주민번호(원주문번호) 
        symbol (str): 종목코드 (예: AAPL)
        qty (int): 남길 수량 (취소는 일반적으로 원수량, 정정은 변경할 수량)
        price (float): 정정할 단가 (취소인 경우는 0으로 전달)
        type (str): "CANCEL" 또는 "MODIFY"
        market (str): 시장 코드 정 (NASD, NYSE, AMEX)
    """
    # 1. 정정(01) / 취소(02) 플래그 코드 설정
    if type == "MODIFY":
        dvsn_cd = "01"
        print(f"🛠️ [정정] 주문 {org_order_no}번의 매매단가를 ${price}(으)로 정정 요청합니다.")
    else:
        dvsn_cd = "02"
        print(f"🗑️ [취소] 주문 {org_order_no}번의 매매 시도를 철회(취소) 요청합니다.")

    now = datetime.datetime.now()
    is_daytime = 10 <= now.hour < 18

    # 2. TR_ID 설정 (시간대 및 모의/실전 적용)
    if is_daytime:
        tr_id = "TTTS6038U"  # 주간거래 정정/취소용
        url = f"{URL_BASE}/uapi/overseas-stock/v1/trading/daytime-order-rvsecncl"
    else:
        if "openapivts" in URL_BASE:
            tr_id = "VTTT1004U"  # 모의투자
        else:
            tr_id = "TTTT1004U"  # 실전투자
        url = f"{URL_BASE}/uapi/overseas-stock/v1/trading/order-rvsecncl"

    # 3. 바디 데이터 (Body JSON) 조립
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": market,
        "PDNO": symbol,
        "ORGN_ODNO": org_order_no,       # ⭐ 가장 중요한 핵심 파라미터
        "RVSE_CNCL_DVSN_CD": dvsn_cd,    # 01(정정), 02(취소)
        "ORD_QTY": str(qty),
        "OVRS_ORD_UNPR": str(price),
        "ORD_SVR_DVSN_CD": "0"           # 고정값 (0)
    }

    # 데이마켓(주간거래)에는 부가적인 빈 항목이 스펙상 필요하기도 합니다.
    if is_daytime:
        data["CTAC_TLNO"] = ""
        data["MGCO_APTM_ODNO"] = ""

    # 4. 헤더 설정
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appKey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P"
    }

    # 5. 해시키 (실전 정규장의 경우 보안 적용)
    if tr_id == "TTTT1004U":
        headers["hashkey"] = hashkey(data)

    # 6. 전송 및 결과 확인
    res = requests.post(url, headers=headers, data=json.dumps(data), timeout=15)

    if res.status_code == 200:
        ret = res.json()
        if ret['rt_cd'] == '0':
            print("✅ 정상적으로 요청이 수락되었습니다!")
            if type == "MODIFY":
                # 정정 성공 시 서버에서 해당 주문 건에 대한 '새로운 주문번호'를 반환합니다.
                new_order_no = ret.get('output', {}).get('ODNO') or ret.get('output', {}).get('KRX_FWDG_ORD_ORGNO', '알수없음')
                print(f"👉 주의: 정정된 건부터는 원래 번호가 폐기되고 [{new_order_no}] 번호로 새로 관리됩니다.")
            return True
        else:
            msg = ret['msg1']
            print(f"❌ 증권사 시스템 에러로 거부됨: {msg}")
    else:
        print(f"❌ 통신 에러 발생. 상태 코드: {res.status_code}")
        print(res.text)

    return False


if __name__ == "__main__":
    print("✂️ 주문 정정/취소(Amend & Cancel) 파라미터 실습 (Chapter 8)\n")
    
    token = get_access_token()
    if token:
        # ⚠️ 테스트 방법: 
        # 실제로 활성화(미체결)되어 있는 주문 번호가 아니면 API 특성 상 
        # "원주문내역을 찾을 수 없습니다" 등으로 실패합니다.
        
        target_dummy_order_no = "0030072265"  # 조회해서 얻은 가상의 미체결 원주문번호
        test_symbol = "AAPL"

        print("=== 1. 활성화된 매수/매도 주문 취소 시도 ===")
        print(" (가상 번호인 경우 원주문번호 조회 실패 에러가 발생하는 것이 정상입니다.)")
        # amend_cancel_order(token, org_order_no=target_dummy_order_no, symbol=test_symbol, qty=1, price=0, type="CANCEL")

        # print("\n=== 2. 활성화된 주문 달러 단가 정정 시도 ===")
        amend_cancel_order(token, org_order_no=target_dummy_order_no, symbol=test_symbol, qty=1, price=100.0, type="MODIFY")

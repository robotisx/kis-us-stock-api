"""
Chapter 6: 미체결 주문 조회 (Pending Orders)

🎯 강의 목표:
   내가 낸 주문(매수/매도) 중 아직 체결되지 않고 호가창에 남아(대기 중) 있는 
   내역 리스트를 가져오는 법을 익힙니다.

📌 핵심 포인트:
   1. TR_ID: TTTS3018R (실전투자) / VTTS3018R (모의투자)
   2. 미체결 조회를 호출하여 확인된 주문번호(odno)를 이용하여 추후 주문을 
      수정(정정)하거나 취소할 수 있습니다.
   3. 요청 파라미터 내 `SORT_SQN`을 "DS"로 주면 정순(먼저 주문한 순서대로) 정렬되며,
      빈칸("")이나 다른 값을 주면 역순(최근 주문 순)으로 정렬됩니다.
   4. 체결된 내역은 반환되지 않습니다! 체결 내역 조회는 다음 챕터에서 학습합니다.

📌 응답 파싱 유의사항:
   결과 객체 `output`은 배열 형태로 넘어오며, 
   `sll_buy_dvsn_cd` 필드 값이 "02"면 매수, "01"은 매도 주문을 의미합니다.
"""

import requests
from config import APP_KEY, APP_SECRET, URL_BASE, CANO, ACNT_PRDT_CD
from chapter1_token import get_access_token

def get_pending_orders(token):
    """
    현재 계좌에서 미체결 상태로 남아있는 모든 해외주식 주문을 조회합니다.
    """
    if "openapi.koreainvestment.com" in URL_BASE:
        tr_id = "TTTS3018R"
    else:
        tr_id = "VTTS3018R"
    
    headers = {
        "authorization": f"Bearer {token}",
        "appKey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
    }
    
    # 미체결 조회 API의 쿼리 스트링 매개변수
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": "NASD",  # 전 시장 통합 "NASD" 
        "SORT_SQN": "DS",        # DS: 정순 (먼저 주문한 것부터), 그외: 역순 (최근 주문부터)
        "CTX_AREA_FK200": "",    # 페이징 시작키
        "CTX_AREA_NK200": ""
    }
    
    try:
        res = requests.get(
            f"{URL_BASE}/uapi/overseas-stock/v1/trading/inquire-nccs",
            headers=headers,
            params=params
        )
        
        if res.status_code == 200:
            data = res.json()
            
            if data['rt_cd'] == '0':
                orders = data.get('output', [])
                
                print(f"✅ 미체결 대기 주문 건수: 총 {len(orders)}건\n")
                if not orders:
                    print("(미체결) 주문이 남아있지 않습니다.")
                    return

                print(f"{'주문번호(ODNO)':<13} | {'티커':<6} | {'구분':<4} | {'수량':>4} | {'주문단가':>8}")
                print("-" * 55)
                
                for order in orders:
                    order_no = order.get('odno', '')
                    symbol = order.get('pdno', '')
                    side_cd = order.get('sll_buy_dvsn_cd', '')
                    side_str = "매수" if side_cd == '02' else "매도"
                    qty = order.get('ft_ord_qty', '0')
                    price = order.get('ft_ord_unpr3', '0')
                    
                    print(f"{order_no:<15} | {symbol:<6} | {side_str:<4} | {qty:>4} | $ {price:>6}")
            else:
                print(f"❌ KIS API 비즈니스 로직 에러: {data['msg1']}")
        else:
            print(f"❌ HTTP 통신 오류: 응답코드 {res.status_code}")
            
    except Exception as e:
        print(f"❌ 네트워크 또는 파싱 오류 발생: {e}")

if __name__ == "__main__":
    print("⏳ 미체결 내역 조회 실습 (Chapter 6)\n")
    token = get_access_token()
    if token:
        get_pending_orders(token)

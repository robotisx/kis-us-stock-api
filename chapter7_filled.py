"""
Chapter 7: 해외주식 체결 내역 조회 (Filled Orders)

🎯 강의 목표:
   API를 통해 실제로 매수/매도 주문이 '체결된 내역'을 안전하게 조회하는 방법을 배웁니다.
   이 API는 미체결 조회(Chapter 6)와 달리 과거 체결 히스토리를 불러올 수 있습니다.

📌 핵심 포인트:
   1. TR_ID: TTTS3035R (실전) / VTTS3035R (모의)
   2. 조회 기간: 시작일(ORD_STRT_DT)과 종료일(ORD_END_DT)을 
      YYYYMMDD 형태로 전달해야 합니다.
   3.Pagination(연속조회):
      해외주식 체결 리스트가 길어질 경우, 증권사 서버는 한 번에 모든 데이터를 주지 않습니다.
      응답 헤더의 `tr_cont` 플래그와 `ctx_area_nk200` 키를 재사용하여 
      다음 페이지를 이어받는 로직의 뼈대를 학습합니다.
"""

import datetime
import requests
import time
from config import APP_KEY, APP_SECRET, URL_BASE, CANO, ACNT_PRDT_CD
from chapter1_token import get_access_token

PAGE_REQUEST_INTERVAL_SECONDS = 0.5
RATE_LIMIT_RETRY_DELAYS = (1.0, 2.0, 3.0)


def _request_filled_orders_page(url, headers, params):
    for attempt, delay in enumerate((0.0, *RATE_LIMIT_RETRY_DELAYS), start=1):
        if delay:
            print(f"   ⏳ 호출 제한 감지로 {delay:.1f}초 대기 후 재시도합니다.")
            time.sleep(delay)

        res = requests.get(url, headers=headers, params=params, timeout=10)

        if res.status_code != 500:
            return res

        body_text = res.text or ""
        if "EGW00201" not in body_text:
            return res

        if attempt > len(RATE_LIMIT_RETRY_DELAYS):
            return res

    return res


def get_filled_orders(token, start_date=None, end_date=None):
    """
    일자별로 해외주식 주문 체결 내역을 조회합니다.
    """
    if "openapivts" in URL_BASE:
        tr_id = "VTTS3035R"
        print("🧪 모의투자 서버 기반으로 체결 내역 조회를 시작합니다.")
    else:
        tr_id = "TTTS3035R"
        print("🚀 실전투자 서버 기반으로 체결 내역 조회를 시작합니다.")

    # 별도의 날짜 입력이 없을 경우 조회 기간을 오늘 하루로 한정합니다.
    today = datetime.datetime.now().strftime("%Y%m%d")
    if start_date is None:
        start_date = today
    if end_date is None:
        end_date = today

    headers = {
        "authorization": f"Bearer {token}",
        "appKey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
    }

    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "%",                   # 종목코드 (전체: "%")
        "ORD_STRT_DT": start_date,     # 조회 시작일
        "ORD_END_DT": end_date,        # 조회 종료일
        "SLL_BUY_DVSN": "01",          # 구분 (00: 전체, 01: 매도, 02: 매수)
        "CCLD_NCCS_DVSN": "00",        # 체결결과 (00: 전체, 01: 체결, 02: 미체결)
        "OVRS_EXCG_CD": "%",           # 거래소 (전체: "%")
        "SORT_SQN": "DS",              # 정렬 (DS: 최신순, AS: 오래된순)
        "ORD_DT": "",
        "ORD_GNO_BRNO": "",
        "ODNO": "",
        "CTX_AREA_FK200": "",          # 연속조회키 1 (첫 조회는 빈값)
        "CTX_AREA_NK200": ""           # 연속조회키 2
    }

    url = f"{URL_BASE}/uapi/overseas-stock/v1/trading/inquire-ccnl"

    print(f"\n===== 📅 체결 내역 조회 ({start_date} ~ {end_date}) =====\n")

    all_orders = []
    max_pages = 30  # 무한루프 방지를 위한 최대 페이지 제한
    current_page = 1
    
    while current_page <= max_pages:
        print(f"🔄 서버에 데이터 요청 중... (페이지 {current_page}/{max_pages})")
        res = _request_filled_orders_page(url, headers, params)

        if res.status_code == 200:
            result = res.json()

            if result.get('rt_cd') == '0':       
                orders = result.get('output', [])
                if orders:
                    all_orders.extend(orders)
                    
                # ───────── 🔄 핵심: 연속 조회 (Pagination) 처리 ─────────
                # 증권사 서버는 한 번에 모든 데이터를 주지 않고 잘라서 전달합니다.
                # 'tr_cont'가 'M' (More) 이면 다음 데이터가 더 있다는 뜻입니다.
                
                tr_cont = res.headers.get('tr_cont', 'D')
                ctx_nk200 = result.get('ctx_area_nk200', '').strip() 
                ctx_fk200 = result.get('ctx_area_fk200', '').strip() 
                
                if tr_cont in ['M', 'F'] and ctx_nk200:
                    print("   ➤ 추가 데이터가 존재합니다. 다음 페이지를 불러옵니다.")
                    # 다음 페이지 요청 시 이어받기 위한 키를 파라미터에 삽입
                    params["CTX_AREA_NK200"] = ctx_nk200
                    params["CTX_AREA_FK200"] = ctx_fk200
                    
                    # 매우 중요: 두 번째 페이지부터는 헤더에 'tr_cont': 'N' (Next)를 지정해야 합니다.
                    headers["tr_cont"] = "N" 
                    
                    current_page += 1
                    time.sleep(PAGE_REQUEST_INTERVAL_SECONDS)
                else:
                    break
            else:
                print(f"❌ API 내에서 처리 오류 발생: {result.get('msg1', '알 수 없는 에러')}")
                break
        else:
            print(f"❌ HTTP 통신 에러: {res.status_code}")
            print(res.text)
            break

    # ----------- 최종 결과 출력 -----------
    if not all_orders:
        print("\n📭 해당 조회 기간 내 체결 내역이 하나도 없습니다.")
        return

    print(f"\n✅ 조회 로직 완료! (총 {current_page}페이지 탐색 / 📋 합계 {len(all_orders)}건 발견)\n")

    for i, order in enumerate(all_orders, 1):
        symbol = order.get('pdno', '???')
        order_no = order.get('odno', '???')
        side = order.get('sll_buy_dvsn_cd_name') or ("매수" if order.get('sll_buy_dvsn_cd') == '02' else "매도")
        status = order.get('prcs_stat_name', '???')    # 처리상태명 (완료, 거부, 접수 등)
        
        ord_qty = int(order.get('ft_ord_qty', 0))      # 총 주문 수량
        ccld_qty = int(order.get('ft_ccld_qty', 0))    # 실제 체결된 수량
        nccs_qty = int(order.get('nccs_qty', 0))       # 잔여 미체결 수량
        price = order.get('ft_ccld_unpr3', '0')        # 체결된 달러 단가
        total_amt = order.get('ft_ccld_amt3', '0')     # 체결 총액
        order_date = order.get('ord_dt', '???')
        order_time = order.get('ord_tmd', '???')
        source = order.get('mdia_dvsn_name', '???')

        print(f"  [{i}] {side} | {symbol} (주문번호: {order_no}) - 처리상태: {status}")
        
        # 거부 사유가 있다면 추가 출력 (코드와 사유명 모두 표시)
        reject_code = order.get('rjct_rson', '').strip()
        reject_reason = order.get('rjct_rson_name', '').strip()
        if reject_reason:
            print(f"      🚨 거부사유: [{reject_code}] {reject_reason}")
            
        # 체결 수량과 잔여 미체결 수량에 따른 상태 출력
        if nccs_qty > 0 and ccld_qty == 0:
            print(f"      수량: 주문 {ord_qty}주 (전량 미체결/접수 대기 중)")
        elif nccs_qty > 0 and ccld_qty > 0:
            print(f"      수량: 주문 {ord_qty}주 중 {ccld_qty}주 부분 체결 (@ ${float(price):,.2f}) / 잔여 대기 {nccs_qty}주")
            if float(total_amt) > 0:
                print(f"      총 체결금액: ${float(total_amt):,.2f}")
        elif nccs_qty == 0 and ccld_qty == 0:
            print(f"      수량: 원래 주문 {ord_qty}주 (전량 취소되거나 오류로 거명됨)")
        else:
            print(f"      수량: {ccld_qty}주 완벽하게 전부 체결! (@ ${float(price):,.2f})")
            if float(total_amt) > 0:
                print(f"      총 체결금액: ${float(total_amt):,.2f}")
                
        print(f"      처리 일시: {order_date} {order_time}")
        print(f"      처리 mdia_dvsn_name: {source}")
        print()


if __name__ == "__main__":
    print("🔖 체결 내역 조회(Pagination 포함) 실습 (Chapter 7)")

    token = get_access_token()
    if token:
        # 예시 1: 오늘 하루치 내역 조회 (기본값)
        # get_filled_orders(token)

        # 예시 2: 특정 과거 기간 조회
        start_str = "20250101"
        end_str = datetime.datetime.now().strftime("%Y%m%d")
        print(f"\n🔍 과거 기간 한정({start_str} ~ {end_str}) 내역 호출 테스트:")
        get_filled_orders(token, start_date=start_str, end_date=end_str)

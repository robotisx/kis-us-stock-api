"""
Chapter 3: 보유 주식 잔고 및 계좌 요약 조회

🎯 강의 목표:
   입력한 계좌 내에 보유중인 해외주식 종목들의 잔고(수량, 평단가)와
   전체 외화 실현/평가 손익(계좌 요약)을 조회하는 방법을 학습합니다.

📌 핵심 포인트:
   1. 데이터 조회 방향 지정: 한국투자증권 실전/모의투자에 따라 `TR_ID`가 분리되어 있습니다.
      - 🔴 실전투자 TR_ID: TTTS3012R
      - 🔵 모의투자 TR_ID: VTTS3012R
   2. 해외거래소별 잔고 조회 시 거래소 코드(OVRS_EXCG_CD) 중요성:
      - [모의투자]: NASD(나스닥), NYSE(뉴욕), AMEX(아멕스)를 각각 분리해서 조회해야만 결과가 정상적으로 반환됩니다.
      - [실전투자]: NASD를 입력해도 미국 전체 종목(뉴욕, 아멕스 포함)이 한 번에 반환되는 특징이 있습니다.
   3. 데이터 객체 구성:
      - API 응답 결과의 `output1` 리스트에는 개별 보유 종목의 내역이 배열로 담깁니다.
      - `output2` 객체에는 계좌 전체의 총 평가 금액 및 실현 손익 등 요약 정보가 담깁니다.
   4. 페이지네이션(연속조회):
      - 한 번에 반환되는 종목 수의 제한이 있다면 `CTX_AREA_FK200`, `CTX_AREA_NK200` 값을 통해 다음 페이지를 요청합니다.

📌 계좌번호 입력 규칙:
   계좌번호 앞 8자리 (CANO) + 계좌상품코드 뒤 2자리 (ACNT_PRDT_CD)
"""

import requests
import json
from config import APP_KEY, APP_SECRET, URL_BASE, CANO, ACNT_PRDT_CD
from chapter1_token import get_access_token

def get_my_stocks(token):
    """
    내 계좌의 보유 해외 주식 목록 및 계좌 요약 정보를 조회합니다.
    """
    
    # 💡 도메인을 기준으로 실전 투자와 모의 투자를 구분해 TR_ID를 동적으로 설정합니다.
    if "openapi.koreainvestment.com" in URL_BASE:
        tr_id = "TTTS3012R"  # 실전투자
        print("🔴 실전투자 모드로 잔고 조회를 요청합니다.")
    else:
        tr_id = "VTTS3012R"  # 모의투자
        print("🔵 모의투자 모드로 잔고 조회를 요청합니다.")
    
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appKey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P"
    }
    
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": "NASD",  # 미국 주식 거래소 공통 코드 지정
        "TR_CRCY_CD": "USD",     # 외화 단위
        "CTX_AREA_FK200": "",    # 연속조회 검색조건 (첫 조회 시 빈 값)
        "CTX_AREA_NK200": ""     # 연속조회 키 (첫 조회 시 빈 값)
    }
    
    try:
        res = requests.get(
            f"{URL_BASE}/uapi/overseas-stock/v1/trading/inquire-balance",
            headers=headers,
            params=params
        )
        
        if res.status_code == 200:
            data = res.json()
            
            if data['rt_cd'] != '0':
                print(f"❌ API 로직 오류: {data['msg1']}")
                return

            print("✅ 보유 주식 잔고 조회 통신 성공!\n")
            
            # 배열로 내려오는 개별 종목 정보
            if 'output1' in data and len(data['output1']) > 0:
                print("================= [보유 종목 상세] =================")
                for stock in data['output1']:
                    qty = float(stock.get('ovrs_cblc_qty', 0)) # 보유 수량
                    if qty > 0:
                        symbol = stock.get('ovrs_pdno')
                        name = stock.get('ovrs_item_name')
                        avg_price = stock.get('pchs_avg_pric')
                        curr_price = stock.get('now_pric2')
                        profit_rate = stock.get('evlu_pfls_rt')
                        profit_amt = stock.get('frcr_evlu_pfls_amt')
                        
                        print(f"📌 {name} ({symbol})")
                        print(f"   - 보유수량: {qty} 주 (주문가능: {stock.get('ord_psbl_qty')} 주)")
                        print(f"   - 매입평균가: {avg_price} $")
                        print(f"   - 실시간현재가: {curr_price} $")
                        print(f"   - 손익 통계: {profit_rate}% 평단 대비수익률 / {profit_amt} $ (외화평가손익)")
                        print("-" * 52)
            else:
                print("ℹ️ 현재 보유중인 해외주식 종목이 없습니다.")
            
            # 객체로 내려오는 계좌 총합 요약 정보
            if 'output2' in data:
                print("\n================= [계좌 요약 상세] =================")
                output2 = data['output2']
                
                print(f"💵 총 매수금액 (외화): {output2.get('frcr_pchs_amt1')} $")
                print(f"📈 해외 총 실현손익: {output2.get('ovrs_tot_pfls')} $ ({output2.get('rlzt_erng_rt')}%)")
                print(f"📊 총 평가손익: {output2.get('tot_evlu_pfls_amt')} $ ({output2.get('tot_pftrt')}%)")
                print("====================================================")
        
        else:
            print(f"❌ 네트워크 연결 실패: {res.status_code}")
            print(res.text)
            
    except Exception as e:
        print(f"❌ 파싱/실행 중 예외 발생: {e}")

if __name__ == "__main__":
    print("💼 계좌 잔고 조회 실습 (Chapter 3)\n")
    token = get_access_token()
    if token:
        get_my_stocks(token)

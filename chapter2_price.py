"""
Chapter 2: 해외주식 현재가 체결가 조회

🎯 강의 목표:
   한국투자증권 API를 사용하여 특정 해외주식 티커(Ticker)의 실시간 현재가, 
   전일 종가 및 등락률 데이터를 조회하는 가장 기본적인 통신 방법을 배웁니다.

📌 핵심 포인트:
   1. 데이터 조회 API는 주로 GET 메소드를 사용합니다.
   2. 공통 헤더 구조의 이해: 
      - 모든 KIS API는 authorization, appKey, appsecret을 포함한 헤더 페이로드를 사용합니다.
      - ⭐️ 호출할 기능에 따라 `tr_id` (트랜잭션 ID)만 교체하여 요청합니다!
   3. 해외 주식을 조회할 때 거래소 코드(EXCD)를 입력해야 합니다:
      - NAS(나스닥), NYS(뉴욕), AMX(아멕스)와 같이 3글자로 넣습니다.
      - ⚠️ (주의) 종목 매수·매도 주문 시에는 형태가 달라집니다 (예: NASD).
"""

import requests
from config import APP_KEY, APP_SECRET, URL_BASE
from chapter1_token import get_access_token

def get_stock_price(token, symbol="AAPL", market="NAS"):
    """
    특정 해외주식 종목의 현재 체결가를 조회합니다.
    
    Args:
        token (str): Chapter 1에서 발급받은 접근 토큰
        symbol (str): 조회할 해외주식 티커 (예: AAPL)
        market (str): 거래소 코드 (NAS, NYS, AMX)
    """
    headers = {
        "authorization": f"Bearer {token}",
        "appKey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "HHDFS00000300",  # 현재가 조회를 의미하는 TR_ID
    }
    
    # URL 쿼리 파라미터 구성
    params = {
        "AUTH": "",
        "EXCD": market,
        "SYMB": symbol
    }
    
    try:
        # KIS API 서버로 GET 요청 전송
        res = requests.get(
            f"{URL_BASE}/uapi/overseas-price/v1/quotations/price",
            headers=headers,
            params=params
        )
        
        if res.status_code == 200:
            data = res.json()
            if data['rt_cd'] == '0':
                output = data['output']
                print(f"✅ [{symbol}] 실시간 시세 조회 성공!")
                print(f"   - 현재가: ${output['last']}")
                print(f"   - 전일종가: ${output['base']}")
                print(f"   - 등락률: {output['rate']}%")
                print(f"   - 오늘 거래량: {output['tvol']} 주")
                return float(output['last'])
            else:
                print(f"❌ API 내에서 에러를 반환했습니다. 메시지: {data['msg1']}")
        else:
            print(f"❌ HTTP 통신 에러 발생. 상태 코드: {res.status_code}")
            print(res.text)
            
    except Exception as e:
        print(f"❌ 네트워크 연결 또는 파싱 오류가 발생했습니다: {e}")
    
    return 0.0

def get_stock_price_detail(token, symbol="AAPL", market="NAS"):
    """
    특정 해외주식 종목의 '상세' 체결가 및 부가 정보를 조회합니다.
    비교 시현을 위해 동일한 API에서 추가 필드를 파싱하는 예제입니다.
    """
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appKey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "HHDFS76200200",  # 해외주식 현재가 상세 (상세정보용)
    }
    
    params = {
        "AUTH": "",
        "EXCD": market,
        "SYMB": symbol
    }
    
    try:
        res = requests.get(
            f"{URL_BASE}/uapi/overseas-price/v1/quotations/price-detail",
            headers=headers,
            params=params
        )
        
        if res.status_code == 200:
            data = res.json()
            if data['rt_cd'] == '0':
                output = data['output']
                print(f"✅ [{symbol}] 상세 시세 데이터(price-detail) 전체 항목 불러오기 성공!\n")
                
                # 수많은 반환 필드들에 대한 한국어 설명 (강의 및 디버깅용)
                field_desc = {
                    "rsym": "실시간조회종목코드", "pvol": "전일거래량", "open": "시가", "high": "고가",
                    "low": "저가", "last": "현재가", "base": "전일종가", "tomv": "시가총액",
                    "pamt": "전일거래대금", "uplp": "상한가", "dnlp": "하한가", "h52p": "52주최고가",
                    "h52d": "52주최고일자", "l52p": "52주최저가", "l52d": "52주최저일자", "perx": "PER",
                    "pbrx": "PBR", "epsx": "EPS", "bpsx": "BPS", "shar": "상장주수",
                    "mcap": "자본금", "curr": "통화", "zdiv": "소수점자리수", "vnit": "매매단위",
                    "t_xprc": "원환산당일가격", "t_xdif": "원환산당일대비", "t_xrat": "원환산당일등락",
                    "p_xprc": "원환산전일가격", "p_xdif": "원환산전일대비", "p_xrat": "원환산전일등락",
                    "t_rate": "당일환율", "p_rate": "전일환율", "t_xsgn": "원환산당일기호",
                    "p_xsng": "원환산전일기호", "e_ordyn": "거래가능여부", "e_hogau": "호가단위",
                    "e_icod": "업종(섹터)", "e_parp": "액면가", "tvol": "거래량", "tamt": "거래대금",
                    "etyp_nm": "ETP 분류명"
                }
                
                print("   [API 응답 전체 상세 항목]")
                print("   --------------------------------------------------")
                for key, value in output.items():
                    desc = field_desc.get(key, '알수없음')
                    print(f"   - {key:<10} | {desc:<12} | {value}")
                print("   --------------------------------------------------")
                
                return output
            else:
                print(f"❌ API 내에서 에러를 반환했습니다. 메시지: {data['msg1']}")
        else:
            print(f"❌ HTTP 통신 에러 발생. 상태 코드: {res.status_code}")
            
    except Exception as e:
        print(f"❌ 네트워크 연결 또는 파싱 오류가 발생했습니다: {e}")
    
    return None

if __name__ == "__main__":
    print("📊 해외주식 시세 조회 실습 (Chapter 2)\n")
    
    # 1. API 호출에 필요한 토큰을 먼저 확보합니다.
    print("[1단계] API 접근 토큰 발급 중...")
    token = get_access_token()
    
    if token:
        # 단일 종목 테스트 (애플, 테슬라, 코스트코)
        print("\n[2단계] AAPL(애플) 시세 조회...")
        get_stock_price(token, "AAPL", "NAS")
        
        print("\n[2단계] TSLA(테슬라) 시세 조회...")
        get_stock_price(token, "TSLA", "NAS")

        print("\n[2단계] COST(코스트코) 시세 조회...")
        get_stock_price(token, "COST", "NAS")

        print("\n[3단계] 테슬라(TSLA) '상세' 정보 조회 비교...")
        get_stock_price_detail(token, "TSLA", "NAS")

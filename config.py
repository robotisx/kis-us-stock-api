from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_config():
    """
    config.yaml 파일에서 한국투자증권 API 키 및 계좌 정보를 로드합니다.
    강의 실습을 위해 프로젝트 루트에 config.yaml 파일이 준비되어 있어야 합니다.
    """
    if not CONFIG_PATH.is_file():
        print("[오류] config.yaml 파일을 찾을 수 없습니다. (발급받은 API 키를 설정해주세요)")
        return None
        
    with CONFIG_PATH.open('r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    return config

# 설정 로드 및 전역 변수 할당
CONFIG = load_config() or {}

if CONFIG:
    APP_KEY = CONFIG.get('APP_KEY')
    APP_SECRET = CONFIG.get('APP_SECRET')
    URL_BASE = CONFIG.get('URL_BASE')
    CANO = CONFIG.get('CANO')
    ACNT_PRDT_CD = CONFIG.get('ACNT_PRDT_CD')
    
    # 텔레그램 연동(선택사항)용 설정
    TELEGRAM_TOKEN = CONFIG.get('TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID = CONFIG.get('TELEGRAM_CHAT_ID')
else:
    APP_KEY = None
    APP_SECRET = None
    URL_BASE = None
    CANO = None
    ACNT_PRDT_CD = None
    TELEGRAM_TOKEN = None
    TELEGRAM_CHAT_ID = None

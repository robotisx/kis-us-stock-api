"""Command handlers for simple_telegram_trading_bot.py.

Handlers in this module receive the main bot module as ``ctx``. Shared runtime
helpers, broker API wrappers, and configuration checks stay in the main module;
each handler focuses on parsing one Telegram command and returning a reply.
"""

from __future__ import annotations


def build_help_text(ctx) -> str:
    mode = "LIVE" if ctx.live_trading() else "DRY-RUN"
    return f"""간단 Telegram 주문 봇 ({mode})

명령어:
/help
/price AAPL [NAS]
/balance
/buy AAPL 1 50.00 [NASD] [00]
/sell AAPL 1 500.00 [NASD] [00]
/modify 31372145 AAPL 1 55.00 [NASD]
/cancel 31372145 AAPL 1 [NASD]

시장 코드:
NASD = 나스닥
NYSE = 뉴욕증권거래소
AMEX = 아멕스

안전 설정:
- 기본값은 DRY-RUN입니다.
- 실제 주문은 TELEGRAM_TRADING_LIVE=true 일 때만 전송됩니다.
"""


def handle_help(ctx, parts, chat_id, token) -> str:
    return build_help_text(ctx)


def price_usage() -> str:
    return """현재가 조회 사용법

형식:
/price 종목코드 [시장코드]

예시:
/price AAPL
/price TSLA NAS

시장코드:
NAS = 나스닥
NYS = 뉴욕증권거래소
AMS = 아멕스
"""


def buy_usage() -> str:
    return """매수 주문 사용법

형식:
/buy 종목코드 수량 가격 [시장코드] [주문유형]

예시:
/buy AAPL 1 50.00
/buy AAPL 1 50.00 NASD 00
/buy DIS 1 100.00 NYSE 00

기본값:
시장코드 = NASD
주문유형 = 00(지정가)

안전 설정:
TELEGRAM_TRADING_LIVE=false 이면 실제 주문은 전송되지 않습니다.
"""


def sell_usage() -> str:
    return """매도 주문 사용법

형식:
/sell 종목코드 수량 가격 [시장코드] [주문유형]

예시:
/sell AAPL 1 500.00
/sell AAPL 1 500.00 NASD 00
/sell DIS 1 120.00 NYSE 00

기본값:
시장코드 = NASD
주문유형 = 00(지정가)

안전 설정:
TELEGRAM_TRADING_LIVE=false 이면 실제 주문은 전송되지 않습니다.
"""


def modify_usage() -> str:
    return """주문 정정 사용법

형식:
/modify 원주문번호 종목코드 수량 새가격 [시장코드]

예시:
/modify 31372145 AAPL 1 55.00
/modify 31372145 AAPL 1 55.00 NASD

설명:
이미 접수된 미체결 주문의 가격을 변경합니다.
"""


def cancel_usage() -> str:
    return """주문 취소 사용법

형식:
/cancel 원주문번호 종목코드 수량 [시장코드]

예시:
/cancel 31372145 AAPL 1
/cancel 31372145 AAPL 1 NASD

설명:
이미 접수된 미체결 주문을 취소합니다.
"""


def handle_balance(ctx, parts, chat_id, token) -> str:
    kis_token = ctx.get_token_or_fail()
    _, logs = ctx.capture_output(ctx.get_my_stocks, kis_token)
    return logs or "잔고 조회 결과가 비어 있습니다."


def handle_price(ctx, parts, chat_id, token) -> str:
    args = parts[1:]
    if not args:
        return price_usage()

    symbol = ctx.normalize_symbol(args[0])
    market = args[1].upper() if len(args) >= 2 else "NAS"

    kis_token = ctx.get_token_or_fail()
    price, logs = ctx.capture_output(ctx.get_stock_price, kis_token, symbol, market)
    if price:
        return f"{symbol} 현재가: ${price:.2f}\n\n{logs}"
    return f"{symbol} 현재가 조회 실패\n\n{logs}"


def _parse_order_args(ctx, parts, usage: str):
    args = parts[1:]
    if len(args) < 3:
        raise ValueError(usage)

    symbol = ctx.normalize_symbol(args[0])
    qty = ctx.parse_positive_int(args[1], "수량")
    price = ctx.parse_positive_price(args[2])
    market = args[3].upper() if len(args) >= 4 else "NASD"
    order_type = args[4] if len(args) >= 5 else "00"
    return symbol, qty, price, market, order_type


def handle_buy(ctx, parts, chat_id, token) -> str:
    if len(parts) < 4:
        return buy_usage()

    symbol, qty, price, market, order_type = _parse_order_args(
        ctx,
        parts,
        buy_usage(),
    )
    title = f"매수 주문: {symbol} {qty}주 @ ${price:.2f}, market={market}, order_type={order_type}"

    if not ctx.live_trading():
        return ctx.dry_run_message(title)

    kis_token = ctx.get_token_or_fail()
    order_no, logs = ctx.capture_output(
        ctx.send_buy_order,
        kis_token,
        symbol,
        qty,
        price,
        market,
        order_type,
    )
    if order_no:
        return f"매수 주문 접수 성공\n주문번호: {order_no}\n\n{logs}"
    return f"매수 주문 실패\n\n{logs}"


def handle_sell(ctx, parts, chat_id, token) -> str:
    if len(parts) < 4:
        return sell_usage()

    symbol, qty, price, market, order_type = _parse_order_args(
        ctx,
        parts,
        sell_usage(),
    )
    title = f"매도 주문: {symbol} {qty}주 @ ${price:.2f}, market={market}, order_type={order_type}"

    if not ctx.live_trading():
        return ctx.dry_run_message(title)

    kis_token = ctx.get_token_or_fail()
    order_no, logs = ctx.capture_output(
        ctx.send_sell_order,
        kis_token,
        symbol,
        qty,
        price,
        market,
        order_type,
    )
    if order_no:
        return f"매도 주문 접수 성공\n주문번호: {order_no}\n\n{logs}"
    return f"매도 주문 실패\n\n{logs}"


def handle_modify(ctx, parts, chat_id, token) -> str:
    args = parts[1:]
    if len(args) < 4:
        return modify_usage()

    org_order_no = args[0]
    symbol = ctx.normalize_symbol(args[1])
    qty = ctx.parse_positive_int(args[2], "수량")
    price = ctx.parse_positive_price(args[3])
    market = args[4].upper() if len(args) >= 5 else "NASD"
    title = f"정정 주문: 원주문번호={org_order_no}, {symbol} {qty}주 @ ${price:.2f}, market={market}"

    if not ctx.live_trading():
        return ctx.dry_run_message(title)

    kis_token = ctx.get_token_or_fail()
    ok, logs = ctx.capture_output(
        ctx.amend_cancel_order,
        kis_token,
        org_order_no,
        symbol,
        qty,
        price,
        "MODIFY",
        market,
    )
    return f"정정 요청 {'성공' if ok else '실패'}\n\n{logs}"


def handle_cancel(ctx, parts, chat_id, token) -> str:
    args = parts[1:]
    if len(args) < 3:
        return cancel_usage()

    org_order_no = args[0]
    symbol = ctx.normalize_symbol(args[1])
    qty = ctx.parse_positive_int(args[2], "수량")
    market = args[3].upper() if len(args) >= 4 else "NASD"
    title = f"취소 주문: 원주문번호={org_order_no}, {symbol} {qty}주, market={market}"

    if not ctx.live_trading():
        return ctx.dry_run_message(title)

    kis_token = ctx.get_token_or_fail()
    ok, logs = ctx.capture_output(
        ctx.amend_cancel_order,
        kis_token,
        org_order_no,
        symbol,
        qty,
        0,
        "CANCEL",
        market,
    )
    return f"취소 요청 {'성공' if ok else '실패'}\n\n{logs}"

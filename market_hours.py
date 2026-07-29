from datetime import datetime, timedelta, timezone


KST = timezone(timedelta(hours=9))
DAYTIME_START_HOUR = 10
DAYTIME_END_HOUR_SUMMER = 17
DAYTIME_END_HOUR_WINTER = 18


def _as_kst(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(KST)
    if now.tzinfo is None:
        return now.replace(tzinfo=KST)
    return now.astimezone(KST)


def _nth_sunday(year: int, month: int, nth: int) -> datetime:
    first_day = datetime(year, month, 1, tzinfo=KST)
    days_until_sunday = (6 - first_day.weekday()) % 7
    return first_day + timedelta(days=days_until_sunday + 7 * (nth - 1))


def is_us_daylight_saving_time(now: datetime | None = None) -> bool:
    """주어진 한국시간이 미국 동부 서머타임 적용 기간인지 반환합니다."""
    now_kst = _as_kst(now)

    # 미국 서머타임은 3월 둘째 일요일 02:00(미 동부 표준시)에 시작하고,
    # 11월 첫째 일요일 02:00(미 동부 서머타임)에 종료됩니다.
    dst_start_kst = _nth_sunday(now_kst.year, 3, 2).replace(hour=16)
    dst_end_kst = _nth_sunday(now_kst.year, 11, 1).replace(hour=15)

    return dst_start_kst <= now_kst < dst_end_kst


def is_us_daytime_trading_time(now: datetime | None = None) -> bool:
    """한국시간 기준 미국주식 주간거래 시간인지 반환합니다."""
    now_kst = _as_kst(now)
    end_hour = (
        DAYTIME_END_HOUR_SUMMER
        if is_us_daylight_saving_time(now_kst)
        else DAYTIME_END_HOUR_WINTER
    )
    session_start = now_kst.replace(
        hour=DAYTIME_START_HOUR,
        minute=0,
        second=0,
        microsecond=0,
    )
    session_end = now_kst.replace(
        hour=end_hour,
        minute=0,
        second=0,
        microsecond=0,
    )
    return session_start <= now_kst < session_end

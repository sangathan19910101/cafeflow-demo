import datetime
import json
import os

_NP_DATA_PATH = os.path.join(os.path.dirname(__file__), "nepali_dates.json")

_NEPALI_YEARS_DATA = None


def _load_data():
    global _NEPALI_YEARS_DATA
    if _NEPALI_YEARS_DATA is not None:
        return _NEPALI_YEARS_DATA
    try:
        with open(_NP_DATA_PATH, "r", encoding="utf-8") as f:
            _NEPALI_YEARS_DATA = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _NEPALI_YEARS_DATA = {}
    return _NEPALI_YEARS_DATA


NEPALI_MONTHS = [
    "Baisakh", "Jestha", "Ashadh", "Shrawan", "Bhadra",
    "Ashoj", "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra",
]
NEPALI_MONTHS_NP = [
    "बैशाख", "जेठ", "असार", "साउन", "भदौ",
    "असोज", "कात्तिक", "मंसिर", "पुष", "माघ", "फागुन", "चैत",
]
NEPALI_DAYS = ["Aaitabar", "Sombar", "Mangalbar", "Budhabar", "Bihibar", "Shukrabar", "Shanibar"]
NEPALI_DIGITS = "०१२३४५६७८९"


def _ad_to_bs_lookup():
    data = _load_data()
    mapping = data.get("ad_to_bs", {})
    result = {}
    for bs_year_str, info in mapping.items():
        bs_year = int(bs_year_str)
        ref_date = info.get("ref_ad_date")
        ref_bs_day = info.get("ref_bs_day", 1)
        ref_bs_month = info.get("ref_bs_month", 1)
        days_in_months = info.get("days_in_months", [])
        result[bs_year] = {
            "ref_ad_date": ref_date,
            "ref_bs_day": ref_bs_day,
            "ref_bs_month": ref_bs_month,
            "days_in_months": days_in_months,
        }
    return result


def _get_bs_year_info(bs_year):
    lookup = _ad_to_bs_lookup()
    return lookup.get(bs_year)


def _parse_ad_date(date_str):
    parts = date_str.split("-")
    return datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))


def ad_to_bs(ad_date):
    """Convert Gregorian (AD) date to Bikram Sambat (BS) date.
    Returns (bs_year, bs_month, bs_day) tuple.
    """
    lookup = _ad_to_bs_lookup()
    if not lookup:
        return _approximate_ad_to_bs(ad_date)

    if isinstance(ad_date, datetime.datetime):
        ad_date = ad_date.date()

    for bs_year, info in lookup.items():
        ref_date = _parse_ad_date(info["ref_ad_date"])
        if ad_date >= ref_date:
            next_year_info = lookup.get(bs_year + 1)
            if next_year_info:
                next_ref = _parse_ad_date(next_year_info["ref_ad_date"])
                if ad_date < next_ref:
                    return _calc_bs(ad_date, ref_date, bs_year, info)
            else:
                return _calc_bs(ad_date, ref_date, bs_year, info)

    sorted_years = sorted(lookup.keys())
    if sorted_years:
        first_bs_year = sorted_years[0]
        first_info = lookup[first_bs_year]
        ref_date = _parse_ad_date(first_info["ref_ad_date"])
        if ad_date < ref_date:
            return _calc_bs(ad_date, ref_date, first_bs_year - 1, first_info)

    return _approximate_ad_to_bs(ad_date)


def _calc_bs(ad_date, ref_date, bs_year, info):
    delta = (ad_date - ref_date).days
    days_in_months = info.get("days_in_months", [])
    ref_bs_month = info.get("ref_bs_month", 1)
    ref_bs_day = info.get("ref_bs_day", 1)

    if not days_in_months:
        return (bs_year, ref_bs_month, ref_bs_day + delta)

    current_day = ref_bs_day
    current_month = ref_bs_month

    if delta >= 0:
        days_left = delta
        while days_left > 0:
            month_idx = current_month - 1
            if month_idx >= len(days_in_months):
                bs_year += 1
                current_month = 1
                continue
            days_this_month = days_in_months[month_idx]
            remaining_in_month = days_this_month - current_day
            if days_left <= remaining_in_month:
                current_day += days_left
                days_left = 0
            else:
                days_left -= (remaining_in_month + 1)
                current_day = 1
                current_month += 1
                if current_month > 12:
                    bs_year += 1
                    current_month = 1
    else:
        days_remaining = -delta
        while days_remaining > 0:
            month_idx = current_month - 1
            days_this_month = days_in_months[month_idx] if month_idx < len(days_in_months) else 30
            remaining_before = current_day - 1
            if days_remaining <= remaining_before:
                current_day -= days_remaining
                days_remaining = 0
            else:
                days_remaining -= (remaining_before + 1)
                current_month -= 1
                if current_month < 1:
                    bs_year -= 1
                    current_month = 12
                    month_idx = current_month - 1
                    days_this_month = days_in_months[month_idx] if month_idx < len(days_in_months) else 30
                current_day = days_in_months[current_month - 1]

    return (bs_year, current_month, current_day)


def _approximate_ad_to_bs(ad_date):
    if isinstance(ad_date, datetime.datetime):
        ad_date = ad_date.date()
    offset_days = 20827
    days_since_epoch = (ad_date - datetime.date(1943, 4, 14)).days
    total_days = offset_days + days_since_epoch
    bs_year = 2000
    remaining = total_days

    while True:
        year_days = _days_in_bs_year(bs_year)
        if remaining < year_days:
            break
        remaining -= year_days
        bs_year += 1

    bs_month = 1
    days_in_months = _get_bs_month_lengths(bs_year)
    for month_days in days_in_months:
        if remaining < month_days:
            break
        remaining -= month_days
        bs_month += 1

    bs_day = remaining + 1
    return (bs_year, bs_month, bs_day)


def _days_in_bs_year(bs_year):
    months = _get_bs_month_lengths(bs_year)
    return sum(months)


def _get_bs_month_lengths(bs_year):
    base = [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30] if bs_year % 4 != 0 else [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30]
    return base


def bs_to_ad(bs_year, bs_month, bs_day):
    """Convert Bikram Sambat (BS) date to Gregorian (AD) date.
    Returns a datetime.date object.
    """
    lookup = _ad_to_bs_lookup()
    if lookup:
        for by, info in lookup.items():
            if by == bs_year:
                ref_date = _parse_ad_date(info["ref_ad_date"])
                ref_bs_month = info.get("ref_bs_month", 1)
                ref_bs_day = info.get("ref_bs_day", 1)
                delta = _bs_date_diff(bs_year, bs_month, bs_day, by, ref_bs_month, ref_bs_day, info.get("days_in_months", []))
                return ref_date + datetime.timedelta(days=delta)
            elif by < bs_year:
                next_yr = lookup.get(by + 1)
                if next_yr and by + 1 > bs_year:
                    continue
                ref_date = _parse_ad_date(info["ref_ad_date"])
                ref_bs_month = info.get("ref_bs_month", 1)
                ref_bs_day = info.get("ref_bs_day", 1)
                delta = _bs_date_diff(bs_year, bs_month, bs_day, by, ref_bs_month, ref_bs_day, info.get("days_in_months", []))
                return ref_date + datetime.timedelta(days=delta)

    return _approximate_bs_to_ad(bs_year, bs_month, bs_day)


def _bs_date_diff(bs_yr1, bs_mo1, bs_day1, bs_yr2, bs_mo2, bs_day2, days_in_months):
    if bs_yr1 == bs_yr2:
        return _bs_days_since(bs_yr1, bs_mo1, bs_day1, days_in_months) - _bs_days_since(bs_yr2, bs_mo2, bs_day2, days_in_months)

    if bs_yr1 > bs_yr2:
        total = 0
        for y in range(bs_yr2, bs_yr1):
            total += _days_in_bs_year(y)
        return total + _bs_days_since(bs_yr1, bs_mo1, bs_day1, days_in_months) - _bs_days_since(bs_yr2, bs_mo2, bs_day2, days_in_months)
    else:
        total = 0
        for y in range(bs_yr1, bs_yr2):
            total += _days_in_bs_year(y)
        return -(total + _bs_days_since(bs_yr2, bs_mo2, bs_day2, days_in_months) - _bs_days_since(bs_yr1, bs_mo1, bs_day1, days_in_months))


def _bs_days_since(bs_year, bs_month, bs_day, days_in_months):
    if not days_in_months:
        days_in_months = _get_bs_month_lengths(bs_year)
    total = 0
    for m in range(bs_month - 1):
        total += days_in_months[m] if m < len(days_in_months) else 30
    total += bs_day - 1
    return total


def _approximate_bs_to_ad(bs_year, bs_month, bs_day):
    epoch = datetime.date(1943, 4, 14)
    offset_days = 20827
    days_since = _bs_days_since(bs_year, bs_month, bs_day, _get_bs_month_lengths(bs_year))
    total_days = days_since - offset_days
    return epoch + datetime.timedelta(days=total_days)


def get_today_bs():
    """Return today's date in BS."""
    return ad_to_bs(datetime.date.today())


def format_bs_date(bs_year, bs_month, bs_day):
    """Format a BS date as readable string."""
    month_name = NEPALI_MONTHS[bs_month - 1] if 1 <= bs_month <= 12 else "???"
    return f"{month_name} {bs_day}, {bs_year}"


def format_bs_date_np(bs_year, bs_month, bs_day):
    """Format a BS date in Nepali script."""
    month_name = NEPALI_MONTHS_NP[bs_month - 1] if 1 <= bs_month <= 12 else "???"
    return f"{month_name} {bs_day}, {bs_year}"


def get_bs_month_days(bs_year, bs_month):
    """Get number of days in a given BS month."""
    lookup = _ad_to_bs_lookup()
    if bs_year in lookup and lookup[bs_year].get("days_in_months"):
        months = lookup[bs_year]["days_in_months"]
        if 1 <= bs_month <= len(months):
            return months[bs_month - 1]
    months = _get_bs_month_lengths(bs_year)
    return months[bs_month - 1] if 1 <= bs_month <= 12 else 30


def get_bs_year_months(bs_year):
    """Get list of (days, month_name) for all months in a BS year."""
    months_data = []
    lookup = _ad_to_bs_lookup()
    if bs_year in lookup and lookup[bs_year].get("days_in_months"):
        days_list = lookup[bs_year]["days_in_months"]
    else:
        days_list = _get_bs_month_lengths(bs_year)
    for i, days in enumerate(days_list):
        months_data.append((days, NEPALI_MONTHS[i]))
    return months_data

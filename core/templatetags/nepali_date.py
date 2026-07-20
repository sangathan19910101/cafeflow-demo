from django import template
from core.nepali_calendar import ad_to_bs, format_bs_date, get_today_bs

register = template.Library()


@register.filter
def bs_date(ad_date):
    """Convert AD date to BS date string."""
    if not ad_date:
        return ""
    try:
        yr, mo, dy = ad_to_bs(ad_date)
        return format_bs_date(yr, mo, dy)
    except Exception:
        return str(ad_date)


@register.filter
def bs_date_short(ad_date):
    """Convert AD date to short BS format YYYY-MM-DD."""
    if not ad_date:
        return ""
    try:
        yr, mo, dy = ad_to_bs(ad_date)
        return f"{yr:04d}-{mo:02d}-{dy:02d}"
    except Exception:
        return str(ad_date)


@register.simple_tag
def today_bs():
    """Return today's date in BS."""
    yr, mo, dy = get_today_bs()
    return format_bs_date(yr, mo, dy)


@register.simple_tag
def today_bs_short():
    """Return today's date in short BS format."""
    yr, mo, dy = get_today_bs()
    return f"{yr:04d}-{mo:02d}-{dy:02d}"


@register.filter
def bs_year(ad_date):
    """Get BS year from AD date."""
    if not ad_date:
        return ""
    try:
        yr, mo, dy = ad_to_bs(ad_date)
        return yr
    except Exception:
        return ""

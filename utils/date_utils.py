from datetime import date, datetime


def month_title(value: date | None = None) -> str:
    value = value or date.today()
    return value.strftime("%B %Y").upper()


def today() -> date:
    return datetime.now().date()

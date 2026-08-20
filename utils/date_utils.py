from datetime import datetime

def month_title():
    return datetime.now().strftime("%B %Y").upper()

def today():
    return datetime.now().date()

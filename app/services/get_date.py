from datetime import date, datetime, time, timedelta

def get_today_range():
    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)
    return start, end

def get_month_range():
    today = datetime.today()
    start = datetime.combine((today - timedelta(days=30)).date(), time.min)
    end = datetime.combine(today.date(), time.max)
    return start, end
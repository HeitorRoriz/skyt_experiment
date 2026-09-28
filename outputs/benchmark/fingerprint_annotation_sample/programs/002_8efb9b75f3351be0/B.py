def valid_date(date):
    if not date:
        return False
    
    parts = date.split('-')
    if len(parts) != 3:
        return False
    
    month, day, year = parts
    if not (month.isdigit() and day.isdigit() and year.isdigit()):
        return False
    
    month = int(month)
    day = int(day)
    year = int(year)
    
    if month < 1 or month > 12:
        return False
    
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 1 <= day <= 31
    elif month in [4, 6, 9, 11]:
        return 1 <= day <= 30
    elif month == 2:
        return 1 <= day <= 29  # Leap year check can be added if needed
    
    return False

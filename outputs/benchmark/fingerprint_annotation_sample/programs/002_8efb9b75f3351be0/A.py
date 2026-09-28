def valid_date(date):
    if not date:
        return False
    
    parts = date.split('-')
    if len(parts) != 3:
        return False
    
    month, day, year = parts
    if not (month.isdigit() and day.isdigit() and year.isdigit()):
        return False
    
    month, day, year = int(month), int(day), int(year)
    
    if month < 1 or month > 12:
        return False
    
    if day < 1:
        return False
    
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return day <= 31
    elif month in [4, 6, 9, 11]:
        return day <= 30
    elif month == 2:
        return day <= 29
    
    return False

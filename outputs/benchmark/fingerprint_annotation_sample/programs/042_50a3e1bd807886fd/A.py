def valid_date(date):
    if not date:
        return False
    if len(date) != 10 or date[2] != '-' or date[5] != '-':
        return False
    try:
        month, day, year = map(int, date.split('-'))
    except ValueError:
        return False
    
    if month < 1 or month > 12:
        return False
    if day < 1:
        return False
    
    if month in {1, 3, 5, 7, 8, 10, 12}:
        return day <= 31
    elif month in {4, 6, 9, 11}:
        return day <= 30
    elif month == 2:
        return day <= 29
    
    return False

def closest_integer(value):
    num = float(value)
    lower = int(num)
    upper = lower + 1
    
    if abs(num - lower) < abs(num - upper):
        return lower
    elif abs(num - lower) > abs(num - upper):
        return upper
    else:
        return upper if num > 0 else lower

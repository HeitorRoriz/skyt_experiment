def closest_integer(value):
    num = float(value)
    
    # Check if we're exactly at .5
    if num > 0:
        # For positive numbers, if decimal part is >= 0.5, round up
        if num - int(num) == 0.5:
            return int(num) + 1
        else:
            return round(num)
    else:
        # For negative numbers, if decimal part is exactly -0.5, round down (away from zero)
        if num - int(num) == -0.5:
            return int(num) - 1
        else:
            return round(num)

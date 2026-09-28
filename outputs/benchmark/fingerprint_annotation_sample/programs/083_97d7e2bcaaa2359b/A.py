def closest_integer(value):
    '''
    Create a function that takes a value (string) representing a number
    and returns the closest integer to it. If the number is equidistant
    from two integers, round it away from zero.

    Examples
    >>> closest_integer("10")
    10
    >>> closest_integer("15.3")
    15

    Note:
    Rounding away from zero means that if the given number is equidistant
    from two integers, the one you should return is the one that is the
    farthest from zero. For example closest_integer("14.5") should
    return 15 and closest_integer("-14.5") should return -15.
    '''
    num = float(value)
    
    # Check if the number is exactly halfway between two integers
    if num >= 0:
        # For positive numbers, round away from zero means round up when at .5
        if num - int(num) == 0.5:
            return int(num) + 1
        else:
            return round(num)
    else:
        # For negative numbers, round away from zero means round down (more negative) when at .5
        if abs(num) - int(abs(num)) == 0.5:
            return int(num) - 1
        else:
            return round(num)

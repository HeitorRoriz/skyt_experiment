def is_simple_power(x, n):
    if n <= 1:
        return x == 1 and n == 1
    power = 1
    while True:
        result = n ** power
        if result == x:
            return True
        if result > x:
            return False
        power += 1

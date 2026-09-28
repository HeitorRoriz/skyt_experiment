def is_simple_power(x, n):
    if n <= 1:
        return x == n
    power = 1
    while True:
        result = n ** power
        if result == x:
            return True
        elif result > x:
            return False
        power += 1

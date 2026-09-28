def is_simple_power(x, n):
    if n <= 1:
        return x == n
    power = 1
    while power < x:
        power *= n
    return power == x

def special_factorial(n):
    from math import factorial
    result = 1
    for i in range(1, n + 1):
        result *= factorial(i)
    return result

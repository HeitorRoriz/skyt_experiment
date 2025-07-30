def fibonacci_2(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    else:
        prev = fibonacci_2(n-1)
        return prev + [prev[-1] + prev[-2]]
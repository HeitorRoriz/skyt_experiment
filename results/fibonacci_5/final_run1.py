def fibonacci_5(n):
    if n <= 1:
        return n
    else:
        return fibonacci_5(n-1) + fibonacci_5(n-2)
def fibonacci_5():
    return [fibonacci_5(i) for i in range(5)]
def fib4(n: int):
    if n == 0:
        return 0
    elif n == 1:
        return 0
    elif n == 2:
        return 2
    elif n == 3:
        return 0

    fib_sequence = [0, 0, 2, 0] + [0] * (n - 3)

    for i in range(4, n + 1):
        fib_sequence[i] = fib_sequence[i - 1] + fib_sequence[i - 2] + fib_sequence[i - 3] + fib_sequence[i - 4]

    return fib_sequence[n]

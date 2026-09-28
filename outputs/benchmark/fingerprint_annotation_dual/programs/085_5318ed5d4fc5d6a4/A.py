def f(n):
    result = []
    for i in range(1, n + 1):
        if i % 2 == 0:  # i is even
            # Calculate factorial of i
            factorial = 1
            for j in range(1, i + 1):
                factorial *= j
            result.append(factorial)
        else:  # i is odd
            # Calculate sum from 1 to i
            sum_val = sum(range(1, i + 1))
            result.append(sum_val)
    return result

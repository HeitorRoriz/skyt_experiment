def is_prime(num):
    if num < 2:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True

def fibonacci():
    a, b = 0, 1
    while True:
        a, b = b, a + b
        yield a

def prime_fib(n: int):
    fib_gen = fibonacci()
    count = 0
    for fib_num in fib_gen:
        if is_prime(fib_num):
            count += 1
            if count == n:
                return fib_num

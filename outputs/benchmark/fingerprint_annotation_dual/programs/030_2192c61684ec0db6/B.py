def prime_fib(n: int):
    def is_prime(num):
        if num < 2:
            return False
        if num == 2:
            return True
        if num % 2 == 0:
            return False
        for i in range(3, int(num ** 0.5) + 1, 2):
            if num % i == 0:
                return False
        return True
    
    count = 0
    fib_a, fib_b = 0, 1
    
    while count < n:
        fib_a, fib_b = fib_b, fib_a + fib_b
        if is_prime(fib_a):
            count += 1
            if count == n:
                return fib_a
    
    return fib_a

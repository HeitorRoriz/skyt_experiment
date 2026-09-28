def is_multiply_prime(a):
    def is_prime(n):
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True
    
    # Get all prime numbers less than 100
    primes = [i for i in range(2, 100) if is_prime(i)]
    
    # Check if a can be expressed as product of exactly 3 primes
    for i in range(len(primes)):
        for j in range(i, len(primes)):
            for k in range(j, len(primes)):
                if primes[i] * primes[j] * primes[k] == a:
                    return True
                if primes[i] * primes[j] * primes[k] > a:
                    break
    return False

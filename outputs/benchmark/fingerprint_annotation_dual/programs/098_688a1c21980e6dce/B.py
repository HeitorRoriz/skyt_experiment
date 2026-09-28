def is_multiply_prime(a):
    def is_prime(n):
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(n**0.5) + 1, 2):
            if n % i == 0:
                return False
        return True
    
    # Find all prime factors
    primes = []
    temp = a
    
    # Check for factor 2
    while temp % 2 == 0:
        primes.append(2)
        temp = temp // 2
    
    # Check for odd factors
    i = 3
    while i * i <= temp:
        while temp % i == 0:
            primes.append(i)
            temp = temp // i
        i += 2
    
    # If temp > 1, then it's a prime factor
    if temp > 1:
        primes.append(temp)
    
    # Check if exactly 3 prime factors (counting multiplicity)
    return len(primes) == 3

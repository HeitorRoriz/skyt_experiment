def get_odd_collatz(n):
    collatz_sequence = []
    
    while n != 1:
        collatz_sequence.append(n)
        if n % 2 == 0:
            n //= 2
        else:
            n = 3 * n + 1
            
    collatz_sequence.append(1)
    
    odd_numbers = [num for num in collatz_sequence if num % 2 != 0]
    return sorted(odd_numbers)

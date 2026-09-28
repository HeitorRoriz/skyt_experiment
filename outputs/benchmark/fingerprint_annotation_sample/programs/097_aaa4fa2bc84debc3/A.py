def count_nums(arr):
    def digit_sum(n):
        if n == 0:
            return 0
        
        if n > 0:
            # Positive number: sum all digits
            total = 0
            while n > 0:
                total += n % 10
                n //= 10
            return total
        else:
            # Negative number: first digit is negative
            n = -n  # Make positive
            digits = []
            while n > 0:
                digits.append(n % 10)
                n //= 10
            digits.reverse()  # Get digits in correct order
            # First digit is negative, rest are positive
            return -digits[0] + sum(digits[1:])
    
    count = 0
    for num in arr:
        if digit_sum(num) > 0:
            count += 1
    return count

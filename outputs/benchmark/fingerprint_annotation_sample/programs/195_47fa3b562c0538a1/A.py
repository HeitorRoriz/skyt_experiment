def starts_one_ends(n):
    if n < 1:
        return 0
    
    if n == 1:
        return 1  # Only the number 1
    
    # Count of n-digit numbers
    total_n_digit_numbers = 9 * (10 ** (n - 1))
    
    # Count of n-digit numbers that start with 1
    start_with_1 = 10 ** (n - 1)
    
    # Count of n-digit numbers that end with 1
    end_with_1 = 9 * (10 ** (n - 2)) if n > 1 else 0
    
    # Total count of numbers that start or end with 1
    return start_with_1 + end_with_1

def order_by_points(nums):
    def sum_of_digits(n):
        # Convert to string and handle negative numbers
        s = str(abs(n))
        total = sum(int(d) for d in s)
        # If the original number was negative, make the sum negative
        if n < 0:
            total = -total
        return total
    
    # Create list of (index, num, sum_of_digits) tuples
    indexed_nums = [(i, num, sum_of_digits(num)) for i, num in enumerate(nums)]
    
    # Sort by sum_of_digits first, then by original index
    indexed_nums.sort(key=lambda x: (x[2], x[0]))
    
    # Return just the numbers
    return [num for i, num, s in indexed_nums]

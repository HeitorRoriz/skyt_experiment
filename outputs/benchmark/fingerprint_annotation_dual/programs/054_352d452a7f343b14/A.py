def order_by_points(nums):
    def sum_of_digits(n):
        if n == 0:
            return 0
        
        # Convert to string to process digits
        s = str(n)
        
        if s[0] == '-':
            # For negative numbers, sum all digits and negate
            return -sum(int(d) for d in s[1:])
        else:
            # For positive numbers, just sum the digits
            return sum(int(d) for d in s)
    
    # Sort by sum of digits, stable sort preserves original order for equal sums
    return sorted(nums, key=sum_of_digits)

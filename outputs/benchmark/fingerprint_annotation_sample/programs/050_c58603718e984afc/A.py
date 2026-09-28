def rounded_avg(n, m):
    if n > m:
        return -1
    
    # Calculate the average of integers from n to m
    avg = sum(range(n, m + 1)) / (m - n + 1)
    
    # Round to nearest integer
    rounded = round(avg)
    
    # Convert to binary
    return bin(rounded)

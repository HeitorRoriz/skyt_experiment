def rounded_avg(n, m):
    if n > m:
        return -1
    
    # Calculate sum of integers from n to m
    total = (n + m) * (m - n + 1) // 2
    
    # Calculate average and round
    count = m - n + 1
    avg = round(total / count)
    
    # Convert to binary
    return bin(avg)

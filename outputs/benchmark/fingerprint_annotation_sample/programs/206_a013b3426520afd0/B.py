def sort_third(l: list):
    if len(l) == 0:
        return []
    
    # Extract elements at indices divisible by 3
    third_elements = [l[i] for i in range(0, len(l), 3)]
    
    # Sort them
    third_elements.sort()
    
    # Create result list
    result = l.copy()
    
    # Put sorted elements back at indices divisible by 3
    for i, val in enumerate(third_elements):
        result[i * 3] = val
    
    return result

def maximum(arr, k):
    if k == 0:
        return []
    
    # Sort the array and take the last k elements
    sorted_arr = sorted(arr)
    result = sorted_arr[-k:]
    
    return result

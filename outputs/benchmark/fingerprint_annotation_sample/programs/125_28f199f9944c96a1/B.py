def move_one_ball(arr):
    if not arr:
        return True
    
    n = len(arr)
    
    # Count the number of positions where arr[i] > arr[i+1]
    break_points = 0
    break_index = -1
    
    for i in range(n - 1):
        if arr[i] > arr[i + 1]:
            break_points += 1
            break_index = i
    
    # If no break points, array is already sorted
    if break_points == 0:
        return True
    
    # If more than one break point, cannot be sorted by rotation
    if break_points > 1:
        return False
    
    # If exactly one break point, check if the last element <= first element
    # This ensures that after rotation, the array will be sorted
    if arr[n - 1] <= arr[0]:
        return True
    
    return False

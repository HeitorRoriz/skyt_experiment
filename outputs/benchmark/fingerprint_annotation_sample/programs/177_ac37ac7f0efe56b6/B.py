def move_one_ball(arr):
    if not arr:
        return True
    
    # Count the number of positions where arr[i] > arr[i+1]
    breaks = 0
    break_pos = -1
    
    for i in range(len(arr) - 1):
        if arr[i] > arr[i + 1]:
            breaks += 1
            break_pos = i
    
    # If already sorted (no breaks)
    if breaks == 0:
        return True
    
    # If more than one break, cannot be sorted by rotation
    if breaks > 1:
        return False
    
    # If exactly one break, check if last element <= first element
    # This ensures that after rotation, the array will be sorted
    if arr[-1] <= arr[0]:
        return True
    
    return False

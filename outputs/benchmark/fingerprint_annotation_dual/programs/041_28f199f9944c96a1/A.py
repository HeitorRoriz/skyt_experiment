def move_one_ball(arr):
    if not arr:
        return True
    
    # Count the number of break points where arr[i] > arr[i+1]
    break_count = 0
    for i in range(len(arr) - 1):
        if arr[i] > arr[i + 1]:
            break_count += 1
    
    # If no breaks, array is already sorted
    if break_count == 0:
        return True
    
    # If exactly one break, check if it's a valid rotation
    # The last element should be <= first element
    if break_count == 1:
        return arr[-1] <= arr[0]
    
    # More than one break means it can't be sorted by rotation
    return False

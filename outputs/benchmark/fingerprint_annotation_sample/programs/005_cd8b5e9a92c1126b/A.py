def can_arrange(arr):
    result = -1
    for i in range(1, len(arr)):
        if arr[i] < arr[i-1]:
            result = i
    return result

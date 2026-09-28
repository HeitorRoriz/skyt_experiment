def sort_array(array):
    if len(array) == 0:
        return []
    
    if len(array) == 1:
        return array.copy()
    
    if (array[0] + array[-1]) % 2 == 1:  # odd
        return sorted(array)
    else:  # even
        return sorted(array, reverse=True)

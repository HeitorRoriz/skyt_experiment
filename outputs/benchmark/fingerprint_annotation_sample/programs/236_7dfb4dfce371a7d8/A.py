def sort_array(array):
    if not array:
        return []
    
    first = array[0]
    last = array[-1]
    sorted_array = sorted(array)
    
    if (first + last) % 2 == 0:
        return sorted_array[::-1]
    else:
        return sorted_array

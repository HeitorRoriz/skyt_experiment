def sort_array(array):
    if not array:
        return []
    
    first = array[0]
    last = array[-1]
    total = first + last
    
    if total % 2 == 0:
        return sorted(array, reverse=True)
    else:
        return sorted(array)

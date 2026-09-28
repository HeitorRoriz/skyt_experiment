def by_length(arr):
    if not arr:
        return []
    
    # Filter and sort the integers between 1 and 9
    filtered = sorted(x for x in arr if 1 <= x <= 9)
    
    # Reverse the sorted list
    reversed_arr = filtered[::-1]
    
    # Mapping from numbers to their corresponding names
    number_names = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    
    # Replace digits with names
    result = [number_names[x - 1] for x in reversed_arr]
    
    return result

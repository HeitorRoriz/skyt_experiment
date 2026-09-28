def by_length(arr):
    if not arr:
        return []
    
    valid_numbers = [num for num in arr if 1 <= num <= 9]
    valid_numbers.sort()
    valid_numbers.reverse()
    
    number_names = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    result = [number_names[num - 1] for num in valid_numbers]
    
    return result

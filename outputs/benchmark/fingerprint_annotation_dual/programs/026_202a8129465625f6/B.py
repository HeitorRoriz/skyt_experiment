def sorted_list_sum(lst):
    # Filter out strings with odd lengths
    even_length_strings = [s for s in lst if len(s) % 2 == 0]
    
    # Sort by length first, then alphabetically
    result = sorted(even_length_strings, key=lambda x: (len(x), x))
    
    return result

def by_length(arr):
    # Dictionary to map digits to their names
    digit_names = {
        1: "One",
        2: "Two",
        3: "Three",
        4: "Four",
        5: "Five",
        6: "Six",
        7: "Seven",
        8: "Eight",
        9: "Nine"
    }
    
    # Filter numbers between 1 and 9 inclusive
    filtered = [num for num in arr if 1 <= num <= 9]
    
    # Sort the filtered array
    filtered.sort()
    
    # Reverse the sorted array
    filtered.reverse()
    
    # Replace each digit with its corresponding name
    result = [digit_names[num] for num in filtered]
    
    return result

def odd_count(lst):
    result = []
    template = "the number of odd elements in the string i of the input."
    
    for s in lst:
        # Count odd digits in the string
        count = sum(1 for char in s if char.isdigit() and int(char) % 2 == 1)
        
        # Replace all 'i' with the count
        output = template.replace('i', str(count))
        result.append(output)
    
    return result

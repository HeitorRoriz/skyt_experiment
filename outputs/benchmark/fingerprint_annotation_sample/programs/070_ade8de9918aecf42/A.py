def odd_count(lst):
    result = []
    template = "the number of odd elements in the string i of the input."
    
    for s in lst:
        # Count odd digits in the string
        count = sum(1 for c in s if c.isdigit() and int(c) % 2 == 1)
        
        # Replace 'i' with the count
        formatted = template.replace('i', str(count))
        result.append(formatted)
    
    return result

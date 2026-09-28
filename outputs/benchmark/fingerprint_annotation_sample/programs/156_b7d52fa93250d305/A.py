def odd_count(lst):
    result = []
    for s in lst:
        # Count odd digits in the string
        count = sum(1 for c in s if c.isdigit() and int(c) % 2 == 1)
        # Create the output string by replacing 'i' with the count
        output = "the number of odd elements in the string i of the input."
        output = output.replace('i', str(count))
        result.append(output)
    return result

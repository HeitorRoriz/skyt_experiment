def odd_count(lst):
    result = []
    for s in lst:
        # Count odd digits in the string
        count = sum(1 for c in s if c.isdigit() and int(c) % 2 == 1)
        # Create the message with 'i' replaced by the count
        message = f"the number of odd elements {count}n the str{count}ng {count} of the {count}nput."
        result.append(message)
    return result

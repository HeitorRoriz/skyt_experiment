def next_smallest(lst):
    unique_elements = list(set(lst))
    if len(unique_elements) < 2:
        return None
    unique_elements.sort()
    return unique_elements[1]

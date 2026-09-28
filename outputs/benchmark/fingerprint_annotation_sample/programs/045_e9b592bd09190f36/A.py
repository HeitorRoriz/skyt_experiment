def sort_even(l: list):
    even_indices = sorted(l[i] for i in range(0, len(l), 2))
    result = l[:]
    result[::2] = even_indices
    return result

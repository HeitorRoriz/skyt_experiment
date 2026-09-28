def is_sorted(lst):
    if len(lst) < 2:
        return True
    seen = set()
    for i in range(len(lst)):
        if lst[i] in seen:
            return False
        seen.add(lst[i])
        if i > 0 and lst[i] < lst[i - 1]:
            return False
    return True

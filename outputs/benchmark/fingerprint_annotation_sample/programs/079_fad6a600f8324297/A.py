def pairs_sum_to_zero(l):
    seen = set()
    for number in l:
        if -number in seen:
            return True
        seen.add(number)
    return False

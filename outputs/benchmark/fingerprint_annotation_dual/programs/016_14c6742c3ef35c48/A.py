def make_a_pile(n):
    stones = []
    for i in range(n):
        if n % 2 == 0:
            stones.append(n + 2 * i)
        else:
            stones.append(n + 2 * i + 1)
    return stones

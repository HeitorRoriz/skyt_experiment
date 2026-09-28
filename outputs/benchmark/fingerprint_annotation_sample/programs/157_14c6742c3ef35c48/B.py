def make_a_pile(n):
    stones = []
    for i in range(n):
        if i == 0:
            stones.append(n)
        else:
            if stones[i - 1] % 2 == 0:
                stones.append(stones[i - 1] + 1)
            else:
                stones.append(stones[i - 1] + 2)
    return stones

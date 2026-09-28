def make_a_pile(n):
    pile = []
    for i in range(n):
        if n % 2 == 0:
            stones = n + i * 2
        else:
            stones = n + i * 2 + 1
        pile.append(stones)
    return pile

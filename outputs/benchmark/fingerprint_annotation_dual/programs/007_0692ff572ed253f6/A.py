def make_a_pile(n):
    pile = []
    for i in range(n):
        if n % 2 == 0:
            stones = n + 2 * i
        else:
            stones = n + 2 * i
        pile.append(stones)
    return pile

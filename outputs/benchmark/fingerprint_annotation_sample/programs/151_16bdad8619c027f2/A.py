def minPath(grid, k):
    n = len(grid)
    
    # Find the position of the minimum value (which is 1)
    min_val = float('inf')
    min_pos = (0, 0)
    for i in range(n):
        for j in range(n):
            if grid[i][j] < min_val:
                min_val = grid[i][j]
                min_pos = (i, j)
    
    # Find the minimum value among all neighbors of any cell
    min_neighbor = float('inf')
    for i in range(n):
        for j in range(n):
            # Check all 4 neighbors
            for di, dj in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < n and 0 <= nj < n:
                    min_neighbor = min(min_neighbor, grid[ni][nj])
    
    # Build the path
    path = []
    
    # Start with the minimum value
    path.append(min_val)
    
    # For remaining k-1 steps, alternate between min_val and min_neighbor
    # if they're different, otherwise just repeat min_val
    for step in range(1, k):
        if min_neighbor < min_val:
            # This shouldn't happen since min_val is 1
            path.append(min_neighbor)
        else:
            # We can always go back to a neighbor and return
            # The optimal strategy is to use the minimum neighbor value
            path.append(min_neighbor)
    
    return path

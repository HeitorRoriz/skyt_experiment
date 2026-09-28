def minPath(grid, k):
    n = len(grid)
    
    # Find the cell with minimum value
    min_val = float('inf')
    min_pos = (0, 0)
    for i in range(n):
        for j in range(n):
            if grid[i][j] < min_val:
                min_val = grid[i][j]
                min_pos = (i, j)
    
    # Start building the path
    path = [min_val]
    current_pos = min_pos
    
    # For remaining k-1 steps
    for _ in range(k - 1):
        i, j = current_pos
        
        # Find minimum value among neighbors
        neighbors = []
        # Up
        if i > 0:
            neighbors.append((grid[i-1][j], (i-1, j)))
        # Down
        if i < n - 1:
            neighbors.append((grid[i+1][j], (i+1, j)))
        # Left
        if j > 0:
            neighbors.append((grid[i][j-1], (i, j-1)))
        # Right
        if j < n - 1:
            neighbors.append((grid[i][j+1], (i, j+1)))
        
        # Find minimum neighbor
        min_neighbor_val, min_neighbor_pos = min(neighbors)
        
        path.append(min_neighbor_val)
        current_pos = min_neighbor_pos
    
    return path

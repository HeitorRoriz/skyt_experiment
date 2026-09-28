def max_fill(grid, capacity):
    total_trips = 0
    for row in grid:
        water_units = sum(row)
        trips_needed = math.ceil(water_units / capacity)
        total_trips += trips_needed
    return total_trips

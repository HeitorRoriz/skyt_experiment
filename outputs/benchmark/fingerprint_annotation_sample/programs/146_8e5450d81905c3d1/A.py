def bf(planet1, planet2):
    planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
    
    # Check if both planets are valid
    if planet1 not in planets or planet2 not in planets:
        return ()
    
    # Get indices of both planets
    idx1 = planets.index(planet1)
    idx2 = planets.index(planet2)
    
    # Ensure idx1 is the smaller index
    if idx1 > idx2:
        idx1, idx2 = idx2, idx1
    
    # Return planets between idx1 and idx2 (exclusive)
    return tuple(planets[idx1 + 1:idx2])

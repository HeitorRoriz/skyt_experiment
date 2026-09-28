def exchange(lst1, lst2):
    # Count total even numbers in both lists
    total_even = sum(1 for x in lst1 if x % 2 == 0) + sum(1 for x in lst2 if x % 2 == 0)
    
    # Check if we have enough even numbers to fill lst1
    if total_even >= len(lst1):
        return "YES"
    else:
        return "NO"

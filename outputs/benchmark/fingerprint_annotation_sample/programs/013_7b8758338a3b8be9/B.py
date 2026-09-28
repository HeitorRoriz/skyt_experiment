def prod_signs(arr):
    if not arr:
        return None
    
    sum_magnitudes = sum(abs(x) for x in arr)
    
    product_signs = 1
    for x in arr:
        if x > 0:
            product_signs *= 1
        elif x < 0:
            product_signs *= -1
        else:  # x == 0
            product_signs *= 0
    
    return sum_magnitudes * product_signs

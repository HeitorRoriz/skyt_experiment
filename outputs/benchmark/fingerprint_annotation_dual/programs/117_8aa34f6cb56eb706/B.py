def int_to_mini_roman(number):
    if not (1 <= number <= 1000):
        raise ValueError("Number must be between 1 and 1000")
    
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syms = [
        "m", "cm", "d", "cd",
        "c", "xc", "l", "xl",
        "x", "ix", "v", "iv",
        "i"
    ]
    
    roman_numeral = ""
    for i in range(len(val)):
        while number >= val[i]:
            roman_numeral += syms[i]
            number -= val[i]
    
    return roman_numeral

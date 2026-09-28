def compare_one(a, b):
    def parse_value(value):
        if isinstance(value, str):
            value = value.replace(',', '.')
        return float(value) if isinstance(value, (int, float, str)) else None

    a_parsed = parse_value(a)
    b_parsed = parse_value(b)

    if a_parsed is None or b_parsed is None:
        return None

    if a_parsed > b_parsed:
        return a
    elif b_parsed > a_parsed:
        return b
    else:
        return None

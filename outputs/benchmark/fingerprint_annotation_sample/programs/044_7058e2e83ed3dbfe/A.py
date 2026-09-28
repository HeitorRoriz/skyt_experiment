def compare_one(a, b):
    def parse_value(value):
        if isinstance(value, str):
            return float(value.replace(',', '.'))
        return float(value)

    if a == b:
        return None

    a_parsed = parse_value(a)
    b_parsed = parse_value(b)

    return a if a_parsed > b_parsed else b

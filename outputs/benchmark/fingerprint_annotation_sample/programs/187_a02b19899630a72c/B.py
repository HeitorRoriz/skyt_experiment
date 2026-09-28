def Strongest_Extension(class_name, extensions):
    def strength(ext):
        CAP = sum(1 for c in ext if c.isupper())
        SM = sum(1 for c in ext if c.islower())
        return CAP - SM

    strongest = extensions[0]
    max_strength = strength(strongest)

    for ext in extensions[1:]:
        current_strength = strength(ext)
        if current_strength > max_strength:
            strongest = ext
            max_strength = current_strength

    return f"{class_name}.{strongest}"

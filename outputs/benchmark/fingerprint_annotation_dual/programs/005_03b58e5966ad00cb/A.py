def check_if_last_char_is_a_letter(txt):
    if not txt or txt[-1] == ' ':
        return False
    last_char = txt.rstrip()[-1]
    return last_char.isalpha() and (len(txt.rstrip().split()) == 1 or txt.rstrip()[-2] == ' ')

def check_if_last_char_is_a_letter(txt):
    if not txt or txt[-1] == ' ':
        return False
    words = txt.split()
    if not words:
        return False
    last_word = words[-1]
    return last_word[-1].isalpha() and len(last_word) > 1 and last_word[-2] == ' '

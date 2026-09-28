def check_if_last_char_is_a_letter(txt):
    if not txt or txt[-1] == ' ':
        return False
    last_word = txt.rstrip().split()[-1]
    return last_word[-1].isalpha() and len(last_word) > 1

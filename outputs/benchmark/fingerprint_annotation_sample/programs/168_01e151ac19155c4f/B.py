def encrypt(s):
    result = []
    for char in s:
        if char.isalpha():
            if char.islower():
                # Shift by 4 positions in lowercase alphabet
                new_char = chr((ord(char) - ord('a') + 4) % 26 + ord('a'))
                result.append(new_char)
            else:
                # Shift by 4 positions in uppercase alphabet
                new_char = chr((ord(char) - ord('A') + 4) % 26 + ord('A'))
                result.append(new_char)
        else:
            result.append(char)
    return ''.join(result)

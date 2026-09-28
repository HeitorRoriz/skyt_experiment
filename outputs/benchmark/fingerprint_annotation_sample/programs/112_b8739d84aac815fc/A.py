def make_palindrome(string: str) -> str:
    """ Find the shortest palindrome that begins with a supplied string.
    Algorithm idea is simple:
    - Find the longest postfix of supplied string that is a palindrome.
    - Append to the end of the string reverse of a string prefix that comes before the palindromic suffix.
    >>> make_palindrome('')
    ''
    >>> make_palindrome('cat')
    'catac'
    >>> make_palindrome('cata')
    'catac'
    """
    if not string:
        return ''
    
    # Find the longest postfix that is a palindrome
    for i in range(len(string)):
        if is_palindrome(string[i:]):
            # Found the longest palindromic postfix starting at index i
            # Append the reverse of the prefix (string[:i]) to the end
            return string + string[:i][::-1]
    
    # If no palindromic postfix found (shouldn't happen as empty string is palindrome)
    return string

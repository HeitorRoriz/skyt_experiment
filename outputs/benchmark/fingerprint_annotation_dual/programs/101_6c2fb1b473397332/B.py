def is_bored(S):
    sentences = [s.strip() for s in S.split('.') + S.split('?') + S.split('!')]
    return sum(1 for sentence in sentences if sentence.startswith('I'))

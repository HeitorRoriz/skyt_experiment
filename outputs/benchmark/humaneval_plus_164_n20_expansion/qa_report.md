# Expansion QA

Gate: **PASS**

## Returned model strings
- haiku45: {'claude-haiku-4-5-20251001': 6560}
- sonnet5: {'claude-sonnet-5': 3280}
- luna: {'gpt-6-luna': 6560}

## Stop reasons
- haiku45 T=0.0: stops={'end_turn': 3280}; extraction fail 15/3280; all-20-identical configs 118/164
- haiku45 T=0.7: stops={'end_turn': 3280}; extraction fail 15/3280; all-20-identical configs 19/164
- sonnet5 default: stops={'end_turn': 3280}; extraction fail 1/3280; all-20-identical configs 24/164
- luna T=0.0: stops={'stop': 3272, 'length': 8}; extraction fail 8/3280; all-20-identical configs 45/164
- luna T=0.7: stops={'stop': 3280}; extraction fail 2/3280; all-20-identical configs 19/164

Thinking responses: {'sonnet5 default': 447}
Thinking leaked into extracted text: none
Luna reasoning tokens: none
Short configs: 0

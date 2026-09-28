def eat(number, need, remaining):
    actually_eaten = min(need, remaining)
    total_eaten = number + actually_eaten
    carrots_left = remaining - actually_eaten
    return [total_eaten, carrots_left]

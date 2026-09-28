import math


def poly(xs: list, x: float):
    """
    Evaluates polynomial with coefficients xs at point x.
    return xs[0] + xs[1] * x + xs[1] * x^2 + .... xs[n] * x^n
    """
    return sum([coeff * math.pow(x, i) for i, coeff in enumerate(xs)])


def find_zero(xs: list):
    """ xs are coefficients of a polynomial.
    find_zero find x such that poly(x) = 0.
    find_zero returns only only zero point, even if there are many.
    Moreover, find_zero only takes list xs having even number of coefficients
    and largest non zero coefficient as it guarantees
    a solution.
    >>> round(find_zero([1, 2]), 2) # f(x) = 1 + 2x
    -0.5
    >>> round(find_zero([-6, 11, -6, 1]), 2) # (x - 1) * (x - 2) * (x - 3) = -6 + 11x - 6x^2 + x^3
    1.0
    """
    def poly_derivative(xs: list):
        """Returns the coefficients of the derivative of the polynomial."""
        return [i * coeff for i, coeff in enumerate(xs) if i > 0]

    def newton_raphson(xs: list, x0: float, tol: float = 1e-7, max_iter: int = 1000):
        """Applies the Newton-Raphson method to find a root of the polynomial."""
        for _ in range(max_iter):
            f_x0 = poly(xs, x0)
            f_prime_x0 = poly(poly_derivative(xs), x0)
            if f_prime_x0 == 0:
                raise ValueError("Derivative is zero. No solution found.")
            x1 = x0 - f_x0 / f_prime_x0
            if abs(x1 - x0) < tol:
                return x1
            x0 = x1
        raise ValueError("Exceeded maximum iterations. No solution found.")

    # Initial guess can be zero
    return newton_raphson(xs, 0.0)

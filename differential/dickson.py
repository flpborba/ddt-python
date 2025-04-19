from sage.all import binomial
from sage.crypto.sbox import SBox


class Dickson(SBox):
    def __init__(self, degree, alpha, name='x'):
        if not isinstance(name, str) or not name.isidentifier():
            raise ValueError("variable name must be a valid identifier")

        self._expression = Dickson._build_expression(degree, alpha, name)

        super().__init__(self._expression)

    def _build_expression(degree, alpha, name):
        x = alpha.parent().polynomial_ring(name).gen()

        return sum(
            alpha**i * x**(degree - 2 * i)
            for i in range(0, degree // 2 + 1)
            if binomial(degree - i, i) * degree // (degree - i) % 2 != 0
        )

    def expression(self):
        return self._expression

    def variable_name(self):
        return self._expression.variable_name()

    def coefficient_variable_name(self):
        return self._expression.base_ring().variable_name()

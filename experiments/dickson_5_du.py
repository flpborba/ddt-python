from differential import Dickson
from differential import binary_field


if __name__ == "__main__":
    field = binary_field(5)
    alpha = field.from_integer(1)
    dickson = Dickson(5, alpha)
    ddt = dickson.difference_distribution_table()

    for a in field:
        # differential uniformity is not defined for 'a == 0'
        if a == 0:
            continue

        trace = ((a**2 + 1) / (a**2)).trace()

        # suppose 'a != 1' and 'Tr((a**2 + 1) / a**2) == 0'
        if a == 1 or trace.trace() != 0:
            continue

        for b in field:
            if b == 0 or a**5 + a**3 + a != b:
                continue

            x = field.polynomial_ring().gen()

            f0 = x**5 + x**3 + x + (x + a)**5 + (x + a)**3 + (x + a) + b

            # simplify 'f0'
            f1 = a * x**4 + a * x**2 + a**4 * x + a**2 * x + a**5 + a**3 + a + b
            assert f1 == f0

            # since 'a**5 + a**3 + a + b = 0', we can remove it from the equation
            f2 = a * x**4 + a * x**2 + a**4 * x + a**2 * x
            assert f2 == f1

            # we can factor out 'a' without changing the roots
            f3 = x**4 + x**2 + (a**3 + a) * x
            assert a * f3 == f2

            # '0' and 'a' are roots of 'f3'
            assert f3(0) == 0
            assert f3(a) == 0
            roots = {0, a}

            # we can factor out '(x + 0)' and '(x + a)' from 'f3'
            f4 = x ** 2 + a * x + a**2 + 1
            assert (x**2 + a * x) * f4 == f3

            # since 'Tr((a**2 + 1) / a**2) = Tr(1 + 1 / a**2) == 0' and 'a != 0', 'f4' has two
            # distinct roots
            assert len({r for (r, _) in f4.roots()}) == 2

            # the roots of 'f4' can't be '0' or 'a', since 'a != 1'
            assert f4(0) != 0
            assert f4(a) != 0
            roots.update({r for (r, _) in f4.roots()})

            # therefore, the differential uniformity of 'dickson' is 4
            assert len(roots) == 4

    for a in field:
        # differential uniformity is not defined for 'a == 0'
        if a == 0:
            continue

        values = {v for v in ddt[a.to_integer()]}
        trace = ((a**2 + 1) / (a**2)).trace()

        # the number of solutions of 'f(x) + f(x + a) = b' is 4 if and only if the conditions hold
        if a != 1 and trace.trace() == 0:
            assert values == {0, 4}
        else:
            assert values == {0, 2}

from time import sleep
from ddt import Dickson
from ddt import binary_field
from sage.all import Subsets


if __name__ == "__main__":
    field = binary_field(7)
    alpha = field.from_integer(1)
    dickson = Dickson(7, alpha)
    ddt = dickson.difference_distribution_table()

    # count = 0
    # trace_0 = 0
    # trace_1 = 0

    # for i, row in enumerate(ddt):
    #     if i == 0:
    #         continue

    #     a = field.from_integer(i)
    #     trace = ((a**2 + 1) / (a**2)).trace()

    #     if max(row) == 6:
    #         count += 1
    #         if trace == 0:
    #             trace_0 += 1
    #         else:
    #             trace_1 += 1

    # print("Count:", count)
    # print("Trace 0:", trace_0)
    # print("Trace 1:", trace_1)

    s = set()

    # for a in field:
    #     # differential uniformity is not defined for 'a == 0'
    #     if a == 0:
    #         continue

    #     trace = ((a**2 + 1) / (a**2)).trace()

    #     # suppose 'a != 1' and 'Tr((a**2 + 1) / a**2) == 0'
    #     if a == 1 or trace.trace() == 0:
    #         for b in field:
    #             x = field.polynomial_ring().gen()
    #             f0 = x**7 + x**5 + x + (x + a)**7 + (x + a)**5 + (x + a) + b
    #             assert len({r for (r, _) in f0.roots()}) < 6
    #         continue

    #     print('==================================================')
    #     print("a                  ->   ", a)

    #     for b in field:
    #         if b == 0:
    #             continue

    #         x = field.polynomial_ring().gen()

    #         f0 = x**7 + x**5 + x + (x + a)**7 + (x + a)**5 + (x + a) + b

    #         # simplify 'f0'
    #         f1 = a * x**6 + a**2 * x**5 + (a**3 + a) * x**4 + a**4 * x**3 + a**5 * x**2 + \
    #             (a**6 + a**4) * x + a**7 + a**5 + a + b
    #         assert f1 == f0

    #         if len({r for (r, _) in f0.roots()}) == 6:
    #             print('--------------------------------------------------')
    #             print("b                  ->   ", b)

    #             subsets = Subsets(range(10))
    #             for subset in sorted(subsets, key=lambda x: max(x) if x else -1):
    #                 subset = list(subset)

    #                 if len(subset) == 0:
    #                     continue

    #                 b_a = 0

    #                 for exponent in subset:
    #                     b_a += a**exponent

    #                 if b_a == b:
    #                     print("b_a                ->   ", subset)
    #                     s.add(tuple(subset))
    #                     break

    for a in field:
        # differential uniformity is not defined for 'a == 0'
        if a == 0:
            continue

        values = {v for v in ddt[a.to_integer()]}
        trace = ((a**2 + 1) / (a**2)).trace()

        # the number of solutions of 'f(x) + f(x + a) = b' is 4 if and only if the conditions hold
        if a == 1 or trace.trace() == 0:
            assert values == {0, 2, 4}, f"{values}"
        else:
            assert values == {0, 2, 6}, f"{values}"

    for e in s:
        print(e)

    for i in range(2, 10):
        field = binary_field(i)
        if field.from_integer(1).trace() == 0:
            print("n:", i)

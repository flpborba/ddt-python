import math

from pyddlib.add import ADD


def make_add(ddt):
    nrows = ddt.nrows()
    depth = int(math.log(nrows, 2))

    def build(i, j, level):
        if level == depth:
            return ADD.constant(int(ddt[i][j]))

        x = ADD.variable(2 * level)
        y = ADD.variable(2 * level + 1)

        half = 1 << (depth - level - 1)

        return (
            ~x * ~y * build(i, j, level + 1)
            + ~x *  y * build(i, j + half, level + 1)
            +  x * ~y * build(i + half, j, level + 1)
            +  x *  y * build(i + half, j + half, level + 1)
        )

    return build(0, 0, 0)


if __name__ == "__main__":
    from sage.crypto.sboxes import SEA

    ddt = SEA.difference_distribution_table()
    ddt.add_to_entry(0, 0, -ddt[0, 0])

    diagram = make_add(ddt)

    print(diagram)

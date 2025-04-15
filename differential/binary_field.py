from sage.all import GF


def binary_field(degree=1, name='x'):
    """Generate a binary extension field.

    Create an extension field over GF(2).

    Parameters
    ----------
    degree : int
        The degree of the extension field over GF(2).

    Returns
    -------
    FiniteField
    """
    if not isinstance(degree, int) or degree <= 0:
        raise ValueError("degree must be a positive integer")

    if not isinstance(name, str) or not name.isidentifier():
        raise ValueError("variable name must be a valid identifier")

    return GF(2**degree, name)

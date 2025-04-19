from differential import Dickson
from differential import binary_field

from pytest import mark
from pytest import raises
from contextlib import nullcontext

INVALID_VARIABLE_MESSAGE = "variable name must be a valid identifier"


@mark.parametrize(
    "field_degree, n, exponents",
    [
        (8, 5, [5, 3, 1]),
        (7, 6, [6, 2]),
        (10, 9, [9, 7, 5, 1]),
        (11, 10, [10, 6, 2]),
    ],
)
def test_dickson_evaluation(field_degree, n, exponents):
    field = binary_field(field_degree, 'a')
    alpha = field.random_element()

    dickson = Dickson(n, alpha)

    x = field.polynomial_ring(dickson.variable_name()).gen()
    expression = sum(alpha ** ((n - e) / 2) * x ** e for e in exponents)

    assert dickson.expression() == expression


@mark.parametrize(
    "variable, context",
    [
        ('x', nullcontext()),
        ('y', nullcontext()),
        ('xy', nullcontext()),
        (None, raises(ValueError, match=INVALID_VARIABLE_MESSAGE)),
        ('', raises(ValueError, match=INVALID_VARIABLE_MESSAGE)),
        (1, raises(ValueError, match=INVALID_VARIABLE_MESSAGE)),
    ]
)
def test_variable(variable, context):
    with context:
        field = binary_field(2, 'a')
        alpha = field.from_integer(2)

        dickson = Dickson(2, alpha, variable)

        assert dickson.variable_name() == variable


def test_default_variable():
    field = binary_field(2)

    assert field.variable_name() == 'x'

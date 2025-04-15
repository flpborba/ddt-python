from differential import binary_field

from pytest import mark
from pytest import raises
from contextlib import nullcontext

INVALID_DEGREE_MESSAGE = "degree must be a positive integer"
INVALID_VARIABLE_MESSAGE = "variable name must be a valid identifier"


@mark.parametrize(
    "degree, context",
    [
        (3, nullcontext()),
        (0, raises(ValueError, match=INVALID_DEGREE_MESSAGE)),
        (-1, raises(ValueError, match=INVALID_DEGREE_MESSAGE)),
        ("", raises(ValueError, match=INVALID_DEGREE_MESSAGE)),
        (None, raises(ValueError, match=INVALID_DEGREE_MESSAGE)),
    ],
)
def test_binary_field(degree, context):
    with context:
        field = binary_field(degree)

        assert field.degree() == degree


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
        field = binary_field(2, variable)

        assert field.variable_name() == variable


def test_default_variable():
    field = binary_field(2)

    assert field.variable_name() == 'x'

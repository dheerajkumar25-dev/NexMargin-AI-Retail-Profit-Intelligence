import pytest

from helpers import small_orders


@pytest.fixture
def orders():
    return small_orders()

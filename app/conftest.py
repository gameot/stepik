import pytest
from django.contrib.auth.models import User

from orders.models import Order


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        username="test_customer",
        email="customer@example.com",
        password="testpassword",
    )


@pytest.fixture
def create_order(db, customer):
    def _create_order(customer_obj=customer, status=Order.STATUS_NEW, amount=100.50):
        return Order.objects.create(customer=customer_obj, amount=amount, status=status)

    return _create_order

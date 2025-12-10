from unittest.mock import patch

import pytest
from django.db import transaction

from finances.models import Operations
from finances.services import FinanceServices


@pytest.mark.django_db
class TestOperationsService:
    def test_add_charge_success(self, customer, create_order):
        amount = 50.00

        order = create_order(amount=amount, customer_obj=customer)

        finance_service = FinanceServices()
        operation = finance_service.add_charge(customer.pk, order.pk, amount)

        assert operation is not None
        assert Operations.objects.count() == 1
        assert operation.type == Operations.TYPE_CHARGE
        assert operation.amount == amount
        assert operation.customer_id == customer.pk
        assert operation.order_id == order.pk

    @patch("finances.services.logger")
    def test_add_charge_integrity_error(self, logger, customer, create_order):
        amount = 100.00

        order = create_order(amount=amount, customer_obj=customer)
        finance_service = FinanceServices()
        finance_service.add_charge(customer.pk, order.pk, amount)

        with transaction.atomic():
            operation = finance_service.add_charge(customer.pk, order.pk, amount)

        assert operation is None
        assert Operations.objects.count() == 1

        logger.error.assert_called_once()
        assert (
            f"Charge operation for customer {customer.pk} and order {order.pk} already exists"
            in logger.error.call_args[0][0]
        )

    def test_make_refund_success(self, customer, create_order):
        amount = 75.50
        order = create_order(amount=amount, customer_obj=customer)

        finance_service = FinanceServices()
        operation = finance_service.make_refund(customer.pk, order.pk, amount)

        assert operation is not None
        assert Operations.objects.count() == 1
        assert operation.type == Operations.TYPE_REFUND
        assert operation.amount == -amount
        assert operation.customer_id == customer.pk

    @patch("finances.services.logger")
    def test_make_refund_integrity_error(self, logger, customer, create_order):
        amount = 50.00
        order = create_order(amount=amount, customer_obj=customer)

        finance_service = FinanceServices()
        finance_service.make_refund(customer.pk, order.pk, amount)

        with transaction.atomic():
            operation = finance_service.make_refund(customer.pk, order.pk, amount)

        assert operation is None
        assert Operations.objects.count() == 1

        logger.error.assert_called_once()
        assert (
            f"Refund operation for customer {customer.pk} and order {order.pk} already exists"
            in logger.error.call_args[0][0]
        )

    @pytest.mark.parametrize("amount,result", [(10.00, -10.00), (-10.00, -10.00), (0.00, 0.00)])
    def test_process_refund_amount(self, amount, result):
        finance_service = FinanceServices()
        assert finance_service._process_refund_amount(amount) == result

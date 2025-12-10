import logging

from django.db import IntegrityError

from finances.models import Operations

logger = logging.getLogger(__name__)


class FinanceServices:
    @staticmethod
    def add_charge(customer_id, order_id, amount):
        try:
            return Operations.objects.create(
                customer_id=customer_id,
                order_id=order_id,
                amount=amount,
                type=Operations.TYPE_CHARGE,
            )
        except IntegrityError:
            logger.error(f"Charge operation for customer {customer_id} and order {order_id} already exists")

    def make_refund(self, customer_id, order_id, amount):
        try:
            return Operations.objects.create(
                customer_id=customer_id,
                order_id=order_id,
                amount=self._process_refund_amount(amount),
                type=Operations.TYPE_REFUND,
            )
        except IntegrityError:
            logger.error(f"Refund operation for customer {customer_id} and order {order_id} already exists")

    @staticmethod
    def _process_refund_amount(amount):
        return amount if amount < 0 else -amount

import logging
from abc import ABC, abstractmethod

from django.db import IntegrityError, transaction

from events.models import Event
from finances.services import FinanceServices
from orders.models import Order

logger = logging.getLogger(__name__)


class BaseEvent(ABC):
    @staticmethod
    def get_event(event_id):
        try:
            event = Event.objects.select_for_update().get(pk=event_id)
        except Event.DoesNotExist:
            logger.error(f"Event with id {event_id} does not exist")
        else:
            return event

    @staticmethod
    def _get_order(order_id):
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist:
            logger.error(f"Order with id {order_id} does not exist")
        else:
            return order

    def save(self, event):
        # event = Event.objects.create(**event)
        # return event
        ...

    @abstractmethod
    def process(self, event_id): ...


class ChargeEvent(BaseEvent):

    @transaction.atomic
    def process(self, event_id):
        event = self.get_event(event_id)
        if event:
            order = self._get_order(event.order_id)
            if order:
                if order.status == Order.STATUS_NEW:
                    order.status = Order.STATUS_PAID
                    order.save()
                    event.status = Event.STATUS_PROCESSED
                    event.save()
                    finance_service = FinanceServices()
                    # Amount берем из order чтобы упростить задачу. Будем считать,
                    # что amount не будет отличаться в заказе, событии и финансах.
                    # Хорошо бы конечно проверять amount
                    finance_service.add_charge(order.customer_id, order.id, order.amount)
                    logger.info(f"Order {order.id} is paid")
                    return
                else:
                    logger.error(
                        f"Can't change status. Receive event {event.provider_event_id} CHARGE, "
                        f"but order {event.id} not in status NEW"
                    )
            else:
                logger.error(f"Event {event.provider_event_id} can't be processed. Order {event.order_id} not found")


class DisputeOpenedEvent(BaseEvent):
    @transaction.atomic
    def process(self, event_id):
        event = self.get_event(event_id)
        if event:
            event.status = Event.STATUS_PROCESSED
            event.save()
            logger.info(f"Dispute opened for order {event.order_id}")


class RefundCreatedEvent(BaseEvent):
    @transaction.atomic
    def process(self, event_id):
        event = self.get_event(event_id)
        if event:
            order = self._get_order(event.order_id)
            if order:
                if order.status == Order.STATUS_PAID:
                    event.status = Event.STATUS_PROCESSED
                    event.save()
                    # Считаем что если пришел refund то заказ отменяется.
                    # Дальше надо запустить задачи по отмене заказа
                    order.status = Order.STATUS_CANCELED
                    order.save()
                    finance_service = FinanceServices()
                    # Ддя упрощения считаем, что возвращаем всю сумму заказа
                    finance_service.make_refund(order.customer_id, order.id, order.amount)
                    logger.info(f"Order {order.id} is refunded")
                else:
                    logger.error(
                        f"Can't make refund. Receive event {event.provider_event_id} REFUND, "
                        f"but order {event.id} not in status PAID"
                    )
            else:
                logger.error(f"Event {event.provider_event_id} can't be processed. Order {event.order_id} not found")


class EventService:
    event_processors = {
        "charge.succeeded": ChargeEvent,
        "dispute.opened": DisputeOpenedEvent,
        "refund.created": RefundCreatedEvent,
    }

    @transaction.atomic
    def save_event(self, provider_event_id, event_type, order_id, data):
        from events.tasks import process_event

        try:
            Event.objects.create(
                provider_event_id=provider_event_id,
                event_type=event_type,
                order_id=order_id,
                data=data,
            )
        except IntegrityError:
            logger.error(f"Event with id {provider_event_id} already exists")
        else:
            transaction.on_commit(lambda: process_event.delay(provider_event_id, event_type))

    def process_event(self, provider_event_id, event_type):
        processor = self.event_processors[event_type]()
        processor.process(provider_event_id)

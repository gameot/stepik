from unittest.mock import MagicMock, patch

import pytest

from events.models import Event
from events.services import BaseEvent, ChargeEvent, DisputeOpenedEvent, EventService, RefundCreatedEvent
from finances.models import Operations
from orders.models import Order


@pytest.mark.django_db
@patch("events.services.logger")
class TestBaseEventMethods:
    def test_get_event_success(self, logger, create_event):
        event_instance = create_event(provider_event_id="find-me")
        result = BaseEvent.get_event(event_instance.pk)
        assert result == event_instance
        logger.error.assert_not_called()

    def test_get_event_not_found(self, logger):
        non_existent_id = 999
        result = BaseEvent.get_event(non_existent_id)
        assert result is None
        logger.error.assert_called_once()
        assert f"Event with id {non_existent_id} does not exist" in logger.error.call_args[0][0]

    def test_get_order_success(self, logger, create_order):
        order_instance = create_order()
        result = BaseEvent._get_order(order_instance.id)
        assert result == order_instance
        logger.error.assert_not_called()

    def test_get_order_not_found(self, logger):
        non_existent_id = -999
        result = BaseEvent._get_order(non_existent_id)
        assert result is None
        logger.error.assert_called_once()
        assert f"Order with id {non_existent_id} does not exist" in logger.error.call_args[0][0]


@pytest.mark.django_db
class TestChargeEvent:
    def test_process_success(self, create_order, create_event):
        order = create_order(status=Order.STATUS_NEW)
        event = create_event(order_id=order.id, status=Event.STATUS_NEW)

        charge_event = ChargeEvent()
        charge_event.process(event.pk)

        order.refresh_from_db()
        event.refresh_from_db()

        operations = Operations.objects.filter(order=order.id, type=Operations.TYPE_CHARGE).count()

        assert order.status == Order.STATUS_PAID
        assert event.status == Event.STATUS_PROCESSED
        assert operations == 1

    @patch("events.services.logger")
    @pytest.mark.parametrize(
        "initial_status",
        [Order.STATUS_PAID, Order.STATUS_CANCELED, Order.STATUS_SHIPPED],
    )
    def test_process_fail_wrong_order_status(self, logger, create_order, create_event, initial_status):
        order = create_order(status=initial_status)
        event = create_event(order_id=order.id, status=Event.STATUS_NEW)

        charge_event = ChargeEvent()
        charge_event.process(event.pk)

        order.refresh_from_db()
        event.refresh_from_db()

        assert order.status == initial_status
        assert event.status == Event.STATUS_NEW
        logger.error.assert_called_once()

    @patch("events.services.logger")
    def test_process_event_not_found(self, logger):
        non_existent_event_id = -9999
        charge_event = ChargeEvent()
        charge_event.process(non_existent_event_id)

        logger.error.assert_called_once()
        assert f"Event with id {non_existent_event_id} does not exist" in logger.error.call_args[0][0]

    @patch("events.services.logger")
    def test_process_order_not_found(self, logger, create_event):
        non_existent_order_id = -9999
        event = create_event(order_id=non_existent_order_id, status=Event.STATUS_NEW)

        charge_event = ChargeEvent()
        charge_event.process(event.pk)

        event.refresh_from_db()

        assert logger.error.call_count == 2
        assert event.status == Event.STATUS_NEW


@pytest.mark.django_db
class TestDisputeOpenedEvent:
    @patch("events.services.logger")
    def test_event_process_success(self, logger, create_event):
        event = create_event()

        dispute_event = DisputeOpenedEvent()
        dispute_event.process(event.id)

        event.refresh_from_db()
        assert event.status == Event.STATUS_PROCESSED
        logger.info.assert_called_once()

    @patch("events.services.logger")
    def test_event_not_found(self, logger):
        non_existent_event_id = -9999

        dispute_event = DisputeOpenedEvent()
        dispute_event.process(non_existent_event_id)

        logger.error.assert_called_once()
        assert f"Event with id {non_existent_event_id} does not exist" in logger.error.call_args[0][0]


@pytest.mark.django_db
class TestRefundEvent:
    def test_process_success(self, create_order, create_event):
        order = create_order(status=Order.STATUS_PAID)
        event = create_event(order_id=order.id, status=Event.STATUS_NEW)

        refund_event = RefundCreatedEvent()
        refund_event.process(event.pk)

        order.refresh_from_db()
        event.refresh_from_db()

        operations = Operations.objects.filter(order=order.id, type=Operations.TYPE_REFUND).count()

        assert event.status == Event.STATUS_PROCESSED
        assert order.status == Order.STATUS_CANCELED
        assert operations == 1

    @patch("events.services.logger")
    @pytest.mark.parametrize(
        "initial_status",
        [Order.STATUS_NEW, Order.STATUS_CANCELED, Order.STATUS_SHIPPED],
    )
    def test_process_fail_wrong_order_status(self, logger, create_order, create_event, initial_status):
        order = create_order(status=initial_status)
        event = create_event(order_id=order.id, status=Event.STATUS_NEW)

        refund_event = RefundCreatedEvent()
        refund_event.process(event.pk)

        order.refresh_from_db()
        event.refresh_from_db()

        assert order.status == initial_status
        assert event.status == Event.STATUS_NEW
        logger.error.assert_called_once()

    @patch("events.services.logger")
    def test_process_event_not_found(self, logger):
        non_existent_event_id = -9999
        refund_event = RefundCreatedEvent()
        refund_event.process(non_existent_event_id)

        logger.error.assert_called_once()
        assert f"Event with id {non_existent_event_id} does not exist" in logger.error.call_args[0][0]

    @patch("events.services.logger")
    def test_process_order_not_found(self, logger, create_event):
        non_existent_order_id = -9999
        event = create_event(order_id=non_existent_order_id, status=Event.STATUS_NEW)

        refund_event = RefundCreatedEvent()
        refund_event.process(event.pk)

        event.refresh_from_db()

        assert logger.error.call_count == 2
        assert event.status == Event.STATUS_NEW


@pytest.mark.django_db
class TestEventService:
    @patch("events.services.transaction")
    @patch("events.services.logger")
    def test_save_event_success(self, logger, mock_transaction):
        event_service = EventService()
        event_data = {
            "provider_event_id": "prov_id_456",
            "event_type": "charge.succeeded",
            "order_id": "ORD-123",
            "data": '{"key": "value"}',
        }
        mock_process_event = MagicMock()
        with patch("events.tasks.process_event", mock_process_event, create=True):
            event_service.save_event(**event_data)

            assert Event.objects.count() == 1
            created_event = Event.objects.get()
            assert created_event.provider_event_id == event_data["provider_event_id"]
            assert created_event.event_type == event_data["event_type"]

            mock_transaction.on_commit.assert_called_once()

            on_commit_func = mock_transaction.on_commit.call_args[0][0]
            on_commit_func()

            mock_process_event.delay.assert_called_once_with(event_data["provider_event_id"], event_data["event_type"])

            logger.error.assert_not_called()

    @patch("events.services.transaction")
    @patch("events.services.logger")
    def test_save_event_integrity_error(self, logger, mock_transaction):
        event_service = EventService()
        event_data = {
            "provider_event_id": "prov_id_456",
            "event_type": "charge.succeeded",
            "order_id": "ORD-123",
            "data": '{"key": "value"}',
        }

        Event.objects.create(**event_data)
        assert Event.objects.count() == 1

        mock_process_event = MagicMock()
        with patch("events.tasks.process_event", mock_process_event, create=True):
            event_service.save_event(**event_data)

            assert Event.objects.count() == 1
            logger.error.assert_called_once_with(f"Event with id {event_data['provider_event_id']} already exists")
            mock_transaction.on_commit.assert_not_called()

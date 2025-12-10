from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from events.tasks import process_event


@pytest.mark.django_db
class TestProcessEvent:
    @patch("events.tasks.process_event.retry")
    @patch("events.tasks.logger")
    def test_process_event_success(self, mock_logger, process_event_retry):
        event_id = 123
        event_type = "charge.succeeded"
        with patch("events.tasks.EventService.process_event") as mock_service:
            process_event(event_id, event_type)

        mock_service.assert_called_once_with(event_id, event_type)

        assert process_event_retry.call_count == 0
        mock_logger.warning.assert_not_called()

    @patch("events.tasks.calculate_delay", return_value=8.5)
    @patch("events.tasks.EventService.process_event")
    @patch("events.tasks.logger")
    @pytest.mark.parametrize("status_code", [429, 500, 503, 599])
    def test_process_event_should_retry(self, mock_logger, mock_event_service, mock_delay, status_code):
        exc = HTTPError("url", status_code, "Test Error", None, None)

        mock_event_service.side_effect = exc

        with pytest.raises(Exception, match="Task can be retried"):
            process_event("event_id_retry", "charge")

        assert process_event.request.retries == 0
        mock_delay.assert_called_once_with(1)
        mock_logger.warning.assert_called_once()
        assert f"Ошибка HTTP {status_code}. Таска" in mock_logger.warning.call_args[0][0]

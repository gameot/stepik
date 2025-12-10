import logging
from urllib.error import HTTPError

from celery import shared_task
from django.conf import settings

from core.utils import calculate_delay
from events.services import EventService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=settings.MAX_RETRIES)
def process_event(self, provider_event_id, event_type):
    try:
        service = EventService()
        service.process_event(provider_event_id, event_type)
    except HTTPError as exc:
        status_code = exc.code
        if status_code == 429 or 500 <= status_code < 600:
            current_retry_count = self.request.retries + 1

            countdown = calculate_delay(current_retry_count)

            logger.warning(
                f"Ошибка HTTP {status_code}. Таска {self.request.id} будет перезапущена через {countdown:.2f} сек. "
                f"Попытка {current_retry_count} из {settings.MAX_RETRIES}."
            )
            raise self.retry(countdown=countdown)

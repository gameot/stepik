from django.db import models


class Event(models.Model):
    STATUS_NEW = "new"
    STATUS_PROCESSED = "processed"
    STATUS_ERROR = "error"

    STATUS_CHOICES = (
        (STATUS_NEW, "Новое"),
        (STATUS_PROCESSED, "Обработано"),
        (STATUS_ERROR, "Ошибка"),
    )

    provider_event_id = models.CharField(
        max_length=255, unique=True, db_index=True, verbose_name="ID события провайдера"
    )
    event_type = models.CharField(max_length=64, verbose_name="тип события")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        verbose_name="Статус обработки",
    )
    order_id = models.CharField(max_length=32, verbose_name="# заказа")
    data = models.TextField(verbose_name="Данные")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата")

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"
        ordering = ["-date"]

    def __str__(self):
        return f"Event ID: {self.provider_event_id} ({self.get_status_display()})"

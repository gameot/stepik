from django.conf import settings
from django.db import models


class Operations(models.Model):
    TYPE_CHARGE = "charge"
    TYPE_REFUND = "refund"

    TYPE_CHOICES = ((TYPE_CHARGE, "Списание"), (TYPE_REFUND, "Возврат"))

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="finances_operations",
        verbose_name="Покупатель",
    )

    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, verbose_name="Заказ")
    type = models.CharField(max_length=32, choices=TYPE_CHOICES, verbose_name="Тип операции")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата")

    class Meta:
        verbose_name = "Финансовая операция"
        verbose_name_plural = "Финансовые операции"
        unique_together = ("order", "type")
        ordering = ["-date"]

    def __str__(self):
        return f"Операция #{self.id} тип {self.type} ({self.date.strftime('%d-%m-%Y')})"

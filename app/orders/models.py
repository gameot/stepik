from django.conf import settings
from django.db import models


class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_PAID = "paid"
    STATUS_CANCELED = "canceled"
    STATUS_SHIPPED = "shipped"

    STATUS_CHOICES = (
        (STATUS_NEW, "Новый"),
        (STATUS_PAID, "Оплачен"),
        (STATUS_CANCELED, "Отменен"),
        (STATUS_SHIPPED, "Отгружен"),
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Покупатель",
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_NEW, verbose_name="Статус")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-date"]

    def __str__(self):
        return f"Заказ #{self.id} от {self.customer.username} ({self.date.strftime('%d-%m-%Y')})"

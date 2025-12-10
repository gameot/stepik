from rest_framework import serializers


class EventSerializer(serializers.Serializer):
    event_id = serializers.CharField(max_length=255, required=True, label="ID События")
    event_type = serializers.CharField(max_length=50, required=True, label="Тип События")
    date = serializers.DateTimeField(label="Дата События")
    order_id = serializers.CharField(max_length=32, required=True, label="# заказа")
    data = serializers.JSONField(required=True, label="Данные (Payload)")

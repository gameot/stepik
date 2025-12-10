from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from app.events.views import EventCreateAPIView

router = DefaultRouter()

urlpatterns = [
    url("events/create/", EventCreateAPIView.as_view(), name="event-create"),
]

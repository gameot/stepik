from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url("v1/webhooks/", include("events.urls", namespace="events")),
]

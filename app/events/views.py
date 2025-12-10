from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .authentication import HMACAuthentication
from .serializers import EventSerializer
from .services import EventService


class EventCreateAPIView(generics.CreateAPIView):
    authentication_classes = [HMACAuthentication]
    serializer_class = EventSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = EventService()
        service.save_event(
            provider_event_id=serializer.validated_data["event_id"],
            event_type=serializer.validated_data["event_type"],
            order_id=serializer.validated_data["order_id"],
            data=serializer.validated_data["data"],
        )

        headers = self.get_success_headers(serializer.validated_data)

        return Response(
            {
                "message": "Event received.",
                "event_id": serializer.validated_data["event_id"],
            },
            status=status.HTTP_200_OK,
            headers=headers,
        )

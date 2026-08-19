from rest_framework.generics import GenericAPIView

from core.responses import api_response
from .selectors import get_dashboard
from .serializers import DashboardSerializer


class DashboardView(GenericAPIView):
    serializer_class = DashboardSerializer

    def get(self, request):
        dashboard = get_dashboard(user=request.user)
        serializer = self.get_serializer(dashboard)
        return api_response(serializer.data, request=request)


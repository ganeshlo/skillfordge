from django.db import connection
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class LivenessSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()


class ReadinessSerializer(serializers.Serializer):
    status = serializers.CharField()
    database = serializers.CharField()


class LivenessView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LivenessSerializer

    def get(self, request):
        return Response({"status": "ok", "service": "learnos-api"})


class ReadinessView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ReadinessSerializer

    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return Response({"status": "ready", "database": "ok"})

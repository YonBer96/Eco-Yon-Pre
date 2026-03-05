from django.contrib.auth.models import User

from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response


# crea usuarios
class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # sin SessionAuth => sin CSRF

    def create(self, request, *args, **kwargs):
        username = (request.data.get("username") or "").strip()
        email = (request.data.get("email") or "").strip()
        password = request.data.get("password") or ""

        if not username or not password:
            return Response({"detail": "username y password son obligatorios"}, status=400)
        if User.objects.filter(username=username).exists():
            return Response({"detail": "El usuario ya existe"}, status=400)

        user = User.objects.create_user(username=username, email=email, password=password)
        return Response({"id": user.id, "username": user.username}, status=201)


# devuelve datos del usuario ya autenticado
class MeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_staff": u.is_staff,
        })